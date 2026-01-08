-- =============================================================================
-- PEOPLE SLOT STRUCTURE ROLLBACK
-- =============================================================================
-- Rollback: 2026-01-08-people-slot-structure_ROLLBACK.sql
-- Purpose: Undo all structural changes from slot structure migration
-- 
-- CAUTION: This will remove all slot structure objects.
-- Any data in people_candidate will be LOST.
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- PHASE 1: DROP GUARD FUNCTION
-- =============================================================================

DROP FUNCTION IF EXISTS people.slot_can_accept_candidate(UUID, VARCHAR);
RAISE NOTICE '✅ Dropped function: people.slot_can_accept_candidate()';

-- =============================================================================
-- PHASE 2: DROP VIEWS
-- =============================================================================

DROP VIEW IF EXISTS people.v_open_slots;
DROP VIEW IF EXISTS people.v_slot_fill_rate;
RAISE NOTICE '✅ Dropped views: v_open_slots, v_slot_fill_rate';

-- =============================================================================
-- PHASE 3: DROP KILL SWITCH TABLE
-- =============================================================================

DROP TABLE IF EXISTS people.slot_ingress_control;
RAISE NOTICE '✅ Dropped table: people.slot_ingress_control';

-- =============================================================================
-- PHASE 4: DROP CANDIDATE TABLE
-- =============================================================================

DROP TABLE IF EXISTS people.people_candidate;
RAISE NOTICE '✅ Dropped table: people.people_candidate';

-- =============================================================================
-- PHASE 5: REMOVE UNIQUE CONSTRAINT
-- =============================================================================

ALTER TABLE people.company_slot
DROP CONSTRAINT IF EXISTS uq_company_slot_outreach_slot_type;
RAISE NOTICE '✅ Dropped constraint: uq_company_slot_outreach_slot_type';

-- =============================================================================
-- PHASE 6: REVERT slot_status CONSTRAINT (optional, keep original)
-- =============================================================================
-- Note: We leave the slot_status constraint as-is since 'quarantined' 
-- is a valid state even without this migration.

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  ROLLBACK COMPLETE — Slot Structure Removed';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  - Constraint uq_company_slot_outreach_slot_type: REMOVED';
    RAISE NOTICE '  - Table people.people_candidate: DROPPED';
    RAISE NOTICE '  - View people.v_open_slots: DROPPED';
    RAISE NOTICE '  - View people.v_slot_fill_rate: DROPPED';
    RAISE NOTICE '  - Function people.slot_can_accept_candidate(): DROPPED';
    RAISE NOTICE '  - Table people.slot_ingress_control: DROPPED';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;

COMMIT;
