-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-4C099B20
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

/**
 * Step 6: Marketing Dashboard - Materialized Views Migration
 * Creates performance views for Barton Doctrine pipeline dashboard
 *
 * Views created:
 * - dashboard_pipeline_health: Lead flow through pipeline stages
 * - dashboard_data_quality: Data validation and accuracy metrics
 * - dashboard_campaign_performance: PLE vs BIT campaign effectiveness
 * - dashboard_attribution_summary: Revenue outcomes and conversion tracking
 * - dashboard_trends_weekly: Time-series performance data
 */

-- Ensure marketing schema exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- Drop existing views if they exist (for migrations/updates)
DROP MATERIALIZED VIEW IF EXISTS marketing.dashboard_pipeline_health CASCADE;
DROP MATERIALIZED VIEW IF EXISTS marketing.dashboard_data_quality CASCADE;
DROP MATERIALIZED VIEW IF EXISTS marketing.dashboard_campaign_performance CASCADE;
DROP MATERIALIZED VIEW IF EXISTS marketing.dashboard_attribution_summary CASCADE;
DROP MATERIALIZED VIEW IF EXISTS marketing.dashboard_trends_weekly CASCADE;

-- 1. Pipeline Health - Lead flow through Barton Doctrine stages
CREATE MATERIALIZED VIEW marketing.dashboard_pipeline_health AS
SELECT
  -- Total leads from intake
  (SELECT COUNT(*) FROM intake.company_raw_intake) AS total_company_leads,
  (SELECT COUNT(*) FROM intake.people_raw_intake) AS total_people_leads,

  -- Validated leads (Step 2)
  (SELECT COUNT(*) FROM intake.company_raw_intake WHERE status = 'validated') AS validated_companies,
  (SELECT COUNT(*) FROM intake.people_raw_intake WHERE status = 'validated') AS validated_people,

  -- Promoted leads (Step 4)
  (SELECT COUNT(*) FROM core.company_master_table WHERE promotion_status = 'promoted') AS promoted_companies,
  (SELECT COUNT(*) FROM core.people_master_table WHERE promotion_status = 'promoted') AS promoted_people,

  -- Cold Outreach (PLE) - companies/people with PLE scoring
  (SELECT COUNT(*) FROM core.company_master_table
   WHERE promotion_status = 'promoted' AND ple_score IS NOT NULL) AS cold_outreach_companies,
  (SELECT COUNT(*) FROM core.people_master_table
   WHERE promotion_status = 'promoted' AND ple_score IS NOT NULL) AS cold_outreach_people,

  -- Sniper Marketing (BIT) - companies/people with BIT signals
  (SELECT COUNT(*) FROM core.company_master_table
   WHERE promotion_status = 'promoted' AND bit_signals IS NOT NULL AND jsonb_array_length(bit_signals) > 0) AS sniper_companies,
  (SELECT COUNT(*) FROM core.people_master_table
   WHERE promotion_status = 'promoted' AND bit_signals IS NOT NULL AND jsonb_array_length(bit_signals) > 0) AS sniper_people,

  -- Conversion rates
  ROUND(100.0 * (SELECT COUNT(*) FROM intake.company_raw_intake WHERE status = 'validated') /
        NULLIF((SELECT COUNT(*) FROM intake.company_raw_intake), 0), 2) AS company_validation_rate,
  ROUND(100.0 * (SELECT COUNT(*) FROM intake.people_raw_intake WHERE status = 'validated') /
        NULLIF((SELECT COUNT(*) FROM intake.people_raw_intake), 0), 2) AS people_validation_rate,
  ROUND(100.0 * (SELECT COUNT(*) FROM core.company_master_table WHERE promotion_status = 'promoted') /
        NULLIF((SELECT COUNT(*) FROM intake.company_raw_intake WHERE status = 'validated'), 0), 2) AS company_promotion_rate,
  ROUND(100.0 * (SELECT COUNT(*) FROM core.people_master_table WHERE promotion_status = 'promoted') /
        NULLIF((SELECT COUNT(*) FROM intake.people_raw_intake WHERE status = 'validated'), 0), 2) AS people_promotion_rate,

  -- Pipeline efficiency
  ROUND(100.0 * (SELECT COUNT(*) FROM core.company_master_table WHERE promotion_status = 'promoted') /
        NULLIF((SELECT COUNT(*) FROM intake.company_raw_intake), 0), 2) AS end_to_end_company_efficiency,
  ROUND(100.0 * (SELECT COUNT(*) FROM core.people_master_table WHERE promotion_status = 'promoted') /
        NULLIF((SELECT COUNT(*) FROM intake.people_raw_intake), 0), 2) AS end_to_end_people_efficiency,

  -- Last updated
  NOW() AS last_updated;

-- 2. Data Quality Metrics - Validation accuracy and completeness
CREATE MATERIALIZED VIEW marketing.dashboard_data_quality AS
SELECT
  -- Email validation metrics
  ROUND(100.0 * COUNT(*) FILTER (WHERE email_status = 'valid') /
        NULLIF(COUNT(*) FILTER (WHERE email IS NOT NULL), 0), 1) AS email_deliverability_rate,
  ROUND(100.0 * COUNT(*) FILTER (WHERE email IS NOT NULL) /
        NULLIF(COUNT(*), 0), 1) AS email_completeness_rate,

  -- Phone validation metrics
  ROUND(100.0 * COUNT(*) FILTER (WHERE work_phone_e164 IS NOT NULL AND work_phone_e164 != '') /
        NULLIF(COUNT(*), 0), 1) AS phone_accuracy_rate,
  ROUND(100.0 * COUNT(*) FILTER (WHERE personal_phone_e164 IS NOT NULL AND personal_phone_e164 != '') /
        NULLIF(COUNT(*), 0), 1) AS personal_phone_accuracy_rate,

  -- LinkedIn profile matching
  ROUND(100.0 * COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL AND linkedin_url != '') /
        NULLIF(COUNT(*), 0), 1) AS linkedin_match_rate,

  -- Company data completeness
  ROUND(100.0 * COUNT(*) FILTER (WHERE company_name IS NOT NULL AND company_name != '') /
        NULLIF(COUNT(*), 0), 1) AS company_name_completeness,
  ROUND(100.0 * COUNT(*) FILTER (WHERE job_title IS NOT NULL AND job_title != '') /
        NULLIF(COUNT(*), 0), 1) AS job_title_completeness,

  -- Overall data quality score (average of key metrics)
  ROUND((
    COALESCE(100.0 * COUNT(*) FILTER (WHERE email_status = 'valid') /
             NULLIF(COUNT(*) FILTER (WHERE email IS NOT NULL), 0), 0) +
    COALESCE(100.0 * COUNT(*) FILTER (WHERE work_phone_e164 IS NOT NULL) /
             NULLIF(COUNT(*), 0), 0) +
    COALESCE(100.0 * COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL) /
             NULLIF(COUNT(*), 0), 0) +
    COALESCE(100.0 * COUNT(*) FILTER (WHERE company_name IS NOT NULL) /
             NULLIF(COUNT(*), 0), 0)
  ) / 4.0, 1) AS overall_quality_score,

  -- Record counts for context
  COUNT(*) AS total_people_records,
  COUNT(*) FILTER (WHERE promotion_status = 'promoted') AS promoted_people_records,

  -- Last updated
  NOW() AS last_updated
FROM core.people_master_table;

-- 3. Campaign Performance - PLE vs BIT effectiveness metrics
CREATE MATERIALIZED VIEW marketing.dashboard_campaign_performance AS
WITH campaign_stats AS (
  SELECT
    CASE
      WHEN campaign_type = 'PLE' OR campaign_name ILIKE '%cold%' OR campaign_name ILIKE '%ple%' THEN 'PLE'
      WHEN campaign_type = 'BIT' OR campaign_name ILIKE '%sniper%' OR campaign_name ILIKE '%bit%' THEN 'BIT'
      ELSE 'OTHER'
    END AS campaign_category,

    -- Email metrics
    SUM(COALESCE(emails_sent, 0)) AS total_emails_sent,
    SUM(COALESCE(emails_opened, 0)) AS total_emails_opened,
    SUM(COALESCE(emails_clicked, 0)) AS total_emails_clicked,
    SUM(COALESCE(emails_replied, 0)) AS total_emails_replied,

    -- Outreach metrics
    SUM(COALESCE(linkedin_messages_sent, 0)) AS total_linkedin_sent,
    SUM(COALESCE(linkedin_messages_opened, 0)) AS total_linkedin_opened,
    SUM(COALESCE(linkedin_messages_replied, 0)) AS total_linkedin_replied,

    -- Phone metrics
    SUM(COALESCE(phone_calls_made, 0)) AS total_calls_made,
    SUM(COALESCE(phone_calls_connected, 0)) AS total_calls_connected,
    SUM(COALESCE(phone_calls_meetings_booked, 0)) AS total_meetings_booked,

    COUNT(*) AS total_campaigns
  FROM marketing.campaign_activity
  WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
  GROUP BY campaign_category
)
SELECT
  campaign_category,

  -- Email performance rates
  ROUND(100.0 * total_emails_opened / NULLIF(total_emails_sent, 0), 1) AS email_open_rate,
  ROUND(100.0 * total_emails_clicked / NULLIF(total_emails_sent, 0), 1) AS email_click_rate,
  ROUND(100.0 * total_emails_replied / NULLIF(total_emails_sent, 0), 1) AS email_response_rate,

  -- LinkedIn performance rates
  ROUND(100.0 * total_linkedin_opened / NULLIF(total_linkedin_sent, 0), 1) AS linkedin_open_rate,
  ROUND(100.0 * total_linkedin_replied / NULLIF(total_linkedin_sent, 0), 1) AS linkedin_response_rate,

  -- Phone performance rates
  ROUND(100.0 * total_calls_connected / NULLIF(total_calls_made, 0), 1) AS phone_connect_rate,
  ROUND(100.0 * total_meetings_booked / NULLIF(total_calls_connected, 0), 1) AS meeting_booking_rate,

  -- Volume metrics
  total_emails_sent,
  total_linkedin_sent,
  total_calls_made,
  total_campaigns,

  -- Overall effectiveness (weighted average of key metrics)
  ROUND((
    COALESCE(100.0 * total_emails_replied / NULLIF(total_emails_sent, 0), 0) * 0.4 +
    COALESCE(100.0 * total_linkedin_replied / NULLIF(total_linkedin_sent, 0), 0) * 0.3 +
    COALESCE(100.0 * total_meetings_booked / NULLIF(total_calls_connected, 0), 0) * 0.3
  ), 1) AS overall_effectiveness_score,

  -- Last updated
  NOW() AS last_updated
FROM campaign_stats
ORDER BY campaign_category;

-- 4. Attribution Summary - Revenue outcomes and pipeline impact
CREATE MATERIALIZED VIEW marketing.dashboard_attribution_summary AS
SELECT
  outcome,
  COUNT(*) AS outcome_count,

  -- Revenue metrics
  SUM(COALESCE(revenue_amount, 0)) AS total_revenue,
  AVG(COALESCE(revenue_amount, 0)) AS average_revenue,
  ROUND(SUM(COALESCE(revenue_amount, 0)) / NULLIF(COUNT(*), 0), 0) AS revenue_per_outcome,

  -- Time metrics
  ROUND(AVG(COALESCE(sales_cycle_days, 0)), 1) AS avg_sales_cycle_days,
  ROUND(AVG(COALESCE(touchpoints_to_close, 0)), 1) AS avg_touchpoints_to_close,

  -- Attribution model breakdown
  COUNT(*) FILTER (WHERE attribution_model = 'first_touch') AS first_touch_attributions,
  COUNT(*) FILTER (WHERE attribution_model = 'last_touch') AS last_touch_attributions,
  COUNT(*) FILTER (WHERE attribution_model = 'multi_touch') AS multi_touch_attributions,

  -- CRM system breakdown
  COUNT(*) FILTER (WHERE crm_system = 'Salesforce') AS salesforce_outcomes,
  COUNT(*) FILTER (WHERE crm_system = 'HubSpot') AS hubspot_outcomes,
  COUNT(*) FILTER (WHERE crm_system = 'Pipedrive') AS pipedrive_outcomes,

  -- Confidence metrics
  ROUND(AVG(COALESCE(attribution_confidence, 1.0)) * 100, 1) AS avg_attribution_confidence,

  -- Time-based metrics
  COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') AS outcomes_last_30_days,
  COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '90 days') AS outcomes_last_90_days,

  -- Last updated
  NOW() AS last_updated
FROM marketing.closed_loop_attribution
WHERE created_at >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY outcome
ORDER BY total_revenue DESC, outcome_count DESC;

-- 5. Weekly Trends - Time-series data for dashboard charts
CREATE MATERIALIZED VIEW marketing.dashboard_trends_weekly AS
WITH weekly_data AS (
  SELECT
    DATE_TRUNC('week', created_at) AS week_start,

    -- Pipeline metrics
    COUNT(*) FILTER (WHERE 'company_raw_intake' = 'company_raw_intake') AS new_company_leads,
    COUNT(*) FILTER (WHERE 'people_raw_intake' = 'people_raw_intake') AS new_people_leads,

    -- Attribution metrics
    COUNT(*) FILTER (WHERE outcome = 'closed_won') AS weekly_closed_won,
    COUNT(*) FILTER (WHERE outcome = 'closed_lost') AS weekly_closed_lost,
    SUM(COALESCE(revenue_amount, 0)) FILTER (WHERE outcome = 'closed_won') AS weekly_revenue,

    -- Campaign metrics from attribution
    COUNT(*) FILTER (WHERE touchpoint_sequence::text ILIKE '%email%') AS weekly_email_attributions,
    COUNT(*) FILTER (WHERE touchpoint_sequence::text ILIKE '%linkedin%') AS weekly_linkedin_attributions,
    COUNT(*) FILTER (WHERE touchpoint_sequence::text ILIKE '%phone%') AS weekly_phone_attributions

  FROM marketing.closed_loop_attribution
  WHERE created_at >= CURRENT_DATE - INTERVAL '12 weeks'
  GROUP BY DATE_TRUNC('week', created_at)
)
SELECT
  week_start,
  week_start + INTERVAL '6 days' AS week_end,

  -- Pipeline growth
  new_company_leads,
  new_people_leads,
  new_company_leads + new_people_leads AS total_new_leads,

  -- Attribution outcomes
  weekly_closed_won,
  weekly_closed_lost,
  weekly_revenue,

  -- Win rate for the week
  ROUND(100.0 * weekly_closed_won / NULLIF(weekly_closed_won + weekly_closed_lost, 0), 1) AS weekly_win_rate,

  -- Channel attribution
  weekly_email_attributions,
  weekly_linkedin_attributions,
  weekly_phone_attributions,

  -- Moving averages (4-week)
  ROUND(AVG(weekly_revenue) OVER (
    ORDER BY week_start ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ), 0) AS revenue_4week_avg,

  ROUND(AVG(weekly_closed_won) OVER (
    ORDER BY week_start ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ), 1) AS closed_won_4week_avg,

  -- Last updated
  NOW() AS last_updated
FROM weekly_data
ORDER BY week_start DESC;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_dashboard_pipeline_health_updated ON marketing.dashboard_pipeline_health (last_updated);
CREATE INDEX IF NOT EXISTS idx_dashboard_data_quality_updated ON marketing.dashboard_data_quality (last_updated);
CREATE INDEX IF NOT EXISTS idx_dashboard_campaign_performance_category ON marketing.dashboard_campaign_performance (campaign_category);
CREATE INDEX IF NOT EXISTS idx_dashboard_attribution_outcome ON marketing.dashboard_attribution_summary (outcome);
CREATE INDEX IF NOT EXISTS idx_dashboard_trends_week ON marketing.dashboard_trends_weekly (week_start);

-- Refresh all materialized views initially
REFRESH MATERIALIZED VIEW marketing.dashboard_pipeline_health;
REFRESH MATERIALIZED VIEW marketing.dashboard_data_quality;
REFRESH MATERIALIZED VIEW marketing.dashboard_campaign_performance;
REFRESH MATERIALIZED VIEW marketing.dashboard_attribution_summary;
REFRESH MATERIALIZED VIEW marketing.dashboard_trends_weekly;

-- Grant permissions
GRANT SELECT ON marketing.dashboard_pipeline_health TO PUBLIC;
GRANT SELECT ON marketing.dashboard_data_quality TO PUBLIC;
GRANT SELECT ON marketing.dashboard_campaign_performance TO PUBLIC;
GRANT SELECT ON marketing.dashboard_attribution_summary TO PUBLIC;
GRANT SELECT ON marketing.dashboard_trends_weekly TO PUBLIC;

-- Add comments for documentation
COMMENT ON MATERIALIZED VIEW marketing.dashboard_pipeline_health IS
'Step 6 Dashboard - Pipeline health metrics showing lead flow through Barton Doctrine stages';

COMMENT ON MATERIALIZED VIEW marketing.dashboard_data_quality IS
'Step 6 Dashboard - Data validation and accuracy metrics for companies and people';

COMMENT ON MATERIALIZED VIEW marketing.dashboard_campaign_performance IS
'Step 6 Dashboard - Campaign effectiveness comparing PLE (Cold Outreach) vs BIT (Sniper Marketing)';

COMMENT ON MATERIALIZED VIEW marketing.dashboard_attribution_summary IS
'Step 6 Dashboard - Revenue attribution outcomes and conversion metrics';

COMMENT ON MATERIALIZED VIEW marketing.dashboard_trends_weekly IS
'Step 6 Dashboard - Time-series trends for pipeline and attribution metrics';