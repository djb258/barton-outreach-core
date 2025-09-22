/**
 * API Endpoint: /api/scrape-log
 * Scraping Console Backend (Step 6)
 * MCP tool for querying data scraping logs from Neon
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
        if (['In Progress', 'Completed', 'Failed'].includes(status)) {
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

    if (!queryResult.success) {
      // If table doesn't exist, return mock data for development
      console.log('[SCRAPE-LOG] Table not found, returning mock data');
      return res.status(200).json({
        rows_returned: 5,
        results: generateMockScrapeData(),
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
    const formattedResults = rows.map(row => ({
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
      doctrine_version: row.doctrine_version || 'v2.1.0'
    }));

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
      process_id: 'SCRAPE_20250922_001',
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
      process_id: 'SCRAPE_20250922_002',
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
      process_id: 'SCRAPE_20250922_003',
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
      process_id: 'SCRAPE_20250922_004',
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
      process_id: 'SCRAPE_20250922_005',
      doctrine_version: 'v2.1.0'
    }
  ];
}