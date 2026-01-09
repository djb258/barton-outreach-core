-- =============================================================================
-- P0 ROLLBACK: TALENT FLOW SPINE ALIGNMENT
-- =============================================================================
-- Migration ID: P0_002
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
--
-- PURPOSE:
--   Rollback P0_002_talent_flow_spine_alignment.sql
--   Removes outreach_id columns and associated objects from Talent Flow tables
--
-- WARNING: This will DELETE the outreach_id data. Ensure backups exist.
-- =============================================================================

-- =============================================================================
-- SECTION A: Rollback talent_flow.movements
-- =============================================================================

-- Drop view first (depends on columns)
DROP VIEW IF EXISTS talent_flow.v_movements_pending_spine;

-- Drop indexes
DROP INDEX IF EXISTS talent_flow.idx_movements_from_outreach_id;
DROP INDEX IF EXISTS talent_flow.idx_movements_to_outreach_id;
DROP INDEX IF EXISTS talent_flow.idx_movements_correlation_id;
DROP INDEX IF EXISTS talent_flow.idx_movements_hash_unique;

-- Remove trigger comment (restore original if needed)
-- Note: The trigger itself is not modified, only the comment

-- Drop columns
ALTER TABLE talent_flow.movements
DROP COLUMN IF EXISTS from_outreach_id;

ALTER TABLE talent_flow.movements
DROP COLUMN IF EXISTS to_outreach_id;

ALTER TABLE talent_flow.movements
DROP COLUMN IF EXISTS correlation_id;

ALTER TABLE talent_flow.movements
DROP COLUMN IF EXISTS movement_hash;

-- =============================================================================
-- SECTION B: Rollback svg_marketing.talent_flow_movements
-- =============================================================================

-- Drop indexes
DROP INDEX IF EXISTS svg_marketing.idx_svg_talent_flow_outreach_id;
DROP INDEX IF EXISTS svg_marketing.idx_svg_talent_flow_correlation_id;

-- Drop columns
ALTER TABLE svg_marketing.talent_flow_movements
DROP COLUMN IF EXISTS outreach_id;

ALTER TABLE svg_marketing.talent_flow_movements
DROP COLUMN IF EXISTS correlation_id;

-- =============================================================================
-- SECTION C: Rollback talent_flow_errors table
-- =============================================================================

-- Drop indexes first
DROP INDEX IF EXISTS talent_flow.idx_tf_errors_outreach_id;
DROP INDEX IF EXISTS talent_flow.idx_tf_errors_pipeline_stage;
DROP INDEX IF EXISTS talent_flow.idx_tf_errors_failure_code;
DROP INDEX IF EXISTS talent_flow.idx_tf_errors_unresolved;
DROP INDEX IF EXISTS talent_flow.idx_tf_errors_correlation_id;

-- Drop table
DROP TABLE IF EXISTS talent_flow.talent_flow_errors;

-- =============================================================================
-- ROLLBACK P0_002 COMPLETE
-- =============================================================================
-- Verify rollback:
--
-- 1. Check talent_flow.movements columns removed:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'talent_flow' AND table_name = 'movements';
-- Should NOT include: from_outreach_id, to_outreach_id, correlation_id, movement_hash
--
-- 2. Check svg_marketing columns removed:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'svg_marketing' AND table_name = 'talent_flow_movements';
-- Should NOT include: outreach_id, correlation_id
--
-- 3. Check talent_flow_errors table removed:
-- SELECT tablename FROM pg_tables WHERE schemaname = 'talent_flow' AND tablename = 'talent_flow_errors';
-- Should return 0 rows
-- =============================================================================
