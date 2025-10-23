/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.34784.863
 * - Altitude: 10000 (Execution Layer)
 * - Input: analytics query parameters and filters
 * - Output: analytics data and metrics
 * - MCP: Composio (Neon integrated)
 */
/**
 * Step 2B Enrichment Status API - Barton Doctrine Pipeline
 * Input: none
 * Output: Batch overview with pending/enriched/failed counts
 *
 * Returns:
 * {
 *   "companies": { "pending": 12, "enriched": 8, "failed": 4 },
 *   "people": { "pending": 5, "enriched": 3, "failed": 2 }
 * }
 *
 * Barton Doctrine Rules:
 * - Reports current enrichment status across both companies and people
 * - Uses Standard Composio MCP pattern for all database operations
 * - Provides real-time visibility into Step 2B enrichment progress
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface EnrichmentStatusSummary {
  pending: number;
  enriched: number;
  failed: number;
  total_records: number;
  last_enrichment_at?: string;
  success_rate: number;
}

interface EnrichmentStatusResponse {
  companies: EnrichmentStatusSummary;
  people: EnrichmentStatusSummary;
  overall_stats: {
    total_enrichment_attempts: number;
    total_successful: number;
    total_failed: number;
    overall_success_rate: number;
  };
  recent_activity: Array<{
    record_type: string;
    unique_id: string;
    action: string;
    status: string;
    source: string;
    created_at: string;
  }>;
  system_health: {
    enrichment_system_status: 'healthy' | 'degraded' | 'down';
    last_batch_processed_at?: string;
    average_processing_time_ms?: number;
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    console.log('[ENRICH-STATUS] Fetching enrichment status overview');

    // Get company enrichment status
    const companiesStatus = await getCompanyEnrichmentStatus(bridge);

    // Get people enrichment status
    const peopleStatus = await getPeopleEnrichmentStatus(bridge);

    // Get overall statistics
    const overallStats = await getOverallEnrichmentStats(bridge);

    // Get recent enrichment activity
    const recentActivity = await getRecentEnrichmentActivity(bridge);

    // Get system health metrics
    const systemHealth = await getEnrichmentSystemHealth(bridge);

    const response: EnrichmentStatusResponse = {
      companies: companiesStatus,
      people: peopleStatus,
      overall_stats: overallStats,
      recent_activity: recentActivity,
      system_health: systemHealth
    };

    console.log('[ENRICH-STATUS] Status overview complete');
    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[ENRICH-STATUS] Failed to get enrichment status:', error);
    return res.status(500).json({
      error: 'Failed to get enrichment status',
      message: error.message
    });
  }
}

/**
 * Get company enrichment status summary
 */
async function getCompanyEnrichmentStatus(
  bridge: StandardComposioNeonBridge
): Promise<EnrichmentStatusSummary> {
  // Get failed companies (pending enrichment)
  const pendingQuery = `
    SELECT COUNT(*) as count
    FROM marketing.company_raw_intake
    WHERE validation_status = 'failed'
  `;

  // Get successfully enriched companies (from audit log)
  const enrichedQuery = `
    SELECT
      COUNT(DISTINCT e.unique_id) as count,
      MAX(e.created_at) as last_enrichment_at
    FROM intake.enrichment_audit_log e
    WHERE e.unique_id LIKE '04.04.01.%'  -- company records
      AND e.action = 'enrich'
      AND e.status = 'success'
      AND e.created_at > NOW() - INTERVAL '24 hours'
  `;

  // Get failed enrichment attempts
  const failedQuery = `
    SELECT COUNT(DISTINCT e.unique_id) as count
    FROM intake.enrichment_audit_log e
    WHERE e.unique_id LIKE '04.04.01.%'  -- company records
      AND e.action = 'enrich'
      AND e.status = 'failed'
      AND e.created_at > NOW() - INTERVAL '24 hours'
  `;

  // Get total company records
  const totalQuery = `
    SELECT COUNT(*) as count
    FROM marketing.company_raw_intake
  `;

  const [pendingResult, enrichedResult, failedResult, totalResult] = await Promise.all([
    bridge.query(pendingQuery),
    bridge.query(enrichedQuery),
    bridge.query(failedQuery),
    bridge.query(totalQuery)
  ]);

  const pending = parseInt(pendingResult.rows[0].count);
  const enriched = parseInt(enrichedResult.rows[0].count);
  const failed = parseInt(failedResult.rows[0].count);
  const total = parseInt(totalResult.rows[0].count);

  const successRate = enriched + failed > 0 ? (enriched / (enriched + failed)) * 100 : 0;

  return {
    pending,
    enriched,
    failed,
    total_records: total,
    last_enrichment_at: enrichedResult.rows[0].last_enrichment_at,
    success_rate: Math.round(successRate * 100) / 100
  };
}

/**
 * Get people enrichment status summary
 */
async function getPeopleEnrichmentStatus(
  bridge: StandardComposioNeonBridge
): Promise<EnrichmentStatusSummary> {
  // Get failed people (pending enrichment)
  const pendingQuery = `
    SELECT COUNT(*) as count
    FROM marketing.people_raw_intake
    WHERE validation_status = 'failed'
  `;

  // Get successfully enriched people (from audit log)
  const enrichedQuery = `
    SELECT
      COUNT(DISTINCT e.unique_id) as count,
      MAX(e.created_at) as last_enrichment_at
    FROM intake.enrichment_audit_log e
    WHERE e.unique_id LIKE '04.04.02.%'  -- people records
      AND e.action = 'enrich'
      AND e.status = 'success'
      AND e.created_at > NOW() - INTERVAL '24 hours'
  `;

  // Get failed enrichment attempts
  const failedQuery = `
    SELECT COUNT(DISTINCT e.unique_id) as count
    FROM intake.enrichment_audit_log e
    WHERE e.unique_id LIKE '04.04.02.%'  -- people records
      AND e.action = 'enrich'
      AND e.status = 'failed'
      AND e.created_at > NOW() - INTERVAL '24 hours'
  `;

  // Get total people records
  const totalQuery = `
    SELECT COUNT(*) as count
    FROM marketing.people_raw_intake
  `;

  const [pendingResult, enrichedResult, failedResult, totalResult] = await Promise.all([
    bridge.query(pendingQuery),
    bridge.query(enrichedQuery),
    bridge.query(failedQuery),
    bridge.query(totalQuery)
  ]);

  const pending = parseInt(pendingResult.rows[0].count);
  const enriched = parseInt(enrichedResult.rows[0].count);
  const failed = parseInt(failedResult.rows[0].count);
  const total = parseInt(totalResult.rows[0].count);

  const successRate = enriched + failed > 0 ? (enriched / (enriched + failed)) * 100 : 0;

  return {
    pending,
    enriched,
    failed,
    total_records: total,
    last_enrichment_at: enrichedResult.rows[0].last_enrichment_at,
    success_rate: Math.round(successRate * 100) / 100
  };
}

/**
 * Get overall enrichment statistics across all record types
 */
async function getOverallEnrichmentStats(
  bridge: StandardComposioNeonBridge
): Promise<{
  total_enrichment_attempts: number;
  total_successful: number;
  total_failed: number;
  overall_success_rate: number;
}> {
  const query = `
    SELECT
      COUNT(*) as total_attempts,
      COUNT(*) FILTER (WHERE status = 'success') as successful,
      COUNT(*) FILTER (WHERE status = 'failed') as failed,
      COUNT(*) FILTER (WHERE status = 'partial') as partial
    FROM intake.enrichment_audit_log
    WHERE action = 'enrich'
      AND created_at > NOW() - INTERVAL '24 hours'
  `;

  const result = await bridge.query(query);
  const row = result.rows[0];

  const totalAttempts = parseInt(row.total_attempts);
  const successful = parseInt(row.successful);
  const failed = parseInt(row.failed);
  const partial = parseInt(row.partial);

  const overallSuccessRate = totalAttempts > 0
    ? ((successful + partial) / totalAttempts) * 100
    : 0;

  return {
    total_enrichment_attempts: totalAttempts,
    total_successful: successful + partial,
    total_failed: failed,
    overall_success_rate: Math.round(overallSuccessRate * 100) / 100
  };
}

/**
 * Get recent enrichment activity for monitoring
 */
async function getRecentEnrichmentActivity(
  bridge: StandardComposioNeonBridge
): Promise<Array<{
  record_type: string;
  unique_id: string;
  action: string;
  status: string;
  source: string;
  created_at: string;
}>> {
  const query = `
    SELECT
      CASE
        WHEN unique_id LIKE '04.04.01.%' THEN 'company'
        WHEN unique_id LIKE '04.04.02.%' THEN 'people'
        ELSE 'unknown'
      END as record_type,
      unique_id,
      action,
      status,
      source,
      created_at
    FROM intake.enrichment_audit_log
    WHERE created_at > NOW() - INTERVAL '2 hours'
    ORDER BY created_at DESC
    LIMIT 20
  `;

  const result = await bridge.query(query);
  return result.rows.map(row => ({
    record_type: row.record_type,
    unique_id: row.unique_id,
    action: row.action,
    status: row.status,
    source: row.source,
    created_at: row.created_at
  }));
}

/**
 * Get enrichment system health indicators
 */
async function getEnrichmentSystemHealth(
  bridge: StandardComposioNeonBridge
): Promise<{
  enrichment_system_status: 'healthy' | 'degraded' | 'down';
  last_batch_processed_at?: string;
  average_processing_time_ms?: number;
}> {
  // Get recent batch activity to determine system status
  const recentBatchQuery = `
    SELECT
      MAX(created_at) as last_batch_at,
      COUNT(*) as recent_batches,
      COUNT(*) FILTER (WHERE status = 'failed') as failed_batches
    FROM intake.enrichment_audit_log
    WHERE created_at > NOW() - INTERVAL '1 hour'
      AND session_id IS NOT NULL
  `;

  // Get average processing performance
  const performanceQuery = `
    SELECT
      AVG(
        EXTRACT(EPOCH FROM (
          LEAD(created_at) OVER (PARTITION BY session_id ORDER BY created_at) - created_at
        )) * 1000
      ) as avg_processing_time_ms
    FROM intake.enrichment_audit_log
    WHERE created_at > NOW() - INTERVAL '24 hours'
      AND session_id IS NOT NULL
  `;

  const [batchResult, performanceResult] = await Promise.all([
    bridge.query(recentBatchQuery),
    bridge.query(performanceQuery)
  ]);

  const batchRow = batchResult.rows[0];
  const recentBatches = parseInt(batchRow.recent_batches);
  const failedBatches = parseInt(batchRow.failed_batches);
  const lastBatchAt = batchRow.last_batch_at;

  const avgProcessingTime = performanceResult.rows[0]?.avg_processing_time_ms;

  // Determine system status
  let systemStatus: 'healthy' | 'degraded' | 'down';

  if (recentBatches === 0) {
    systemStatus = 'down'; // No recent activity
  } else if (failedBatches / recentBatches > 0.5) {
    systemStatus = 'degraded'; // High failure rate
  } else {
    systemStatus = 'healthy';
  }

  return {
    enrichment_system_status: systemStatus,
    last_batch_processed_at: lastBatchAt,
    average_processing_time_ms: avgProcessingTime ? Math.round(avgProcessingTime) : undefined
  };
}