-- ============================================================================
-- Phase 2F — Worker Orchestration Contract (DB-First)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0840_PHASE2F_WORKER_ORCHESTRATION_CONTRACT_DB_FIRST
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:    lcs.worker_run_log (SUPPORTING, append-only with completion update)
--   Function: lcs.fn_finalize_dispatch_batch(int) — stub (no transport yet)
--   Function: lcs.fn_worker_tick(text, int) — dispatcher entry point
--   Role:     lcs_worker (EXECUTE-only, no direct table writes)
--
-- fn_worker_tick is the sole DB-owned execution surface for workers.
-- Workers call fn_worker_tick → it dispatches to batch functions → logs result.
-- No RAISE-after-DML. Errors reflected in status/result JSON.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CTB Registration
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'worker_run_log', 'SUPPORTING', FALSE, 'phase2f_worker_contract', 'Worker execution log — append-only with completion update')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 2. lcs.worker_run_log — Worker execution log
-- ============================================================================
-- Append-only with completion carve-out:
--   INSERT creates STARTED row
--   UPDATE allowed: finished_at, status, attempted_count, success_count, error_count, notes
--   Immutable: run_id, run_type, started_at
--   No DELETE
-- ============================================================================

CREATE TABLE lcs.worker_run_log (
    run_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type        TEXT        NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    status          TEXT        NOT NULL DEFAULT 'STARTED',
    attempted_count INTEGER     NOT NULL DEFAULT 0,
    success_count   INTEGER     NOT NULL DEFAULT 0,
    error_count     INTEGER     NOT NULL DEFAULT 0,
    notes           JSONB
);

ALTER TABLE lcs.worker_run_log ADD CONSTRAINT chk_worker_run_type
    CHECK (run_type IN ('PROMOTE_EMISSIONS', 'FINALIZE_DISPATCH'));

ALTER TABLE lcs.worker_run_log ADD CONSTRAINT chk_worker_run_status
    CHECK (status IN ('STARTED', 'SUCCESS', 'PARTIAL', 'FAIL'));

CREATE INDEX idx_worker_run_log_type   ON lcs.worker_run_log(run_type);
CREATE INDEX idx_worker_run_log_status ON lcs.worker_run_log(status, started_at DESC);

-- Guard: identity columns immutable after insert
CREATE OR REPLACE FUNCTION lcs.fn_worker_run_log_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.run_id   != OLD.run_id   OR
       NEW.run_type != OLD.run_type OR
       NEW.started_at != OLD.started_at THEN
        RAISE EXCEPTION 'lcs.worker_run_log: identity columns (run_id, run_type, started_at) are immutable. run_id=%', OLD.run_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_worker_run_log_guard
    BEFORE UPDATE ON lcs.worker_run_log
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_worker_run_log_guard();

-- No DELETE
CREATE OR REPLACE FUNCTION lcs.fn_worker_run_log_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.worker_run_log rows cannot be deleted. run_id=%', OLD.run_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_worker_run_log_no_delete
    BEFORE DELETE ON lcs.worker_run_log
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_worker_run_log_no_delete();

-- ============================================================================
-- 3. lcs.fn_finalize_dispatch_batch — Stub
-- ============================================================================
-- No transport layer yet. Returns 0.
-- Will be replaced when transport adapter is implemented.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_finalize_dispatch_batch(p_limit INTEGER DEFAULT 100)
RETURNS INTEGER AS $$
BEGIN
    -- Stub: no transport layer. Nothing to finalize.
    RETURN 0;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. lcs.fn_worker_tick — Dispatcher entry point
-- ============================================================================
-- Sole DB-owned execution surface for workers.
--   1. INSERT run log (STARTED)
--   2. Dispatch to batch function based on run_type
--   3. UPDATE run log with counts + status
--   4. Return strict JSON summary
-- No RAISE-after-DML. Errors reflected in status field.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_worker_tick(
    p_run_type TEXT,
    p_limit    INTEGER DEFAULT 250
)
RETURNS JSONB AS $$
DECLARE
    v_run_id        UUID;
    v_staged_before INTEGER;
    v_attempted     INTEGER := 0;
    v_success       INTEGER := 0;
    v_errors        INTEGER := 0;
    v_status        TEXT;
BEGIN
    -- Validate run_type early (before any DML)
    IF p_run_type NOT IN ('PROMOTE_EMISSIONS', 'FINALIZE_DISPATCH') THEN
        RETURN jsonb_build_object(
            'run_id', NULL,
            'run_type', p_run_type,
            'attempted', 0,
            'success', 0,
            'errors', 0,
            'status', 'FAIL',
            'error', 'invalid run_type: must be PROMOTE_EMISSIONS or FINALIZE_DISPATCH');
    END IF;

    -- 1. Insert STARTED run log
    INSERT INTO lcs.worker_run_log (run_type, status)
    VALUES (p_run_type, 'STARTED')
    RETURNING run_id INTO v_run_id;

    -- 2. Dispatch
    BEGIN
        IF p_run_type = 'PROMOTE_EMISSIONS' THEN
            -- Count available work before batch
            SELECT count(*) INTO v_staged_before
            FROM lcs.movement_emission_intake
            WHERE status = 'STAGED';

            v_attempted := LEAST(v_staged_before, p_limit);

            -- Run promotion batch
            v_success := lcs.fn_promote_emission_batch(p_limit);
            v_errors  := GREATEST(v_attempted - v_success, 0);

        ELSIF p_run_type = 'FINALIZE_DISPATCH' THEN
            -- Dispatch to finalize batch (stub returns 0)
            v_success   := lcs.fn_finalize_dispatch_batch(p_limit);
            v_attempted := v_success;
            v_errors    := 0;
        END IF;

        -- Determine status
        IF v_attempted = 0 THEN
            v_status := 'SUCCESS';
        ELSIF v_errors = 0 THEN
            v_status := 'SUCCESS';
        ELSIF v_success > 0 THEN
            v_status := 'PARTIAL';
        ELSE
            v_status := 'FAIL';
        END IF;

    EXCEPTION WHEN OTHERS THEN
        -- Unexpected error: run log INSERT survives (outside this block)
        v_status  := 'FAIL';
        v_errors  := v_attempted;
        v_success := 0;
    END;

    -- 3. Update run log with results
    UPDATE lcs.worker_run_log
    SET finished_at      = NOW(),
        status           = v_status,
        attempted_count  = v_attempted,
        success_count    = v_success,
        error_count      = v_errors
    WHERE run_id = v_run_id;

    -- 4. Return strict JSON summary
    RETURN jsonb_build_object(
        'run_id',    v_run_id,
        'run_type',  p_run_type,
        'attempted', v_attempted,
        'success',   v_success,
        'errors',    v_errors,
        'status',    v_status
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. PERMISSIONS — lcs_worker role (EXECUTE-only)
-- ============================================================================

DO $$ BEGIN
    CREATE ROLE lcs_worker NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

GRANT EXECUTE ON FUNCTION lcs.fn_worker_tick(TEXT, INTEGER) TO lcs_worker;

-- No direct table writes
REVOKE ALL ON lcs.worker_run_log FROM lcs_worker;
REVOKE ALL ON lcs.movement_emission_intake FROM lcs_worker;
REVOKE ALL ON lcs.cid_intake FROM lcs_worker;
REVOKE ALL ON lcs.sid_registry FROM lcs_worker;
REVOKE ALL ON lcs.mid_ledger FROM lcs_worker;
REVOKE ALL ON lcs.lcs_canonical FROM lcs_worker;
REVOKE ALL ON lcs.lcs_errors FROM lcs_worker;

-- ============================================================================
-- 6. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.worker_run_log IS
    'SUPPORTING — Worker execution log. Append-only with completion update. Identity columns immutable.';
COMMENT ON FUNCTION lcs.fn_worker_tick(TEXT, INTEGER) IS
    'DB-owned worker entry point. Dispatches to batch functions, logs results, returns strict JSON summary. No RAISE-after-DML.';
COMMENT ON FUNCTION lcs.fn_finalize_dispatch_batch(INTEGER) IS
    'Stub — no transport layer yet. Returns 0. Will be replaced when transport adapter is implemented.';

COMMIT;
