-- =============================================================================
-- P2 CANARY INGESTION ROLLBACK
-- =============================================================================
-- Rollback: 2026-01-08-people-slot-canary-ingestion_ROLLBACK.sql
-- Purpose: Undo all P2 canary ingestion changes
-- 
-- CAUTION: This will remove canary infrastructure.
-- Any data in slot_ingress_canary will be LOST.
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- PHASE 1: DROP OBSERVABILITY VIEWS
-- =============================================================================

DROP VIEW IF EXISTS people.v_candidate_canary_activity;
DROP VIEW IF EXISTS people.v_canary_queue_depth;

RAISE NOTICE '✅ Dropped observability views';

-- =============================================================================
-- PHASE 2: REVERT GUARD FUNCTION TO P1 VERSION
-- =============================================================================

CREATE OR REPLACE FUNCTION people.slot_can_accept_candidate(
    p_outreach_id UUID,
    p_slot_type VARCHAR(20)
)
RETURNS TABLE (
    can_accept BOOLEAN,
    reason TEXT,
    slot_id TEXT,
    current_status TEXT
) AS $$
DECLARE
    v_slot_id TEXT;
    v_slot_status TEXT;
    v_resolution_pending BOOLEAN;
    v_kill_switch_active BOOLEAN;
BEGIN
    -- Check kill switch first
    SELECT COALESCE(
        (SELECT is_enabled FROM people.slot_ingress_control WHERE switch_name = 'slot_ingress' LIMIT 1),
        FALSE
    ) INTO v_kill_switch_active;
    
    IF NOT v_kill_switch_active THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'KILL_SWITCH_OFF: slot_ingress_control is disabled'::TEXT,
            NULL::TEXT,
            NULL::TEXT;
        RETURN;
    END IF;

    -- Check if slot exists
    SELECT cs.slot_id, cs.slot_status
    INTO v_slot_id, v_slot_status
    FROM people.company_slot cs
    WHERE cs.outreach_id = p_outreach_id
      AND cs.slot_type = p_slot_type;
    
    IF v_slot_id IS NULL THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'SLOT_NOT_FOUND: No slot exists for this outreach_id + slot_type'::TEXT,
            NULL::TEXT,
            NULL::TEXT;
        RETURN;
    END IF;
    
    -- Check slot status
    IF v_slot_status != 'open' THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            format('SLOT_NOT_OPEN: Slot status is %s', v_slot_status)::TEXT,
            v_slot_id,
            v_slot_status;
        RETURN;
    END IF;
    
    -- Check resolution history for pending/active attempts
    SELECT EXISTS (
        SELECT 1 
        FROM people.people_resolution_queue prq
        WHERE prq.outreach_id = p_outreach_id
          AND prq.slot_id = v_slot_id
          AND prq.resolution_status = 'pending'
    ) INTO v_resolution_pending;
    
    IF v_resolution_pending THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'RESOLUTION_PENDING: Slot has pending resolution attempt'::TEXT,
            v_slot_id,
            v_slot_status;
        RETURN;
    END IF;
    
    -- All checks passed
    RETURN QUERY SELECT 
        TRUE::BOOLEAN, 
        'SLOT_READY: Slot can accept candidate'::TEXT,
        v_slot_id,
        v_slot_status;
END;
$$ LANGUAGE plpgsql STABLE;

RAISE NOTICE '✅ Reverted guard function to P1 version (no canary check)';

-- =============================================================================
-- PHASE 3: REMOVE CANARY_MODE COLUMN
-- =============================================================================

ALTER TABLE people.slot_ingress_control
DROP COLUMN IF EXISTS canary_mode;

RAISE NOTICE '✅ Removed canary_mode column';

-- =============================================================================
-- PHASE 4: DROP CANARY TABLE
-- =============================================================================

DROP TABLE IF EXISTS people.slot_ingress_canary;

RAISE NOTICE '✅ Dropped people.slot_ingress_canary table';

-- =============================================================================
-- PHASE 5: DISABLE KILL SWITCH
-- =============================================================================

UPDATE people.slot_ingress_control
SET is_enabled = FALSE,
    disabled_by = 'rollback',
    disabled_at = NOW(),
    description = 'Master kill switch for slot candidate ingestion. When OFF, slot_can_accept_candidate() always returns FALSE.'
WHERE switch_name = 'slot_ingress';

RAISE NOTICE '✅ Disabled kill switch';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  P2 CANARY ROLLBACK — COMPLETE';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  - View v_candidate_canary_activity: DROPPED';
    RAISE NOTICE '  - View v_canary_queue_depth: DROPPED';
    RAISE NOTICE '  - Guard function: REVERTED to P1';
    RAISE NOTICE '  - Column canary_mode: REMOVED';
    RAISE NOTICE '  - Table slot_ingress_canary: DROPPED';
    RAISE NOTICE '  - Kill switch: DISABLED';
    RAISE NOTICE '';
    RAISE NOTICE '  STATE: Reverted to P1 (structure only, no canary)';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;

COMMIT;
