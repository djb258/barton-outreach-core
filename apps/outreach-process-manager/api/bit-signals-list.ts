/**
 * Doctrine Spec:
 * - Barton ID: 08.04.03.07.10000.008
 * - Altitude: 10000 (Execution Layer)
 * - Input: signal filter and pagination parameters
 * - Output: BIT signal list with weights and status
 * - MCP: Composio (Neon integrated)
 */
import type { VercelRequest, VercelResponse } from 'import ComposioNeonBridge from './lib/composio-neon-bridge.js';
@vercel/node';
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
    // Initialize MCP bridge for Barton Doctrine compliance
    const mcpBridge = new ComposioNeonBridge();
    await mcpBridge.initialize();

    const signals = await mcpBridge.executeNeonOperation('QUERY_ROWS', {
      sql: `SELECT
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
      ORDER BY bsw.weight DESC, bsw.effectiveness_score DESC`,
      mode: 'read'
    });

    if (!signals.success) {
      throw new Error(`MCP operation failed: ${signals.error}`);
    }

    return res.status(200).json({
      status: 'success',
      signals
    });
  } catch (error) {
    console.error('[MCP BIT Signals List] Error:', error);
    return res.status(500).json({
      status: 'failed',
      message: 'Failed to fetch BIT signals'
    });
  }
}