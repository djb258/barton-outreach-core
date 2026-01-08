-- =============================================================================
-- P0 ROLLBACK: HISTORY SIDECAR TABLES
-- =============================================================================
-- Migration ID: P0_004
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
--
-- PURPOSE:
--   Rollback P0_004_history_sidecar_tables.sql
--   Removes all history sidecar tables and associated objects
--
-- WARNING: This will DELETE all history data. Operations may re-run
--          (re-scrape, re-enrich, re-pay) without this protection.
-- =============================================================================

-- =============================================================================
-- SECTION A: Drop helper functions
-- =============================================================================

DROP FUNCTION IF EXISTS outreach.blog_url_exists(UUID, TEXT);
DROP FUNCTION IF EXISTS people.person_already_resolved(UUID, VARCHAR, TEXT);
DROP FUNCTION IF EXISTS talent_flow.movement_already_recorded(TEXT, UUID, UUID);
DROP FUNCTION IF EXISTS outreach.bit_signal_already_processed(UUID, TEXT);

-- =============================================================================
-- SECTION B: Drop blog_source_history
-- =============================================================================

DROP TRIGGER IF EXISTS trg_blog_history_append_only ON outreach.blog_source_history;
DROP TRIGGER IF EXISTS trg_blog_history_no_delete ON outreach.blog_source_history;
DROP FUNCTION IF EXISTS outreach.enforce_blog_history_append_only();
DROP FUNCTION IF EXISTS outreach.block_blog_history_delete();

DROP INDEX IF EXISTS outreach.idx_blog_source_history_outreach;
DROP INDEX IF EXISTS outreach.idx_blog_source_history_status;
DROP INDEX IF EXISTS outreach.idx_blog_source_history_last_checked;
DROP INDEX IF EXISTS outreach.idx_blog_source_history_checksum;

DROP TABLE IF EXISTS outreach.blog_source_history;

-- =============================================================================
-- SECTION C: Drop people_resolution_history
-- =============================================================================

DROP TRIGGER IF EXISTS trg_resolution_history_no_update ON people.people_resolution_history;
DROP TRIGGER IF EXISTS trg_resolution_history_no_delete ON people.people_resolution_history;
DROP FUNCTION IF EXISTS people.block_resolution_history_update();
DROP FUNCTION IF EXISTS people.block_resolution_history_delete();

DROP INDEX IF EXISTS people.idx_people_resolution_outreach;
DROP INDEX IF EXISTS people.idx_people_resolution_slot;
DROP INDEX IF EXISTS people.idx_people_resolution_outcome;
DROP INDEX IF EXISTS people.idx_people_resolution_identifier;
DROP INDEX IF EXISTS people.idx_people_resolution_checked;

DROP TABLE IF EXISTS people.people_resolution_history;

-- =============================================================================
-- SECTION D: Drop movement_history
-- =============================================================================

DROP TRIGGER IF EXISTS trg_movement_history_no_update ON talent_flow.movement_history;
DROP TRIGGER IF EXISTS trg_movement_history_no_delete ON talent_flow.movement_history;
DROP FUNCTION IF EXISTS talent_flow.block_movement_history_update();
DROP FUNCTION IF EXISTS talent_flow.block_movement_history_delete();

DROP INDEX IF EXISTS talent_flow.idx_movement_history_person;
DROP INDEX IF EXISTS talent_flow.idx_movement_history_from;
DROP INDEX IF EXISTS talent_flow.idx_movement_history_to;
DROP INDEX IF EXISTS talent_flow.idx_movement_history_detected;
DROP INDEX IF EXISTS talent_flow.idx_movement_history_correlation;

DROP TABLE IF EXISTS talent_flow.movement_history;

-- =============================================================================
-- SECTION E: Drop bit_input_history
-- =============================================================================

DROP TRIGGER IF EXISTS trg_bit_history_append_only ON outreach.bit_input_history;
DROP TRIGGER IF EXISTS trg_bit_history_no_delete ON outreach.bit_input_history;
DROP FUNCTION IF EXISTS outreach.enforce_bit_history_append_only();
DROP FUNCTION IF EXISTS outreach.block_bit_history_delete();

DROP INDEX IF EXISTS outreach.idx_bit_input_history_outreach;
DROP INDEX IF EXISTS outreach.idx_bit_input_history_signal_type;
DROP INDEX IF EXISTS outreach.idx_bit_input_history_source;
DROP INDEX IF EXISTS outreach.idx_bit_input_history_fingerprint;
DROP INDEX IF EXISTS outreach.idx_bit_input_history_first_seen;

DROP TABLE IF EXISTS outreach.bit_input_history;

-- =============================================================================
-- ROLLBACK P0_004 COMPLETE
-- =============================================================================
-- Verify rollback:
--
-- 1. Check tables removed:
-- SELECT tablename FROM pg_tables
-- WHERE tablename IN ('blog_source_history', 'people_resolution_history', 'movement_history', 'bit_input_history');
-- Should return 0 rows
--
-- 2. Check functions removed:
-- SELECT routine_name FROM information_schema.routines
-- WHERE routine_name IN ('blog_url_exists', 'person_already_resolved', 'movement_already_recorded', 'bit_signal_already_processed');
-- Should return 0 rows
-- =============================================================================
