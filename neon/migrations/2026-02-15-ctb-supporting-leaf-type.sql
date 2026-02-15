-- ============================================================================
-- ADR-020: Add SUPPORTING Leaf Type + Reclassify people_master
-- ============================================================================
-- Date:    2026-02-15
-- Author:  ADR-020 (People Sub-Hub Reclassification)
-- Scope:   ctb.table_registry
--
-- What this does:
--   1. Adds SUPPORTING to the leaf_type CHECK constraint
--   2. Reclassifies people.people_master from CANONICAL to SUPPORTING
--
-- Why:
--   people_master supports company_slot (the canonical table of the people
--   sub-hub). Slots define structure (3 per company). People fill slots.
--   Having 2 CANONICAL tables violates OWN-10a. Reclassifying people_master
--   as SUPPORTING makes the people sub-hub compliant.
--
-- Rollback:
--   See bottom of file.
-- ============================================================================

BEGIN;

-- -------------------------------------------------------------------------
-- Step 1: Drop old CHECK constraint, add new one with SUPPORTING
-- -------------------------------------------------------------------------
ALTER TABLE ctb.table_registry
    DROP CONSTRAINT table_registry_leaf_type_check;

ALTER TABLE ctb.table_registry
    ADD CONSTRAINT table_registry_leaf_type_check
    CHECK (leaf_type IN (
        'CANONICAL',
        'ERROR',
        'MV',
        'REGISTRY',
        'STAGING',
        'ARCHIVE',
        'SYSTEM',
        'DEPRECATED',
        'SUPPORTING'
    ));

-- -------------------------------------------------------------------------
-- Step 2: Reclassify people_master from CANONICAL to SUPPORTING
-- -------------------------------------------------------------------------
UPDATE ctb.table_registry
SET leaf_type = 'SUPPORTING',
    notes = 'ADR-020: Reclassified from CANONICAL to SUPPORTING. Supports company_slot (the canonical table). Holds person data that fills slots.'
WHERE table_schema = 'people'
  AND table_name = 'people_master';

-- -------------------------------------------------------------------------
-- Verify
-- -------------------------------------------------------------------------
-- Should show: people.people_master | SUPPORTING
SELECT table_schema, table_name, leaf_type, is_frozen, notes
FROM ctb.table_registry
WHERE table_schema = 'people'
ORDER BY table_name;

COMMIT;

-- ============================================================================
-- ROLLBACK (if needed):
-- ============================================================================
-- BEGIN;
--
-- UPDATE ctb.table_registry
-- SET leaf_type = 'CANONICAL',
--     notes = NULL
-- WHERE table_schema = 'people'
--   AND table_name = 'people_master';
--
-- ALTER TABLE ctb.table_registry
--     DROP CONSTRAINT table_registry_leaf_type_check;
--
-- ALTER TABLE ctb.table_registry
--     ADD CONSTRAINT table_registry_leaf_type_check
--     CHECK (leaf_type IN (
--         'CANONICAL', 'ERROR', 'MV', 'REGISTRY',
--         'STAGING', 'ARCHIVE', 'SYSTEM', 'DEPRECATED'
--     ));
--
-- COMMIT;
-- ============================================================================
