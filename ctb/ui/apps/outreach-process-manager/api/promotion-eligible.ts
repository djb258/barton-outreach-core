/**
 * Doctrine Spec:
 * - Barton ID: 99.99.99.07.52328.704
 * - Altitude: 10000 (Execution Layer)
 * - Input: data query parameters and filters
 * - Output: database records and metadata
 * - MCP: Composio (Neon integrated)
 */
/**
 * Promotion Eligible Records API - Barton Doctrine Pipeline
 * Input: { type: "company" | "people" }
 * Output: Count of records eligible for promotion and summary stats
 *
 * This endpoint provides summary information for the Step 4 Promotion Console
 * without actually executing promotions.
 *
 * Barton Doctrine Rules:
 * - Only counts records with validation_status='passed'
 * - Excludes already promoted records
 * - Uses Standard Composio MCP pattern for all database operations
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface EligibleRequest {
  type: 'company' | 'people';
}

interface EligibleResponse {
  success: boolean;
  summary: {
    total_eligible: number;
    rows_promoted: number;
    rows_failed: number;
    last_promotion_at: string | null;
    success_rate: number;
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const { type } = req.query;

    if (!type || !['company', 'people'].includes(type)) {
      return res.status(400).json({
        error: 'Invalid or missing type parameter. Must be "company" or "people"'
      });
    }

    console.log(`[PROMOTION-ELIGIBLE] Getting eligible ${type} records for promotion`);

    // Get promotion summary stats
    const summary = await getPromotionSummary(bridge, type);

    const response: EligibleResponse = {
      success: true,
      summary
    };

    console.log(`[PROMOTION-ELIGIBLE] Found ${summary.total_eligible} eligible ${type} records`);
    return res.status(200).json(response);

  } catch (error: any) {
    console.error('[PROMOTION-ELIGIBLE] Failed to get eligible records:', error);
    return res.status(500).json({
      error: 'Failed to get promotion eligibility data',
      message: error.message
    });
  }
}

/**
 * Get promotion summary statistics for a record type
 */
async function getPromotionSummary(
  bridge: StandardComposioNeonBridge,
  type: string
): Promise<{
  total_eligible: number;
  rows_promoted: number;
  rows_failed: number;
  last_promotion_at: string | null;
  success_rate: number;
}> {
  let eligibleQuery: string;
  let promotedQuery: string;
  let failedQuery: string;
  let lastPromotionQuery: string;

  if (type === 'company') {
    // Count eligible records (validated and not yet promoted)
    eligibleQuery = `
      SELECT COUNT(*) as count
      FROM marketing.company_raw_intake
      WHERE validation_status = 'passed'
        AND (promotion_status IS NULL OR promotion_status != 'promoted')
    `;

    // Count already promoted records
    promotedQuery = `
      SELECT COUNT(*) as count
      FROM marketing.company_raw_intake
      WHERE promotion_status = 'promoted'
    `;

    // Count failed promotion attempts
    failedQuery = `
      SELECT COUNT(DISTINCT company_unique_id) as count
      FROM marketing.company_audit_log
      WHERE action = 'promote'
        AND status = 'failed'
        AND created_at > NOW() - INTERVAL '30 days'
    `;

    // Get last promotion timestamp
    lastPromotionQuery = `
      SELECT MAX(created_at) as last_promotion_at
      FROM marketing.company_audit_log
      WHERE action = 'promote'
        AND status = 'success'
    `;

  } else {
    // People queries
    eligibleQuery = `
      SELECT COUNT(*) as count
      FROM marketing.people_raw_intake
      WHERE validation_status = 'passed'
        AND (promotion_status IS NULL OR promotion_status != 'promoted')
    `;

    promotedQuery = `
      SELECT COUNT(*) as count
      FROM marketing.people_raw_intake
      WHERE promotion_status = 'promoted'
    `;

    failedQuery = `
      SELECT COUNT(DISTINCT unique_id) as count
      FROM marketing.people_audit_log
      WHERE action = 'promote'
        AND status = 'failed'
        AND created_at > NOW() - INTERVAL '30 days'
    `;

    lastPromotionQuery = `
      SELECT MAX(created_at) as last_promotion_at
      FROM marketing.people_audit_log
      WHERE action = 'promote'
        AND status = 'success'
    `;
  }

  const [eligibleResult, promotedResult, failedResult, lastPromotionResult] = await Promise.all([
    bridge.query(eligibleQuery),
    bridge.query(promotedQuery),
    bridge.query(failedQuery),
    bridge.query(lastPromotionQuery)
  ]);

  const totalEligible = parseInt(eligibleResult.rows[0]?.count || '0');
  const rowsPromoted = parseInt(promotedResult.rows[0]?.count || '0');
  const rowsFailed = parseInt(failedResult.rows[0]?.count || '0');
  const lastPromotionAt = lastPromotionResult.rows[0]?.last_promotion_at;

  // Calculate success rate
  const totalAttempts = rowsPromoted + rowsFailed;
  const successRate = totalAttempts > 0 ? (rowsPromoted / totalAttempts) * 100 : 100;

  return {
    total_eligible: totalEligible,
    rows_promoted: rowsPromoted,
    rows_failed: rowsFailed,
    last_promotion_at: lastPromotionAt,
    success_rate: Math.round(successRate * 100) / 100
  };
}