/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.007
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Analytics endpoints for trends and compliance
 * - Query Target: Various views and aggregates
 */

import express from 'express';
import sql from '../../utils/neonClient.js';

const router = express.Router();

/**
 * GET /neon/analytics/error-trend
 * Returns error trend data over time for charting
 */
router.get('/analytics/error-trend', async (req, res) => {
  try {
    console.log('📈 Fetching error trend analytics...');

    const hours = parseInt(req.query.hours) || 24;
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    const trend = await sql`
      SELECT
        DATE_TRUNC('hour', occurred_at) as hour,
        COUNT(*)::int as total_errors,
        COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END)::int as critical,
        COUNT(CASE WHEN severity = 'HIGH' THEN 1 END)::int as high,
        COUNT(CASE WHEN severity = 'MEDIUM' THEN 1 END)::int as medium,
        COUNT(CASE WHEN severity = 'LOW' THEN 1 END)::int as low,
        COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END)::int as resolved
      FROM shq.master_error_log
      WHERE occurred_at >= ${windowStart}::timestamptz
      GROUP BY DATE_TRUNC('hour', occurred_at)
      ORDER BY hour ASC
    `;

    res.json({
      success: true,
      data: trend.map(point => ({
        timestamp: point.hour,
        total: point.total_errors,
        critical: point.critical,
        high: point.high,
        medium: point.medium,
        low: point.low,
        resolved: point.resolved,
        unresolved: point.total_errors - point.resolved
      })),
      timeWindow: `${hours}h`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Error trend fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch error trend',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * GET /neon/analytics/doctrine-compliance
 * Returns Barton Doctrine compliance metrics by step
 */
router.get('/analytics/doctrine-compliance', async (req, res) => {
  try {
    console.log('📊 Fetching doctrine compliance analytics...');

    const hours = parseInt(req.query.hours) || 168; // Default 7 days
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    // Query process registry for doctrine step compliance
    const compliance = await sql`
      SELECT
        stage,
        COUNT(*)::int as total_processes,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::int as completed,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::int as failed,
        ROUND(
          COUNT(CASE WHEN status = 'completed' THEN 1 END)::numeric /
          NULLIF(COUNT(*)::numeric, 0) * 100,
          2
        ) as completion_rate,
        ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - created_at))), 2) as avg_duration_seconds
      FROM shq.process_registry
      WHERE created_at >= ${windowStart}::timestamptz
      GROUP BY stage
      ORDER BY
        CASE stage
          WHEN 'input' THEN 1
          WHEN 'middle' THEN 2
          WHEN 'output' THEN 3
          ELSE 4
        END
    `.catch(() => []);

    res.json({
      success: true,
      data: {
        byStage: compliance.map(stage => ({
          stage: stage.stage,
          totalProcesses: stage.total_processes,
          completed: stage.completed,
          failed: stage.failed,
          completionRate: parseFloat(stage.completion_rate) || 0,
          avgDurationSeconds: parseFloat(stage.avg_duration_seconds) || 0
        })),
        overall: {
          totalProcesses: compliance.reduce((sum, s) => sum + s.total_processes, 0),
          avgCompletionRate: compliance.length > 0
            ? Math.round(compliance.reduce((sum, s) => sum + parseFloat(s.completion_rate), 0) / compliance.length)
            : 0
        }
      },
      timeWindow: `${hours}h`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Doctrine compliance fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch doctrine compliance',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * GET /neon/analytics/latency
 * Returns system latency and performance metrics
 */
router.get('/analytics/latency', async (req, res) => {
  try {
    console.log('⏱️ Fetching latency analytics...');

    const hours = parseInt(req.query.hours) || 24;
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    // Query process durations
    const latency = await sql`
      SELECT
        DATE_TRUNC('hour', created_at) as hour,
        COUNT(*)::int as process_count,
        ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)) as avg_latency_ms,
        ROUND(MIN(EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)) as min_latency_ms,
        ROUND(MAX(EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)) as max_latency_ms,
        ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)) as p50_latency_ms,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)) as p95_latency_ms,
        ROUND(PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - created_at)) * 1000)) as p99_latency_ms
      FROM shq.process_registry
      WHERE created_at >= ${windowStart}::timestamptz
        AND completed_at IS NOT NULL
      GROUP BY DATE_TRUNC('hour', created_at)
      ORDER BY hour ASC
    `.catch(() => []);

    res.json({
      success: true,
      data: latency.map(point => ({
        timestamp: point.hour,
        processCount: point.process_count,
        avgLatencyMs: parseInt(point.avg_latency_ms) || 0,
        minLatencyMs: parseInt(point.min_latency_ms) || 0,
        maxLatencyMs: parseInt(point.max_latency_ms) || 0,
        p50LatencyMs: parseInt(point.p50_latency_ms) || 0,
        p95LatencyMs: parseInt(point.p95_latency_ms) || 0,
        p99LatencyMs: parseInt(point.p99_latency_ms) || 0
      })),
      timeWindow: `${hours}h`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Latency analytics fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch latency analytics',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * GET /neon/analytics/data-quality
 * Returns data quality metrics over time
 */
router.get('/analytics/data-quality', async (req, res) => {
  try {
    console.log('🔍 Fetching data quality analytics...');

    const hours = parseInt(req.query.hours) || 168; // Default 7 days
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    // Aggregate integrity audit data
    const quality = await sql`
      SELECT
        DATE_TRUNC('day', audited_at) as day,
        COUNT(*)::int as total_checks,
        COUNT(CASE WHEN status = 'passed' THEN 1 END)::int as passed,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::int as failed,
        ROUND(AVG(failure_rate), 2) as avg_failure_rate,
        ROUND(
          COUNT(CASE WHEN status = 'passed' THEN 1 END)::numeric /
          NULLIF(COUNT(*)::numeric, 0) * 100,
          2
        ) as pass_rate
      FROM shq.integrity_audit
      WHERE audited_at >= ${windowStart}::timestamptz
      GROUP BY DATE_TRUNC('day', audited_at)
      ORDER BY day ASC
    `.catch(() => []);

    res.json({
      success: true,
      data: quality.map(point => ({
        date: point.day,
        totalChecks: point.total_checks,
        passed: point.passed,
        failed: point.failed,
        avgFailureRate: parseFloat(point.avg_failure_rate) || 0,
        passRate: parseFloat(point.pass_rate) || 100
      })),
      timeWindow: `${hours}h`,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Data quality analytics fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch data quality analytics',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;
