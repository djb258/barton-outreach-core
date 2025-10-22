-- ============================================================================
-- Migration: Create marketing.outreach_history Unified View
-- Date: 2025-10-22
-- Purpose: Provide single source of truth for campaign/execution/message activity
-- Barton Doctrine: Unified outreach reporting requirement
-- ============================================================================

-- ============================================================================
-- VIEW: marketing.outreach_history
-- ============================================================================
-- Combines data from three sources:
--   1. marketing.campaigns - Campaign master records
--   2. marketing.campaign_executions - Individual execution steps
--   3. marketing.message_log - Message delivery records
--
-- This view satisfies Barton Doctrine requirement for unified outreach reporting
-- and provides a single query point for all campaign-related activity.
-- ============================================================================

CREATE OR REPLACE VIEW marketing.outreach_history AS
SELECT
  -- Campaign Information
  c.campaign_id,
  c.campaign_type,
  c.trigger_event,
  c.company_unique_id,
  c.status AS campaign_status,
  c.created_at AS campaign_created_at,
  c.launched_at AS campaign_launched_at,

  -- Campaign Execution Information
  ce.execution_step,
  ce.step_type,
  ce.scheduled_at,
  ce.executed_at,
  ce.status AS execution_status,
  ce.target_person_id,
  ce.target_email AS execution_target_email,
  ce.target_linkedin,
  ce.response AS execution_response,
  ce.error_message AS execution_error,

  -- Message Log Information
  ml.message_log_id,
  ml.contact_id AS message_contact_id,
  ml.direction AS message_direction,
  ml.channel AS message_channel,
  ml.subject AS message_subject,
  ml.body AS message_body,
  ml.sent_at AS message_sent_at

FROM marketing.campaigns c
LEFT JOIN marketing.campaign_executions ce
  ON c.campaign_id = ce.campaign_id
LEFT JOIN marketing.message_log ml
  ON c.campaign_id::text = ml.campaign_id::text;

-- ============================================================================
-- VIEW COMMENTS
-- ============================================================================

COMMENT ON VIEW marketing.outreach_history IS
    'Unified outreach history view combining campaigns, executions, and messages.
    Provides single source of truth for all campaign-related activity tracking.
    Satisfies Barton Doctrine requirement for consolidated outreach reporting.

    Source Tables:
    - marketing.campaigns: Campaign master records and metadata
    - marketing.campaign_executions: Individual step executions within campaigns
    - marketing.message_log: Actual message delivery records

    Use Cases:
    - Campaign performance reporting
    - Execution timeline analysis
    - Message delivery tracking
    - Multi-channel outreach auditing
    - Response rate calculations';

-- ============================================================================
-- COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN marketing.outreach_history.campaign_id IS
    'Unique campaign identifier (Barton ID format: 04.04.03.XX.XXXXX.XXX)';

COMMENT ON COLUMN marketing.outreach_history.campaign_type IS
    'Campaign type: PLE (Promoted Lead Enrichment) or BIT (Buyer Intent Tool)';

COMMENT ON COLUMN marketing.outreach_history.trigger_event IS
    'Event that triggered campaign creation (e.g., record_promoted, bit_signal_fired)';

COMMENT ON COLUMN marketing.outreach_history.execution_step IS
    'Sequential step number within campaign execution';

COMMENT ON COLUMN marketing.outreach_history.step_type IS
    'Type of execution step: email, linkedin_connect, phone_call, sms, etc.';

COMMENT ON COLUMN marketing.outreach_history.execution_status IS
    'Execution status: pending, executing, completed, failed, skipped';

COMMENT ON COLUMN marketing.outreach_history.message_channel IS
    'Message delivery channel: email, linkedin, phone, other';

COMMENT ON COLUMN marketing.outreach_history.message_direction IS
    'Message direction: outbound (sent) or inbound (received)';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Get all outreach activity for a specific company
-- SELECT * FROM marketing.outreach_history
-- WHERE company_unique_id = '04.04.01.84.48151.001'
-- ORDER BY campaign_created_at DESC, execution_step;

-- Example 2: Find all failed campaign executions in the last 7 days
-- SELECT campaign_id, step_type, execution_error, executed_at
-- FROM marketing.outreach_history
-- WHERE execution_status = 'failed'
--   AND executed_at >= NOW() - INTERVAL '7 days'
-- ORDER BY executed_at DESC;

-- Example 3: Calculate campaign response rates
-- SELECT
--   campaign_id,
--   campaign_type,
--   COUNT(DISTINCT CASE WHEN execution_status = 'completed' THEN execution_step END) as completed_steps,
--   COUNT(DISTINCT CASE WHEN message_direction = 'inbound' THEN message_log_id END) as responses,
--   ROUND(
--     COUNT(DISTINCT CASE WHEN message_direction = 'inbound' THEN message_log_id END)::numeric /
--     NULLIF(COUNT(DISTINCT CASE WHEN execution_status = 'completed' THEN execution_step END), 0) * 100,
--     2
--   ) as response_rate_pct
-- FROM marketing.outreach_history
-- WHERE campaign_launched_at >= NOW() - INTERVAL '30 days'
-- GROUP BY campaign_id, campaign_type
-- ORDER BY response_rate_pct DESC NULLS LAST;

-- Example 4: Track multi-channel campaign activity
-- SELECT
--   campaign_id,
--   step_type,
--   message_channel,
--   COUNT(*) as touch_count,
--   COUNT(CASE WHEN execution_status = 'completed' THEN 1 END) as successful_touches
-- FROM marketing.outreach_history
-- WHERE campaign_type = 'PLE'
-- GROUP BY campaign_id, step_type, message_channel
-- ORDER BY campaign_id, execution_step;

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT SELECT ON marketing.outreach_history TO authenticated;
-- GRANT SELECT ON marketing.outreach_history TO analytics_role;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- View: marketing.outreach_history (created)
-- Source Tables: campaigns, campaign_executions, message_log (unchanged)
-- Purpose: Unified outreach activity reporting
-- Doctrine Compliance: ✅ Satisfies unified reporting requirement
-- ============================================================================

-- ============================================================================
-- IMPLEMENTATION NOTES
-- ============================================================================
--
-- 1. Data Sources:
--    - marketing.campaigns: Campaign metadata, status, and triggers
--    - marketing.campaign_executions: Individual step execution details
--    - marketing.message_log: Actual message send/receive records
--
-- 2. Join Strategy:
--    - LEFT JOIN used to preserve all campaigns even without executions/messages
--    - campaign_id used as primary join key
--    - Multiple rows per campaign possible (one per execution × message combination)
--
-- 3. Use Cases Supported:
--    - Campaign performance dashboards
--    - Execution timeline analysis
--    - Multi-channel attribution
--    - Response tracking and analytics
--    - Failed execution debugging
--    - Compliance and audit reporting
--
-- 4. Performance Considerations:
--    - View is not materialized - queries run against source tables
--    - For heavy analytics, consider creating materialized view
--    - Indexes on source tables (campaign_id) will improve query performance
--    - For large datasets, add WHERE clauses to limit date ranges
--
-- 5. Doctrine Compliance:
--    - ✅ marketing.outreach_history exists (as view)
--    - ✅ Unified reporting capability provided
--    - ✅ Single source of truth for outreach activity
--    - ⚠️ Implementation as view (not table) for real-time accuracy
--
-- 6. Future Enhancements:
--    - Add computed columns for response rates
--    - Include campaign template details
--    - Add aggregated metrics (total sent, total responses)
--    - Consider materialized view for analytics performance
--    - Add campaign cost tracking if available
--
-- ============================================================================
