import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NEON_DB_URL || '');

interface ScoringStatsResponse {
  status: 'success' | 'failed';
  scoring_stats?: {
    avg_score: number;
    total_leads: number;
    hot_leads: number;
    warm_leads: number;
    cool_leads: number;
    cold_leads: number;
    distribution: {
      hot: number;
      warm: number;
      cool: number;
      cold: number;
    };
    model_version: string;
    last_updated: string;
  };
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<ScoringStatsResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed'
    });
  }

  try {
    // Get overall lead scoring statistics
    const statsResult = await sql`
      SELECT
        COUNT(*) as total_leads,
        ROUND(AVG(score), 1) as avg_score,
        COUNT(*) FILTER (WHERE score >= 85) as hot_leads,
        COUNT(*) FILTER (WHERE score >= 70 AND score < 85) as warm_leads,
        COUNT(*) FILTER (WHERE score >= 50 AND score < 70) as cool_leads,
        COUNT(*) FILTER (WHERE score < 50) as cold_leads,
        MAX(model_version) as model_version,
        MAX(last_scored_at) as last_updated
      FROM marketing.ple_lead_scoring
    `;

    const stats = statsResult[0];

    return res.status(200).json({
      status: 'success',
      scoring_stats: {
        avg_score: parseFloat(stats.avg_score) || 0,
        total_leads: parseInt(stats.total_leads) || 0,
        hot_leads: parseInt(stats.hot_leads) || 0,
        warm_leads: parseInt(stats.warm_leads) || 0,
        cool_leads: parseInt(stats.cool_leads) || 0,
        cold_leads: parseInt(stats.cold_leads) || 0,
        distribution: {
          hot: parseInt(stats.hot_leads) || 0,
          warm: parseInt(stats.warm_leads) || 0,
          cool: parseInt(stats.cool_leads) || 0,
          cold: parseInt(stats.cold_leads) || 0
        },
        model_version: stats.model_version || '1.0.0',
        last_updated: stats.last_updated || new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('[Scoring Stats] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch scoring statistics'
    });
  }
}