-- ============================================================================
-- LCS Spine v1 — CTB Cantonal Refactor
-- ============================================================================
-- WORK_PACKET: WP_20260224T0720_LCS_SPINE_V1_CTB_REFACTOR
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:     lcs.lcs_canonical  (one row per sovereign_id)
--   Table:     lcs.lcs_errors     (cantonal error capture)
--   View:      lcs.lcs_intake     (doctrinal surface over cid_intake)
--
-- Updates:
--   Function:  lcs.fn_process_cid(uuid)       — adds canonical UPSERT + error logging
--   Function:  lcs.fn_finalize_dispatch(uuid, jsonb) — adds canonical update + error logging
--
-- CTB Registry:
--   Reclassifies cid_intake, sid_registry, mid_ledger → SUPPORTING
--   Registers lcs_canonical (CANONICAL), lcs_errors (ERROR)
--
-- Preserves all v0 enforcement: append-only CID, MID immutability, forward-only FSM.
-- No v0 tables deleted. No references to dropped views.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 0. CTB PRE-REGISTRATION (DDL gate requires registry entry before CREATE)
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES
    ('lcs', 'lcs_canonical', 'CANONICAL', FALSE, 'lcs_v1_ctb_refactor', 'Single authoritative row per company in LCS'),
    ('lcs', 'lcs_errors',    'ERROR',     FALSE, 'lcs_v1_ctb_refactor', 'Cantonal error capture for LCS function failures')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- Reclassify v0 tables: CANONICAL → SUPPORTING (they now serve lcs_canonical)
UPDATE ctb.table_registry
SET leaf_type = 'SUPPORTING',
    notes = COALESCE(notes, '') || ' | Reclassified v1: serves lcs.lcs_canonical'
WHERE table_schema = 'lcs'
  AND table_name IN ('cid_intake', 'sid_registry', 'mid_ledger')
  AND leaf_type = 'CANONICAL';

-- ============================================================================
-- 1. lcs.lcs_canonical — Single authoritative row per company
-- ============================================================================

CREATE TABLE lcs.lcs_canonical (
    sovereign_id            UUID        PRIMARY KEY
                                        REFERENCES cl.company_identity(company_unique_id),
    current_lifecycle_stage lcs.lifecycle_stage NOT NULL DEFAULT 'IDENTIFIED',
    current_sid             UUID        REFERENCES lcs.sid_registry(sid),
    current_mid             UUID        REFERENCES lcs.mid_ledger(mid),
    current_dispatch_state  lcs.dispatch_state,
    last_cid                UUID        REFERENCES lcs.cid_intake(cid),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_lcs_canonical_stage    ON lcs.lcs_canonical(current_lifecycle_stage);
CREATE INDEX idx_lcs_canonical_dispatch ON lcs.lcs_canonical(current_dispatch_state)
    WHERE current_dispatch_state IN ('MINTED', 'QUEUED', 'DISPATCHED');

-- Guard trigger: writes only through LCS functions (session-var enforcement skeleton)
CREATE OR REPLACE FUNCTION lcs.fn_lcs_canonical_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF current_setting('lcs.allow_canonical_write', TRUE) != 'on' THEN
        RAISE EXCEPTION 'lcs.lcs_canonical may only be updated through LCS functions. Direct writes are blocked.';
    END IF;
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lcs_canonical_guard
    BEFORE INSERT OR UPDATE ON lcs.lcs_canonical
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_lcs_canonical_guard();

-- ============================================================================
-- 2. lcs.lcs_errors — Cantonal error capture
-- ============================================================================

CREATE TABLE lcs.lcs_errors (
    error_id        UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    error_stage     TEXT        NOT NULL,
    error_type      TEXT        NOT NULL,
    retry_strategy  TEXT        NOT NULL DEFAULT 'manual_fix',
    sovereign_id    UUID        REFERENCES cl.company_identity(company_unique_id),
    cid             UUID        REFERENCES lcs.cid_intake(cid),
    sid             UUID        REFERENCES lcs.sid_registry(sid),
    mid             UUID        REFERENCES lcs.mid_ledger(mid),
    error_payload   JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at     TIMESTAMPTZ
);

-- CHECK constraints (matching repo error-table pattern)
ALTER TABLE lcs.lcs_errors ADD CONSTRAINT chk_lcs_errors_type
    CHECK (error_type IN ('validation', 'state_violation', 'expired', 'conflict', 'external_fail'));

ALTER TABLE lcs.lcs_errors ADD CONSTRAINT chk_lcs_errors_stage
    CHECK (error_stage IN ('cid_processing', 'sid_creation', 'mid_minting', 'dispatch_finalization', 'canonical_update'));

ALTER TABLE lcs.lcs_errors ADD CONSTRAINT chk_lcs_errors_retry
    CHECK (retry_strategy IN ('manual_fix', 'auto_retry', 'discard'));

CREATE INDEX idx_lcs_errors_sovereign  ON lcs.lcs_errors(sovereign_id);
CREATE INDEX idx_lcs_errors_unresolved ON lcs.lcs_errors(created_at) WHERE resolved_at IS NULL;

-- Append-only enforcement: only resolved_at may be updated
CREATE OR REPLACE FUNCTION lcs.fn_lcs_errors_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.error_id       != OLD.error_id       OR
       NEW.error_stage    != OLD.error_stage     OR
       NEW.error_type     != OLD.error_type      OR
       NEW.retry_strategy != OLD.retry_strategy  OR
       NEW.sovereign_id   IS DISTINCT FROM OLD.sovereign_id OR
       NEW.cid            IS DISTINCT FROM OLD.cid  OR
       NEW.sid            IS DISTINCT FROM OLD.sid  OR
       NEW.mid            IS DISTINCT FROM OLD.mid  OR
       NEW.error_payload  != OLD.error_payload   OR
       NEW.created_at     != OLD.created_at      THEN
        RAISE EXCEPTION 'lcs.lcs_errors is append-only. Only resolved_at may be updated. error_id=%', OLD.error_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lcs_errors_guard
    BEFORE UPDATE ON lcs.lcs_errors
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_lcs_errors_guard();

CREATE OR REPLACE FUNCTION lcs.fn_lcs_errors_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.lcs_errors rows cannot be deleted. error_id=%', OLD.error_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_lcs_errors_no_delete
    BEFORE DELETE ON lcs.lcs_errors
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_lcs_errors_no_delete();

-- ============================================================================
-- 3. lcs.lcs_intake — Doctrinal INTAKE view over cid_intake
-- ============================================================================

CREATE VIEW lcs.lcs_intake AS
SELECT
    cid,
    outreach_id,
    sovereign_id,
    movement_type_code,
    status,
    lifecycle_stage,
    source_hub,
    source_table,
    source_record_id,
    evidence,
    detected_at,
    processed_at,
    expires_at,
    created_at
FROM lcs.cid_intake;

COMMENT ON VIEW lcs.lcs_intake IS
    'Doctrinal INTAKE surface — view over lcs.cid_intake. Preserves underlying append-only enforcement.';

-- ============================================================================
-- 4. fn_process_cid — Updated: canonical UPSERT + error logging
-- ============================================================================
-- Changes from v0:
--   - Validation failures log to lcs.lcs_errors and return NULL (instead of RAISE)
--   - Execution phase wrapped in BEGIN/EXCEPTION for unexpected error capture
--   - Step 6 added: UPSERT lcs.lcs_canonical with current state
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_process_cid(p_cid UUID)
RETURNS UUID AS $$
DECLARE
    v_cid_row       lcs.cid_intake%ROWTYPE;
    v_sid           UUID;
    v_mid           UUID;
BEGIN
    -- ----------------------------------------------------------------
    -- Phase 1: Validate (no state changes except EXPIRED marking)
    -- ----------------------------------------------------------------

    -- 1. Lock and validate CID
    SELECT * INTO v_cid_row
    FROM lcs.cid_intake
    WHERE cid = p_cid
    FOR UPDATE;

    IF NOT FOUND THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, error_payload)
        VALUES ('cid_processing', 'validation', 'manual_fix',
                jsonb_build_object('reason', 'CID not found', 'cid', p_cid::text));
        RETURN NULL;
    END IF;

    IF v_cid_row.status != 'PENDING' THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, cid, error_payload)
        VALUES ('cid_processing', 'state_violation', 'discard', v_cid_row.sovereign_id, p_cid,
                jsonb_build_object('reason', format('CID not PENDING (status: %s)', v_cid_row.status)));
        RETURN NULL;
    END IF;

    -- Check TTL
    IF v_cid_row.expires_at IS NOT NULL AND v_cid_row.expires_at < NOW() THEN
        UPDATE lcs.cid_intake SET status = 'EXPIRED', processed_at = NOW()
        WHERE cid = p_cid;
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, cid, error_payload)
        VALUES ('cid_processing', 'expired', 'discard', v_cid_row.sovereign_id, p_cid,
                jsonb_build_object('reason', 'CID expired', 'expires_at', v_cid_row.expires_at::text));
        RETURN NULL;
    END IF;

    -- ----------------------------------------------------------------
    -- Phase 2: Execute (wrapped for unexpected error capture)
    -- ----------------------------------------------------------------
    BEGIN
        -- 2. Get-or-create SID
        SELECT sid INTO v_sid
        FROM lcs.sid_registry
        WHERE outreach_id = v_cid_row.outreach_id;

        IF NOT FOUND THEN
            INSERT INTO lcs.sid_registry (outreach_id, sovereign_id, lifecycle_stage, last_cid, last_movement_at)
            VALUES (v_cid_row.outreach_id, v_cid_row.sovereign_id, 'QUALIFIED', p_cid, v_cid_row.detected_at)
            RETURNING sid INTO v_sid;
        ELSE
            UPDATE lcs.sid_registry
            SET lifecycle_stage  = 'QUALIFIED',
                last_cid         = p_cid,
                last_movement_at = v_cid_row.detected_at,
                updated_at       = NOW()
            WHERE sid = v_sid;
        END IF;

        -- 3. Mint MID
        INSERT INTO lcs.mid_ledger (cid, sid, outreach_id, sovereign_id, dispatch_state, movement_type_code)
        VALUES (p_cid, v_sid, v_cid_row.outreach_id, v_cid_row.sovereign_id, 'MINTED', v_cid_row.movement_type_code)
        RETURNING mid INTO v_mid;

        -- 4. Update CID status
        UPDATE lcs.cid_intake
        SET status = 'ACCEPTED', processed_at = NOW(), lifecycle_stage = 'QUALIFIED'
        WHERE cid = p_cid;

        -- 5. Advance SID
        UPDATE lcs.sid_registry
        SET mid_count       = mid_count + 1,
            lifecycle_stage = 'ENGAGED',
            updated_at      = NOW()
        WHERE sid = v_sid;

        -- 6. UPSERT canonical (guard requires session var)
        PERFORM set_config('lcs.allow_canonical_write', 'on', TRUE);

        INSERT INTO lcs.lcs_canonical
            (sovereign_id, current_lifecycle_stage, current_sid, current_mid, current_dispatch_state, last_cid)
        VALUES
            (v_cid_row.sovereign_id, 'ENGAGED', v_sid, v_mid, 'MINTED', p_cid)
        ON CONFLICT (sovereign_id) DO UPDATE
        SET current_lifecycle_stage = 'ENGAGED',
            current_sid             = EXCLUDED.current_sid,
            current_mid             = EXCLUDED.current_mid,
            current_dispatch_state  = 'MINTED',
            last_cid                = EXCLUDED.last_cid;

        RETURN v_mid;

    EXCEPTION WHEN OTHERS THEN
        -- Unexpected error: log and return NULL (inner block rolled back via savepoint)
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, cid, error_payload)
        VALUES ('cid_processing', 'external_fail', 'auto_retry', v_cid_row.sovereign_id, p_cid,
                jsonb_build_object('reason', SQLERRM, 'sqlstate', SQLSTATE));
        RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. fn_finalize_dispatch — Updated: canonical update + error logging
-- ============================================================================
-- Changes from v0:
--   - Validation failures log to lcs.lcs_errors and return (instead of RAISE)
--   - Execution phase wrapped in BEGIN/EXCEPTION for unexpected error capture
--   - Step 5 added: update lcs.lcs_canonical dispatch state
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_finalize_dispatch(p_mid UUID, p_result JSONB)
RETURNS VOID AS $$
DECLARE
    v_outcome   TEXT;
    v_state     lcs.dispatch_state;
    v_mid_row   lcs.mid_ledger%ROWTYPE;
BEGIN
    -- ----------------------------------------------------------------
    -- Phase 1: Validate
    -- ----------------------------------------------------------------

    -- 1. Lock and validate MID
    SELECT * INTO v_mid_row
    FROM lcs.mid_ledger
    WHERE mid = p_mid
    FOR UPDATE;

    IF NOT FOUND THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, error_payload)
        VALUES ('dispatch_finalization', 'validation', 'manual_fix',
                jsonb_build_object('reason', 'MID not found', 'mid', p_mid::text));
        RETURN;
    END IF;

    -- 2. Extract and validate outcome
    v_outcome := p_result ->> 'outcome';
    IF v_outcome IS NULL THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy,
                                     mid, sovereign_id, cid, sid, error_payload)
        VALUES ('dispatch_finalization', 'validation', 'manual_fix',
                p_mid, v_mid_row.sovereign_id, v_mid_row.cid, v_mid_row.sid,
                jsonb_build_object('reason', 'missing outcome key', 'input', p_result));
        RETURN;
    END IF;

    -- 3. Map outcome to dispatch_state
    v_state := CASE v_outcome
        WHEN 'DELIVERED' THEN 'DELIVERED'::lcs.dispatch_state
        WHEN 'BOUNCED'   THEN 'BOUNCED'::lcs.dispatch_state
        WHEN 'FAILED'    THEN 'FAILED'::lcs.dispatch_state
        ELSE NULL
    END;

    IF v_state IS NULL THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy,
                                     mid, sovereign_id, cid, sid, error_payload)
        VALUES ('dispatch_finalization', 'validation', 'manual_fix',
                p_mid, v_mid_row.sovereign_id, v_mid_row.cid, v_mid_row.sid,
                jsonb_build_object('reason', format('invalid outcome: %s', v_outcome), 'input', p_result));
        RETURN;
    END IF;

    -- ----------------------------------------------------------------
    -- Phase 2: Execute (wrapped for unexpected error capture)
    -- ----------------------------------------------------------------
    BEGIN
        -- 4. Update MID ledger (triggers enforce forward-only + column immutability)
        UPDATE lcs.mid_ledger
        SET dispatch_state  = v_state,
            dispatch_result = p_result,
            finalized_at    = NOW()
        WHERE mid = p_mid;

        -- 5. Update canonical dispatch state
        PERFORM set_config('lcs.allow_canonical_write', 'on', TRUE);

        UPDATE lcs.lcs_canonical
        SET current_dispatch_state = v_state
        WHERE sovereign_id = v_mid_row.sovereign_id;

    EXCEPTION WHEN OTHERS THEN
        -- Unexpected error (e.g. FSM violation on already-finalized MID)
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy,
                                     mid, sovereign_id, cid, sid, error_payload)
        VALUES ('dispatch_finalization', 'external_fail', 'manual_fix',
                p_mid, v_mid_row.sovereign_id, v_mid_row.cid, v_mid_row.sid,
                jsonb_build_object('reason', SQLERRM, 'sqlstate', SQLSTATE, 'input', p_result));
        RETURN;
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.lcs_canonical IS
    'CTB CANONICAL — Single authoritative row per company in LCS. Updated exclusively by fn_process_cid and fn_finalize_dispatch.';
COMMENT ON TABLE lcs.lcs_errors IS
    'CTB ERROR — Cantonal error capture for LCS function failure paths. Append-only except resolved_at.';
COMMENT ON FUNCTION lcs.fn_process_cid(UUID) IS
    'v1: Process PENDING CID → validate, get-or-create SID, mint MID, UPSERT canonical. Logs failures to lcs_errors, returns NULL on error.';
COMMENT ON FUNCTION lcs.fn_finalize_dispatch(UUID, JSONB) IS
    'v1: Finalize MID with terminal outcome → update mid_ledger + canonical dispatch state. Logs failures to lcs_errors.';

COMMIT;
