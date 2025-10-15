/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.002
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Dashboard summary endpoint
 * - Query Target: shq.dashboard_summary view/function
 */

import express from 'express';
import sql from '../../utils/neonClient.js';

const router = express.Router();

/**
 * GET /neon/dashboard-summary
 * Returns KPIs for Control Tower & Executive Overview
 *
 * Response format:
 * {
 *   success: boolean,
 *   data: {
 *     errorStats: { critical, high, medium, low, total },
 *     processStats: { started, completed, failed, successRate },
 *     agentStats: { active, failing, healthyPercentage },
 *     performanceMetrics: { avgDuration, errorRate, throughput }
 *   }
 * }
 */
router.get('/dashboard-summary', async (req, res) => {
  try {
    console.log('📊 Fetching dashboard summary...');

    // Get time window (default 24 hours)
    const hours = parseInt(req.query.hours) || 24;
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    // Query error statistics
    const errorStats = await sql`
      SELECT
        COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END)::int as critical,
        COUNT(CASE WHEN severity = 'HIGH' THEN 1 END)::int as high,
        COUNT(CASE WHEN severity = 'MEDIUM' THEN 1 END)::int as medium,
        COUNT(CASE WHEN severity = 'LOW' THEN 1 END)::int as low,
        COUNT(*)::int as total,
        COUNT(CASE WHEN resolved_at IS NULL THEN 1 END)::int as unresolved
      FROM shq.master_error_log
      WHERE occurred_at >= ${windowStart}::timestamptz
    `;

    // Query process registry statistics (if table exists)
    const processStats = await sql`
      SELECT
        COUNT(*)::int as total_processes,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::int as completed,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::int as failed,
        COUNT(CASE WHEN status = 'running' THEN 1 END)::int as running,
        ROUND(
          COUNT(CASE WHEN status = 'completed' THEN 1 END)::numeric /
          NULLIF(COUNT(*)::numeric, 0) * 100,
          2
        ) as success_rate
      FROM shq.process_registry
      WHERE created_at >= ${windowStart}::timestamptz
    `.catch(() => [{
      total_processes: 0,
      completed: 0,
      failed: 0,
      running: 0,
      success_rate: 0
    }]);

    // Query agent statistics
    const agentStats = await sql`
      SELECT
        COUNT(DISTINCT agent_id)::int as total_agents,
        COUNT(DISTINCT CASE WHEN severity IN ('CRITICAL', 'HIGH') THEN agent_id END)::int as failing_agents
      FROM shq.master_error_log
      WHERE occurred_at >= ${windowStart}::timestamptz
    `;

    // Calculate performance metrics
    const performanceMetrics = await sql`
      SELECT
        ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - occurred_at)) * 1000)) as avg_resolution_time_ms,
        ROUND(
          COUNT(*)::numeric / ${hours}::numeric,
          2
        ) as errors_per_hour
      FROM shq.master_error_log
      WHERE occurred_at >= ${windowStart}::timestamptz
        AND resolved_at IS NOT NULL
    `;

    const errors = errorStats[0] || {};
    const processes = processStats[0] || {};
    const agents = agentStats[0] || {};
    const performance = performanceMetrics[0] || {};

    // Calculate derived metrics
    const totalAgents = agents.total_agents || 0;
    const failingAgents = agents.failing_agents || 0;
    const healthyAgents = totalAgents - failingAgents;
    const healthyPercentage = totalAgents > 0
      ? Math.round((healthyAgents / totalAgents) * 100)
      : 100;

    res.json({
      success: true,
      data: {
        errorStats: {
          critical: errors.critical || 0,
          high: errors.high || 0,
          medium: errors.medium || 0,
          low: errors.low || 0,
          total: errors.total || 0,
          unresolved: errors.unresolved || 0
        },
        processStats: {
          total: processes.total_processes || 0,
          completed: processes.completed || 0,
          failed: processes.failed || 0,
          running: processes.running || 0,
          successRate: parseFloat(processes.success_rate) || 0
        },
        agentStats: {
          total: totalAgents,
          active: healthyAgents,
          failing: failingAgents,
          healthyPercentage
        },
        performanceMetrics: {
          avgResolutionTimeMs: parseInt(performance.avg_resolution_time_ms) || 0,
          errorsPerHour: parseFloat(performance.errors_per_hour) || 0,
          timeWindow: `${hours}h`
        }
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Dashboard summary error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch dashboard summary',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;
