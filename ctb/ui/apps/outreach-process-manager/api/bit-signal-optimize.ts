/**
 * Doctrine Spec:
 * - Barton ID: 08.04.02.07.10000.003
 * - Altitude: 10000 (Execution Layer)
 * - Input: optimization parameters and attribution feedback
 * - Output: optimized BIT signal weights
 * - MCP: Composio (Neon integrated)
 */
import type { VercelRequest, VercelResponse } from '@vercel/node';
import ComposioNeonBridge from './lib/composio-neon-bridge.js';

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
  performance_change: number;
}

interface OptimizationResponse {
  status: 'success' | 'failed';
  optimization_id?: string;
  signals_optimized?: number;
  performance_improvements?: SignalPerformance[];
  model_version?: string;
  dry_run?: boolean;
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<OptimizationResponse>
) {
  // Doctrine enforcement: Only POST method allowed
  if (req.method !== 'POST') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed. Only POST is permitted by doctrine.'
    });
  }

  try {
    // Initialize MCP bridge for Barton Doctrine compliance
    const mcpBridge = new ComposioNeonBridge();
    await mcpBridge.initialize();

    const {
      trigger_type = 'manual',
      optimization_window = 30,
      min_sample_size = 50,
      dry_run = false
    } = req.body as BITSignalOptimizeRequest;

    // Generate optimization ID
    const optimizationId = `opt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    console.log(`[BIT Signal Optimize] Starting optimization ${optimizationId} via MCP`);
    console.log(`Window: ${optimization_window} days, Min samples: ${min_sample_size}, Dry run: ${dry_run}`);

    // Get current signal weights via MCP
    const currentWeightsQuery = `
      SELECT
        signal_name,
        weight as current_weight,
        model_version,
        last_updated
      FROM marketing.bit_signal_weights
      WHERE is_active = true
      ORDER BY signal_name
    `;

    const currentWeightsResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: currentWeightsQuery,
      mode: 'read'
    });

    if (!currentWeightsResult.success) {
      throw new Error(`Failed to fetch current weights: ${currentWeightsResult.error}`);
    }

    const currentWeights = currentWeightsResult.data.rows;

    // Get attribution feedback for performance analysis via MCP
    const attributionQuery = `
      SELECT
        bse.signal_name,
        bse.signal_value,
        af.outcome,
        af.outcome_date,
        bse.created_at as signal_date
      FROM marketing.bit_signal_events bse
      JOIN marketing.attribution_feedback af ON af.person_unique_id = bse.person_unique_id
      WHERE bse.created_at >= NOW() - INTERVAL '${optimization_window} days'
      AND af.outcome_date >= NOW() - INTERVAL '${optimization_window} days'
      AND af.outcome IN ('closed_won', 'qualified', 'demo_completed')
      ORDER BY bse.signal_name, af.outcome_date
    `;

    const attributionResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: attributionQuery,
      mode: 'read'
    });

    if (!attributionResult.success) {
      throw new Error(`Failed to fetch attribution data: ${attributionResult.error}`);
    }

    const attributionData = attributionResult.data.rows;

    // Calculate performance metrics for each signal
    const signalPerformance = await calculateSignalPerformance(
      currentWeights,
      attributionData,
      min_sample_size
    );

    // Filter signals with sufficient data
    const optimizableSignals = signalPerformance.filter(
      signal => signal.sample_size >= min_sample_size
    );

    if (optimizableSignals.length === 0) {
      return res.status(200).json({
        status: 'success',
        optimization_id: optimizationId,
        signals_optimized: 0,
        performance_improvements: [],
        dry_run,
        message: `No signals with sufficient data (min ${min_sample_size} samples) for optimization`
      });
    }

    // Calculate new weights using conversion rate optimization
    const optimizedSignals = optimizableSignals.map(signal => {
      const performanceMultiplier = Math.max(0.1, Math.min(3.0, signal.conversion_rate / 0.1));
      const newWeight = Math.round(signal.current_weight * performanceMultiplier * 100) / 100;

      return {
        ...signal,
        new_weight: Math.max(0.01, Math.min(1.0, newWeight)),
        performance_change: ((newWeight - signal.current_weight) / signal.current_weight) * 100
      };
    });

    // Begin transaction via MCP if not dry run
    if (!dry_run) {
      await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
        sql: 'BEGIN',
        mode: 'write'
      });

      try {
        // Get current model version
        const modelVersionQuery = `
          SELECT version
          FROM marketing.scoring_model_versions
          WHERE model_type = 'BIT'
          AND is_active = true
          LIMIT 1
        `;

        const modelVersionResult = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
          sql: modelVersionQuery,
          mode: 'read'
        });

        const currentModelVersion = modelVersionResult.success && modelVersionResult.data.rows.length > 0
          ? modelVersionResult.data.rows[0].version
          : '1.0.0';

        // Update signal weights via MCP
        for (const signal of optimizedSignals) {
          const updateQuery = `
            UPDATE marketing.bit_signal_weights
            SET
              weight = ${signal.new_weight},
              last_updated = NOW(),
              optimization_id = '${optimizationId}',
              updated_at = NOW()
            WHERE signal_name = '${signal.signal_name}'
            AND is_active = true
          `;

          await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
            sql: updateQuery,
            mode: 'write'
          });
        }

        // Log optimization history via MCP
        for (const signal of optimizedSignals) {
          const historyQuery = `
            INSERT INTO marketing.optimization_history (
              optimization_id,
              signal_name,
              previous_weight,
              new_weight,
              conversion_rate,
              sample_size,
              performance_change,
              trigger_type,
              model_version,
              optimization_date
            ) VALUES (
              '${optimizationId}',
              '${signal.signal_name}',
              ${signal.current_weight},
              ${signal.new_weight},
              ${signal.conversion_rate},
              ${signal.sample_size},
              ${signal.performance_change},
              '${trigger_type}',
              '${currentModelVersion}',
              NOW()
            )
          `;

          await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
            sql: historyQuery,
            mode: 'write'
          });
        }

        // Commit transaction via MCP
        await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
          sql: 'COMMIT',
          mode: 'write'
        });

        console.log(`[BIT Signal Optimize] SUCCESS: Optimized ${optimizedSignals.length} signals via MCP`);

      } catch (error) {
        // Rollback transaction via MCP
        await mcpBridge.executeNeonOperation('EXECUTE_SQL', {
          sql: 'ROLLBACK',
          mode: 'write'
        });
        throw error;
      }
    }

    return res.status(200).json({
      status: 'success',
      optimization_id: optimizationId,
      signals_optimized: optimizedSignals.length,
      performance_improvements: optimizedSignals,
      model_version: await getCurrentModelVersion(mcpBridge),
      dry_run,
      message: dry_run
        ? `Dry run complete: ${optimizedSignals.length} signals would be optimized`
        : `Successfully optimized ${optimizedSignals.length} signals via MCP`
    });

  } catch (error) {
    console.error('[BIT Signal Optimize] MCP ERROR:', error);

    return res.status(500).json({
      status: 'failed',
      message: 'Failed to optimize BIT signals via MCP'
    });
  }
}

// Calculate signal performance from attribution data
async function calculateSignalPerformance(
  currentWeights: any[],
  attributionData: any[],
  minSampleSize: number
): Promise<SignalPerformance[]> {
  const signalPerformance: SignalPerformance[] = [];

  // Group attribution data by signal
  const signalGroups = attributionData.reduce((groups, row) => {
    if (!groups[row.signal_name]) {
      groups[row.signal_name] = [];
    }
    groups[row.signal_name].push(row);
    return groups;
  }, {} as Record<string, any[]>);

  // Calculate performance for each signal
  for (const weight of currentWeights) {
    const signalData = signalGroups[weight.signal_name] || [];

    if (signalData.length < minSampleSize) {
      continue;
    }

    const closedWonCount = signalData.filter(d => d.outcome === 'closed_won').length;
    const conversionRate = closedWonCount / signalData.length;

    signalPerformance.push({
      signal_name: weight.signal_name,
      current_weight: weight.current_weight,
      new_weight: weight.current_weight, // Will be calculated later
      conversion_rate: conversionRate,
      sample_size: signalData.length,
      closed_won_count: closedWonCount,
      performance_change: 0 // Will be calculated later
    });
  }

  return signalPerformance;
}

// Get current model version via MCP
async function getCurrentModelVersion(mcpBridge: any): Promise<string> {
  try {
    const query = `
      SELECT version
      FROM marketing.scoring_model_versions
      WHERE model_type = 'BIT'
      AND is_active = true
      LIMIT 1
    `;

    const result = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: query,
      mode: 'read'
    });

    return result.success && result.data.rows.length > 0 ? result.data.rows[0].version : '1.0.0';
  } catch (error) {
    console.error('[Get Model Version] MCP Error:', error);
    return '1.0.0';
  }
}