-- =============================================================================
-- P0 ROLLBACK: DOL SPINE ALIGNMENT
-- =============================================================================
-- Migration ID: P0_001
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
--
-- PURPOSE:
--   Rollback P0_001_dol_spine_alignment.sql
--   Removes outreach_id column and associated objects from dol.ein_linkage
--
-- WARNING: This will DELETE the outreach_id data. Ensure backups exist.
-- =============================================================================

-- Step 1: Drop view
DROP VIEW IF EXISTS dol.v_ein_linkage_pending_spine;

-- Step 2: Drop index
DROP INDEX IF EXISTS dol.idx_ein_linkage_outreach_id;

-- Step 3: Drop FK constraint (if it was added)
ALTER TABLE dol.ein_linkage
DROP CONSTRAINT IF EXISTS fk_ein_linkage_outreach;

-- Step 4: Drop column
ALTER TABLE dol.ein_linkage
DROP COLUMN IF EXISTS outreach_id;

-- =============================================================================
-- ROLLBACK COMPLETE
-- =============================================================================
-- Verify rollback:
-- SELECT column_name FROM information_schema.columns
-- WHERE table_schema = 'dol' AND table_name = 'ein_linkage';
-- Should NOT include 'outreach_id'
-- =============================================================================
