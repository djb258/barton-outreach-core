/**
 * Test endpoint for /api/audit-log
 * Use this to test the audit log viewer functionality
 */

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({
      error: 'Method not allowed',
      altitude: 10000,
      doctrine: 'STAMPED'
    });
  }

  // Mock test data for different scenarios
  const mockAuditLogs = [
    {
      log_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
      promotion_timestamp: '2025-09-21T14:30:00Z',
      promoted_unique_id: '02.01.03.04.10000.001',
      process_id: 'PROMOTE_20250921_1430_ABC',
      status: 'PROMOTED',
      error_log: null,
      doctrine_version: 'v2.1.0',
      batch_id: '2025-09-21-001',
      company_name: 'Acme Corp',
      entry_count: 1
    },
    {
      log_id: 'b2c3d4e5-f678-90ab-cdef-1234567890ab',
      promotion_timestamp: '2025-09-21T14:31:00Z',
      promoted_unique_id: '02.01.03.04.10000.002',
      process_id: 'PROMOTE_20250921_1430_ABC',
      status: 'PROMOTED',
      error_log: null,
      doctrine_version: 'v2.1.0',
      batch_id: '2025-09-21-001',
      company_name: 'TechStart Inc',
      entry_count: 1
    },
    {
      log_id: 'c3d4e5f6-7890-abcd-ef12-34567890abcd',
      promotion_timestamp: '2025-09-21T14:32:00Z',
      promoted_unique_id: '02.01.03.04.10000.003',
      process_id: 'PROMOTE_20250921_1430_ABC',
      status: 'FAILED',
      error_log: ['missing_email', 'invalid_domain'],
      doctrine_version: 'v2.1.0',
      batch_id: '2025-09-21-001',
      company_name: 'Bad Email LLC',
      entry_count: 1
    },
    {
      log_id: 'd4e5f678-90ab-cdef-1234-567890abcdef',
      promotion_timestamp: '2025-09-21T15:00:00Z',
      promoted_unique_id: '02.01.03.04.10000.004',
      process_id: 'PROMOTE_20250921_1500_DEF',
      status: 'PROMOTED',
      error_log: null,
      doctrine_version: 'v2.1.0',
      batch_id: '2025-09-21-002',
      company_name: 'Global Solutions Ltd',
      entry_count: 1
    },
    {
      log_id: 'e5f67890-abcd-ef12-3456-7890abcdef12',
      promotion_timestamp: '2025-09-21T15:01:00Z',
      promoted_unique_id: '02.01.03.04.10000.005',
      process_id: 'PROMOTE_20250921_1500_DEF',
      status: 'FAILED',
      error_log: ['duplicate_company', 'blacklisted_domain'],
      doctrine_version: 'v2.1.0',
      batch_id: '2025-09-21-002',
      company_name: 'Duplicate Corp',
      entry_count: 1
    }
  ];

  // Extract filters
  const { filters = {} } = req.body;
  const {
    date_range = [null, null],
    status = 'ALL',
    batch_id = null
  } = filters;

  // Filter mock data based on input filters
  let filteredResults = [...mockAuditLogs];

  // Apply date range filter
  if (date_range[0] && date_range[1]) {
    const startDate = new Date(date_range[0]);
    const endDate = new Date(date_range[1] + 'T23:59:59Z');
    filteredResults = filteredResults.filter(log => {
      const logDate = new Date(log.promotion_timestamp);
      return logDate >= startDate && logDate <= endDate;
    });
  }

  // Apply status filter
  if (status && status !== 'ALL') {
    filteredResults = filteredResults.filter(log => log.status === status);
  }

  // Apply batch_id filter
  if (batch_id) {
    filteredResults = filteredResults.filter(log => log.batch_id === batch_id);
  }

  console.log('[AUDIT-LOG-TEST] Filters applied:', {
    date_range,
    status,
    batch_id
  });
  console.log(`[AUDIT-LOG-TEST] Returning ${filteredResults.length} mock audit logs`);

  // Return response in the exact format specified
  return res.status(200).json({
    rows_returned: filteredResults.length,
    results: filteredResults.map(log => ({
      log_id: log.log_id,
      promotion_timestamp: log.promotion_timestamp,
      promoted_unique_id: log.promoted_unique_id,
      process_id: log.process_id,
      status: log.status,
      error_log: log.error_log,
      doctrine_version: log.doctrine_version,
      batch_id: log.batch_id,
      // Additional fields for UI
      company_name: log.company_name,
      entry_count: log.entry_count
    })),
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
      source: 'marketing.company_promotion_log',
      test_mode: true
    }
  });
}