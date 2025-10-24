-- ════════════════════════════════════════════════════════════════════════════════
-- PIPELINE ERROR LOGGING SYSTEM
-- ════════════════════════════════════════════════════════════════════════════════
-- Purpose: Centralized error tracking for event-driven pipeline
-- Author: Pipeline Automation Team
-- Date: 2025-10-24
-- ════════════════════════════════════════════════════════════════════════════════

-- ────────────────────────────────────────────────────────────────────────────────
-- 1. CREATE ERROR LOG TABLE
-- ────────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.pipeline_errors (
  id SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  record_id TEXT NOT NULL, -- Could be INT, TEXT, or UUID depending on source
  error_message TEXT NOT NULL,
  error_details JSONB, -- Stack trace, response codes, etc.
  severity TEXT DEFAULT 'error' CHECK (severity IN ('warning', 'error', 'critical')),
  resolved BOOLEAN DEFAULT FALSE,
  resolved_at TIMESTAMP,
  resolved_by TEXT,
  resolution_notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_errors_event ON marketing.pipeline_errors(event_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_errors_record ON marketing.pipeline_errors(record_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_errors_resolved ON marketing.pipeline_errors(resolved, created_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_errors_severity ON marketing.pipeline_errors(severity);

COMMENT ON TABLE marketing.pipeline_errors IS 'Centralized error log for all pipeline stages';
COMMENT ON COLUMN marketing.pipeline_errors.event_type IS 'Pipeline stage: company_created, company_validated, company_promoted, slots_created, contact_enriched, email_verified';
COMMENT ON COLUMN marketing.pipeline_errors.record_id IS 'Identifier of the record that failed (company ID, slot ID, etc.)';
COMMENT ON COLUMN marketing.pipeline_errors.error_details IS 'JSON object with stack traces, API responses, retry counts, etc.';
COMMENT ON COLUMN marketing.pipeline_errors.severity IS 'Error severity: warning (recoverable), error (needs attention), critical (blocking)';

-- ────────────────────────────────────────────────────────────────────────────────
-- 2. HELPER FUNCTION: Log Pipeline Error
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION marketing.log_pipeline_error(
  p_event_type TEXT,
  p_record_id TEXT,
  p_error_message TEXT,
  p_error_details JSONB DEFAULT NULL,
  p_severity TEXT DEFAULT 'error'
)
RETURNS INT AS $$
DECLARE
  error_id INT;
BEGIN
  INSERT INTO marketing.pipeline_errors (
    event_type,
    record_id,
    error_message,
    error_details,
    severity
  ) VALUES (
    p_event_type,
    p_record_id,
    p_error_message,
    p_error_details,
    p_severity
  )
  RETURNING id INTO error_id;

  -- Also mark the corresponding pipeline event as failed if it exists
  UPDATE marketing.pipeline_events
  SET status = 'failed',
      error_message = p_error_message,
      processed_at = NOW()
  WHERE payload->>'record_id' = p_record_id
    AND event_type = p_event_type
    AND status IN ('pending', 'processing');

  RETURN error_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.log_pipeline_error IS 'Log pipeline error and update corresponding event status - called by n8n error handlers';

-- ────────────────────────────────────────────────────────────────────────────────
-- 3. HELPER FUNCTION: Resolve Error
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION marketing.resolve_pipeline_error(
  p_error_id INT,
  p_resolved_by TEXT,
  p_resolution_notes TEXT
)
RETURNS VOID AS $$
BEGIN
  UPDATE marketing.pipeline_errors
  SET resolved = TRUE,
      resolved_at = NOW(),
      resolved_by = p_resolved_by,
      resolution_notes = p_resolution_notes
  WHERE id = p_error_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.resolve_pipeline_error IS 'Mark error as resolved with resolution notes';

-- ────────────────────────────────────────────────────────────────────────────────
-- 4. VIEW: Unresolved Errors Summary
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW marketing.vw_unresolved_errors AS
SELECT
  event_type,
  severity,
  COUNT(*) as error_count,
  MAX(created_at) as latest_error,
  array_agg(DISTINCT error_message) as error_messages
FROM marketing.pipeline_errors
WHERE resolved = FALSE
GROUP BY event_type, severity
ORDER BY
  CASE severity
    WHEN 'critical' THEN 1
    WHEN 'error' THEN 2
    WHEN 'warning' THEN 3
  END,
  latest_error DESC;

COMMENT ON VIEW marketing.vw_unresolved_errors IS 'Summary of unresolved errors by event type and severity';

-- ────────────────────────────────────────────────────────────────────────────────
-- 5. VIEW: Error Rate by Stage (Last 24 Hours)
-- ────────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW marketing.vw_error_rate_24h AS
SELECT
  event_type,
  COUNT(*) as total_errors,
  COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
  COUNT(*) FILTER (WHERE severity = 'error') as error_count,
  COUNT(*) FILTER (WHERE severity = 'warning') as warning_count,
  COUNT(*) FILTER (WHERE resolved = TRUE) as resolved_count,
  ROUND(
    COUNT(*) FILTER (WHERE resolved = TRUE)::NUMERIC / NULLIF(COUNT(*), 0) * 100,
    2
  ) as resolution_rate_pct
FROM marketing.pipeline_errors
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY event_type
ORDER BY total_errors DESC;

COMMENT ON VIEW marketing.vw_error_rate_24h IS 'Error metrics by pipeline stage for last 24 hours';

-- ────────────────────────────────────────────────────────────────────────────────
-- 6. SAMPLE USAGE
-- ────────────────────────────────────────────────────────────────────────────────

-- Log an error from n8n workflow
-- SELECT marketing.log_pipeline_error(
--   'company_validated',
--   '12345',
--   'Failed to promote company: Barton ID constraint violation',
--   jsonb_build_object(
--     'http_status', 500,
--     'barton_id', '04.04.01.00001.001',
--     'constraint', 'company_master_barton_id_format'
--   ),
--   'error'
-- );

-- Resolve an error
-- SELECT marketing.resolve_pipeline_error(
--   1,
--   'admin@example.com',
--   'Fixed Barton ID generation format - reprocessed batch'
-- );

-- Check unresolved errors
-- SELECT * FROM marketing.vw_unresolved_errors;

-- Check error rate
-- SELECT * FROM marketing.vw_error_rate_24h;

-- ────────────────────────────────────────────────────────────────────────────────
-- 7. CLEANUP QUERY: Purge Old Resolved Errors (Run Periodically)
-- ────────────────────────────────────────────────────────────────────────────────

-- Delete resolved errors older than 90 days
-- Run this via scheduled n8n workflow or cron job
-- DELETE FROM marketing.pipeline_errors
-- WHERE resolved = TRUE
--   AND resolved_at < NOW() - INTERVAL '90 days';

-- ════════════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION 006 - PIPELINE ERROR LOGGING
-- ════════════════════════════════════════════════════════════════════════════════
