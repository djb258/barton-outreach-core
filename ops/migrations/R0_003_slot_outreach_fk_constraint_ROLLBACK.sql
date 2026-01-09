-- =============================================================================
-- R0 ROLLBACK: FK CONSTRAINT ON PEOPLE.COMPANY_SLOT
-- =============================================================================
-- Migration ID: R0_003 ROLLBACK
-- Date: 2026-01-09
-- Author: Claude Code (Path Integrity Remediation)
--
-- PURPOSE:
--   Remove FK constraint from people.company_slot.outreach_id.
--   This unlocks the table for R0_002 rollback if needed.
--
-- WARNING:
--   Removing FK constraint removes path integrity enforcement.
--   Only roll back if there's a critical issue requiring it.
-- =============================================================================

-- =============================================================================
-- SECTION 1: DROP FK CONSTRAINT
-- =============================================================================

ALTER TABLE people.company_slot
DROP CONSTRAINT IF EXISTS fk_company_slot_outreach;

-- =============================================================================
-- SECTION 2: DROP INDEX (OPTIONAL)
-- =============================================================================
-- The index is still useful for queries even without FK.
-- Uncomment to remove if desired:

-- DROP INDEX IF EXISTS people.idx_company_slot_outreach_id;

-- =============================================================================
-- VERIFICATION
-- =============================================================================
-- Run after rollback:
--
-- SELECT conname FROM pg_constraint
-- WHERE conrelid = 'people.company_slot'::regclass
--   AND conname = 'fk_company_slot_outreach';
-- Expected: 0 rows (constraint removed)

-- =============================================================================
-- ROLLBACK R0_003 COMPLETE
-- =============================================================================
