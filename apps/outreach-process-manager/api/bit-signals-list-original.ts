import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NEON_DB_URL || '');

interface BITSignalsListResponse {
  status: 'success' | 'failed';
  signals?: any[];
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<BITSignalsListResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed'
    });
  }

  try {
    const signals = await sql`
      SELECT
        bsw.signal_name,
        bsw.weight,
        bsw.signal_category,
        bsw.signal_description,
        bsw.model_version,
        bsw.effectiveness_score,
        bsw.conversion_rate,
        bsw.attribution_count,
        bsw.last_optimized,
        bsw.last_updated,
        COUNT(bse.id) as total_events,
        COUNT(bse.id) FILTER (WHERE bse.detected_at >= NOW() - INTERVAL '30 days') as recent_events
      FROM marketing.bit_signal_weights bsw
      LEFT JOIN marketing.bit_signal_events bse ON bse.signal_name = bsw.signal_name
      GROUP BY bsw.signal_name, bsw.weight, bsw.signal_category, bsw.signal_description,
               bsw.model_version, bsw.effectiveness_score, bsw.conversion_rate,
               bsw.attribution_count, bsw.last_optimized, bsw.last_updated
      ORDER BY bsw.weight DESC, bsw.effectiveness_score DESC
    `;

    return res.status(200).json({
      status: 'success',
      signals
    });
  } catch (error) {
    console.error('[BIT Signals List] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch BIT signals'
    });
  }
}