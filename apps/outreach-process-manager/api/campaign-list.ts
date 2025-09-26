/**
 * Doctrine Spec:
 * - Barton ID: 08.05.03.07.10000.006
 * - Altitude: 10000 (Execution Layer)
 * - Input: campaign filter and pagination parameters
 * - Output: campaign list with status and metrics
 * - MCP: Composio (Neon integrated)
 */
import type { VercelRequest, VercelResponse } from 'import ComposioNeonBridge from './lib/composio-neon-bridge.js';
@vercel/node';
interface CampaignListResponse {
  status: 'success' | 'failed';
  campaigns?: any[];
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<CampaignListResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed'
    });
  }

  try {
    // Initialize MCP bridge for Barton Doctrine compliance
    const mcpBridge = new ComposioNeonBridge();
    await mcpBridge.initialize();

    const campaigns = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT
        c.campaign_id,
        c.campaign_type,
        c.trigger_event,
        c.template,
        c.company_unique_id,
        c.people_ids,
        c.marketing_score,
        c.status,
        c.created_at,
        c.launched_at,
        cm.company_name,
        COUNT(DISTINCT ce.id) as execution_count
      FROM marketing.campaigns c
      LEFT JOIN marketing.company_master cm ON cm.unique_id = c.company_unique_id
      LEFT JOIN marketing.campaign_executions ce ON ce.campaign_id = c.campaign_id
      GROUP BY c.campaign_id, c.campaign_type, c.trigger_event, c.template,
               c.company_unique_id, c.people_ids, c.marketing_score, c.status,
               c.created_at, c.launched_at, cm.company_name
      ORDER BY c.created_at DESC
      LIMIT 100`,
      mode: 'read'
    });

    if (!campaigns.success) {
      throw new Error(`MCP operation failed: ${campaigns.error}`);
    }

    return res.status(200).json({
      status: 'success',
      campaigns
    });
  } catch (error) {
    console.error('[MCP Campaign List] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch campaigns'
    });
  }
}