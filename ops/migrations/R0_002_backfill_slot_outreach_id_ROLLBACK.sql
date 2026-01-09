-- =============================================================================
-- R0 ROLLBACK: BACKFILL ORPHANED SLOT OUTREACH_IDs
-- =============================================================================
-- Migration ID: R0_002 ROLLBACK
-- Date: 2026-01-09
-- Author: Claude Code (Path Integrity Remediation)
--
-- PURPOSE:
--   Revert R0_002 backfill - restore slots to orphaned state.
--   Uses snapshot table to restore original NULL values.
--
-- WARNING:
--   Only run this if R0_003 (FK constraint) has NOT been applied.
--   If FK exists, drop it first or this rollback will fail.
-- =============================================================================

-- =============================================================================
-- SECTION 1: VERIFY SNAPSHOT EXISTS
-- =============================================================================
-- If this fails, the snapshot table doesn't exist and rollback cannot proceed

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'people'
        AND table_name = 'slot_orphan_snapshot_r0_002'
    ) THEN
        RAISE EXCEPTION 'ROLLBACK BLOCKED: Snapshot table people.slot_orphan_snapshot_r0_002 does not exist';
    END IF;
END $$;

-- =============================================================================
-- SECTION 2: RESTORE NULL OUTREACH_IDs
-- =============================================================================
-- Only restore slots that were in the snapshot (i.e., were orphaned before R0_002)

UPDATE people.company_slot cs
SET outreach_id = NULL
FROM people.slot_orphan_snapshot_r0_002 snap
WHERE cs.company_slot_unique_id = snap.company_slot_unique_id
  AND snap.original_outreach_id IS NULL;

-- =============================================================================
-- SECTION 3: CLEANUP ROLLBACK ARTIFACTS
-- =============================================================================

-- Drop quarantine table
DROP TABLE IF EXISTS people.slot_quarantine_r0_002;

-- Drop snapshot table (optional - keep for audit)
-- Uncomment if you want full cleanup:
-- DROP TABLE IF EXISTS people.slot_orphan_snapshot_r0_002;

-- =============================================================================
-- VERIFICATION
-- =============================================================================
-- Run after rollback:
--
-- SELECT COUNT(*) FROM people.company_slot WHERE outreach_id IS NULL;
-- Expected: ~1,053 (back to original orphan count)

-- =============================================================================
-- ROLLBACK R0_002 COMPLETE
-- =============================================================================
