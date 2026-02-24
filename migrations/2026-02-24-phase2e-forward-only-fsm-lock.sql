-- ============================================================================
-- Phase 2E — Forward-Only FSM Lock (Emission + CID + Canonical)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0830_PHASE2E_EMISSION_CANONICAL_FORWARD_ONLY_FSM_LOCK
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Part 1: Emission status FSM — STAGED→{PROMOTED,REJECTED,ERROR} only.
--          Terminal states cannot transition further.
-- Part 2: CID immutability — verified (v0 triggers already enforce).
-- Part 3: Canonical monotonic guard — lifecycle/SID/MID/dispatch forward-only.
--
-- Hard rule: All lifecycle state machines are forward-only. No rewind.
-- No silent correction. No implicit downgrade. Violations fail loudly.
-- ============================================================================

BEGIN;

-- ============================================================================
-- PART 1: Emission Status FSM
-- ============================================================================
-- Allowed transitions:
--   STAGED → PROMOTED  (success path)
--   STAGED → REJECTED  (validation failure)
--   STAGED → ERROR     (execution failure)
-- Terminal: PROMOTED, REJECTED, ERROR (no further transitions)
-- Same-status updates (e.g. updating reject_reason) are allowed.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_validate_emission_transition(
    p_old_status TEXT,
    p_new_status TEXT
)
RETURNS VOID AS $$
BEGIN
    -- Same status = not a transition, always allowed
    IF p_old_status = p_new_status THEN
        RETURN;
    END IF;

    -- Legal transitions from STAGED
    IF p_old_status = 'STAGED' AND p_new_status IN ('PROMOTED', 'REJECTED', 'ERROR') THEN
        RETURN;
    END IF;

    -- Everything else is illegal
    RAISE EXCEPTION
        'lcs.movement_emission_intake: illegal status transition (% -> %). '
        'STAGED may transition to PROMOTED/REJECTED/ERROR only. '
        'PROMOTED/REJECTED/ERROR are terminal.',
        p_old_status, p_new_status;
END;
$$ LANGUAGE plpgsql;

-- Trigger function that calls the validator
CREATE OR REPLACE FUNCTION lcs.fn_emission_status_fsm()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM lcs.fn_validate_emission_transition(OLD.status, NEW.status);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Only fires when status actually changes (avoids overhead on non-transition updates)
CREATE TRIGGER trg_emission_status_fsm
    BEFORE UPDATE ON lcs.movement_emission_intake
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION lcs.fn_emission_status_fsm();

-- ============================================================================
-- PART 2: CID Intake Hard Immutability — VERIFIED (v0 enforcement intact)
-- ============================================================================
-- v0 already provides:
--   trg_cid_intake_no_update  — blocks UPDATE when OLD.status != 'PENDING'
--                                (allows one PENDING→ACCEPTED transition by fn_process_cid,
--                                 then row is permanently locked)
--   trg_cid_intake_no_delete  — blocks all DELETE
--
-- This is the correct enforcement pattern: fn_process_cid needs the single
-- PENDING→ACCEPTED update. Full UPDATE block would break the CID pipeline.
-- No new triggers needed.
-- ============================================================================

-- Verify v0 triggers still exist (will raise notice if not found)
DO $$
BEGIN
    PERFORM 1 FROM pg_trigger
    WHERE tgname = 'trg_cid_intake_no_update'
      AND tgrelid = 'lcs.cid_intake'::regclass;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Phase 2E audit: trg_cid_intake_no_update is missing from lcs.cid_intake';
    END IF;

    PERFORM 1 FROM pg_trigger
    WHERE tgname = 'trg_cid_intake_no_delete'
      AND tgrelid = 'lcs.cid_intake'::regclass;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Phase 2E audit: trg_cid_intake_no_delete is missing from lcs.cid_intake';
    END IF;
END $$;

-- ============================================================================
-- PART 3: Canonical Monotonic Guard
-- ============================================================================
-- Prevents:
--   1. Lifecycle stage regression (ordinal comparison)
--   2. SID change after first assignment (once set, immutable)
--   3. MID null regression (non-NULL → NULL blocked)
--   4. last_cid null regression (non-NULL → NULL blocked)
--   5. Dispatch state regression WITHIN same MID
--      (MID change = new cycle, dispatch restarts at MINTED — allowed)
--
-- Fires AFTER the session-var guard (alphabetical: trg_lcs_canonical_guard < trg_lcs_canonical_monotonic)
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
    IF NEW.current_mid IS NOT DISTINCT FROM OLD.current_mid
       AND OLD.current_dispatch_state IS NOT NULL
       AND NEW.current_dispatch_state IS NOT NULL THEN

        v_old_dispatch_ord := CASE OLD.current_dispatch_state
            WHEN 'MINTED'     THEN 1
            WHEN 'QUEUED'     THEN 2
            WHEN 'DISPATCHED' THEN 3
            WHEN 'DELIVERED'  THEN 4
            WHEN 'BOUNCED'    THEN 4
            WHEN 'FAILED'     THEN 4
        END;
        v_new_dispatch_ord := CASE NEW.current_dispatch_state
            WHEN 'MINTED'     THEN 1
            WHEN 'QUEUED'     THEN 2
            WHEN 'DISPATCHED' THEN 3
            WHEN 'DELIVERED'  THEN 4
            WHEN 'BOUNCED'    THEN 4
            WHEN 'FAILED'     THEN 4
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

CREATE TRIGGER trg_lcs_canonical_monotonic
    BEFORE UPDATE ON lcs.lcs_canonical
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_canonical_monotonic_guard();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON FUNCTION lcs.fn_validate_emission_transition(TEXT, TEXT) IS
    'Emission status FSM validator. STAGED→{PROMOTED,REJECTED,ERROR}. All three are terminal.';
COMMENT ON FUNCTION lcs.fn_canonical_monotonic_guard() IS
    'Canonical monotonic guard. Blocks lifecycle regression, SID rewind, MID/CID null regression, dispatch regression within same MID.';

COMMIT;
