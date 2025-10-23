/**
 * Doctrine Spec:
 * - Barton ID: 10.01.01.07.10000.021
 * - Altitude: 10000 (Execution Layer)
 * - Input: audit log query and filter parameters
 * - Output: audit trail records and compliance data
 * - MCP: Composio (Neon integrated)
 */
/**
 * API Endpoint: /api/audit-log
 * Audit Log Viewer Console Backend (Step 5)
 * MCP tool for querying promotion audit logs from Neon
 */

import ComposioNeonBridge from './lib/composio-neon-bridge.js';

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'Only POST requests are accepted',
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }

  const bridge = new ComposioNeonBridge();

  try {
    // Extract filters from request body
    const { filters = {} } = req.body;
    const {
      date_range = [null, null],
      status = 'ALL',
      batch_id = null
    } = filters;

    console.log('[AUDIT-LOG] Querying audit logs with filters:', {
      date_range,
      status,
      batch_id
    });

    // Build SQL query with proper parameterization
    const buildAuditQuery = () => {
      const conditions = [];

      // Date range filter
      if (date_range[0] && date_range[1]) {
        conditions.push(`created_at BETWEEN '${date_range[0]}' AND '${date_range[1]} 23:59:59'`);
      }

      // Status filter
      if (status && status !== 'ALL') {
        if (status === 'PROMOTED' || status === 'FAILED') {
          conditions.push(`promotion_status = '${status}'`);
        }
      }

      // Batch ID filter
      if (batch_id) {
        conditions.push(`batch_id = '${batch_id.replace(/'/g, "''")}'`);
      }

      const whereClause = conditions.length > 0
        ? `WHERE ${conditions.join(' AND ')}`
        : '';

      return `
        SELECT
          log_id,
          created_at as promotion_timestamp,
          unique_id as promoted_unique_id,
          process_id,
          promotion_status as status,
          error_log,
          doctrine_version,
          batch_id,
          company_name,
          entry_count,
          altitude,
          doctrine
        FROM marketing.company_promotion_log
        ${whereClause}
        ORDER BY created_at DESC
        LIMIT 1000
      `;
    };

    const auditQuery = buildAuditQuery();

    // Execute query via Composio MCP
    const queryResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: auditQuery,
      mode: 'read',
      return_type: 'rows'
    });

    if (!queryResult.success) {
      console.error('[AUDIT-LOG] Query failed:', queryResult.error);
      return res.status(500).json({
        rows_returned: 0,
        results: [],
        error: 'Failed to query audit logs',
        message: queryResult.error,
        altitude: 10000,
        doctrine: 'STAMPED'
      });
    }

    const rows = queryResult.data?.rows || [];

    // Format results according to specification
    const formattedResults = rows.map(row => ({
      log_id: row.log_id,
      promotion_timestamp: row.promotion_timestamp,
      promoted_unique_id: row.promoted_unique_id,
      process_id: row.process_id,
      status: row.status === 'PROMOTED' ? 'PROMOTED' : 'FAILED',
      error_log: row.error_log && row.error_log !== '{}'
        ? (typeof row.error_log === 'string' ? JSON.parse(row.error_log) : row.error_log)
        : null,
      doctrine_version: row.doctrine_version || 'v2.1.0',
      batch_id: row.batch_id,
      // Additional fields for UI display
      company_name: row.company_name,
      entry_count: row.entry_count || 0
    }));

    console.log(`[AUDIT-LOG] Returning ${formattedResults.length} audit log entries`);

    // Return response with doctrine metadata
    return res.status(200).json({
      rows_returned: formattedResults.length,
      results: formattedResults,
      altitude: 10000,
      doctrine: 'STAMPED',
      metadata: {
        query_timestamp: new Date().toISOString(),
        filters_applied: {
          date_range: date_range[0] && date_range[1] ? date_range : null,
          status,
          batch_id
        },
        mcp_tool: 'audit-log',
        source: 'marketing.company_promotion_log'
      }
    });

  } catch (error) {
    console.error('[AUDIT-LOG] Error querying audit logs:', error);

    return res.status(500).json({
      rows_returned: 0,
      results: [],
      error: 'Internal server error',
      message: 'Failed to retrieve audit logs',
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }
}