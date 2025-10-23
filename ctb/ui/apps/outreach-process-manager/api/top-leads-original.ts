import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NEON_DB_URL || '');

interface TopLeadsResponse {
  status: 'success' | 'failed';
  leads?: any[];
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<TopLeadsResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed'
    });
  }

  try {
    const { limit = '25', min_score = '50' } = req.query;

    const leads = await sql`
      SELECT
        lsa.person_unique_id,
        lsa.company_unique_id,
        lsa.score,
        lsa.lead_temperature,
        lsa.first_name,
        lsa.last_name,
        lsa.email,
        lsa.company_name,
        lsa.industry,
        lsa.employee_count,
        lsa.firmographics_score,
        lsa.engagement_score,
        lsa.intent_score,
        lsa.attribution_score,
        lsa.last_scored_at,
        pm.promotion_status
      FROM marketing.lead_scoring_analytics lsa
      JOIN marketing.people_master pm ON pm.unique_id = lsa.person_unique_id
      WHERE lsa.score >= ${parseInt(min_score as string)}
      AND pm.promotion_status = 'promoted'
      ORDER BY lsa.score DESC, lsa.last_scored_at DESC
      LIMIT ${parseInt(limit as string)}
    `;

    return res.status(200).json({
      status: 'success',
      leads
    });
  } catch (error) {
    console.error('[Top Leads] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch top leads'
    });
  }
}