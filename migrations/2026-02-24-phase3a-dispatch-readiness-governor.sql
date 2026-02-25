-- ============================================================================
-- Phase 3A — Dispatch Readiness Governor (MID READY Gate)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0850_PHASE3A_DISPATCH_READINESS_GOVERNOR_MID_READY_GATE
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Enum values: COMPILED, READY, SENT added to lcs.dispatch_state
--   Column:      lcs.mid_ledger.ready_at
--   Function:    lcs.fn_mid_suppression_check(uuid) — stub (always TRUE)
--   Function:    lcs.fn_mark_mid_ready(uuid) — READY gate
--
-- Modifies:
--   Function:    lcs.fn_dispatch_state_forward_only() — explicit whitelist
--   Function:    lcs.fn_canonical_monotonic_guard() — updated dispatch ordinals
--   Permissions: lcs_worker EXECUTE on fn_mark_mid_ready
--
-- New FSM:
--   MINTED → COMPILED → READY → SENT → DELIVERED | FAILED | BOUNCED
--   QUEUED/DISPATCHED deprecated (no transitions from/to)
--   Terminal: DELIVERED, FAILED, BOUNCED
--
-- No RAISE-after-DML. Errors reflected in lcs_errors.
-- ============================================================================

-- Enum additions MUST run outside transaction (PostgreSQL requirement).
-- IF NOT EXISTS prevents re-run failures.
ALTER TYPE lcs.dispatch_state ADD VALUE IF NOT EXISTS 'COMPILED' AFTER 'MINTED';
ALTER TYPE lcs.dispatch_state ADD VALUE IF NOT EXISTS 'READY' AFTER 'COMPILED';
ALTER TYPE lcs.dispatch_state ADD VALUE IF NOT EXISTS 'SENT' AFTER 'READY';

BEGIN;

-- ============================================================================
-- 1. Add ready_at column to mid_ledger
-- ============================================================================

ALTER TABLE lcs.mid_ledger ADD COLUMN IF NOT EXISTS ready_at TIMESTAMPTZ;

-- Partial index for transport dispatch queries (find READY MIDs)
CREATE INDEX IF NOT EXISTS idx_mid_ledger_ready
    ON lcs.mid_ledger(dispatch_state) WHERE dispatch_state = 'READY';

-- ============================================================================
-- 2. Replace forward-only trigger with explicit whitelist
-- ============================================================================
-- Old: ordinal-based (MINTED=1 → QUEUED=2 → DISPATCHED=3 → terminal=4)
-- New: explicit whitelist of allowed transitions
--   MINTED → COMPILED → READY → SENT → DELIVERED | FAILED | BOUNCED
--   All other transitions blocked. QUEUED/DISPATCHED deprecated.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_dispatch_state_forward_only()
RETURNS TRIGGER AS $$
BEGIN
    -- Terminal states cannot transition
    IF OLD.dispatch_state IN ('DELIVERED', 'BOUNCED', 'FAILED') THEN
        RAISE EXCEPTION 'dispatch_state % is terminal. mid=% cannot transition further.',
            OLD.dispatch_state, OLD.mid;
    END IF;

    -- Explicit whitelist of allowed transitions
    IF (OLD.dispatch_state = 'MINTED'   AND NEW.dispatch_state = 'COMPILED')
    OR (OLD.dispatch_state = 'COMPILED' AND NEW.dispatch_state = 'READY')
    OR (OLD.dispatch_state = 'READY'    AND NEW.dispatch_state = 'SENT')
    OR (OLD.dispatch_state = 'SENT'     AND NEW.dispatch_state IN ('DELIVERED', 'FAILED', 'BOUNCED'))
    THEN
        RETURN NEW;
    END IF;

    RAISE EXCEPTION 'dispatch_state transition % -> % is not allowed for mid=%',
        OLD.dispatch_state, NEW.dispatch_state, OLD.mid;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. Update canonical monotonic guard with new dispatch ordinals
-- ============================================================================
-- Includes COMPILED, READY, SENT. Deprecated QUEUED/DISPATCHED retained
-- at compatible ordinals so existing canonical rows (if any) don't break.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_canonical_monotonic_guard()
RETURNS TRIGGER AS $$
DECLARE
    v_old_lifecycle_ord INTEGER;
    v_new_lifecycle_ord INTEGER;
    v_old_dispatch_ord  INTEGER;
    v_new_dispatch_ord  INTEGER;
BEGIN
    -- 1. Lifecycle stage: forward-only
    v_old_lifecycle_ord := CASE OLD.current_lifecycle_stage
        WHEN 'SUSPECT'    THEN 1
        WHEN 'IDENTIFIED' THEN 2
        WHEN 'QUALIFIED'  THEN 3
        WHEN 'ENGAGED'    THEN 4
        WHEN 'CONVERTED'  THEN 5
        WHEN 'SUPPRESSED' THEN 6
    END;
    v_new_lifecycle_ord := CASE NEW.current_lifecycle_stage
        WHEN 'SUSPECT'    THEN 1
        WHEN 'IDENTIFIED' THEN 2
        WHEN 'QUALIFIED'  THEN 3
        WHEN 'ENGAGED'    THEN 4
        WHEN 'CONVERTED'  THEN 5
        WHEN 'SUPPRESSED' THEN 6
    END;

    IF v_new_lifecycle_ord < v_old_lifecycle_ord THEN
        RAISE EXCEPTION
            'lcs.lcs_canonical: lifecycle regression blocked (% -> %). sovereign_id=%',
            OLD.current_lifecycle_stage, NEW.current_lifecycle_stage, OLD.sovereign_id;
    END IF;

    -- 2. SID: once set, cannot change to different value
    IF OLD.current_sid IS NOT NULL AND NEW.current_sid IS DISTINCT FROM OLD.current_sid THEN
        RAISE EXCEPTION
            'lcs.lcs_canonical: SID rewind blocked. current_sid cannot change once set. sovereign_id=%',
            OLD.sovereign_id;
    END IF;

    -- 3. MID: cannot regress to NULL
    IF OLD.current_mid IS NOT NULL AND NEW.current_mid IS NULL THEN
        RAISE EXCEPTION
            'lcs.lcs_canonical: MID null regression blocked. sovereign_id=%',
            OLD.sovereign_id;
    END IF;

    -- 4. last_cid: cannot regress to NULL
    IF OLD.last_cid IS NOT NULL AND NEW.last_cid IS NULL THEN
        RAISE EXCEPTION
            'lcs.lcs_canonical: last_cid null regression blocked. sovereign_id=%',
            OLD.sovereign_id;
    END IF;

    -- 5. Dispatch state: forward-only WITHIN same MID
    --    If MID changed, dispatch restarts (new cycle) — no regression check.
    --    Updated ordinals include COMPILED, READY, SENT.
    --    Deprecated QUEUED/DISPATCHED at compatible ordinals.
    IF NEW.current_mid IS NOT DISTINCT FROM OLD.current_mid
       AND OLD.current_dispatch_state IS NOT NULL
       AND NEW.current_dispatch_state IS NOT NULL THEN

        v_old_dispatch_ord := CASE OLD.current_dispatch_state
            WHEN 'MINTED'     THEN 1
            WHEN 'COMPILED'   THEN 2
            WHEN 'QUEUED'     THEN 2   -- deprecated, ordinal compat with COMPILED
            WHEN 'READY'      THEN 3
            WHEN 'DISPATCHED' THEN 4   -- deprecated, ordinal compat with SENT
            WHEN 'SENT'       THEN 4
            WHEN 'DELIVERED'  THEN 5
            WHEN 'BOUNCED'    THEN 5
            WHEN 'FAILED'     THEN 5
        END;
        v_new_dispatch_ord := CASE NEW.current_dispatch_state
            WHEN 'MINTED'     THEN 1
            WHEN 'COMPILED'   THEN 2
            WHEN 'QUEUED'     THEN 2
            WHEN 'READY'      THEN 3
            WHEN 'DISPATCHED' THEN 4
            WHEN 'SENT'       THEN 4
            WHEN 'DELIVERED'  THEN 5
            WHEN 'BOUNCED'    THEN 5
            WHEN 'FAILED'     THEN 5
        END;

        IF v_new_dispatch_ord < v_old_dispatch_ord THEN
            RAISE EXCEPTION
                'lcs.lcs_canonical: dispatch state regression blocked (% -> %). sovereign_id=%',
                OLD.current_dispatch_state, NEW.current_dispatch_state, OLD.sovereign_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. Suppression check stub (Phase 3B placeholder)
-- ============================================================================
-- Always returns TRUE (not suppressed). Will be replaced by Phase 3B
-- cadence/suppression engine.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_mid_suppression_check(p_mid UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Stub: always passes. Phase 3B will implement cadence/cooldown logic.
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. fn_mark_mid_ready — READY gate
-- ============================================================================
-- Sole entry point for transitioning a MID from COMPILED → READY.
--   1. Lock MID row in mid_ledger
--   2. Validate MID exists
--   3. Validate dispatch_state = COMPILED
--   4. Validate canonical lifecycle permits dispatch (QUALIFIED+, not SUPPRESSED)
--   5. Check suppression (fn_mid_suppression_check)
--   6. Update dispatch_state = READY, ready_at = NOW()
--   On failure: log lcs_errors row, RETURN cleanly. No RAISE-after-DML.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_mark_mid_ready(p_mid UUID)
RETURNS VOID AS $$
DECLARE
    v_mid_row       lcs.mid_ledger%ROWTYPE;
    v_lifecycle     TEXT;
    v_lifecycle_ord INTEGER;
    v_suppression   BOOLEAN;
BEGIN
    -- 1. Lock MID row
    SELECT * INTO v_mid_row
    FROM lcs.mid_ledger
    WHERE mid = p_mid
    FOR UPDATE;

    IF NOT FOUND THEN
        -- mid FK constraint: cannot reference non-existent MID, use NULL
        INSERT INTO lcs.lcs_errors (error_stage, error_type, error_payload)
        VALUES ('mid_minting', 'validation',
            jsonb_build_object('message', 'MID not found in mid_ledger', 'attempted_mid', p_mid::text));
        RETURN;
    END IF;

    -- 2. Validate dispatch_state = COMPILED
    IF v_mid_row.dispatch_state != 'COMPILED' THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, mid, sovereign_id, error_payload)
        VALUES ('mid_minting', 'state_violation', p_mid, v_mid_row.sovereign_id,
            jsonb_build_object('message', format('MID dispatch_state is %s, expected COMPILED', v_mid_row.dispatch_state),
                'current_state', v_mid_row.dispatch_state::text));
        RETURN;
    END IF;

    -- 3. Validate canonical lifecycle permits dispatch
    SELECT current_lifecycle_stage INTO v_lifecycle
    FROM lcs.lcs_canonical
    WHERE sovereign_id = v_mid_row.sovereign_id;

    IF v_lifecycle IS NULL THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, mid, sovereign_id, error_payload)
        VALUES ('mid_minting', 'validation', p_mid, v_mid_row.sovereign_id,
            jsonb_build_object('message', 'No canonical record for sovereign_id'));
        RETURN;
    END IF;

    v_lifecycle_ord := CASE v_lifecycle
        WHEN 'SUSPECT'    THEN 1
        WHEN 'IDENTIFIED' THEN 2
        WHEN 'QUALIFIED'  THEN 3
        WHEN 'ENGAGED'    THEN 4
        WHEN 'CONVERTED'  THEN 5
        WHEN 'SUPPRESSED' THEN 6
    END;

    -- Dispatch eligible: QUALIFIED (3), ENGAGED (4), CONVERTED (5)
    -- Not eligible: SUSPECT (1), IDENTIFIED (2), SUPPRESSED (6)
    IF v_lifecycle_ord < 3 OR v_lifecycle = 'SUPPRESSED' THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, mid, sovereign_id, error_payload)
        VALUES ('mid_minting', 'conflict', p_mid, v_mid_row.sovereign_id,
            jsonb_build_object('message', format('Lifecycle stage %s does not permit dispatch', v_lifecycle),
                'lifecycle_stage', v_lifecycle));
        RETURN;
    END IF;

    -- 4. Suppression check
    v_suppression := lcs.fn_mid_suppression_check(p_mid);
    IF NOT v_suppression THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, mid, sovereign_id, error_payload)
        VALUES ('mid_minting', 'conflict', p_mid, v_mid_row.sovereign_id,
            jsonb_build_object('message', 'MID suppressed by fn_mid_suppression_check'));
        RETURN;
    END IF;

    -- 5. Mark READY
    UPDATE lcs.mid_ledger
    SET dispatch_state = 'READY',
        ready_at = NOW()
    WHERE mid = p_mid;

END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. PERMISSIONS — lcs_worker EXECUTE on fn_mark_mid_ready
-- ============================================================================

REVOKE EXECUTE ON FUNCTION lcs.fn_mark_mid_ready(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION lcs.fn_mark_mid_ready(UUID) TO lcs_worker;

GRANT EXECUTE ON FUNCTION lcs.fn_mid_suppression_check(UUID) TO lcs_worker;

-- ============================================================================
-- 7. COMMENTS
-- ============================================================================

COMMENT ON FUNCTION lcs.fn_mark_mid_ready(UUID) IS
    'READY gate — transitions MID from COMPILED → READY after lifecycle/suppression validation. Logs errors to lcs_errors, no RAISE-after-DML.';
COMMENT ON FUNCTION lcs.fn_mid_suppression_check(UUID) IS
    'Stub — always returns TRUE. Phase 3B will implement cadence/cooldown logic.';
COMMENT ON FUNCTION lcs.fn_dispatch_state_forward_only() IS
    'Phase 3A: Explicit whitelist FSM. MINTED→COMPILED→READY→SENT→DELIVERED|FAILED|BOUNCED. QUEUED/DISPATCHED deprecated.';
COMMENT ON FUNCTION lcs.fn_canonical_monotonic_guard() IS
    'Canonical monotonic guard. Updated Phase 3A: includes COMPILED/READY/SENT dispatch ordinals. Blocks lifecycle regression, SID rewind, MID/CID null regression, dispatch regression within same MID.';

COMMIT;
