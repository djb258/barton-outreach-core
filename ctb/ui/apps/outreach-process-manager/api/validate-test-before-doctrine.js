/**
 * Test endpoint for /api/validate
 * Use this to test the validation endpoint locally
 */

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Mock test data
  const mockRequest = {
    batch_id: '2025-09-21-001',
    filters: { validated: null }
  };

  // Mock response based on the expected format
  const mockResponse = {
    success: true,
    rows_validated: 95,
    rows_failed: 5,
    results: [
      {
        unique_id: '02.01.03.04.10000.001',
        process_id: 'Validate Company Record',
        company_name: 'Acme Corp',
        validated: true,
        errors: [],
        enrichment_applied: true,
        dedupe_status: 'unique'
      },
      {
        unique_id: '02.01.03.04.10000.002',
        process_id: 'Validate Company Record',
        company_name: 'Bad Email LLC',
        validated: false,
        errors: ['missing_email', 'duplicate_domain'],
        enrichment_applied: false,
        dedupe_status: 'duplicate',
        duplicate_of: '02.01.03.04.10000.050'
      },
      {
        unique_id: '02.01.03.04.10000.003',
        process_id: 'Validate Company Record',
        company_name: 'TechStart Inc',
        validated: true,
        errors: [],
        enrichment_applied: true,
        dedupe_status: 'unique',
        email_validation: {
          valid: true,
          quality_score: 0.92,
          provider: 'google'
        }
      }
    ],
    altitude: 10000,
    doctrine: 'STAMPED',
    process_metadata: {
      batch_id: '2025-09-21-001',
      process_id: 'VALIDATE_20250921_1234_ABC',
      started_at: new Date().toISOString(),
      completed_at: new Date(Date.now() + 2500).toISOString(),
      total_processing_time_ms: 2500,
      performance_grade: 'A',
      composio_session: 'mcp_session_12345'
    }
  };

  console.log('[VALIDATE-TEST] Mock validation request:', mockRequest);
  console.log('[VALIDATE-TEST] Returning mock response');

  return res.status(200).json(mockResponse);
}