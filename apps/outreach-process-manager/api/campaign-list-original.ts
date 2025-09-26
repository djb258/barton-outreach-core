import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NEON_DB_URL || '');

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
    const campaigns = await sql`
      SELECT
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
      LIMIT 100
    `;

    return res.status(200).json({
      status: 'success',
      campaigns
    });
  } catch (error) {
    console.error('[Campaign List] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch campaigns'
    });
  }
}