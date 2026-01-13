-- =============================================================================
-- PEOPLE SLOT CANARY INGESTION (P2)
-- =============================================================================
-- Migration: 2026-01-08-people-slot-canary-ingestion.sql
-- Purpose: Enable canary-scoped candidate ingestion (structure only)
-- Hub: people-intelligence
-- subhub_unique_id: 2e5bf57e-4ca8-4d09-8c50-6ea785306b97
--
-- SCOPE:
--   ✅ Canary allowlist table (people.slot_ingress_canary)
--   ✅ Augmented guard function with canary + history checks
--   ✅ Observability view for canary activity
--   ✅ Kill switch metadata update (NOT auto-enabled)
--
-- HARD CONSTRAINTS:
--   ❌ No enrichment
--   ❌ No scraping
--   ❌ No slot resolution
--   ❌ No movement logic
--   ❌ No writes to people_master
--   ❌ No auto-promotion of candidates
--   ✅ Candidate ingestion only into people.people_candidate
--
-- =============================================================================

BEGIN;

-- =============================================================================
-- PHASE 1: CREATE CANARY ALLOWLIST TABLE
-- =============================================================================
-- Only outreach_ids in this table can have candidates ingested
-- Manual population only — no automation

CREATE TABLE IF NOT EXISTS people.slot_ingress_canary (
    outreach_id     UUID PRIMARY KEY,
    added_by        VARCHAR(100) NOT NULL,
    added_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    notes           TEXT
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_slot_ingress_canary_added_at 
    ON people.slot_ingress_canary(added_at);

COMMENT ON TABLE people.slot_ingress_canary IS
'PI.CANARY.001 | Canary allowlist for slot candidate ingestion.
Only outreach_ids in this table can accept candidates.
Population is MANUAL ONLY — no automation permitted.
Typical size: 10-25 outreach_ids for initial validation.';

COMMENT ON COLUMN people.slot_ingress_canary.outreach_id IS
'PI.CANARY.002 | Outreach ID allowed for candidate ingestion (spine anchor)';

COMMENT ON COLUMN people.slot_ingress_canary.added_by IS
'PI.CANARY.003 | Human operator who added this outreach_id to canary';

COMMENT ON COLUMN people.slot_ingress_canary.notes IS
'PI.CANARY.004 | Optional notes on why this outreach_id was selected';

RAISE NOTICE '✅ Phase 1: Created people.slot_ingress_canary table';

-- =============================================================================
-- PHASE 2: AUGMENT GUARD FUNCTION (CANARY-AWARE)
-- =============================================================================
-- Order of checks (non-negotiable):
--   1. Kill switch enabled
--   2. outreach_id in canary allowlist
--   3. Slot exists for (outreach_id, slot_type)
--   4. Slot status = 'open'
--   5. No pending resolution attempt
--   6. No prior attempt in people.people_resolution_history

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
    v_kill_switch_active BOOLEAN;
    v_in_canary BOOLEAN;
    v_resolution_pending BOOLEAN;
    v_prior_resolution BOOLEAN;
BEGIN
    -- =========================================================================
    -- CHECK 1: Kill switch must be enabled
    -- =========================================================================
    SELECT COALESCE(
        (SELECT is_enabled FROM people.slot_ingress_control 
         WHERE switch_name = 'slot_ingress' LIMIT 1),
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

    -- =========================================================================
    -- CHECK 2: outreach_id must be in canary allowlist
    -- =========================================================================
    SELECT EXISTS (
        SELECT 1 FROM people.slot_ingress_canary c
        WHERE c.outreach_id = p_outreach_id
    ) INTO v_in_canary;
    
    IF NOT v_in_canary THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            'NOT_IN_CANARY: outreach_id is not in slot_ingress_canary allowlist'::TEXT,
            NULL::TEXT,
            NULL::TEXT;
        RETURN;
    END IF;

    -- =========================================================================
    -- CHECK 3: Slot must exist for (outreach_id, slot_type)
    -- =========================================================================
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
    
    -- =========================================================================
    -- CHECK 4: Slot status must be 'open'
    -- =========================================================================
    IF v_slot_status != 'open' THEN
        RETURN QUERY SELECT 
            FALSE::BOOLEAN, 
            format('SLOT_NOT_OPEN: Slot status is %s', v_slot_status)::TEXT,
            v_slot_id,
            v_slot_status;
        RETURN;
    END IF;
    
    -- =========================================================================
    -- CHECK 5: No pending resolution attempt in queue
    -- =========================================================================
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
            'RESOLUTION_PENDING: Slot has pending resolution attempt in queue'::TEXT,
            v_slot_id,
            v_slot_status;
        RETURN;
    END IF;
    
    -- =========================================================================
    -- CHECK 6: No prior attempt in resolution history
    -- =========================================================================
    -- Check if people.people_resolution_history exists first
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'people' 
        AND table_name = 'people_resolution_history'
    ) THEN
        SELECT EXISTS (
            SELECT 1 
            FROM people.people_resolution_history prh
            WHERE prh.outreach_id = p_outreach_id
              AND prh.slot_id = v_slot_id
        ) INTO v_prior_resolution;
        
        IF v_prior_resolution THEN
            RETURN QUERY SELECT 
                FALSE::BOOLEAN, 
                'PRIOR_RESOLUTION: Slot has prior resolution attempt in history'::TEXT,
                v_slot_id,
                v_slot_status;
            RETURN;
        END IF;
    END IF;
    
    -- =========================================================================
    -- ALL CHECKS PASSED
    -- =========================================================================
    RETURN QUERY SELECT 
        TRUE::BOOLEAN, 
        'SLOT_READY: Slot can accept candidate (canary-approved)'::TEXT,
        v_slot_id,
        v_slot_status;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION people.slot_can_accept_candidate(UUID, VARCHAR) IS
'PI.GUARD.001 | Canary-aware guard function for slot candidate ingestion.
Enforces (in order, non-negotiable):
  1. Kill switch is enabled (slot_ingress_control)
  2. outreach_id is in canary allowlist (slot_ingress_canary)
  3. Slot exists for (outreach_id, slot_type)
  4. Slot status = open
  5. No pending resolution attempt in queue
  6. No prior resolution attempt in history
Returns: (can_accept, reason, slot_id, current_status)
Version: P2 Canary-Aware';

RAISE NOTICE '✅ Phase 2: Augmented people.slot_can_accept_candidate() with canary checks';

-- =============================================================================
-- PHASE 3: KILL SWITCH METADATA (PREPARE, DO NOT AUTO-ENABLE)
-- =============================================================================
-- This section prepares the kill switch for human enablement
-- The actual UPDATE is provided separately for human execution

-- Add canary_mode column to track that we're in canary phase
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'people'
        AND table_name = 'slot_ingress_control'
        AND column_name = 'canary_mode'
    ) THEN
        ALTER TABLE people.slot_ingress_control
        ADD COLUMN canary_mode BOOLEAN NOT NULL DEFAULT TRUE;
        
        COMMENT ON COLUMN people.slot_ingress_control.canary_mode IS
        'PI.KILL.003 | When TRUE, ingestion is limited to canary allowlist only';
        
        RAISE NOTICE '✅ Phase 3: Added canary_mode column to slot_ingress_control';
    ELSE
        RAISE NOTICE '⏭️  Phase 3: canary_mode column already exists';
    END IF;
END $$;

-- Update metadata to indicate canary mode (but keep is_enabled = FALSE)
UPDATE people.slot_ingress_control
SET canary_mode = TRUE,
    description = 'Master kill switch for slot candidate ingestion. When OFF, all ingestion blocked. When ON with canary_mode=TRUE, only canary allowlist outreach_ids accepted.'
WHERE switch_name = 'slot_ingress';

RAISE NOTICE '⚠️  Phase 3: Kill switch prepared but NOT enabled. Human must execute enablement SQL.';

-- =============================================================================
-- PHASE 4: OBSERVABILITY VIEW
-- =============================================================================
-- Read-only view of canary activity

CREATE OR REPLACE VIEW people.v_candidate_canary_activity AS
SELECT
    pc.candidate_id,
    pc.outreach_id,
    pc.slot_type,
    pc.person_name,
    pc.person_email,
    pc.source,
    pc.status,
    pc.rejection_reason,
    pc.confidence_score,
    pc.created_at,
    pc.processed_at,
    c.added_by AS canary_added_by,
    c.added_at AS canary_added_at,
    c.notes AS canary_notes
FROM people.people_candidate pc
JOIN people.slot_ingress_canary c
  ON pc.outreach_id = c.outreach_id
ORDER BY pc.created_at DESC;

COMMENT ON VIEW people.v_candidate_canary_activity IS
'PI.VIEW.003 | Read-only view of candidate activity for canary outreach_ids.
Shows all candidates submitted for outreach_ids in the canary allowlist.
Used for monitoring canary ingestion success/failure rates.';

-- Additional view: canary queue depth
CREATE OR REPLACE VIEW people.v_canary_queue_depth AS
SELECT
    c.outreach_id,
    c.added_by,
    c.added_at,
    COUNT(pc.candidate_id) FILTER (WHERE pc.status = 'pending') AS pending_count,
    COUNT(pc.candidate_id) FILTER (WHERE pc.status = 'accepted') AS accepted_count,
    COUNT(pc.candidate_id) FILTER (WHERE pc.status = 'rejected') AS rejected_count,
    COUNT(pc.candidate_id) AS total_candidates
FROM people.slot_ingress_canary c
LEFT JOIN people.people_candidate pc ON c.outreach_id = pc.outreach_id
GROUP BY c.outreach_id, c.added_by, c.added_at
ORDER BY c.added_at DESC;

COMMENT ON VIEW people.v_canary_queue_depth IS
'PI.VIEW.004 | Queue depth metrics per canary outreach_id.
Shows pending/accepted/rejected counts for each canary slot.';

RAISE NOTICE '✅ Phase 4: Created observability views';

-- =============================================================================
-- VERIFICATION BLOCK
-- =============================================================================

DO $$
DECLARE
    v_canary_table BOOLEAN;
    v_guard_updated BOOLEAN;
    v_canary_mode_col BOOLEAN;
    v_activity_view BOOLEAN;
    v_depth_view BOOLEAN;
    v_kill_switch_off BOOLEAN;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    RAISE NOTICE '  P2 CANARY INGESTION — VERIFICATION';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
    
    -- Check canary table
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'people' AND table_name = 'slot_ingress_canary'
    ) INTO v_canary_table;
    RAISE NOTICE '  ✓ people.slot_ingress_canary: %', 
        CASE WHEN v_canary_table THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Check guard function updated
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'people' AND p.proname = 'slot_can_accept_candidate'
    ) INTO v_guard_updated;
    RAISE NOTICE '  ✓ slot_can_accept_candidate (canary): %', 
        CASE WHEN v_guard_updated THEN 'UPDATED' ELSE 'MISSING' END;
    
    -- Check canary_mode column
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'people'
        AND table_name = 'slot_ingress_control'
        AND column_name = 'canary_mode'
    ) INTO v_canary_mode_col;
    RAISE NOTICE '  ✓ canary_mode column: %', 
        CASE WHEN v_canary_mode_col THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Check views
    SELECT EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_schema = 'people' AND table_name = 'v_candidate_canary_activity'
    ) INTO v_activity_view;
    RAISE NOTICE '  ✓ v_candidate_canary_activity: %', 
        CASE WHEN v_activity_view THEN 'EXISTS' ELSE 'MISSING' END;
    
    SELECT EXISTS (
        SELECT 1 FROM information_schema.views 
        WHERE table_schema = 'people' AND table_name = 'v_canary_queue_depth'
    ) INTO v_depth_view;
    RAISE NOTICE '  ✓ v_canary_queue_depth: %', 
        CASE WHEN v_depth_view THEN 'EXISTS' ELSE 'MISSING' END;
    
    -- Verify kill switch is still OFF
    SELECT NOT COALESCE(
        (SELECT is_enabled FROM people.slot_ingress_control WHERE switch_name = 'slot_ingress'),
        TRUE
    ) INTO v_kill_switch_off;
    RAISE NOTICE '  ✓ Kill switch (is_enabled): %', 
        CASE WHEN v_kill_switch_off THEN 'OFF (safe)' ELSE '⚠️ ON' END;
    
    RAISE NOTICE '';
    RAISE NOTICE '  STATUS: P2 Canary structure complete';
    RAISE NOTICE '  KILL SWITCH: OFF (human must enable)';
    RAISE NOTICE '  CANARY: Empty (human must populate)';
    RAISE NOTICE '  INGESTION: BLOCKED until both conditions met';
    RAISE NOTICE '═══════════════════════════════════════════════════════════════';
END $$;

COMMIT;

-- =============================================================================
-- HUMAN ACTIONS REQUIRED (DO NOT AUTO-EXECUTE)
-- =============================================================================
-- 
-- STEP 1: Populate canary allowlist (10-25 outreach_ids)
-- 
-- INSERT INTO people.slot_ingress_canary (outreach_id, added_by, notes)
-- VALUES 
--     ('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', 'your_name', 'Canary test #1'),
--     ('yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy', 'your_name', 'Canary test #2');
--
-- STEP 2: Enable kill switch (after canary is populated)
--
-- UPDATE people.slot_ingress_control
-- SET is_enabled = TRUE,
--     enabled_by = 'your_name',
--     enabled_at = NOW()
-- WHERE switch_name = 'slot_ingress';
--
-- STEP 3: Verify with test query
--
-- SELECT * FROM people.slot_can_accept_candidate(
--     'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'::UUID, 
--     'CEO'
-- );
--
-- =============================================================================
