/**
 * Doctrine Spec:
 * - Barton ID: 03.01.01.07.10000.006
 * - Altitude: 10000 (Execution Layer)
 * - Purpose: Messaging/campaign performance endpoint
 * - Query Target: marketing.campaign_metrics
 */

import express from 'express';
import sql from '../../utils/neonClient.js';

const router = express.Router();

/**
 * GET /neon/messaging
 * Returns outbound campaign performance metrics
 *
 * Query params:
 * - hours: Time window in hours (default: 24)
 * - campaign_id: Filter by specific campaign
 * - source: Filter by source (instantly, heyreach, etc.)
 *
 * Response format:
 * {
 *   success: boolean,
 *   data: {
 *     summary: { sent, delivered, opened, clicked, replied, bounced },
 *     campaigns: Array<CampaignMetric>,
 *     trend: Array<TrendPoint>
 *   }
 * }
 */
router.get('/messaging', async (req, res) => {
  try {
    console.log('📧 Fetching messaging metrics...');

    const hours = parseInt(req.query.hours) || 24;
    const campaignId = req.query.campaign_id;
    const source = req.query.source;
    const windowStart = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();

    // Build WHERE clause
    const conditions = [`created_at >= '${windowStart}'::timestamptz`];
    if (campaignId) {
      conditions.push(`campaign_id = '${campaignId}'`);
    }
    if (source) {
      conditions.push(`source = '${source}'`);
    }
    const whereClause = `WHERE ${conditions.join(' AND ')}`;

    // Get summary metrics
    const summary = await sql`
      SELECT
        COUNT(*)::int as total_sent,
        COUNT(CASE WHEN status = 'delivered' THEN 1 END)::int as delivered,
        COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::int as opened,
        COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END)::int as clicked,
        COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END)::int as replied,
        COUNT(CASE WHEN status = 'bounced' THEN 1 END)::int as bounced,
        ROUND(
          COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::numeric /
          NULLIF(COUNT(*)::numeric, 0) * 100,
          2
        ) as open_rate,
        ROUND(
          COUNT(CASE WHEN clicked_at IS NOT NULL THEN 1 END)::numeric /
          NULLIF(COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::numeric, 0) * 100,
          2
        ) as click_through_rate,
        ROUND(
          COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END)::numeric /
          NULLIF(COUNT(*)::numeric, 0) * 100,
          2
        ) as reply_rate
      FROM marketing.campaign_metrics
      ${sql.unsafe(whereClause)}
    `.catch(() => [{
      total_sent: 0,
      delivered: 0,
      opened: 0,
      clicked: 0,
      replied: 0,
      bounced: 0,
      open_rate: 0,
      click_through_rate: 0,
      reply_rate: 0
    }]);

    // Get per-campaign breakdown
    const campaigns = await sql`
      SELECT
        campaign_id,
        campaign_name,
        source,
        COUNT(*)::int as sent,
        COUNT(CASE WHEN status = 'delivered' THEN 1 END)::int as delivered,
        COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::int as opened,
        COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END)::int as replied,
        MIN(created_at) as started_at,
        MAX(updated_at) as last_activity
      FROM marketing.campaign_metrics
      ${sql.unsafe(whereClause)}
      GROUP BY campaign_id, campaign_name, source
      ORDER BY sent DESC
      LIMIT 20
    `.catch(() => []);

    // Get hourly trend
    const trend = await sql`
      SELECT
        DATE_TRUNC('hour', created_at) as hour,
        COUNT(*)::int as sent,
        COUNT(CASE WHEN opened_at IS NOT NULL THEN 1 END)::int as opened,
        COUNT(CASE WHEN replied_at IS NOT NULL THEN 1 END)::int as replied
      FROM marketing.campaign_metrics
      ${sql.unsafe(whereClause)}
      GROUP BY DATE_TRUNC('hour', created_at)
      ORDER BY hour ASC
    `.catch(() => []);

    const summaryData = summary[0] || {
      total_sent: 0,
      delivered: 0,
      opened: 0,
      clicked: 0,
      replied: 0,
      bounced: 0,
      open_rate: 0,
      click_through_rate: 0,
      reply_rate: 0
    };

    res.json({
      success: true,
      data: {
        summary: {
          sent: summaryData.total_sent,
          delivered: summaryData.delivered,
          opened: summaryData.opened,
          clicked: summaryData.clicked,
          replied: summaryData.replied,
          bounced: summaryData.bounced,
          openRate: parseFloat(summaryData.open_rate) || 0,
          clickThroughRate: parseFloat(summaryData.click_through_rate) || 0,
          replyRate: parseFloat(summaryData.reply_rate) || 0,
          timeWindow: `${hours}h`
        },
        campaigns: campaigns.map(campaign => ({
          campaignId: campaign.campaign_id,
          campaignName: campaign.campaign_name,
          source: campaign.source,
          sent: campaign.sent,
          delivered: campaign.delivered,
          opened: campaign.opened,
          replied: campaign.replied,
          openRate: campaign.sent > 0
            ? Math.round((campaign.opened / campaign.sent) * 100)
            : 0,
          replyRate: campaign.sent > 0
            ? Math.round((campaign.replied / campaign.sent) * 100)
            : 0,
          startedAt: campaign.started_at,
          lastActivity: campaign.last_activity
        })),
        trend: trend.map(point => ({
          hour: point.hour,
          sent: point.sent,
          opened: point.opened,
          replied: point.replied,
          openRate: point.sent > 0
            ? Math.round((point.opened / point.sent) * 100)
            : 0
        }))
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ Messaging metrics fetch error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to fetch messaging metrics',
      source: 'neon',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

export default router;
