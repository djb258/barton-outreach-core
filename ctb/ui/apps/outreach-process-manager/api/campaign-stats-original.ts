import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NEON_DB_URL || '');

interface CampaignStatsResponse {
  status: 'success' | 'failed';
  stats?: {
    total: number;
    active: number;
    launched: number;
    failed: number;
    completed: number;
    draft: number;
    ple_count: number;
    bit_count: number;
    total_targets: number;
    avg_targets_per_campaign: number;
  };
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<CampaignStatsResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed'
    });
  }

  try {
    // Get overall campaign stats
    const statsResult = await sql`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status = 'active') as active,
        COUNT(*) FILTER (WHERE status = 'failed') as failed,
        COUNT(*) FILTER (WHERE status = 'completed') as completed,
        COUNT(*) FILTER (WHERE status = 'draft') as draft,
        COUNT(*) FILTER (WHERE campaign_type = 'PLE') as ple_count,
        COUNT(*) FILTER (WHERE campaign_type = 'BIT') as bit_count,
        SUM(array_length(people_ids, 1)) as total_targets,
        AVG(array_length(people_ids, 1))::integer as avg_targets_per_campaign
      FROM marketing.campaigns
    `;

    // Get campaigns launched today
    const launchedTodayResult = await sql`
      SELECT COUNT(*) as launched_today
      FROM marketing.campaigns
      WHERE launched_at >= CURRENT_DATE
    `;

    const stats = {
      total: parseInt(statsResult[0].total) || 0,
      active: parseInt(statsResult[0].active) || 0,
      launched: parseInt(launchedTodayResult[0].launched_today) || 0,
      failed: parseInt(statsResult[0].failed) || 0,
      completed: parseInt(statsResult[0].completed) || 0,
      draft: parseInt(statsResult[0].draft) || 0,
      ple_count: parseInt(statsResult[0].ple_count) || 0,
      bit_count: parseInt(statsResult[0].bit_count) || 0,
      total_targets: parseInt(statsResult[0].total_targets) || 0,
      avg_targets_per_campaign: parseInt(statsResult[0].avg_targets_per_campaign) || 0
    };

    return res.status(200).json({
      status: 'success',
      stats
    });
  } catch (error) {
    console.error('[Campaign Stats] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch campaign stats'
    });
  }
}