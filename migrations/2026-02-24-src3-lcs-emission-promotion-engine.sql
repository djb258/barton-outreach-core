-- ============================================================================
-- SRC 3 — LCS Emission Promotion Engine
-- ============================================================================
-- WORK_PACKET: WP_20260224T0740_SRC3_LCS_EMISSION_PROMOTION_ENGINE
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Function:  lcs.fn_promote_emission(uuid)      — single-row atomic promotion
--   Function:  lcs.fn_promote_emission_batch(int)  — batch promotion, returns count
--
-- Atomic flow per emission:
--   Lock row → validate STAGED → INSERT cid_intake → fn_process_cid() →
--   update PROMOTED → return. On error: log + update status → return clean.
--
-- CORRECTNESS RULE: No RAISE EXCEPTION after error logging.
--   Error paths: INSERT lcs_errors → UPDATE emission status → RETURN.
--   Batch wrapper uses return-state logic, not exception control flow.
--
-- NOTE: WP references ingest_status/RECEIVED; existing schema uses
-- status/STAGED (from Phase 2A). Same semantic — adapted to live schema.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. fn_promote_emission — Single-row atomic promotion
-- ============================================================================
-- Locks emission row, validates STAGED, mints CID in cid_intake,
-- calls fn_process_cid() for full CID→SID→MID flow, marks PROMOTED.
-- On failure: logs to lcs_errors, updates emission status, returns clean.
-- No RAISE after state mutation — error state is never rolled back.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_promote_emission(p_emission_id UUID)
RETURNS VOID AS $$
DECLARE
    v_emission      lcs.movement_emission_intake%ROWTYPE;
    v_cid           UUID;
    v_mid           UUID;
    v_error_id      UUID;
BEGIN
    -- 1. Lock and validate
    SELECT * INTO v_emission
    FROM lcs.movement_emission_intake
    WHERE emission_id = p_emission_id
    FOR UPDATE;

    IF NOT FOUND THEN
        -- No row to update — log error and return clean
        INSERT INTO lcs.lcs_errors
            (error_stage, error_type, retry_strategy, error_payload)
        VALUES
            ('emission_processing', 'validation', 'manual_fix',
             jsonb_build_object('reason', 'emission_id not found',
                                'emission_id', p_emission_id::text));
        RETURN;
    END IF;

    IF v_emission.status != 'STAGED' THEN
        -- Wrong state — log error and return clean (do not alter existing status)
        INSERT INTO lcs.lcs_errors
            (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
        VALUES
            ('emission_processing', 'state_violation', 'discard', v_emission.sovereign_id,
             jsonb_build_object('reason', format('emission not STAGED (status: %s)', v_emission.status),
                                'emission_id', p_emission_id::text));
        RETURN;
    END IF;

    -- 2. Validate FK targets
    IF v_emission.outreach_id IS NOT NULL THEN
        PERFORM 1 FROM outreach.outreach WHERE outreach_id = v_emission.outreach_id;
        IF NOT FOUND THEN
            INSERT INTO lcs.lcs_errors
                (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
            VALUES
                ('emission_processing', 'validation', 'manual_fix', v_emission.sovereign_id,
                 jsonb_build_object('reason', 'outreach_id not found in outreach.outreach',
                                    'emission_id', p_emission_id::text,
                                    'outreach_id', v_emission.outreach_id::text))
            RETURNING error_id INTO v_error_id;

            UPDATE lcs.movement_emission_intake
            SET status = 'REJECTED', error_id = v_error_id, processed_at = NOW()
            WHERE emission_id = p_emission_id;

            RETURN;
        END IF;
    END IF;

    IF v_emission.sovereign_id IS NOT NULL THEN
        PERFORM 1 FROM cl.company_identity WHERE company_unique_id = v_emission.sovereign_id;
        IF NOT FOUND THEN
            INSERT INTO lcs.lcs_errors
                (error_stage, error_type, retry_strategy, error_payload)
            VALUES
                ('emission_processing', 'validation', 'manual_fix',
                 jsonb_build_object('reason', 'sovereign_id not found in cl.company_identity',
                                    'emission_id', p_emission_id::text,
                                    'sovereign_id', v_emission.sovereign_id::text))
            RETURNING error_id INTO v_error_id;

            UPDATE lcs.movement_emission_intake
            SET status = 'REJECTED', error_id = v_error_id, processed_at = NOW()
            WHERE emission_id = p_emission_id;

            RETURN;
        END IF;
    END IF;

    -- 3. Mint CID in cid_intake
    INSERT INTO lcs.cid_intake
        (outreach_id, sovereign_id, movement_type_code, status,
         detected_at, source_hub, source_record_id, evidence)
    VALUES
        (v_emission.outreach_id, v_emission.sovereign_id, v_emission.movement_type_code,
         'PENDING', v_emission.created_at, v_emission.source_hub,
         p_emission_id::text, v_emission.evidence)
    RETURNING cid INTO v_cid;

    -- 4. Process CID → SID → MID (full atomic flow)
    v_mid := lcs.fn_process_cid(v_cid);

    IF v_mid IS NULL THEN
        -- fn_process_cid logged its own error; mark emission as ERROR and return clean
        UPDATE lcs.movement_emission_intake
        SET status = 'ERROR', processed_at = NOW()
        WHERE emission_id = p_emission_id;

        RETURN;
    END IF;

    -- 5. Mark PROMOTED
    UPDATE lcs.movement_emission_intake
    SET status = 'PROMOTED', promoted_cid = v_cid, processed_at = NOW()
    WHERE emission_id = p_emission_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 2. fn_promote_emission_batch — Batch promotion with count
-- ============================================================================
-- Deterministic ordering by created_at. Calls fn_promote_emission per row.
-- No exception control flow — reads emission status after each call.
-- Returns count of successfully promoted emissions.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_promote_emission_batch(p_limit INTEGER DEFAULT 100)
RETURNS INTEGER AS $$
DECLARE
    v_emission_id   UUID;
    v_promoted      INTEGER := 0;
    v_status        TEXT;
BEGIN
    FOR v_emission_id IN
        SELECT emission_id
        FROM lcs.movement_emission_intake
        WHERE status = 'STAGED'
        ORDER BY created_at
        LIMIT p_limit
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Call promotion — returns clean on success or failure
        PERFORM lcs.fn_promote_emission(v_emission_id);

        -- Check result by reading emission status (return-state logic)
        SELECT status INTO v_status
        FROM lcs.movement_emission_intake
        WHERE emission_id = v_emission_id;

        IF v_status = 'PROMOTED' THEN
            v_promoted := v_promoted + 1;
        END IF;
    END LOOP;

    RETURN v_promoted;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. COMMENTS
-- ============================================================================

COMMENT ON FUNCTION lcs.fn_promote_emission(UUID) IS
    'Atomic single-row promotion: STAGED → CID → fn_process_cid → SID + MID → PROMOTED. Error paths log + update status + return clean. No RAISE after state mutation.';
COMMENT ON FUNCTION lcs.fn_promote_emission_batch(INTEGER) IS
    'Batch promotion engine. Deterministic ordering, return-state logic (no exception control flow), returns count of successfully promoted emissions.';

COMMIT;
