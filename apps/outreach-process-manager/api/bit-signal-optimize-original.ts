import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

// Initialize Neon client
const sql = neon(process.env.NEON_DB_URL || '');

interface BITSignalOptimizeRequest {
  trigger_type?: 'manual' | 'scheduled' | 'attribution_update';
  optimization_window?: number; // Days to look back
  min_sample_size?: number; // Minimum events for optimization
  dry_run?: boolean; // Preview changes without applying
}

interface SignalPerformance {
  signal_name: string;
  current_weight: number;
  new_weight: number;
  conversion_rate: number;
  sample_size: number;
  closed_won_count: number;
  weight_change: number;
  effectiveness_score: number;
}

interface BITSignalOptimizeResponse {
  status: 'success' | 'failed';
  model_version?: string;
  previous_version?: string;
  optimized_signals?: SignalPerformance[];
  summary?: {
    total_signals: number;
    signals_increased: number;
    signals_decreased: number;
    signals_unchanged: number;
    avg_conversion_rate: number;
  };
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<BITSignalOptimizeResponse>
) {
  // Accept both POST (manual trigger) and GET (scheduled/automated)
  if (req.method !== 'POST' && req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed. Only POST and GET are permitted.'
    });
  }

  try {
    const {
      trigger_type = 'manual',
      optimization_window = 90, // Default: 3 months
      min_sample_size = 10,
      dry_run = false
    } = req.method === 'POST' ? req.body : req.query as BITSignalOptimizeRequest;

    // Get current model version
    const currentVersion = await getCurrentBITModelVersion();

    // Generate new version number
    const newVersion = generateNewVersion();

    // Analyze signal performance
    const signalPerformance = await analyzeSignalPerformance(
      optimization_window,
      min_sample_size
    );

    if (signalPerformance.length === 0) {
      return res.status(200).json({
        status: 'success',
        message: 'No signals with sufficient data for optimization',
        model_version: currentVersion,
        optimized_signals: []
      });
    }

    // Calculate optimized weights
    const optimizedSignals = await optimizeWeights(signalPerformance);

    // Prepare summary statistics
    const summary = calculateSummary(optimizedSignals);

    if (dry_run) {
      // Return preview without applying changes
      return res.status(200).json({
        status: 'success',
        model_version: currentVersion,
        optimized_signals: optimizedSignals,
        summary,
        message: 'Dry run completed. Changes not applied.'
      });
    }

    // Begin transaction to apply optimizations
    await sql('BEGIN');

    try {
      // Update signal weights
      for (const signal of optimizedSignals) {
        await sql`
          UPDATE marketing.bit_signal_weights
          SET
            weight = ${signal.new_weight},
            model_version = ${newVersion},
            effectiveness_score = ${signal.effectiveness_score},
            conversion_rate = ${signal.conversion_rate},
            attribution_count = ${signal.closed_won_count},
            last_optimized = NOW(),
            last_updated = NOW()
          WHERE signal_name = ${signal.signal_name}
        `;

        // Log optimization in audit
        await sql`
          INSERT INTO marketing.campaign_audit_log (
            campaign_id,
            action,
            status,
            details,
            initiated_by,
            mcp_tool
          ) VALUES (
            'BIT_OPTIMIZATION_' || ${newVersion},
            'update',
            'success',
            ${JSON.stringify({
              signal: signal.signal_name,
              old_weight: signal.current_weight,
              new_weight: signal.new_weight,
              conversion_rate: signal.conversion_rate,
              sample_size: signal.sample_size
            })},
            ${trigger_type},
            'bit_optimizer'
          )
        `;
      }

      // Create new model version record
      await sql`
        INSERT INTO marketing.scoring_model_versions (
          model_type,
          version,
          model_config,
          avg_score,
          closed_won_correlation,
          closed_lost_correlation,
          is_active,
          activated_at,
          created_by,
          notes
        ) VALUES (
          'BIT',
          ${newVersion},
          ${JSON.stringify({
            weights: Object.fromEntries(
              optimizedSignals.map(s => [s.signal_name, s.new_weight])
            ),
            optimization_window,
            min_sample_size,
            trigger_type,
            summary
          })},
          ${summary.avg_conversion_rate},
          ${calculateWinCorrelation(optimizedSignals)},
          ${calculateLossCorrelation(optimizedSignals)},
          true,
          NOW(),
          'bit_signal_optimizer',
          ${`Automated optimization based on ${optimization_window} days of attribution data`}
        )
      `;

      // Deactivate previous version
      await sql`
        UPDATE marketing.scoring_model_versions
        SET is_active = false,
            deactivated_at = NOW()
        WHERE model_type = 'BIT'
        AND version = ${currentVersion}
      `;

      // Process pending BIT signals with new weights
      await processSignalBacklog(newVersion);

      // Commit transaction
      await sql('COMMIT');

      // Log success
      console.log(`[BIT Signal Optimize] SUCCESS: Applied version ${newVersion} with ${optimizedSignals.length} optimized signals`);

      return res.status(200).json({
        status: 'success',
        model_version: newVersion,
        previous_version: currentVersion,
        optimized_signals: optimizedSignals,
        summary,
        message: `Successfully optimized ${optimizedSignals.length} signals. New model version: ${newVersion}`
      });

    } catch (error) {
      // Rollback transaction
      await sql('ROLLBACK');
      throw error;
    }

  } catch (error) {
    console.error('[BIT Signal Optimize] ERROR:', error);

    return res.status(500).json({
      status: 'failed',
      message: 'Failed to optimize BIT signals',
      optimized_signals: []
    });
  }
}

// Get current active BIT model version
async function getCurrentBITModelVersion(): Promise<string> {
  try {
    const result = await sql`
      SELECT version
      FROM marketing.scoring_model_versions
      WHERE model_type = 'BIT'
      AND is_active = true
      LIMIT 1
    `;

    return result[0]?.version || '1.0.0';
  } catch (error) {
    console.error('[Get BIT Model Version] Error:', error);
    return '1.0.0';
  }
}

// Generate new version number
function generateNewVersion(): string {
  const timestamp = new Date().toISOString()
    .replace(/[-:]/g, '')
    .replace('T', '.')
    .substring(0, 15);
  return `1.1.${timestamp}`;
}

// Analyze signal performance based on attribution data
async function analyzeSignalPerformance(
  windowDays: number,
  minSampleSize: number
): Promise<any[]> {
  try {
    const result = await sql`
      WITH signal_performance AS (
        SELECT
          bsw.signal_name,
          bsw.weight as current_weight,
          bsw.signal_category,
          COUNT(DISTINCT bse.id) as total_events,
          COUNT(DISTINCT bse.company_unique_id) as unique_companies,
          COUNT(DISTINCT bse.person_unique_id) as unique_people,
          COUNT(DISTINCT af.id) FILTER (WHERE af.outcome = 'closed_won') as closed_won_count,
          COUNT(DISTINCT af.id) FILTER (WHERE af.outcome = 'closed_lost') as closed_lost_count,
          COUNT(DISTINCT af.id) FILTER (WHERE af.outcome = 'qualified') as qualified_count,
          AVG(af.deal_value) FILTER (WHERE af.outcome = 'closed_won') as avg_deal_value
        FROM marketing.bit_signal_weights bsw
        LEFT JOIN marketing.bit_signal_events bse
          ON bse.signal_name = bsw.signal_name
          AND bse.detected_at >= NOW() - INTERVAL '${windowDays} days'
        LEFT JOIN marketing.attribution_feedback af
          ON (af.person_unique_id = bse.person_unique_id
              OR af.company_unique_id = bse.company_unique_id)
          AND af.outcome_date >= bse.detected_at
          AND af.outcome_date <= bse.detected_at + INTERVAL '30 days'
        GROUP BY bsw.signal_name, bsw.weight, bsw.signal_category
      )
      SELECT
        signal_name,
        current_weight,
        signal_category,
        total_events,
        unique_companies,
        unique_people,
        closed_won_count,
        closed_lost_count,
        qualified_count,
        avg_deal_value,
        CASE
          WHEN total_events > 0 THEN
            (closed_won_count::NUMERIC * 100.0 / total_events)
          ELSE 0
        END as conversion_rate,
        CASE
          WHEN total_events > 0 THEN
            ((closed_won_count * 2 + qualified_count) * 100.0 / total_events)
          ELSE 0
        END as effectiveness_score
      FROM signal_performance
      WHERE total_events >= ${minSampleSize}
      ORDER BY conversion_rate DESC
    `;

    return result;
  } catch (error) {
    console.error('[Analyze Signal Performance] Error:', error);
    return [];
  }
}

// Optimize weights based on performance
async function optimizeWeights(
  signalPerformance: any[]
): Promise<SignalPerformance[]> {
  const optimizedSignals: SignalPerformance[] = [];

  for (const signal of signalPerformance) {
    let newWeight = signal.current_weight;
    const conversionRate = parseFloat(signal.conversion_rate) || 0;
    const effectivenessScore = parseFloat(signal.effectiveness_score) || 0;

    // Weight optimization algorithm
    // Based on conversion rate and effectiveness
    if (conversionRate > 15) {
      // High performer: increase weight by 20-30%
      newWeight = Math.min(100, signal.current_weight * 1.25);
    } else if (conversionRate > 10) {
      // Good performer: increase weight by 10-15%
      newWeight = Math.min(95, signal.current_weight * 1.12);
    } else if (conversionRate > 5) {
      // Average performer: slight increase or maintain
      newWeight = Math.min(90, signal.current_weight * 1.05);
    } else if (conversionRate > 2) {
      // Below average: slight decrease
      newWeight = Math.max(20, signal.current_weight * 0.95);
    } else {
      // Poor performer: significant decrease
      newWeight = Math.max(10, signal.current_weight * 0.8);
    }

    // Apply category-based adjustments
    if (signal.signal_category === 'demo_request' && conversionRate > 0) {
      // Demo requests are high-value, don't reduce below 70
      newWeight = Math.max(70, newWeight);
    } else if (signal.signal_category === 'funding' && signal.avg_deal_value > 100000) {
      // High-value funding signals get a boost
      newWeight = Math.min(100, newWeight * 1.1);
    } else if (signal.signal_category === 'engagement' && signal.total_events > 100) {
      // High-volume engagement signals are normalized
      newWeight = Math.min(75, newWeight);
    }

    // Round to nearest 5 for cleaner weights
    newWeight = Math.round(newWeight / 5) * 5;

    optimizedSignals.push({
      signal_name: signal.signal_name,
      current_weight: signal.current_weight,
      new_weight: newWeight,
      conversion_rate: conversionRate,
      sample_size: signal.total_events,
      closed_won_count: signal.closed_won_count,
      weight_change: newWeight - signal.current_weight,
      effectiveness_score: effectivenessScore
    });
  }

  return optimizedSignals;
}

// Calculate summary statistics
function calculateSummary(optimizedSignals: SignalPerformance[]) {
  const increased = optimizedSignals.filter(s => s.weight_change > 0).length;
  const decreased = optimizedSignals.filter(s => s.weight_change < 0).length;
  const unchanged = optimizedSignals.filter(s => s.weight_change === 0).length;

  const avgConversionRate = optimizedSignals.reduce(
    (sum, s) => sum + s.conversion_rate, 0
  ) / optimizedSignals.length;

  return {
    total_signals: optimizedSignals.length,
    signals_increased: increased,
    signals_decreased: decreased,
    signals_unchanged: unchanged,
    avg_conversion_rate: Math.round(avgConversionRate * 100) / 100
  };
}

// Calculate win correlation for model metrics
function calculateWinCorrelation(signals: SignalPerformance[]): number {
  const highWeightSignals = signals.filter(s => s.new_weight >= 70);
  if (highWeightSignals.length === 0) return 0;

  const avgWinRate = highWeightSignals.reduce(
    (sum, s) => sum + s.conversion_rate, 0
  ) / highWeightSignals.length;

  return Math.round(avgWinRate * 100) / 100;
}

// Calculate loss correlation for model metrics
function calculateLossCorrelation(signals: SignalPerformance[]): number {
  const lowWeightSignals = signals.filter(s => s.new_weight <= 30);
  if (lowWeightSignals.length === 0) return 0;

  const avgLossRate = lowWeightSignals.reduce(
    (sum, s) => sum + (100 - s.conversion_rate), 0
  ) / lowWeightSignals.length;

  return Math.round(avgLossRate * 100) / 100;
}

// Process pending BIT signals with new weights
async function processSignalBacklog(modelVersion: string): Promise<void> {
  try {
    // Find unprocessed high-weight signals
    const pendingSignals = await sql`
      SELECT DISTINCT
        bse.id,
        bse.signal_name,
        bse.company_unique_id,
        bse.person_unique_id,
        bsw.weight
      FROM marketing.bit_signal_events bse
      JOIN marketing.bit_signal_weights bsw ON bsw.signal_name = bse.signal_name
      WHERE bse.processed = false
      AND bsw.weight >= 70
      AND bse.detected_at >= NOW() - INTERVAL '7 days'
      ORDER BY bsw.weight DESC, bse.detected_at DESC
      LIMIT 50
    `;

    // Mark high-priority signals for campaign creation
    for (const signal of pendingSignals) {
      if (signal.weight >= 85) {
        await sql`
          INSERT INTO marketing.campaign_audit_log (
            campaign_id,
            action,
            status,
            details,
            mcp_tool
          ) VALUES (
            'BIT_SIGNAL_' || ${signal.id},
            'create',
            'pending',
            ${JSON.stringify({
              trigger: 'high_weight_bit_signal',
              signal_name: signal.signal_name,
              weight: signal.weight,
              company_id: signal.company_unique_id,
              person_id: signal.person_unique_id,
              model_version: modelVersion
            })},
            'bit_optimizer'
          )
        `;

        // Mark as processed
        await sql`
          UPDATE marketing.bit_signal_events
          SET processed = true,
              processed_at = NOW()
          WHERE id = ${signal.id}
        `;
      }
    }
  } catch (error) {
    console.error('[Process Signal Backlog] Error:', error);
  }
}