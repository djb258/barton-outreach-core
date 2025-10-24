-- ════════════════════════════════════════════════════════════════════════════════
-- MIGRATION 008: Workflow Statistics Table
-- ════════════════════════════════════════════════════════════════════════════════
-- Purpose: Track n8n workflow execution stats for monitoring and analytics
-- Date: 2025-10-24
-- Dependencies: None
-- ════════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────────
-- 1. CREATE WORKFLOW STATS TABLE
-- ────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.workflow_stats (
  id SERIAL PRIMARY KEY,
  workflow_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('ok', 'error', 'timeout', 'cancelled')),
  duration_seconds NUMERIC,
  error_message TEXT,
  triggered_by TEXT, -- 'neon_event', 'schedule', 'manual', 'webhook'
  batch_id TEXT,
  record_id TEXT,
  metadata JSONB, -- Additional workflow-specific data
  created_at TIMESTAMP DEFAULT NOW()
);

-- ────────────────────────────────────────────────────────────────────────────────
-- 2. CREATE INDEXES
-- ────────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_workflow_stats_name ON marketing.workflow_stats(workflow_name);
CREATE INDEX IF NOT EXISTS idx_workflow_stats_status ON marketing.workflow_stats(status);
CREATE INDEX IF NOT EXISTS idx_workflow_stats_created ON marketing.workflow_stats(created_at);
CREATE INDEX IF NOT EXISTS idx_workflow_stats_batch ON marketing.workflow_stats(batch_id) WHERE batch_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_workflow_stats_name_created ON marketing.workflow_stats(workflow_name, created_at);

-- ────────────────────────────────────────────────────────────────────────────────
-- 3. ADD COMMENTS
-- ────────────────────────────────────────────────────────────────────────────────

COMMENT ON TABLE marketing.workflow_stats IS 'Execution statistics for n8n workflows - logged by WF_LogToNeon';
COMMENT ON COLUMN marketing.workflow_stats.workflow_name IS 'Name of the n8n workflow that executed';
COMMENT ON COLUMN marketing.workflow_stats.status IS 'Execution result: ok, error, timeout, or cancelled';
COMMENT ON COLUMN marketing.workflow_stats.duration_seconds IS 'How long the workflow took to execute';
COMMENT ON COLUMN marketing.workflow_stats.error_message IS 'Error details if status = error';
COMMENT ON COLUMN marketing.workflow_stats.triggered_by IS 'What triggered the workflow: neon_event, schedule, manual, webhook';
COMMENT ON COLUMN marketing.workflow_stats.batch_id IS 'Import batch ID if workflow processes a batch';
COMMENT ON COLUMN marketing.workflow_stats.record_id IS 'Specific record ID processed by workflow';
COMMENT ON COLUMN marketing.workflow_stats.metadata IS 'Additional workflow-specific data as JSON';

-- ────────────────────────────────────────────────────────────────────────────────
-- 4. CREATE HELPER VIEW: Recent Workflow Stats
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW marketing.v_workflow_stats_recent AS
SELECT
  workflow_name,
  status,
  duration_seconds,
  error_message,
  triggered_by,
  batch_id,
  created_at
FROM marketing.workflow_stats
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 1000;

COMMENT ON VIEW marketing.v_workflow_stats_recent IS 'Last 1000 workflow executions (max 24 hours)';

-- ────────────────────────────────────────────────────────────────────────────────
-- 5. CREATE HELPER VIEW: Workflow Summary by Name
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW marketing.v_workflow_summary AS
SELECT
  workflow_name,
  COUNT(*) as total_runs,
  COUNT(*) FILTER (WHERE status = 'ok') as successful_runs,
  COUNT(*) FILTER (WHERE status = 'error') as error_runs,
  COUNT(*) FILTER (WHERE status = 'timeout') as timeout_runs,
  ROUND(
    (COUNT(*) FILTER (WHERE status = 'error')::NUMERIC / NULLIF(COUNT(*), 0)) * 100,
    2
  ) as error_rate_pct,
  ROUND(AVG(duration_seconds), 2) as avg_duration_seconds,
  MAX(created_at) as last_run_at
FROM marketing.workflow_stats
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY workflow_name
ORDER BY total_runs DESC;

COMMENT ON VIEW marketing.v_workflow_summary IS 'Workflow performance summary (last 7 days)';

-- ────────────────────────────────────────────────────────────────────────────────
-- 6. CREATE HELPER VIEW: Hourly Stats (for monitoring)
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW marketing.v_workflow_stats_hourly AS
SELECT
  workflow_name,
  COUNT(*) AS runs_last_hour,
  SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) AS errors_last_hour,
  ROUND(AVG(duration_seconds), 2) AS avg_duration,
  MAX(created_at) as last_run
FROM marketing.workflow_stats
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY workflow_name
ORDER BY errors_last_hour DESC, runs_last_hour DESC;

COMMENT ON VIEW marketing.v_workflow_stats_hourly IS 'Workflow stats for the last hour - used by WF_Monitor_LogToNeon';

-- ════════════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ════════════════════════════════════════════════════════════════════════════════

-- Check table exists
SELECT COUNT(*) as workflow_stats_exists
FROM information_schema.tables
WHERE table_schema = 'marketing'
  AND table_name = 'workflow_stats';

-- Check views exist
SELECT table_name
FROM information_schema.views
WHERE table_schema = 'marketing'
  AND table_name LIKE 'v_workflow%'
ORDER BY table_name;

-- ════════════════════════════════════════════════════════════════════════════════
-- SAMPLE QUERIES
-- ════════════════════════════════════════════════════════════════════════════════

-- Recent workflow runs
-- SELECT * FROM marketing.v_workflow_stats_recent LIMIT 20;

-- Workflow performance summary
-- SELECT * FROM marketing.v_workflow_summary;

-- Hourly stats (for alerts)
-- SELECT * FROM marketing.v_workflow_stats_hourly;

-- Find slow workflows
-- SELECT workflow_name, AVG(duration_seconds) as avg_duration
-- FROM marketing.workflow_stats
-- WHERE created_at > NOW() - INTERVAL '24 hours'
-- GROUP BY workflow_name
-- ORDER BY avg_duration DESC;

-- Find workflows with errors
-- SELECT workflow_name, error_message, created_at
-- FROM marketing.workflow_stats
-- WHERE status = 'error'
--   AND created_at > NOW() - INTERVAL '24 hours'
-- ORDER BY created_at DESC;

-- ════════════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION 008
-- ════════════════════════════════════════════════════════════════════════════════
