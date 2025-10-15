/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.004
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Data integrity audit endpoint
 * - Query Target: shq.integrity_audit
 */

import express from 'express';
import sql from '../../utils/neonClient.js';

const router = express.Router();

/**
 * GET /neon/integrity
 * Returns data integrity audit records and trends
 *
 * Query params:
 * - limit: Number of records (default: 50)
 * - status: Filter by status (passed/failed)
 * - hours: Time window in hours (default: 24)
 *
 * Response format:
 * {
 *   success: boolean,
 *   data: {
 *     summary: { total, passed, failed, passRate },
 *     records: Array<IntegrityRecord>,
 *     trend: Array<TrendPoint>
 *   }
 * }
 */
router.get('/integrity', async (req, res) => {
  try {
    console.log('🔍 Fetching integrity audit data...');

    const limit = Math.min(parseInt(req.query.limit) || 50, 500);
    const status = req.query.status;
    const hours = parseInt(req.query.hours) || 24;
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    // Build WHERE clause
    const conditions = [`audited_at >= '${windowStart}'::timestamptz`];
    if (status && ['passed', 'failed'].includes(status.toLowerCase())) {
      conditions.push(`status = '${status.toLowerCase()}'`);
    }
    const whereClause = `WHERE ${conditions.join(' AND ')}`;

    // Get summary statistics
    const summary = await sql`
      SELECT
        COUNT(*)::int as total,
        COUNT(CASE WHEN status = 'passed' THEN 1 END)::int as passed,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::int as failed,
        ROUND(
          COUNT(CASE WHEN status = 'passed' THEN 1 END)::numeric /
          NULLIF(COUNT(*)::numeric, 0) * 100,
          2
        ) as pass_rate
      FROM shq.integrity_audit
      ${sql.unsafe(whereClause)}
    `.catch(() => [{
      total: 0,
      passed: 0,
      failed: 0,
      pass_rate: 100
    }]);

    // Get recent audit records
    const records = await sql`
      SELECT
        audit_id,
        audited_at,
        data_source,
        table_name,
        check_name,
        status,
        records_checked,
        records_failed,
        failure_rate,
        details,
        severity
      FROM shq.integrity_audit
      ${sql.unsafe(whereClause)}
      ORDER BY audited_at DESC
      LIMIT ${limit}
    `.catch(() => []);

    // Get hourly trend data
    const trend = await sql`
      SELECT
        DATE_TRUNC('hour', audited_at) as hour,
        COUNT(*)::int as total_checks,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::int as failed_checks,
        ROUND(AVG(failure_rate), 2) as avg_failure_rate
      FROM shq.integrity_audit
      ${sql.unsafe(whereClause)}
      GROUP BY DATE_TRUNC('hour', audited_at)
      ORDER BY hour DESC
      LIMIT 24
    `.catch(() => []);

    const summaryData = summary[0] || { total: 0, passed: 0, failed: 0, pass_rate: 100 };

    res.json({
      success: true,
      data: {
        summary: {
          total: summaryData.total,
          passed: summaryData.passed,
          failed: summaryData.failed,
          passRate: parseFloat(summaryData.pass_rate) || 100,
          timeWindow: `${hours}h`
        },
        records: records.map(record => ({
          auditId: record.audit_id,
          auditedAt: record.audited_at,
          dataSource: record.data_source,
          tableName: record.table_name,
          checkName: record.check_name,
          status: record.status,
          recordsChecked: record.records_checked,
          recordsFailed: record.records_failed,
          failureRate: parseFloat(record.failure_rate) || 0,
          details: record.details,
          severity: record.severity || 'medium'
        })),
        trend: trend.map(point => ({
          hour: point.hour,
          totalChecks: point.total_checks,
          failedChecks: point.failed_checks,
          avgFailureRate: parseFloat(point.avg_failure_rate) || 0
        })).reverse() // Chronological order
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Integrity audit fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch integrity audit data',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;
