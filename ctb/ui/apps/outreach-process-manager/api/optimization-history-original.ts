import type { VercelRequest, VercelResponse } from '@vercel/node';
import { neon } from '@neondatabase/serverless';

const sql = neon(process.env.NEON_DB_URL || '');

interface OptimizationHistoryResponse {
  status: 'success' | 'failed';
  history?: any[];
  message?: string;
}

export default async function handler(
  req: VercelRequest,
  res: VercelResponse<OptimizationHistoryResponse>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({
      status: 'failed',
      message: 'Method not allowed'
    });
  }

  try {
    const { limit = '50' } = req.query;

    const history = await sql`
      SELECT
        smv.id,
        smv.model_type,
        smv.version,
        smv.model_config,
        smv.avg_score,
        smv.score_distribution,
        smv.accuracy_rate,
        smv.closed_won_correlation,
        smv.closed_lost_correlation,
        smv.is_active,
        smv.activated_at,
        smv.deactivated_at,
        smv.created_by,
        smv.created_at,
        smv.notes,
        CASE
          WHEN smv.model_config ? 'weights' THEN
            jsonb_array_length(jsonb_object_keys(smv.model_config->'weights'))
          ELSE 0
        END as signals_changed,
        CASE
          WHEN smv.model_config ? 'summary' THEN
            (smv.model_config->'summary'->>'avg_conversion_rate')::NUMERIC
          ELSE NULL
        END as avg_weight_change
      FROM marketing.scoring_model_versions smv
      ORDER BY smv.created_at DESC
      LIMIT ${parseInt(limit as string)}
    `;

    return res.status(200).json({
      status: 'success',
      history
    });
  } catch (error) {
    console.error('[Optimization History] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch optimization history'
    });
  }
}