/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.005
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Missing data registry endpoint
 * - Query Target: shq.missing_data_registry
 */

import express from 'express';
import sql from '../../utils/neonClient.js';

const router = express.Router();

/**
 * GET /neon/missing
 * Returns missing/incomplete data records for data quality monitoring
 *
 * Query params:
 * - limit: Number of records (default: 100)
 * - severity: Filter by severity (critical/high/medium/low)
 * - resolved: Filter by resolution status
 *
 * Response format:
 * {
 *   success: boolean,
 *   data: {
 *     summary: { total, critical, high, resolvedCount },
 *     records: Array<MissingDataRecord>
 *   }
 * }
 */
router.get('/missing', async (req, res) => {
  try {
    console.log('📋 Fetching missing data registry...');

    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const severity = req.query.severity?.toLowerCase();
    const resolved = req.query.resolved;

    // Build WHERE clause
    const conditions = [];
    if (severity && ['critical', 'high', 'medium', 'low'].includes(severity)) {
      conditions.push(`severity = '${severity}'`);
    }
    if (resolved !== undefined) {
      if (resolved === 'true') {
        conditions.push('resolved_at IS NOT NULL');
      } else if (resolved === 'false') {
        conditions.push('resolved_at IS NULL');
      }
    }

    const whereClause = conditions.length > 0
      ? `WHERE ${conditions.join(' AND ')}`
      : '';

    // Get summary statistics
    const summary = await sql`
      SELECT
        COUNT(*)::int as total,
        COUNT(CASE WHEN severity = 'critical' THEN 1 END)::int as critical,
        COUNT(CASE WHEN severity = 'high' THEN 1 END)::int as high,
        COUNT(CASE WHEN severity = 'medium' THEN 1 END)::int as medium,
        COUNT(CASE WHEN severity = 'low' THEN 1 END)::int as low,
        COUNT(CASE WHEN resolved_at IS NOT NULL THEN 1 END)::int as resolved
      FROM shq.missing_data_registry
      ${sql.unsafe(whereClause)}
    `.catch(() => [{
      total: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      resolved: 0
    }]);

    // Get missing data records
    const records = await sql`
      SELECT
        id,
        detected_at,
        resolved_at,
        entity_type,
        entity_id,
        missing_field,
        field_importance,
        severity,
        impact_description,
        suggested_source,
        resolution_notes
      FROM shq.missing_data_registry
      ${sql.unsafe(whereClause)}
      ORDER BY
        CASE severity
          WHEN 'critical' THEN 1
          WHEN 'high' THEN 2
          WHEN 'medium' THEN 3
          WHEN 'low' THEN 4
        END,
        detected_at DESC
      LIMIT ${limit}
    `.catch(() => []);

    const summaryData = summary[0] || {
      total: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      resolved: 0
    };

    res.json({
      success: true,
      data: {
        summary: {
          total: summaryData.total,
          critical: summaryData.critical,
          high: summaryData.high,
          medium: summaryData.medium,
          low: summaryData.low,
          resolved: summaryData.resolved,
          unresolved: summaryData.total - summaryData.resolved
        },
        records: records.map(record => ({
          id: record.id,
          detectedAt: record.detected_at,
          resolvedAt: record.resolved_at,
          entityType: record.entity_type,
          entityId: record.entity_id,
          missingField: record.missing_field,
          fieldImportance: record.field_importance,
          severity: record.severity,
          impactDescription: record.impact_description,
          suggestedSource: record.suggested_source,
          resolutionNotes: record.resolution_notes,
          isResolved: record.resolved_at !== null
        }))
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Missing data fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch missing data registry',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;
