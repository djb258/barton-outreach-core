-- =============================================================================
-- P0 ROLLBACK: OUTREACH EXECUTION SPINE ALIGNMENT
-- =============================================================================
-- Migration ID: P0_003
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
--
-- PURPOSE:
--   Rollback P0_003_outreach_execution_spine_alignment.sql
--   Removes Outreach Execution tables created by this migration
--
-- WARNING: This will DELETE all campaign, send_log, and error data.
--          Ensure backups exist before running.
-- =============================================================================

-- =============================================================================
-- SECTION A: Drop views first (depend on tables)
-- =============================================================================

DROP VIEW IF EXISTS outreach.v_campaign_summary;
DROP VIEW IF EXISTS outreach.v_send_activity;

-- =============================================================================
-- SECTION B: Drop triggers
-- =============================================================================

DROP TRIGGER IF EXISTS set_updated_at ON outreach.campaigns;
DROP TRIGGER IF EXISTS set_updated_at ON outreach.send_log;

-- =============================================================================
-- SECTION C: Drop execution_errors table
-- =============================================================================

DROP INDEX IF EXISTS outreach.idx_exec_errors_outreach_id;
DROP INDEX IF EXISTS outreach.idx_exec_errors_campaign_id;
DROP INDEX IF EXISTS outreach.idx_exec_errors_pipeline_stage;
DROP INDEX IF EXISTS outreach.idx_exec_errors_failure_code;
DROP INDEX IF EXISTS outreach.idx_exec_errors_unresolved;

DROP TABLE IF EXISTS outreach.execution_errors;

-- =============================================================================
-- SECTION D: Drop send_log table
-- =============================================================================

DROP INDEX IF EXISTS outreach.idx_send_log_outreach_id;
DROP INDEX IF EXISTS outreach.idx_send_log_campaign_id;
DROP INDEX IF EXISTS outreach.idx_send_log_person_id;
DROP INDEX IF EXISTS outreach.idx_send_log_email;
DROP INDEX IF EXISTS outreach.idx_send_log_status;
DROP INDEX IF EXISTS outreach.idx_send_log_sent_at;
DROP INDEX IF EXISTS outreach.idx_send_log_correlation_id;

DROP TABLE IF EXISTS outreach.send_log;

-- =============================================================================
-- SECTION E: Drop campaigns table
-- =============================================================================

DROP INDEX IF EXISTS outreach.idx_campaigns_outreach_id;
DROP INDEX IF EXISTS outreach.idx_campaigns_status;
DROP INDEX IF EXISTS outreach.idx_campaigns_type;
DROP INDEX IF EXISTS outreach.idx_campaigns_scheduled_start;

DROP TABLE IF EXISTS outreach.campaigns;

-- =============================================================================
-- ROLLBACK P0_003 COMPLETE
-- =============================================================================
-- Verify rollback:
--
-- 1. Check tables removed:
-- SELECT tablename FROM pg_tables WHERE schemaname = 'outreach'
-- AND tablename IN ('campaigns', 'send_log', 'execution_errors');
-- Should return 0 rows
--
-- 2. Check views removed:
-- SELECT viewname FROM pg_views WHERE schemaname = 'outreach'
-- AND viewname IN ('v_campaign_summary', 'v_send_activity');
-- Should return 0 rows
-- =============================================================================
