/**
 * Doctrine Spec:
 * - Barton ID: 05.01.01.07.10000.011
 * - Altitude: 10000 (Execution Layer)
 * - Input: attribution query parameters and filters
 * - Output: attribution analytics and performance data
 * - MCP: Composio (Neon integrated)
 */
/**
 * Attribution Analytics API - Performance Insights for PLE & BIT
 * Provides analytics and insights from closed-loop attribution data
 *
 * Endpoints:
 * - GET /api/attribution-analytics?type=summary
 * - GET /api/attribution-analytics?type=ple_performance
 * - GET /api/attribution-analytics?type=bit_signals
 * - GET /api/attribution-analytics?type=revenue_attribution
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface AttributionSummary {
  total_attributions: number;
  outcomes: {
    closed_won: { count: number; revenue: number };
    closed_lost: { count: number; potential_revenue: number };
    nurture: { count: number };
    churn: { count: number };
    qualified: { count: number };
    disqualified: { count: number };
  };
  conversion_rates: {
    win_rate: number;
    qualification_rate: number;
    churn_rate: number;
  };
  revenue_metrics: {
    total_revenue: number;
    average_deal_size: number;
    revenue_per_attribution: number;
  };
  time_metrics: {
    average_sales_cycle_days: number;
    average_touchpoints_to_close: number;
  };
}

interface PLEPerformance {
  model_accuracy: {
    overall_accuracy: number;
    accuracy_by_outcome: Record<string, number>;
    accuracy_trend: Array<{ date: string; accuracy: number }>;
  };
  scoring_impact: {
    score_improvements: number;
    accurate_predictions: number;
    prediction_errors: number;
  };
  segment_performance: {
    hot_leads_conversion: number;
    warm_leads_conversion: number;
    cold_leads_conversion: number;
  };
}

interface BITSignalPerformance {
  signal_effectiveness: Array<{
    signal_type: string;
    correlation_strength: number;
    true_positive_rate: number;
    false_positive_rate: number;
    weight_adjustment: number;
    outcomes_influenced: number;
  }>;
  top_performing_signals: string[];
  underperforming_signals: string[];
  signal_weight_changes: Array<{
    signal_type: string;
    weight_before: number;
    weight_after: number;
    reason: string;
  }>;
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const { type = 'summary', date_from, date_to } = req.query;

    console.log(`[ATTRIBUTION-ANALYTICS] Fetching ${type} analytics`);

    switch (type) {
      case 'summary':
        const summary = await getAttributionSummary(bridge, date_from, date_to);
        return res.status(200).json({ success: true, data: summary });

      case 'ple_performance':
        const plePerformance = await getPLEPerformance(bridge, date_from, date_to);
        return res.status(200).json({ success: true, data: plePerformance });

      case 'bit_signals':
        const bitPerformance = await getBITSignalPerformance(bridge, date_from, date_to);
        return res.status(200).json({ success: true, data: bitPerformance });

      case 'revenue_attribution':
        const revenueData = await getRevenueAttribution(bridge, date_from, date_to);
        return res.status(200).json({ success: true, data: revenueData });

      default:
        return res.status(400).json({ error: 'Invalid analytics type' });
    }

  } catch (error: any) {
    console.error('[ATTRIBUTION-ANALYTICS] Failed:', error);
    return res.status(500).json({
      error: 'Attribution analytics failed',
      message: error.message
    });
  }
}

/**
 * Get comprehensive attribution summary
 */
async function getAttributionSummary(
  bridge: StandardComposioNeonBridge,
  dateFrom?: string,
  dateTo?: string
): Promise<AttributionSummary> {
  const dateFilter = buildDateFilter(dateFrom, dateTo);

  // Get outcome counts and revenue
  const outcomesQuery = `
    SELECT
      outcome,
      COUNT(*) as count,
      SUM(COALESCE(revenue_amount, 0)) as total_revenue,
      AVG(COALESCE(revenue_amount, 0)) as avg_revenue,
      AVG(COALESCE(sales_cycle_days, 0)) as avg_sales_cycle,
      AVG(COALESCE(touchpoints_to_close, 0)) as avg_touchpoints
    FROM marketing.closed_loop_attribution
    WHERE 1=1 ${dateFilter}
    GROUP BY outcome
  `;

  const outcomesResult = await bridge.query(outcomesQuery);
  const outcomeData = outcomesResult.rows;

  // Build outcome summary
  const outcomes = {
    closed_won: { count: 0, revenue: 0 },
    closed_lost: { count: 0, potential_revenue: 0 },
    nurture: { count: 0 },
    churn: { count: 0 },
    qualified: { count: 0 },
    disqualified: { count: 0 }
  };

  let totalRevenue = 0;
  let totalAttributions = 0;
  let totalSalesCycle = 0;
  let totalTouchpoints = 0;
  let salesCycleCount = 0;
  let touchpointCount = 0;

  outcomeData.forEach(row => {
    const outcome = row.outcome as keyof typeof outcomes;
    if (outcomes[outcome]) {
      if (outcome === 'closed_won') {
        outcomes[outcome].count = parseInt(row.count);
        outcomes[outcome].revenue = parseFloat(row.total_revenue);
        totalRevenue += parseFloat(row.total_revenue);
      } else if (outcome === 'closed_lost') {
        outcomes[outcome].count = parseInt(row.count);
        outcomes[outcome].potential_revenue = parseFloat(row.total_revenue);
      } else {
        (outcomes[outcome] as any).count = parseInt(row.count);
      }
    }

    totalAttributions += parseInt(row.count);
    if (row.avg_sales_cycle > 0) {
      totalSalesCycle += parseFloat(row.avg_sales_cycle) * parseInt(row.count);
      salesCycleCount += parseInt(row.count);
    }
    if (row.avg_touchpoints > 0) {
      totalTouchpoints += parseFloat(row.avg_touchpoints) * parseInt(row.count);
      touchpointCount += parseInt(row.count);
    }
  });

  // Calculate rates
  const totalWon = outcomes.closed_won.count;
  const totalLost = outcomes.closed_lost.count;
  const totalQualified = outcomes.qualified.count;
  const totalChurn = outcomes.churn.count;

  const winRate = totalWon + totalLost > 0 ? (totalWon / (totalWon + totalLost)) * 100 : 0;
  const qualificationRate = totalAttributions > 0 ? (totalQualified / totalAttributions) * 100 : 0;
  const churnRate = totalAttributions > 0 ? (totalChurn / totalAttributions) * 100 : 0;

  return {
    total_attributions: totalAttributions,
    outcomes,
    conversion_rates: {
      win_rate: Math.round(winRate * 100) / 100,
      qualification_rate: Math.round(qualificationRate * 100) / 100,
      churn_rate: Math.round(churnRate * 100) / 100
    },
    revenue_metrics: {
      total_revenue: totalRevenue,
      average_deal_size: totalWon > 0 ? totalRevenue / totalWon : 0,
      revenue_per_attribution: totalAttributions > 0 ? totalRevenue / totalAttributions : 0
    },
    time_metrics: {
      average_sales_cycle_days: salesCycleCount > 0 ? totalSalesCycle / salesCycleCount : 0,
      average_touchpoints_to_close: touchpointCount > 0 ? totalTouchpoints / touchpointCount : 0
    }
  };
}

/**
 * Get PLE (Perpetual Lead Engine) performance metrics
 */
async function getPLEPerformance(
  bridge: StandardComposioNeonBridge,
  dateFrom?: string,
  dateTo?: string
): Promise<PLEPerformance> {
  const dateFilter = buildDateFilter(dateFrom, dateTo, 'created_at');

  // Get overall prediction accuracy
  const accuracyQuery = `
    SELECT
      AVG(prediction_accuracy) as overall_accuracy,
      attribution_outcome,
      AVG(prediction_accuracy) as outcome_accuracy,
      COUNT(*) as predictions
    FROM marketing.ple_lead_scoring_history
    WHERE prediction_accuracy IS NOT NULL ${dateFilter}
    GROUP BY attribution_outcome
  `;

  const accuracyResult = await bridge.query(accuracyQuery);
  const accuracyData = accuracyResult.rows;

  const overallAccuracy = accuracyData.length > 0
    ? accuracyData.reduce((sum, row) => sum + parseFloat(row.overall_accuracy) * parseInt(row.predictions), 0) /
      accuracyData.reduce((sum, row) => sum + parseInt(row.predictions), 0)
    : 0;

  const accuracyByOutcome: Record<string, number> = {};
  accuracyData.forEach(row => {
    accuracyByOutcome[row.attribution_outcome] = Math.round(parseFloat(row.outcome_accuracy) * 100) / 100;
  });

  // Get accuracy trend over time
  const trendQuery = `
    SELECT
      DATE_TRUNC('week', created_at) as week,
      AVG(prediction_accuracy) as accuracy
    FROM marketing.ple_lead_scoring_history
    WHERE prediction_accuracy IS NOT NULL ${dateFilter}
    GROUP BY DATE_TRUNC('week', created_at)
    ORDER BY week DESC
    LIMIT 12
  `;

  const trendResult = await bridge.query(trendQuery);
  const accuracyTrend = trendResult.rows.map(row => ({
    date: row.week.toISOString().split('T')[0],
    accuracy: Math.round(parseFloat(row.accuracy) * 100) / 100
  }));

  // Get scoring impact metrics
  const impactQuery = `
    SELECT
      COUNT(*) FILTER (WHERE score_after > score_before) as score_improvements,
      COUNT(*) FILTER (WHERE prediction_accuracy >= 80) as accurate_predictions,
      COUNT(*) FILTER (WHERE prediction_accuracy < 50) as prediction_errors
    FROM marketing.ple_lead_scoring_history
    WHERE 1=1 ${dateFilter}
  `;

  const impactResult = await bridge.query(impactQuery);
  const impactData = impactResult.rows[0];

  return {
    model_accuracy: {
      overall_accuracy: Math.round(overallAccuracy * 100) / 100,
      accuracy_by_outcome: accuracyByOutcome,
      accuracy_trend: accuracyTrend.reverse()
    },
    scoring_impact: {
      score_improvements: parseInt(impactData.score_improvements),
      accurate_predictions: parseInt(impactData.accurate_predictions),
      prediction_errors: parseInt(impactData.prediction_errors)
    },
    segment_performance: {
      hot_leads_conversion: 0, // TODO: Calculate from master table segments
      warm_leads_conversion: 0,
      cold_leads_conversion: 0
    }
  };
}

/**
 * Get BIT (Buyer Intent Trigger) signal performance
 */
async function getBITSignalPerformance(
  bridge: StandardComposioNeonBridge,
  dateFrom?: string,
  dateTo?: string
): Promise<BITSignalPerformance> {
  const dateFilter = buildDateFilter(dateFrom, dateTo, 'updated_at');

  // Get signal effectiveness metrics
  const signalQuery = `
    SELECT
      signal_type,
      AVG(correlation_strength) as avg_correlation,
      AVG(true_positive_rate) as avg_true_positive_rate,
      AVG(false_positive_rate) as avg_false_positive_rate,
      AVG(weight_after - weight_before) as avg_weight_adjustment,
      COUNT(*) as outcomes_influenced
    FROM marketing.bit_signal_performance
    WHERE attribution_outcome IS NOT NULL ${dateFilter}
    GROUP BY signal_type
    HAVING COUNT(*) >= 3  -- Only signals with sufficient data
    ORDER BY avg_correlation DESC
  `;

  const signalResult = await bridge.query(signalQuery);
  const signalData = signalResult.rows;

  const signalEffectiveness = signalData.map(row => ({
    signal_type: row.signal_type,
    correlation_strength: Math.round(parseFloat(row.avg_correlation || 0) * 100) / 100,
    true_positive_rate: Math.round(parseFloat(row.avg_true_positive_rate || 0) * 100) / 100,
    false_positive_rate: Math.round(parseFloat(row.avg_false_positive_rate || 0) * 100) / 100,
    weight_adjustment: Math.round(parseFloat(row.avg_weight_adjustment || 0) * 10000) / 10000,
    outcomes_influenced: parseInt(row.outcomes_influenced)
  }));

  // Get top and underperforming signals
  const topPerforming = signalEffectiveness
    .filter(s => s.correlation_strength >= 0.7)
    .slice(0, 5)
    .map(s => s.signal_type);

  const underperforming = signalEffectiveness
    .filter(s => s.correlation_strength < 0.3 && s.outcomes_influenced >= 5)
    .slice(0, 5)
    .map(s => s.signal_type);

  // Get recent weight changes
  const weightChangesQuery = `
    SELECT
      signal_type,
      weight_before,
      weight_after,
      weight_adjustment_reason
    FROM marketing.bit_signal_performance
    WHERE weight_before IS NOT NULL
      AND weight_after IS NOT NULL
      AND ABS(weight_after - weight_before) > 0.001 ${dateFilter}
    ORDER BY updated_at DESC
    LIMIT 20
  `;

  const weightChangesResult = await bridge.query(weightChangesQuery);
  const signalWeightChanges = weightChangesResult.rows.map(row => ({
    signal_type: row.signal_type,
    weight_before: Math.round(parseFloat(row.weight_before) * 10000) / 10000,
    weight_after: Math.round(parseFloat(row.weight_after) * 10000) / 10000,
    reason: row.weight_adjustment_reason
  }));

  return {
    signal_effectiveness: signalEffectiveness,
    top_performing_signals: topPerforming,
    underperforming_signals: underperforming,
    signal_weight_changes: signalWeightChanges
  };
}

/**
 * Get revenue attribution data
 */
async function getRevenueAttribution(
  bridge: StandardComposioNeonBridge,
  dateFrom?: string,
  dateTo?: string
): Promise<any> {
  const dateFilter = buildDateFilter(dateFrom, dateTo);

  const revenueQuery = `
    SELECT
      crm_system,
      outcome,
      COUNT(*) as deals,
      SUM(COALESCE(revenue_amount, 0)) as total_revenue,
      AVG(COALESCE(revenue_amount, 0)) as avg_revenue,
      DATE_TRUNC('month', actual_close_date) as month
    FROM marketing.closed_loop_attribution
    WHERE revenue_amount > 0 ${dateFilter}
    GROUP BY crm_system, outcome, DATE_TRUNC('month', actual_close_date)
    ORDER BY month DESC, total_revenue DESC
  `;

  const revenueResult = await bridge.query(revenueQuery);
  return {
    revenue_by_system: revenueResult.rows
  };
}

/**
 * Helper function to build date filter
 */
function buildDateFilter(dateFrom?: string, dateTo?: string, dateColumn: string = 'created_at'): string {
  let filter = '';

  if (dateFrom) {
    filter += ` AND ${dateColumn} >= '${dateFrom}'`;
  }

  if (dateTo) {
    filter += ` AND ${dateColumn} <= '${dateTo}'`;
  }

  return filter;
}