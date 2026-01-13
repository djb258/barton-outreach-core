-- =============================================================================
-- R0 REMEDIATION: ADD FK CONSTRAINT ON PEOPLE.COMPANY_SLOT
-- =============================================================================
-- Migration ID: R0_003
-- Date: 2026-01-09
-- Author: Claude Code (Path Integrity Remediation)
-- Mode: SCHEMA CHANGE - Adds FK constraint
--
-- PURPOSE:
--   Lock down people.company_slot.outreach_id with a foreign key constraint
--   to outreach.outreach.outreach_id, ensuring path integrity.
--
-- PREREQUISITE:
--   R0_002 MUST be applied first to backfill orphaned outreach_ids.
--   This migration will FAIL if there are slots with outreach_id values
--   that don't exist in outreach.outreach.
--
-- SAFETY:
--   - Non-derivable slots (from R0_002) have NULL outreach_id
--   - NULL values are allowed by FK (no constraint violation)
--   - Only non-NULL values must reference valid outreach.outreach records
--
-- PRE-FLIGHT CHECKS:
--   Run these BEFORE applying migration:
--
--   -- Verify no orphaned outreach_ids (MUST be 0):
--   SELECT COUNT(*) FROM people.company_slot cs
--   WHERE cs.outreach_id IS NOT NULL
--     AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = cs.outreach_id);
--   -- Expected: 0
--
--   -- Count NULL outreach_ids (these are allowed):
--   SELECT COUNT(*) FROM people.company_slot WHERE outreach_id IS NULL;
--   -- Expected: ~75 (non-derivable quarantined slots)
--
-- ROLLBACK: See R0_003_slot_outreach_fk_constraint_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- SECTION 1: PRE-FLIGHT VALIDATION
-- =============================================================================
-- Block migration if orphaned outreach_ids exist

DO $$
DECLARE
    orphan_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO orphan_count
    FROM people.company_slot cs
    WHERE cs.outreach_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = cs.outreach_id);

    IF orphan_count > 0 THEN
        RAISE EXCEPTION 'MIGRATION BLOCKED: % slots have outreach_id values that do not exist in outreach.outreach. Run R0_002 first.', orphan_count;
    END IF;
END $$;

-- =============================================================================
-- SECTION 2: ADD FOREIGN KEY CONSTRAINT
-- =============================================================================
-- This constraint ensures:
-- - All non-NULL outreach_id values MUST exist in outreach.outreach
-- - NULL values are allowed (for quarantined slots)
-- - Future inserts/updates must respect this constraint

ALTER TABLE people.company_slot
ADD CONSTRAINT fk_company_slot_outreach
FOREIGN KEY (outreach_id)
REFERENCES outreach.outreach(outreach_id)
ON DELETE RESTRICT
ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_company_slot_outreach ON people.company_slot IS
'R0_003 | Enforces path integrity: every slot must belong to a valid outreach record.
NULL allowed for quarantined slots pending investigation.
ON DELETE RESTRICT: Cannot delete outreach record if slots exist.
ON UPDATE CASCADE: If outreach_id changes (rare), slots follow.';

-- =============================================================================
-- SECTION 3: CREATE INDEX FOR FK PERFORMANCE
-- =============================================================================
-- FK lookups benefit from an index on the referencing column

CREATE INDEX IF NOT EXISTS idx_company_slot_outreach_id
ON people.company_slot(outreach_id)
WHERE outreach_id IS NOT NULL;

COMMENT ON INDEX people.idx_company_slot_outreach_id IS
'R0_003 | Partial index for FK lookups. Excludes NULL values (quarantined slots).';

-- =============================================================================
-- SECTION 4: ADD NOT NULL CONSTRAINT (DEFERRED)
-- =============================================================================
-- NOTE: We are NOT adding NOT NULL constraint yet.
-- The ~75 quarantined slots have NULL outreach_id and need investigation.
-- Once those are resolved, a follow-up migration can add NOT NULL.
--
-- Future migration (when ready):
-- ALTER TABLE people.company_slot ALTER COLUMN outreach_id SET NOT NULL;

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Verify FK exists:
-- SELECT conname, contype
-- FROM pg_constraint
-- WHERE conrelid = 'people.company_slot'::regclass
--   AND conname = 'fk_company_slot_outreach';
-- Expected: fk_company_slot_outreach, f
--
-- 2. Verify index exists:
-- SELECT indexname FROM pg_indexes
-- WHERE schemaname = 'people'
--   AND indexname = 'idx_company_slot_outreach_id';
-- Expected: idx_company_slot_outreach_id
--
-- 3. Test FK enforcement (should fail):
-- INSERT INTO people.company_slot (company_slot_unique_id, company_unique_id, slot_type, outreach_id)
-- VALUES ('test_fk', 'test_company', 'CEO', 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee');
-- Expected: ERROR - violates foreign key constraint

-- =============================================================================
-- MIGRATION R0_003 COMPLETE
-- =============================================================================
-- ACTIONS TAKEN:
--   1. Validated no orphaned outreach_ids exist
--   2. Added FK constraint fk_company_slot_outreach
--   3. Created partial index for FK performance
--
-- CONSTRAINTS:
--   - Non-NULL outreach_id MUST exist in outreach.outreach
--   - NULL allowed (for quarantined slots)
--   - DELETE RESTRICT prevents orphaning slots
--   - UPDATE CASCADE keeps slots in sync
--
-- PATH INTEGRITY:
--   people.company_slot.outreach_id -> outreach.outreach.outreach_id [LOCKED]
-- =============================================================================
