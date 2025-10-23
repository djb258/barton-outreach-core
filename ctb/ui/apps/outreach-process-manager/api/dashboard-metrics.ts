/**
 * Doctrine Spec:
 * - Barton ID: 09.01.01.07.10000.019
 * - Altitude: 10000 (Execution Layer)
 * - Input: metrics query parameters and date range
 * - Output: dashboard metrics and KPI data
 * - MCP: Composio (Neon integrated)
 */
/**
 * Dashboard Metrics API - Step 6 Marketing Dashboard
 * Provides real-time metrics from materialized views for Barton Doctrine pipeline
 *
 * Endpoints:
 * - GET /api/dashboard-metrics
 * - GET /api/dashboard-metrics?filter=pipeline_health
 * - GET /api/dashboard-metrics?filter=data_quality
 * - GET /api/dashboard-metrics?filter=campaign_performance
 * - GET /api/dashboard-metrics?filter=attribution_summary
 */

import { StandardComposioNeonBridge } from '../utils/standard-composio-neon-bridge';

interface PipelineHealthMetrics {
  total_company_leads: number;
  total_people_leads: number;
  validated_companies: number;
  validated_people: number;
  promoted_companies: number;
  promoted_people: number;
  cold_outreach_companies: number;
  cold_outreach_people: number;
  sniper_companies: number;
  sniper_people: number;
  company_validation_rate: number;
  people_validation_rate: number;
  company_promotion_rate: number;
  people_promotion_rate: number;
  end_to_end_company_efficiency: number;
  end_to_end_people_efficiency: number;
}

interface DataQualityMetrics {
  email_deliverability_rate: number;
  email_completeness_rate: number;
  phone_accuracy_rate: number;
  personal_phone_accuracy_rate: number;
  linkedin_match_rate: number;
  company_name_completeness: number;
  job_title_completeness: number;
  overall_quality_score: number;
  total_people_records: number;
  promoted_people_records: number;
}

interface CampaignPerformanceMetrics {
  PLE?: {
    email_open_rate: number;
    email_click_rate: number;
    email_response_rate: number;
    linkedin_open_rate: number;
    linkedin_response_rate: number;
    phone_connect_rate: number;
    meeting_booking_rate: number;
    total_emails_sent: number;
    total_linkedin_sent: number;
    total_calls_made: number;
    overall_effectiveness_score: number;
  };
  BIT?: {
    email_open_rate: number;
    email_click_rate: number;
    email_response_rate: number;
    linkedin_open_rate: number;
    linkedin_response_rate: number;
    phone_connect_rate: number;
    meeting_booking_rate: number;
    total_emails_sent: number;
    total_linkedin_sent: number;
    total_calls_made: number;
    overall_effectiveness_score: number;
  };
}

interface AttributionSummaryMetrics {
  closed_won: {
    count: number;
    total_revenue: number;
    average_revenue: number;
    avg_sales_cycle_days: number;
    avg_touchpoints_to_close: number;
  };
  closed_lost: {
    count: number;
    avg_sales_cycle_days: number;
    avg_touchpoints_to_close: number;
  };
  nurture: {
    count: number;
  };
  qualified: {
    count: number;
  };
  disqualified: {
    count: number;
  };
  churn: {
    count: number;
  };
}

export default async function handler(req: any, res: any) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const bridge = new StandardComposioNeonBridge();

  try {
    const { filter, refresh = 'false' } = req.query;

    console.log(`[DASHBOARD-METRICS] Fetching dashboard metrics (filter: ${filter || 'all'})`);

    // Refresh materialized views if requested
    if (refresh === 'true') {
      await refreshMaterializedViews(bridge);
    }

    switch (filter) {
      case 'pipeline_health':
        const pipelineHealth = await getPipelineHealthMetrics(bridge);
        return res.status(200).json({ success: true, data: { pipeline_health: pipelineHealth } });

      case 'data_quality':
        const dataQuality = await getDataQualityMetrics(bridge);
        return res.status(200).json({ success: true, data: { data_quality: dataQuality } });

      case 'campaign_performance':
        const campaignPerformance = await getCampaignPerformanceMetrics(bridge);
        return res.status(200).json({ success: true, data: { campaign_performance: campaignPerformance } });

      case 'attribution_summary':
        const attributionSummary = await getAttributionSummaryMetrics(bridge);
        return res.status(200).json({ success: true, data: { attribution_summary: attributionSummary } });

      default:
        // Return all metrics
        const allMetrics = await getAllDashboardMetrics(bridge);
        return res.status(200).json({ success: true, data: allMetrics });
    }

  } catch (error: any) {
    console.error('[DASHBOARD-METRICS] Failed:', error);
    return res.status(500).json({
      error: 'Dashboard metrics fetch failed',
      message: error.message
    });
  }
}

/**
 * Get all dashboard metrics from materialized views
 */
async function getAllDashboardMetrics(bridge: StandardComposioNeonBridge) {
  console.log('[DASHBOARD-METRICS] Fetching all metrics from materialized views');

  const [pipelineHealth, dataQuality, campaignPerformance, attributionSummary] = await Promise.all([
    getPipelineHealthMetrics(bridge),
    getDataQualityMetrics(bridge),
    getCampaignPerformanceMetrics(bridge),
    getAttributionSummaryMetrics(bridge)
  ]);

  return {
    pipeline_health: pipelineHealth,
    data_quality: dataQuality,
    campaign_performance: campaignPerformance,
    attribution_summary: attributionSummary,
    metadata: {
      generated_at: new Date().toISOString(),
      altitude: 10000,
      doctrine: 'BARTON',
      pipeline_step: '6_marketing_dashboard',
      data_sources: ['pipeline_health', 'data_quality', 'campaign_performance', 'attribution_summary']
    }
  };
}

/**
 * Get pipeline health metrics
 */
async function getPipelineHealthMetrics(bridge: StandardComposioNeonBridge): Promise<PipelineHealthMetrics> {
  const query = `
    SELECT
      total_company_leads,
      total_people_leads,
      validated_companies,
      validated_people,
      promoted_companies,
      promoted_people,
      cold_outreach_companies,
      cold_outreach_people,
      sniper_companies,
      sniper_people,
      company_validation_rate,
      people_validation_rate,
      company_promotion_rate,
      people_promotion_rate,
      end_to_end_company_efficiency,
      end_to_end_people_efficiency
    FROM marketing.dashboard_pipeline_health
    LIMIT 1
  `;

  const result = await bridge.query(query);

  if (result.rows.length === 0) {
    throw new Error('No pipeline health data available');
  }

  const row = result.rows[0];
  return {
    total_company_leads: parseInt(row.total_company_leads) || 0,
    total_people_leads: parseInt(row.total_people_leads) || 0,
    validated_companies: parseInt(row.validated_companies) || 0,
    validated_people: parseInt(row.validated_people) || 0,
    promoted_companies: parseInt(row.promoted_companies) || 0,
    promoted_people: parseInt(row.promoted_people) || 0,
    cold_outreach_companies: parseInt(row.cold_outreach_companies) || 0,
    cold_outreach_people: parseInt(row.cold_outreach_people) || 0,
    sniper_companies: parseInt(row.sniper_companies) || 0,
    sniper_people: parseInt(row.sniper_people) || 0,
    company_validation_rate: parseFloat(row.company_validation_rate) || 0,
    people_validation_rate: parseFloat(row.people_validation_rate) || 0,
    company_promotion_rate: parseFloat(row.company_promotion_rate) || 0,
    people_promotion_rate: parseFloat(row.people_promotion_rate) || 0,
    end_to_end_company_efficiency: parseFloat(row.end_to_end_company_efficiency) || 0,
    end_to_end_people_efficiency: parseFloat(row.end_to_end_people_efficiency) || 0
  };
}

/**
 * Get data quality metrics
 */
async function getDataQualityMetrics(bridge: StandardComposioNeonBridge): Promise<DataQualityMetrics> {
  const query = `
    SELECT
      email_deliverability_rate,
      email_completeness_rate,
      phone_accuracy_rate,
      personal_phone_accuracy_rate,
      linkedin_match_rate,
      company_name_completeness,
      job_title_completeness,
      overall_quality_score,
      total_people_records,
      promoted_people_records
    FROM marketing.dashboard_data_quality
    LIMIT 1
  `;

  const result = await bridge.query(query);

  if (result.rows.length === 0) {
    throw new Error('No data quality metrics available');
  }

  const row = result.rows[0];
  return {
    email_deliverability_rate: parseFloat(row.email_deliverability_rate) || 0,
    email_completeness_rate: parseFloat(row.email_completeness_rate) || 0,
    phone_accuracy_rate: parseFloat(row.phone_accuracy_rate) || 0,
    personal_phone_accuracy_rate: parseFloat(row.personal_phone_accuracy_rate) || 0,
    linkedin_match_rate: parseFloat(row.linkedin_match_rate) || 0,
    company_name_completeness: parseFloat(row.company_name_completeness) || 0,
    job_title_completeness: parseFloat(row.job_title_completeness) || 0,
    overall_quality_score: parseFloat(row.overall_quality_score) || 0,
    total_people_records: parseInt(row.total_people_records) || 0,
    promoted_people_records: parseInt(row.promoted_people_records) || 0
  };
}

/**
 * Get campaign performance metrics (PLE vs BIT)
 */
async function getCampaignPerformanceMetrics(bridge: StandardComposioNeonBridge): Promise<CampaignPerformanceMetrics> {
  const query = `
    SELECT
      campaign_category,
      email_open_rate,
      email_click_rate,
      email_response_rate,
      linkedin_open_rate,
      linkedin_response_rate,
      phone_connect_rate,
      meeting_booking_rate,
      total_emails_sent,
      total_linkedin_sent,
      total_calls_made,
      overall_effectiveness_score
    FROM marketing.dashboard_campaign_performance
    ORDER BY campaign_category
  `;

  const result = await bridge.query(query);
  const metrics: CampaignPerformanceMetrics = {};

  result.rows.forEach(row => {
    const category = row.campaign_category as 'PLE' | 'BIT';
    if (category === 'PLE' || category === 'BIT') {
      metrics[category] = {
        email_open_rate: parseFloat(row.email_open_rate) || 0,
        email_click_rate: parseFloat(row.email_click_rate) || 0,
        email_response_rate: parseFloat(row.email_response_rate) || 0,
        linkedin_open_rate: parseFloat(row.linkedin_open_rate) || 0,
        linkedin_response_rate: parseFloat(row.linkedin_response_rate) || 0,
        phone_connect_rate: parseFloat(row.phone_connect_rate) || 0,
        meeting_booking_rate: parseFloat(row.meeting_booking_rate) || 0,
        total_emails_sent: parseInt(row.total_emails_sent) || 0,
        total_linkedin_sent: parseInt(row.total_linkedin_sent) || 0,
        total_calls_made: parseInt(row.total_calls_made) || 0,
        overall_effectiveness_score: parseFloat(row.overall_effectiveness_score) || 0
      };
    }
  });

  return metrics;
}

/**
 * Get attribution summary metrics
 */
async function getAttributionSummaryMetrics(bridge: StandardComposioNeonBridge): Promise<AttributionSummaryMetrics> {
  const query = `
    SELECT
      outcome,
      outcome_count,
      total_revenue,
      average_revenue,
      avg_sales_cycle_days,
      avg_touchpoints_to_close
    FROM marketing.dashboard_attribution_summary
    ORDER BY outcome
  `;

  const result = await bridge.query(query);
  const metrics: any = {
    closed_won: { count: 0, total_revenue: 0, average_revenue: 0, avg_sales_cycle_days: 0, avg_touchpoints_to_close: 0 },
    closed_lost: { count: 0, avg_sales_cycle_days: 0, avg_touchpoints_to_close: 0 },
    nurture: { count: 0 },
    qualified: { count: 0 },
    disqualified: { count: 0 },
    churn: { count: 0 }
  };

  result.rows.forEach(row => {
    const outcome = row.outcome as keyof AttributionSummaryMetrics;
    if (metrics[outcome]) {
      metrics[outcome].count = parseInt(row.outcome_count) || 0;

      if (outcome === 'closed_won') {
        metrics[outcome].total_revenue = parseFloat(row.total_revenue) || 0;
        metrics[outcome].average_revenue = parseFloat(row.average_revenue) || 0;
        metrics[outcome].avg_sales_cycle_days = parseFloat(row.avg_sales_cycle_days) || 0;
        metrics[outcome].avg_touchpoints_to_close = parseFloat(row.avg_touchpoints_to_close) || 0;
      } else if (outcome === 'closed_lost') {
        metrics[outcome].avg_sales_cycle_days = parseFloat(row.avg_sales_cycle_days) || 0;
        metrics[outcome].avg_touchpoints_to_close = parseFloat(row.avg_touchpoints_to_close) || 0;
      }
    }
  });

  return metrics as AttributionSummaryMetrics;
}

/**
 * Refresh all materialized views
 */
async function refreshMaterializedViews(bridge: StandardComposioNeonBridge): Promise<void> {
  console.log('[DASHBOARD-METRICS] Refreshing materialized views');

  const refreshQueries = [
    'REFRESH MATERIALIZED VIEW marketing.dashboard_pipeline_health',
    'REFRESH MATERIALIZED VIEW marketing.dashboard_data_quality',
    'REFRESH MATERIALIZED VIEW marketing.dashboard_campaign_performance',
    'REFRESH MATERIALIZED VIEW marketing.dashboard_attribution_summary'
  ];

  for (const query of refreshQueries) {
    try {
      await bridge.query(query);
    } catch (error) {
      console.error(`[DASHBOARD-METRICS] Failed to refresh view: ${query}`, error);
      // Continue with other views even if one fails
    }
  }

  console.log('[DASHBOARD-METRICS] Materialized views refreshed');
}