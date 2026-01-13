-- =============================================================================
-- R0 REMEDIATION: BACKFILL ORPHANED SLOT OUTREACH_IDs
-- =============================================================================
-- Migration ID: R0_002
-- Date: 2026-01-09
-- Author: Claude Code (Path Integrity Remediation)
-- Mode: DATA BACKFILL - No schema changes
--
-- PURPOSE:
--   Backfill outreach_id on people.company_slot records that are missing it.
--   These 1,053 orphaned slots cannot participate in waterfall joins.
--
-- SCOPE:
--   - 1,053 slots without outreach_id
--   - 978 are derivable via bridge path
--   - 75 are non-derivable (will be quarantined)
--
-- DERIVATION PATH:
--   people.company_slot.company_unique_id (TEXT)
--     -> company.company_master.company_unique_id (TEXT)
--     -> cl.company_identity_bridge.source_company_id (TEXT)
--     -> cl.company_identity_bridge.company_sov_id (UUID)
--     -> outreach.outreach.sovereign_id (UUID)
--     -> outreach.outreach.outreach_id (UUID)
--
-- PRE-FLIGHT CHECKS:
--   Run these BEFORE applying migration:
--
--   -- Count orphans
--   SELECT COUNT(*) FROM people.company_slot WHERE outreach_id IS NULL;
--   -- Expected: ~1,053
--
--   -- Count derivable
--   SELECT COUNT(*) FROM people.company_slot cs
--   WHERE cs.outreach_id IS NULL
--     AND EXISTS (
--         SELECT 1 FROM company.company_master cm
--         JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
--         JOIN outreach.outreach o ON cib.company_sov_id = o.sovereign_id
--         WHERE cm.company_unique_id = cs.company_unique_id
--     );
--   -- Expected: ~978
--
-- ROLLBACK: See R0_002_backfill_slot_outreach_id_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- SECTION 1: PRE-MIGRATION SNAPSHOT
-- =============================================================================
-- Create a snapshot of orphaned slots for audit trail and rollback

CREATE TABLE IF NOT EXISTS people.slot_orphan_snapshot_r0_002 (
    snapshot_id SERIAL PRIMARY KEY,
    company_slot_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    slot_type TEXT NOT NULL,
    original_outreach_id UUID,  -- Should be NULL for all
    derived_outreach_id UUID,   -- What we're about to set
    derivation_status TEXT,     -- 'DERIVED', 'NON_DERIVABLE'
    snapshot_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE people.slot_orphan_snapshot_r0_002 IS
'R0_002 | Snapshot of orphaned slots before backfill. Used for audit and rollback.';

-- =============================================================================
-- SECTION 2: CAPTURE SNAPSHOT
-- =============================================================================

INSERT INTO people.slot_orphan_snapshot_r0_002 (
    company_slot_unique_id,
    company_unique_id,
    slot_type,
    original_outreach_id,
    derived_outreach_id,
    derivation_status
)
SELECT
    cs.company_slot_unique_id,
    cs.company_unique_id,
    cs.slot_type,
    cs.outreach_id AS original_outreach_id,
    o.outreach_id AS derived_outreach_id,
    CASE
        WHEN o.outreach_id IS NOT NULL THEN 'DERIVED'
        ELSE 'NON_DERIVABLE'
    END AS derivation_status
FROM people.company_slot cs
LEFT JOIN company.company_master cm ON cs.company_unique_id = cm.company_unique_id
LEFT JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
LEFT JOIN outreach.outreach o ON cib.company_sov_id = o.sovereign_id
WHERE cs.outreach_id IS NULL;

-- =============================================================================
-- SECTION 3: BACKFILL DERIVABLE SLOTS
-- =============================================================================

UPDATE people.company_slot cs
SET outreach_id = derived.outreach_id
FROM (
    SELECT
        cs_inner.company_slot_unique_id,
        o.outreach_id
    FROM people.company_slot cs_inner
    JOIN company.company_master cm ON cs_inner.company_unique_id = cm.company_unique_id
    JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
    JOIN outreach.outreach o ON cib.company_sov_id = o.sovereign_id
    WHERE cs_inner.outreach_id IS NULL
) AS derived
WHERE cs.company_slot_unique_id = derived.company_slot_unique_id;

-- =============================================================================
-- SECTION 4: QUARANTINE NON-DERIVABLE SLOTS
-- =============================================================================
-- These slots have company_unique_id that cannot be traced back to CL/outreach.
-- Mark them for investigation rather than deleting.

CREATE TABLE IF NOT EXISTS people.slot_quarantine_r0_002 (
    quarantine_id SERIAL PRIMARY KEY,
    company_slot_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    slot_type TEXT NOT NULL,
    quarantine_reason TEXT NOT NULL,
    quarantined_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO people.slot_quarantine_r0_002 (
    company_slot_unique_id,
    company_unique_id,
    slot_type,
    quarantine_reason
)
SELECT
    cs.company_slot_unique_id,
    cs.company_unique_id,
    cs.slot_type,
    'NON_DERIVABLE: No path from company_unique_id to outreach.outreach via bridge'
FROM people.company_slot cs
WHERE cs.outreach_id IS NULL;

COMMENT ON TABLE people.slot_quarantine_r0_002 IS
'R0_002 | Quarantined slots that could not be linked to outreach spine.
These need manual investigation - company_unique_id has no bridge entry.';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Count remaining orphans (should be ~75):
-- SELECT COUNT(*) FROM people.company_slot WHERE outreach_id IS NULL;
--
-- 2. Verify backfill count:
-- SELECT derivation_status, COUNT(*)
-- FROM people.slot_orphan_snapshot_r0_002
-- GROUP BY derivation_status;
-- Expected: DERIVED ~978, NON_DERIVABLE ~75
--
-- 3. Verify quarantine:
-- SELECT COUNT(*) FROM people.slot_quarantine_r0_002;
-- Expected: ~75
--
-- 4. Verify no orphaned outreach_ids (should be 0):
-- SELECT COUNT(*) FROM people.company_slot cs
-- WHERE cs.outreach_id IS NOT NULL
--   AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = cs.outreach_id);
-- Expected: 0

-- =============================================================================
-- MIGRATION R0_002 COMPLETE
-- =============================================================================
-- ACTIONS TAKEN:
--   1. Created snapshot table (people.slot_orphan_snapshot_r0_002)
--   2. Captured all 1,053 orphaned slots with derivation status
--   3. Backfilled ~978 derivable slots with outreach_id
--   4. Quarantined ~75 non-derivable slots for investigation
--
-- REMAINING ORPHANS:
--   ~75 slots still have NULL outreach_id
--   These are in quarantine table and need manual resolution
--
-- NEXT STEP:
--   Apply R0_003 to add FK constraint (after verifying this migration)
-- =============================================================================
