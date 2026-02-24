-- ============================================================================
-- Phase 2D — Promotion Determinism Guard (Idempotency + Replay Safety)
-- ============================================================================
-- WORK_PACKET: WP_20260224T0810_PHASE2D_PROMOTION_DETERMINISM_GUARD
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Adds:
--   Column:     lcs.cid_intake.emission_id UUID
--   Index:      uq_cid_intake_emission_id (partial unique WHERE emission_id IS NOT NULL)
--
-- Updates:
--   Function:   lcs.fn_promote_emission(uuid) — idempotent + replay-safe
--               - Already-PROMOTED emissions return clean
--               - Pre-check for existing CID before INSERT
--               - Conflict path resolves existing CID, marks PROMOTED, returns clean
--               - No RAISE on any path
--
-- Hard rules:
--   One emission → one CID
--   Replays are safe
--   Parallel workers cannot double-mint CIDs
--   Status transitions remain forward-only
--
-- Depends on: Phase 2A (table), SRC 3 (fn_promote_emission), SRC 4 (guard trigger)
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. ADD emission_id column to cid_intake
-- ============================================================================

ALTER TABLE lcs.cid_intake ADD COLUMN IF NOT EXISTS emission_id UUID;

-- Backfill from source_record_id for promotion-created CIDs (UUID format)
UPDATE lcs.cid_intake
SET emission_id = source_record_id::uuid
WHERE emission_id IS NULL
  AND source_record_id IS NOT NULL
  AND source_record_id ~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- ============================================================================
-- 2. UNIQUE INDEX — one emission → one CID
-- ============================================================================
-- Partial: allows NULLs for non-promotion CID rows (direct fn_process_cid path)

CREATE UNIQUE INDEX IF NOT EXISTS uq_cid_intake_emission_id
    ON lcs.cid_intake (emission_id) WHERE emission_id IS NOT NULL;

-- ============================================================================
-- 3. fn_promote_emission — Idempotent + replay-safe
-- ============================================================================
-- Replaces SRC 3 version. Adds:
--   - Already-PROMOTED check (return clean on replay)
--   - Pre-check for existing CID before INSERT (conflict safety)
--   - No RAISE on any path (preserved from SRC 3 correctness patch)
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_promote_emission(p_emission_id UUID)
RETURNS VOID AS $$
DECLARE
    v_emission      lcs.movement_emission_intake%ROWTYPE;
    v_cid           UUID;
    v_existing_cid  UUID;
    v_mid           UUID;
    v_error_id      UUID;
BEGIN
    -- 1. Lock and validate
    SELECT * INTO v_emission
    FROM lcs.movement_emission_intake
    WHERE emission_id = p_emission_id
    FOR UPDATE;

    IF NOT FOUND THEN
        INSERT INTO lcs.lcs_errors
            (error_stage, error_type, retry_strategy, error_payload)
        VALUES
            ('emission_processing', 'validation', 'manual_fix',
             jsonb_build_object('reason', 'emission_id not found',
                                'emission_id', p_emission_id::text));
        RETURN;
    END IF;

    -- 1b. Idempotent: already PROMOTED → return clean (replay safety)
    IF v_emission.status = 'PROMOTED' AND v_emission.promoted_cid IS NOT NULL THEN
        RETURN;
    END IF;

    IF v_emission.status != 'STAGED' THEN
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

    -- 3. Check for existing CID (replay/conflict safety)
    SELECT cid INTO v_existing_cid
    FROM lcs.cid_intake
    WHERE emission_id = p_emission_id;

    IF v_existing_cid IS NOT NULL THEN
        -- CID already minted for this emission — resolve and mark PROMOTED
        UPDATE lcs.movement_emission_intake
        SET status = 'PROMOTED', promoted_cid = v_existing_cid, processed_at = NOW()
        WHERE emission_id = p_emission_id;

        RETURN;
    END IF;

    -- 4. Mint CID in cid_intake (with emission_id for uniqueness)
    INSERT INTO lcs.cid_intake
        (outreach_id, sovereign_id, movement_type_code, status,
         detected_at, source_hub, source_record_id, evidence, emission_id)
    VALUES
        (v_emission.outreach_id, v_emission.sovereign_id, v_emission.movement_type_code,
         'PENDING', v_emission.created_at, v_emission.source_hub,
         p_emission_id::text, v_emission.evidence, p_emission_id)
    RETURNING cid INTO v_cid;

    -- 5. Process CID → SID → MID (full atomic flow)
    v_mid := lcs.fn_process_cid(v_cid);

    IF v_mid IS NULL THEN
        UPDATE lcs.movement_emission_intake
        SET status = 'ERROR', processed_at = NOW()
        WHERE emission_id = p_emission_id;

        RETURN;
    END IF;

    -- 6. Mark PROMOTED
    UPDATE lcs.movement_emission_intake
    SET status = 'PROMOTED', promoted_cid = v_cid, processed_at = NOW()
    WHERE emission_id = p_emission_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 4. COMMENTS
-- ============================================================================
-- Batch wrapper (fn_promote_emission_batch) is unchanged from SRC 3 —
-- already uses FOR UPDATE SKIP LOCKED and return-state logic.
-- Idempotency is handled entirely within fn_promote_emission.

COMMENT ON FUNCTION lcs.fn_promote_emission(UUID) IS
    'Idempotent single-row promotion: STAGED → CID → fn_process_cid → SID + MID → PROMOTED. Replay-safe via emission_id uniqueness check. One emission → one CID. Error paths return clean.';

COMMIT;
