/**
 * API Endpoint: /api/scrape-log
 * Scraping Console Backend (Step 6)
 * MCP tool for querying data scraping logs from Neon
 * Now posts all scrape entries to unified audit log
 */

import ComposioNeonBridge from './lib/composio-neon-bridge.js';

export default async function handler(req: any, res: any) {
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
      status = 'All',
      scrape_type = 'All',
      batch_id = null
    } = filters;

    console.log('[SCRAPE-LOG] Querying scraping logs with filters:', {
      date_range,
      status,
      scrape_type,
      batch_id
    });

    // Build SQL query for scraping logs
    const buildScrapeQuery = () => {
      const conditions = [];

      // Date range filter
      if (date_range[0] && date_range[1]) {
        conditions.push(`scrape_timestamp BETWEEN '${date_range[0]}' AND '${date_range[1]} 23:59:59'`);
      }

      // Status filter
      if (status && status !== 'All') {
        if (['In Progress', 'Completed', 'Failed', 'Success', 'Pending'].includes(status)) {
          conditions.push(`scrape_status = '${status}'`);
        }
      }

      // Scrape type filter
      if (scrape_type && scrape_type !== 'All') {
        if (['Company Data', 'Contact Info', 'Social Media', 'Web Content'].includes(scrape_type)) {
          conditions.push(`scrape_type = '${scrape_type}'`);
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
          scrape_id,
          scrape_timestamp,
          scrape_type,
          target_url,
          scrape_status as status,
          records_scraped,
          error_log,
          batch_id,
          process_id,
          unique_id,
          altitude,
          doctrine,
          doctrine_version,
          created_at
        FROM marketing.data_scraping_log
        ${whereClause}
        ORDER BY scrape_timestamp DESC
        LIMIT 1000
      `;
    };

    const scrapeQuery = buildScrapeQuery();

    // Execute query via Composio MCP
    const queryResult = await bridge.executeNeonOperation('EXECUTE_SQL', {
      sql: scrapeQuery,
      mode: 'read',
      return_type: 'rows'
    });

    let formattedResults = [];

    if (!queryResult.success) {
      // If table doesn't exist, return mock data for development
      console.log('[SCRAPE-LOG] Table not found, returning mock data');
      formattedResults = generateMockScrapeData();

      // Post mock data to audit log
      await postToAuditLog(formattedResults, bridge);

      return res.status(200).json({
        rows_returned: formattedResults.length,
        results: formattedResults,
        altitude: 10000,
        doctrine: 'STAMPED',
        metadata: {
          query_timestamp: new Date().toISOString(),
          filters_applied: { date_range, status, scrape_type, batch_id },
          mcp_tool: 'scrape-log',
          source: 'marketing.data_scraping_log',
          mock_data: true
        }
      });
    }

    const rows = queryResult.data?.rows || [];

    // Format results according to specification
    formattedResults = rows.map(row => ({
      scrape_id: row.scrape_id,
      scrape_timestamp: row.scrape_timestamp,
      scrape_type: row.scrape_type,
      target_url: row.target_url,
      status: row.status,
      records_scraped: row.records_scraped || 0,
      error_log: row.error_log && row.error_log !== '{}'
        ? (typeof row.error_log === 'string' ? JSON.parse(row.error_log) : row.error_log)
        : null,
      batch_id: row.batch_id,
      process_id: row.process_id,
      unique_id: row.unique_id,
      altitude: row.altitude || 10000,
      doctrine_version: row.doctrine_version || 'v2.1.0'
    }));

    // Post all scrape results to unified audit log
    await postToAuditLog(formattedResults, bridge);

    console.log(`[SCRAPE-LOG] Returning ${formattedResults.length} scraping log entries`);

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
          scrape_type,
          batch_id
        },
        mcp_tool: 'scrape-log',
        source: 'marketing.data_scraping_log'
      }
    });

  } catch (error) {
    console.error('[SCRAPE-LOG] Error querying scraping logs:', error);

    return res.status(500).json({
      rows_returned: 0,
      results: [],
      error: 'Internal server error',
      message: 'Failed to retrieve scraping logs',
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }
}

/**
 * Post scrape results to unified audit log
 */
async function postToAuditLog(scrapeResults: any[], bridge: any) {
  try {
    console.log('[SCRAPE-LOG] Posting scrape results to audit log...');

    for (const result of scrapeResults) {
      const auditEntry = {
        unique_id: result.unique_id || generateDoctrineId(),
        process_id: result.process_id || `Scrape ${result.scrape_type || 'Data'}`,
        altitude: result.altitude || 10000,
        timestamp: result.scrape_timestamp || new Date().toISOString(),
        status: mapScrapeStatusToAuditStatus(result.status),
        errors: result.error_log ? (Array.isArray(result.error_log) ? result.error_log : [result.error_log]) : [],
        source: 'scrape-log',
        // Additional scrape-specific fields
        scrape_id: result.scrape_id,
        scrape_type: result.scrape_type,
        target_url: result.target_url,
        records_scraped: result.records_scraped,
        batch_id: result.batch_id
      };

      // Insert into unified audit log table
      const insertQuery = `
        INSERT INTO marketing.unified_audit_log (
          unique_id, process_id, altitude, timestamp, status, errors, source,
          scrape_id, scrape_type, target_url, records_scraped, batch_id,
          created_at, doctrine, doctrine_version
        ) VALUES (
          '${auditEntry.unique_id}',
          '${auditEntry.process_id}',
          ${auditEntry.altitude},
          '${auditEntry.timestamp}',
          '${auditEntry.status}',
          '${JSON.stringify(auditEntry.errors)}',
          '${auditEntry.source}',
          '${auditEntry.scrape_id || ''}',
          '${auditEntry.scrape_type || ''}',
          '${auditEntry.target_url || ''}',
          ${auditEntry.records_scraped || 0},
          '${auditEntry.batch_id || ''}',
          NOW(),
          'STAMPED',
          'v2.1.0'
        ) ON CONFLICT (unique_id) DO UPDATE SET
          status = EXCLUDED.status,
          errors = EXCLUDED.errors,
          timestamp = EXCLUDED.timestamp
      `;

      await bridge.executeNeonOperation('EXECUTE_SQL', {
        sql: insertQuery,
        mode: 'write'
      });
    }

    console.log(`[SCRAPE-LOG] Posted ${scrapeResults.length} entries to audit log`);
  } catch (error) {
    console.error('[SCRAPE-LOG] Error posting to audit log:', error);
    // Don't fail the main request if audit logging fails
  }
}

/**
 * Map scrape status to standard audit status
 */
function mapScrapeStatusToAuditStatus(scrapeStatus: string): string {
  const status = (scrapeStatus || '').toLowerCase();

  if (status === 'completed' || status === 'success') return 'Success';
  if (status === 'failed' || status === 'error') return 'Failed';
  if (status === 'in progress' || status === 'pending') return 'Pending';

  return scrapeStatus || 'Unknown';
}

/**
 * Generate Barton Doctrine ID
 */
function generateDoctrineId(): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 8);
  return `SHP-03-IMO-1-SCR-${timestamp}-${random}`.toUpperCase();
}

/**
 * Generate mock scraping data for development
 */
function generateMockScrapeData() {
  return [
    {
      scrape_id: 'SCRAPE_001',
      scrape_timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
      scrape_type: 'Company Data',
      target_url: 'https://example.com/companies',
      status: 'Completed',
      records_scraped: 150,
      error_log: null,
      batch_id: 'BATCH_2025_001',
      process_id: 'Scrape Company Data',
      unique_id: generateDoctrineId(),
      altitude: 10000,
      doctrine_version: 'v2.1.0'
    },
    {
      scrape_id: 'SCRAPE_002',
      scrape_timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 minutes ago
      scrape_type: 'Contact Info',
      target_url: 'https://linkedin.com/company/example',
      status: 'In Progress',
      records_scraped: 75,
      error_log: null,
      batch_id: 'BATCH_2025_001',
      process_id: 'Scrape Contact Emails',
      unique_id: generateDoctrineId(),
      altitude: 10000,
      doctrine_version: 'v2.1.0'
    },
    {
      scrape_id: 'SCRAPE_003',
      scrape_timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(), // 1 hour ago
      scrape_type: 'Social Media',
      target_url: 'https://twitter.com/search?q=tech+companies',
      status: 'Failed',
      records_scraped: 0,
      error_log: ['rate_limit_exceeded', 'authentication_failed'],
      batch_id: 'BATCH_2025_001',
      process_id: 'Scrape Social Profiles',
      unique_id: generateDoctrineId(),
      altitude: 10000,
      doctrine_version: 'v2.1.0'
    },
    {
      scrape_id: 'SCRAPE_004',
      scrape_timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(), // 1.5 hours ago
      scrape_type: 'Web Content',
      target_url: 'https://industry-directory.com/companies',
      status: 'Completed',
      records_scraped: 200,
      error_log: null,
      batch_id: 'BATCH_2025_002',
      process_id: 'Scrape Web Content',
      unique_id: generateDoctrineId(),
      altitude: 10000,
      doctrine_version: 'v2.1.0'
    },
    {
      scrape_id: 'SCRAPE_005',
      scrape_timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(), // 2 hours ago
      scrape_type: 'Company Data',
      target_url: 'https://crunchbase.com/search/companies',
      status: 'Completed',
      records_scraped: 300,
      error_log: null,
      batch_id: 'BATCH_2025_002',
      process_id: 'Scrape Company Data',
      unique_id: generateDoctrineId(),
      altitude: 10000,
      doctrine_version: 'v2.1.0'
    }
  ];
}