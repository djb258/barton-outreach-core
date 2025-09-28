/**
 * Dashboard Trends API - Step 6 Marketing Dashboard
 * Provides time-series trend data for Barton Doctrine pipeline performance
 *
 * Endpoints:
 * - GET /api/dashboard-trends?period=weekly
 * - GET /api/dashboard-trends?period=monthly
 * - GET /api/dashboard-trends?period=daily&days=30
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface WeeklyTrend {
  week_start: string;
  week_end: string;
  new_company_leads: number;
  new_people_leads: number;
  total_new_leads: number;
  weekly_closed_won: number;
  weekly_closed_lost: number;
  weekly_revenue: number;
  weekly_win_rate: number;
  weekly_email_attributions: number;
  weekly_linkedin_attributions: number;
  weekly_phone_attributions: number;
  revenue_4week_avg: number;
  closed_won_4week_avg: number;
}

interface MonthlyTrend {
  month_start: string;
  month_end: string;
  new_company_leads: number;
  new_people_leads: number;
  total_new_leads: number;
  monthly_closed_won: number;
  monthly_closed_lost: number;
  monthly_revenue: number;
  monthly_win_rate: number;
  monthly_email_attributions: number;
  monthly_linkedin_attributions: number;
  monthly_phone_attributions: number;
  revenue_3month_avg: number;
  closed_won_3month_avg: number;
}

interface DailyTrend {
  date: string;
  new_company_leads: number;
  new_people_leads: number;
  total_new_leads: number;
  daily_closed_won: number;
  daily_closed_lost: number;
  daily_revenue: number;
  daily_win_rate: number;
  revenue_7day_avg: number;
  closed_won_7day_avg: number;
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const {
      period = 'weekly',
      days = '90',
      weeks = '12',
      months = '12',
      refresh = 'false'
    } = req.query;

    console.log(`[DASHBOARD-TRENDS] Fetching ${period} trends`);

    // Refresh materialized views if requested
    if (refresh === 'true') {
      await refreshTrendViews(bridge);
    }

    switch (period) {
      case 'weekly':
        const weeklyTrends = await getWeeklyTrends(bridge, parseInt(weeks));
        return res.status(200).json({
          success: true,
          data: {
            trends: weeklyTrends,
            period: 'weekly',
            weeks: parseInt(weeks)
          }
        });

      case 'monthly':
        const monthlyTrends = await getMonthlyTrends(bridge, parseInt(months));
        return res.status(200).json({
          success: true,
          data: {
            trends: monthlyTrends,
            period: 'monthly',
            months: parseInt(months)
          }
        });

      case 'daily':
        const dailyTrends = await getDailyTrends(bridge, parseInt(days));
        return res.status(200).json({
          success: true,
          data: {
            trends: dailyTrends,
            period: 'daily',
            days: parseInt(days)
          }
        });

      default:
        return res.status(400).json({
          error: 'Invalid period',
          message: 'Period must be one of: weekly, monthly, daily',
          supported_periods: ['weekly', 'monthly', 'daily']
        });
    }

  } catch (error: any) {
    console.error('[DASHBOARD-TRENDS] Failed:', error);
    return res.status(500).json({
      error: 'Dashboard trends fetch failed',
      message: error.message
    });
  }
}

/**
 * Get weekly trend data from materialized view
 */
async function getWeeklyTrends(bridge: StandardComposioNeonBridge, weeks: number = 12): Promise<WeeklyTrend[]> {
  const query = `
    SELECT
      week_start::date,
      week_end::date,
      new_company_leads,
      new_people_leads,
      total_new_leads,
      weekly_closed_won,
      weekly_closed_lost,
      weekly_revenue,
      weekly_win_rate,
      weekly_email_attributions,
      weekly_linkedin_attributions,
      weekly_phone_attributions,
      revenue_4week_avg,
      closed_won_4week_avg
    FROM marketing.dashboard_trends_weekly
    WHERE week_start >= CURRENT_DATE - INTERVAL '${weeks} weeks'
    ORDER BY week_start DESC
    LIMIT ${weeks}
  `;

  const result = await bridge.query(query);

  return result.rows.map(row => ({
    week_start: row.week_start,
    week_end: row.week_end,
    new_company_leads: parseInt(row.new_company_leads) || 0,
    new_people_leads: parseInt(row.new_people_leads) || 0,
    total_new_leads: parseInt(row.total_new_leads) || 0,
    weekly_closed_won: parseInt(row.weekly_closed_won) || 0,
    weekly_closed_lost: parseInt(row.weekly_closed_lost) || 0,
    weekly_revenue: parseFloat(row.weekly_revenue) || 0,
    weekly_win_rate: parseFloat(row.weekly_win_rate) || 0,
    weekly_email_attributions: parseInt(row.weekly_email_attributions) || 0,
    weekly_linkedin_attributions: parseInt(row.weekly_linkedin_attributions) || 0,
    weekly_phone_attributions: parseInt(row.weekly_phone_attributions) || 0,
    revenue_4week_avg: parseFloat(row.revenue_4week_avg) || 0,
    closed_won_4week_avg: parseFloat(row.closed_won_4week_avg) || 0
  }));
}

/**
 * Get monthly trend data (aggregated from weekly/daily data)
 */
async function getMonthlyTrends(bridge: StandardComposioNeonBridge, months: number = 12): Promise<MonthlyTrend[]> {
  const query = `
    WITH monthly_attribution_data AS (
      SELECT
        DATE_TRUNC('month', created_at) AS month_start,
        COUNT(*) FILTER (WHERE outcome = 'closed_won') AS monthly_closed_won,
        COUNT(*) FILTER (WHERE outcome = 'closed_lost') AS monthly_closed_lost,
        SUM(COALESCE(revenue_amount, 0)) FILTER (WHERE outcome = 'closed_won') AS monthly_revenue,
        COUNT(*) FILTER (WHERE touchpoint_sequence::text ILIKE '%email%') AS monthly_email_attributions,
        COUNT(*) FILTER (WHERE touchpoint_sequence::text ILIKE '%linkedin%') AS monthly_linkedin_attributions,
        COUNT(*) FILTER (WHERE touchpoint_sequence::text ILIKE '%phone%') AS monthly_phone_attributions
      FROM marketing.closed_loop_attribution
      WHERE created_at >= CURRENT_DATE - INTERVAL '${months} months'
      GROUP BY DATE_TRUNC('month', created_at)
    ),
    monthly_intake_data AS (
      SELECT
        DATE_TRUNC('month', created_at) AS month_start,
        COUNT(*) AS new_company_leads
      FROM intake.company_raw_intake
      WHERE created_at >= CURRENT_DATE - INTERVAL '${months} months'
      GROUP BY DATE_TRUNC('month', created_at)

      UNION ALL

      SELECT
        DATE_TRUNC('month', created_at) AS month_start,
        COUNT(*) AS new_people_leads
      FROM intake.people_raw_intake
      WHERE created_at >= CURRENT_DATE - INTERVAL '${months} months'
      GROUP BY DATE_TRUNC('month', created_at)
    )
    SELECT
      a.month_start::date,
      (a.month_start + INTERVAL '1 month' - INTERVAL '1 day')::date AS month_end,
      COALESCE(SUM(i.new_company_leads) FILTER (WHERE i.month_start IS NOT NULL), 0) AS new_company_leads,
      COALESCE(SUM(i.new_people_leads) FILTER (WHERE i.month_start IS NOT NULL), 0) AS new_people_leads,
      COALESCE(SUM(i.new_company_leads + i.new_people_leads) FILTER (WHERE i.month_start IS NOT NULL), 0) AS total_new_leads,
      a.monthly_closed_won,
      a.monthly_closed_lost,
      a.monthly_revenue,
      ROUND(100.0 * a.monthly_closed_won / NULLIF(a.monthly_closed_won + a.monthly_closed_lost, 0), 1) AS monthly_win_rate,
      a.monthly_email_attributions,
      a.monthly_linkedin_attributions,
      a.monthly_phone_attributions,
      ROUND(AVG(a.monthly_revenue) OVER (
        ORDER BY a.month_start ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
      ), 0) AS revenue_3month_avg,
      ROUND(AVG(a.monthly_closed_won) OVER (
        ORDER BY a.month_start ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
      ), 1) AS closed_won_3month_avg
    FROM monthly_attribution_data a
    LEFT JOIN monthly_intake_data i ON a.month_start = i.month_start
    ORDER BY a.month_start DESC
    LIMIT ${months}
  `;

  const result = await bridge.query(query);

  return result.rows.map(row => ({
    month_start: row.month_start,
    month_end: row.month_end,
    new_company_leads: parseInt(row.new_company_leads) || 0,
    new_people_leads: parseInt(row.new_people_leads) || 0,
    total_new_leads: parseInt(row.total_new_leads) || 0,
    monthly_closed_won: parseInt(row.monthly_closed_won) || 0,
    monthly_closed_lost: parseInt(row.monthly_closed_lost) || 0,
    monthly_revenue: parseFloat(row.monthly_revenue) || 0,
    monthly_win_rate: parseFloat(row.monthly_win_rate) || 0,
    monthly_email_attributions: parseInt(row.monthly_email_attributions) || 0,
    monthly_linkedin_attributions: parseInt(row.monthly_linkedin_attributions) || 0,
    monthly_phone_attributions: parseInt(row.monthly_phone_attributions) || 0,
    revenue_3month_avg: parseFloat(row.revenue_3month_avg) || 0,
    closed_won_3month_avg: parseFloat(row.closed_won_3month_avg) || 0
  }));
}

/**
 * Get daily trend data (for recent performance tracking)
 */
async function getDailyTrends(bridge: StandardComposioNeonBridge, days: number = 30): Promise<DailyTrend[]> {
  const query = `
    WITH daily_attribution_data AS (
      SELECT
        DATE(created_at) AS date,
        COUNT(*) FILTER (WHERE outcome = 'closed_won') AS daily_closed_won,
        COUNT(*) FILTER (WHERE outcome = 'closed_lost') AS daily_closed_lost,
        SUM(COALESCE(revenue_amount, 0)) FILTER (WHERE outcome = 'closed_won') AS daily_revenue
      FROM marketing.closed_loop_attribution
      WHERE created_at >= CURRENT_DATE - INTERVAL '${days} days'
      GROUP BY DATE(created_at)
    ),
    daily_intake_data AS (
      SELECT
        DATE(created_at) AS date,
        COUNT(*) AS new_company_leads
      FROM intake.company_raw_intake
      WHERE created_at >= CURRENT_DATE - INTERVAL '${days} days'
      GROUP BY DATE(created_at)

      UNION ALL

      SELECT
        DATE(created_at) AS date,
        COUNT(*) AS new_people_leads
      FROM intake.people_raw_intake
      WHERE created_at >= CURRENT_DATE - INTERVAL '${days} days'
      GROUP BY DATE(created_at)
    ),
    date_series AS (
      SELECT generate_series(
        CURRENT_DATE - INTERVAL '${days} days',
        CURRENT_DATE,
        INTERVAL '1 day'
      )::date AS date
    )
    SELECT
      ds.date,
      COALESCE(SUM(i.new_company_leads) FILTER (WHERE i.date = ds.date), 0) AS new_company_leads,
      COALESCE(SUM(i.new_people_leads) FILTER (WHERE i.date = ds.date), 0) AS new_people_leads,
      COALESCE(SUM(i.new_company_leads + i.new_people_leads) FILTER (WHERE i.date = ds.date), 0) AS total_new_leads,
      COALESCE(a.daily_closed_won, 0) AS daily_closed_won,
      COALESCE(a.daily_closed_lost, 0) AS daily_closed_lost,
      COALESCE(a.daily_revenue, 0) AS daily_revenue,
      ROUND(100.0 * COALESCE(a.daily_closed_won, 0) / NULLIF(COALESCE(a.daily_closed_won, 0) + COALESCE(a.daily_closed_lost, 0), 0), 1) AS daily_win_rate,
      ROUND(AVG(COALESCE(a.daily_revenue, 0)) OVER (
        ORDER BY ds.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
      ), 0) AS revenue_7day_avg,
      ROUND(AVG(COALESCE(a.daily_closed_won, 0)) OVER (
        ORDER BY ds.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
      ), 1) AS closed_won_7day_avg
    FROM date_series ds
    LEFT JOIN daily_attribution_data a ON ds.date = a.date
    LEFT JOIN daily_intake_data i ON ds.date = i.date
    ORDER BY ds.date DESC
    LIMIT ${days}
  `;

  const result = await bridge.query(query);

  return result.rows.map(row => ({
    date: row.date,
    new_company_leads: parseInt(row.new_company_leads) || 0,
    new_people_leads: parseInt(row.new_people_leads) || 0,
    total_new_leads: parseInt(row.total_new_leads) || 0,
    daily_closed_won: parseInt(row.daily_closed_won) || 0,
    daily_closed_lost: parseInt(row.daily_closed_lost) || 0,
    daily_revenue: parseFloat(row.daily_revenue) || 0,
    daily_win_rate: parseFloat(row.daily_win_rate) || 0,
    revenue_7day_avg: parseFloat(row.revenue_7day_avg) || 0,
    closed_won_7day_avg: parseFloat(row.closed_won_7day_avg) || 0
  }));
}

/**
 * Refresh trend-related materialized views
 */
async function refreshTrendViews(bridge: StandardComposioNeonBridge): Promise<void> {
  console.log('[DASHBOARD-TRENDS] Refreshing trend materialized views');

  const refreshQueries = [
    'REFRESH MATERIALIZED VIEW marketing.dashboard_trends_weekly'
  ];

  for (const query of refreshQueries) {
    try {
      await bridge.query(query);
    } catch (error) {
      console.error(`[DASHBOARD-TRENDS] Failed to refresh view: ${query}`, error);
      // Continue with other views even if one fails
    }
  }

  console.log('[DASHBOARD-TRENDS] Trend views refreshed');
}