-- ════════════════════════════════════════════════════════════════════════════════
-- MIGRATION 009: Dashboard Views for Outreach Command Center
-- ════════════════════════════════════════════════════════════════════════════════
-- Purpose: Create views for UI dashboard showing phase stats and errors
-- Date: 2025-10-24
-- Dependencies: 007_fix_event_triggers.sql, 008_workflow_stats.sql
-- ════════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────────
-- 1. PHASE STATISTICS VIEW
-- ────────────────────────────────────────────────────────────────────────────────
-- Categorize workflows into phases and calculate error rates

DROP VIEW IF EXISTS marketing.v_phase_stats CASCADE;

CREATE VIEW marketing.v_phase_stats AS
SELECT
  CASE
    WHEN workflow_name ILIKE '%validate%' OR workflow_name ILIKE '%enrich%' OR workflow_name ILIKE '%verify%' THEN 'enrichment'
    WHEN workflow_name ILIKE '%ple%' OR workflow_name ILIKE '%bit%' OR workflow_name ILIKE '%intelligence%' THEN 'intelligence'
    WHEN workflow_name ILIKE '%message%' OR workflow_name ILIKE '%write%' OR workflow_name ILIKE '%campaign%' THEN 'messaging'
    WHEN workflow_name ILIKE '%promote%' OR workflow_name ILIKE '%send%' OR workflow_name ILIKE '%launch%' OR workflow_name ILIKE '%slot%' THEN 'delivery'
    ELSE 'other'
  END AS phase,
  COUNT(*) AS total_runs,
  SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS errors,
  ROUND((SUM(CASE WHEN status='error' THEN 1 ELSE 0 END)::NUMERIC / NULLIF(COUNT(*), 0)) * 100, 2) AS error_rate,
  ROUND(AVG(duration_seconds), 2) AS avg_duration
FROM marketing.workflow_stats
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;

COMMENT ON VIEW marketing.v_phase_stats IS 'Pipeline phase statistics (enrichment, intelligence, messaging, delivery) for last 24 hours';

-- ────────────────────────────────────────────────────────────────────────────────
-- 2. RECENT ERRORS VIEW
-- ────────────────────────────────────────────────────────────────────────────────
-- Show last 200 pipeline errors for error console

DROP VIEW IF EXISTS marketing.v_error_recent CASCADE;

CREATE VIEW marketing.v_error_recent AS
SELECT
  id,
  event_type,
  record_id,
  error_message,
  severity,
  resolved,
  created_at
FROM marketing.pipeline_errors
WHERE created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC
LIMIT 200;

COMMENT ON VIEW marketing.v_error_recent IS 'Last 200 pipeline errors (max 7 days) for error console';

-- ────────────────────────────────────────────────────────────────────────────────
-- 3. SNIPER TARGETS VIEW (Intelligence Layer)
-- ────────────────────────────────────────────────────────────────────────────────
-- High-value targets identified by PLE/BIT scoring

-- Create placeholder tables if they don't exist yet
CREATE TABLE IF NOT EXISTS marketing.ple_results (
  id SERIAL PRIMARY KEY,
  company_id TEXT NOT NULL,
  ple_score NUMERIC DEFAULT 0,
  ple_model_version TEXT,
  calculated_at TIMESTAMP DEFAULT NOW(),
  metadata JSONB
);

COMMENT ON TABLE marketing.ple_results IS 'Pipeline Learning Engine (PLE) scoring results - AI-driven lead scoring';

CREATE TABLE IF NOT EXISTS marketing.bit_signals (
  id SERIAL PRIMARY KEY,
  company_id TEXT NOT NULL,
  bit_intent_score NUMERIC DEFAULT 0,
  signal_type TEXT, -- 'website_visit', 'email_open', 'content_download', etc.
  signal_timestamp TIMESTAMP,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE marketing.bit_signals IS 'Barton Intelligence Tracker (BIT) intent signals - buyer behavior tracking';

DROP VIEW IF EXISTS marketing.v_sniper_targets CASCADE;

CREATE VIEW marketing.v_sniper_targets AS
SELECT
  COALESCE(p.company_id, b.company_id) as company_id,
  p.ple_score,
  MAX(b.bit_intent_score) as bit_intent_score,
  MAX(p.calculated_at) as ple_updated_at,
  MAX(b.signal_timestamp) as last_signal_at
FROM marketing.ple_results p
FULL OUTER JOIN marketing.bit_signals b ON p.company_id = b.company_id
WHERE p.ple_score > 0.75 OR b.bit_intent_score > 0.75
GROUP BY COALESCE(p.company_id, b.company_id), p.ple_score
ORDER BY GREATEST(COALESCE(p.ple_score, 0), COALESCE(MAX(b.bit_intent_score), 0)) DESC;

COMMENT ON VIEW marketing.v_sniper_targets IS 'High-value targets (PLE score > 0.75 or BIT intent > 0.75) for priority outreach';

-- ────────────────────────────────────────────────────────────────────────────────
-- 4. WORKFLOW HEALTH DASHBOARD VIEW
-- ────────────────────────────────────────────────────────────────────────────────
-- Overall system health metrics

DROP VIEW IF EXISTS marketing.v_workflow_health CASCADE;

CREATE VIEW marketing.v_workflow_health AS
WITH recent_stats AS (
  SELECT
    workflow_name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
    AVG(duration_seconds) as avg_duration,
    MAX(created_at) as last_run
  FROM marketing.workflow_stats
  WHERE created_at > NOW() - INTERVAL '1 hour'
  GROUP BY workflow_name
)
SELECT
  workflow_name,
  total_runs,
  error_count,
  ROUND((error_count::NUMERIC / NULLIF(total_runs, 0)) * 100, 2) as error_rate_pct,
  ROUND(avg_duration, 2) as avg_duration_sec,
  last_run,
  CASE
    WHEN error_rate_pct > 10 THEN 'critical'
    WHEN error_rate_pct > 5 THEN 'warning'
    WHEN total_runs = 0 THEN 'idle'
    ELSE 'healthy'
  END as health_status
FROM recent_stats
ORDER BY error_rate_pct DESC, total_runs DESC;

COMMENT ON VIEW marketing.v_workflow_health IS 'Workflow health status for last hour - shows critical/warning/healthy/idle';

-- ────────────────────────────────────────────────────────────────────────────────
-- 5. EVENT QUEUE STATUS VIEW
-- ────────────────────────────────────────────────────────────────────────────────
-- Real-time event queue monitoring

DROP VIEW IF EXISTS marketing.v_event_queue_status CASCADE;

CREATE VIEW marketing.v_event_queue_status AS
SELECT
  event_type,
  COUNT(*) as pending_count,
  MIN(created_at) as oldest_pending,
  MAX(created_at) as newest_pending,
  ROUND(
    EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) / 60,
    2
  ) as oldest_age_minutes
FROM marketing.pipeline_events
WHERE status = 'pending'
GROUP BY event_type
ORDER BY oldest_age_minutes DESC, pending_count DESC;

COMMENT ON VIEW marketing.v_event_queue_status IS 'Pending events by type with age - alerts if events are stuck';

-- ────────────────────────────────────────────────────────────────────────────────
-- 6. DAILY THROUGHPUT VIEW
-- ────────────────────────────────────────────────────────────────────────────────
-- Daily processing volume metrics

DROP VIEW IF EXISTS marketing.v_daily_throughput CASCADE;

CREATE VIEW marketing.v_daily_throughput AS
SELECT
  DATE(created_at) as date,
  COUNT(*) as total_events,
  COUNT(*) FILTER (WHERE status = 'processed') as processed_events,
  COUNT(*) FILTER (WHERE status = 'failed') as failed_events,
  COUNT(*) FILTER (WHERE status = 'pending') as pending_events,
  ROUND(
    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))),
    2
  ) as avg_processing_time_seconds
FROM marketing.pipeline_events
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

COMMENT ON VIEW marketing.v_daily_throughput IS 'Daily event processing volume and performance (last 30 days)';

-- ════════════════════════════════════════════════════════════════════════════════
-- VERIFICATION
-- ════════════════════════════════════════════════════════════════════════════════

SELECT
  table_name as view_name,
  'marketing' as schema
FROM information_schema.views
WHERE table_schema = 'marketing'
  AND table_name LIKE 'v_%'
ORDER BY table_name;

-- ════════════════════════════════════════════════════════════════════════════════
-- SAMPLE QUERIES FOR DASHBOARD
-- ════════════════════════════════════════════════════════════════════════════════

-- Phase stats for dashboard cards
-- SELECT * FROM marketing.v_phase_stats;

-- Recent errors for error console
-- SELECT * FROM marketing.v_error_recent LIMIT 50;

-- High-value targets for sales team
-- SELECT * FROM marketing.v_sniper_targets LIMIT 20;

-- Overall workflow health
-- SELECT * FROM marketing.v_workflow_health;

-- Event queue status (check for stuck events)
-- SELECT * FROM marketing.v_event_queue_status;

-- Daily throughput trends
-- SELECT * FROM marketing.v_daily_throughput ORDER BY date DESC LIMIT 7;

-- ════════════════════════════════════════════════════════════════════════════════
-- GRANT PERMISSIONS (if using read-only dashboard user)
-- ════════════════════════════════════════════════════════════════════════════════

-- GRANT SELECT ON ALL TABLES IN SCHEMA marketing TO dashboard_user;
-- GRANT USAGE ON SCHEMA marketing TO dashboard_user;

-- ════════════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION 009
-- ════════════════════════════════════════════════════════════════════════════════
