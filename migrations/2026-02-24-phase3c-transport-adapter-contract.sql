-- ============================================================================
-- Phase 3C — Transport Adapter Contract (External Boundary Lock)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0910_PHASE3C_TRANSPORT_ADAPTER_CONTRACT_EXTERNAL_BOUNDARY_LOCK
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Columns:  lcs.mid_ledger.{provider, external_message_id, delivered_at, failed_at, bounced_at}
--   Table:    lcs.dispatch_event_log (SUPPORTING, append-only, CTB-registered)
--   Function: lcs.fn_record_dispatch_result(uuid, text, text, text, jsonb)
--   Role:     lcs_transport (EXECUTE-only, no direct table writes)
--
-- fn_record_dispatch_result is the ONLY legal DB entry point for transport
-- result reporting. No adapter may mutate mid_ledger directly.
-- Existing forward-only FSM trigger enforces SENT → terminal transitions.
-- No RAISE-after-DML.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. CTB Registration for dispatch_event_log
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'dispatch_event_log', 'SUPPORTING', FALSE, 'phase3c_transport_contract',
    'Append-only transport result event log. One row per dispatch outcome report.')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 2. Add transport columns to mid_ledger
-- ============================================================================
-- These are mutable (not in fn_mid_ledger_guard immutable list).

ALTER TABLE lcs.mid_ledger ADD COLUMN IF NOT EXISTS provider TEXT;
ALTER TABLE lcs.mid_ledger ADD COLUMN IF NOT EXISTS external_message_id TEXT;
ALTER TABLE lcs.mid_ledger ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMPTZ;
ALTER TABLE lcs.mid_ledger ADD COLUMN IF NOT EXISTS failed_at TIMESTAMPTZ;
ALTER TABLE lcs.mid_ledger ADD COLUMN IF NOT EXISTS bounced_at TIMESTAMPTZ;

-- ============================================================================
-- 3. lcs.dispatch_event_log — Transport result event log
-- ============================================================================
-- Append-only. No UPDATE, no DELETE.
-- One row per dispatch outcome report from transport adapters.
-- ============================================================================

CREATE TABLE lcs.dispatch_event_log (
    event_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    mid             UUID        NOT NULL REFERENCES lcs.mid_ledger(mid),
    provider        TEXT        NOT NULL,
    external_message_id TEXT,
    result_state    TEXT        NOT NULL,
    metadata        JSONB,
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE lcs.dispatch_event_log ADD CONSTRAINT chk_dispatch_event_result_state
    CHECK (result_state IN ('DELIVERED', 'FAILED', 'BOUNCED'));

CREATE INDEX idx_dispatch_event_log_mid ON lcs.dispatch_event_log(mid);
CREATE INDEX idx_dispatch_event_log_provider ON lcs.dispatch_event_log(provider, recorded_at DESC);

-- Append-only: no UPDATE
CREATE OR REPLACE FUNCTION lcs.fn_dispatch_event_log_no_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.dispatch_event_log is append-only. event_id=% cannot be modified.', OLD.event_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dispatch_event_log_no_update
    BEFORE UPDATE ON lcs.dispatch_event_log
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_dispatch_event_log_no_update();

-- Append-only: no DELETE
CREATE OR REPLACE FUNCTION lcs.fn_dispatch_event_log_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.dispatch_event_log rows cannot be deleted. event_id=%', OLD.event_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dispatch_event_log_no_delete
    BEFORE DELETE ON lcs.dispatch_event_log
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_dispatch_event_log_no_delete();

-- ============================================================================
-- 4. fn_record_dispatch_result — External boundary entry point
-- ============================================================================
-- Sole legal DB entry point for transport result reporting.
--   1. Lock MID row
--   2. Validate dispatch_state = SENT
--   3. Validate p_result_state in {DELIVERED, FAILED, BOUNCED}
--   4. Update mid_ledger (FSM trigger enforces forward-only)
--   5. Insert dispatch_event_log row
--   On failure: log lcs_errors, RETURN cleanly. No RAISE-after-DML.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_record_dispatch_result(
    p_mid                UUID,
    p_provider           TEXT,
    p_external_message_id TEXT,
    p_result_state       TEXT,
    p_metadata           JSONB DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    v_mid_row   lcs.mid_ledger%ROWTYPE;
BEGIN
    -- 1. Lock MID row
    SELECT * INTO v_mid_row
    FROM lcs.mid_ledger
    WHERE mid = p_mid
    FOR UPDATE;

    IF NOT FOUND THEN
        -- mid FK constraint: cannot reference non-existent MID, use NULL
        INSERT INTO lcs.lcs_errors (error_stage, error_type, error_payload)
        VALUES ('dispatch_finalization', 'validation',
            jsonb_build_object('message', 'MID not found in mid_ledger', 'attempted_mid', p_mid::text));
        RETURN;
    END IF;

    -- 2. Validate dispatch_state = SENT
    IF v_mid_row.dispatch_state != 'SENT' THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, mid, sovereign_id, error_payload)
        VALUES ('dispatch_finalization', 'state_violation', p_mid, v_mid_row.sovereign_id,
            jsonb_build_object('message', format('MID dispatch_state is %s, expected SENT', v_mid_row.dispatch_state),
                'current_state', v_mid_row.dispatch_state::text, 'provider', p_provider));
        RETURN;
    END IF;

    -- 3. Validate p_result_state
    IF p_result_state NOT IN ('DELIVERED', 'FAILED', 'BOUNCED') THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, mid, sovereign_id, error_payload)
        VALUES ('dispatch_finalization', 'validation', p_mid, v_mid_row.sovereign_id,
            jsonb_build_object('message', format('Invalid result_state: %s. Must be DELIVERED, FAILED, or BOUNCED', p_result_state),
                'result_state', p_result_state, 'provider', p_provider));
        RETURN;
    END IF;

    -- 4. Update mid_ledger (FSM trigger enforces SENT → terminal)
    UPDATE lcs.mid_ledger
    SET dispatch_state      = p_result_state::lcs.dispatch_state,
        provider            = p_provider,
        external_message_id = p_external_message_id,
        dispatch_result     = p_metadata,
        finalized_at        = NOW(),
        delivered_at        = CASE WHEN p_result_state = 'DELIVERED' THEN NOW() ELSE NULL END,
        failed_at           = CASE WHEN p_result_state = 'FAILED'    THEN NOW() ELSE NULL END,
        bounced_at          = CASE WHEN p_result_state = 'BOUNCED'   THEN NOW() ELSE NULL END
    WHERE mid = p_mid;

    -- 5. Insert dispatch event log
    INSERT INTO lcs.dispatch_event_log (mid, provider, external_message_id, result_state, metadata)
    VALUES (p_mid, p_provider, p_external_message_id, p_result_state, p_metadata);

END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. PERMISSIONS — lcs_transport role (EXECUTE-only)
-- ============================================================================

DO $$ BEGIN
    CREATE ROLE lcs_transport NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

REVOKE EXECUTE ON FUNCTION lcs.fn_record_dispatch_result(UUID, TEXT, TEXT, TEXT, JSONB) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION lcs.fn_record_dispatch_result(UUID, TEXT, TEXT, TEXT, JSONB) TO lcs_transport;

-- No direct table writes
REVOKE ALL ON lcs.mid_ledger FROM lcs_transport;
REVOKE ALL ON lcs.dispatch_event_log FROM lcs_transport;
REVOKE ALL ON lcs.lcs_errors FROM lcs_transport;
REVOKE ALL ON lcs.lcs_canonical FROM lcs_transport;
REVOKE ALL ON lcs.worker_run_log FROM lcs_transport;

-- ============================================================================
-- 6. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.dispatch_event_log IS
    'SUPPORTING — Append-only transport result event log. One row per dispatch outcome report. No UPDATE, no DELETE.';
COMMENT ON FUNCTION lcs.fn_record_dispatch_result(UUID, TEXT, TEXT, TEXT, JSONB) IS
    'External boundary lock — sole legal DB entry point for transport result reporting. Validates SENT state, terminal result, updates mid_ledger, logs event. No RAISE-after-DML.';

COMMIT;
