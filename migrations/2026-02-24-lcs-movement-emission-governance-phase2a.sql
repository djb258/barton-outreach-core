-- ============================================================================
-- LCS Movement Emission Governance — Phase 2A
-- ============================================================================
-- WORK_PACKET: WP_20260224T0730_LCS_MOVEMENT_EMISSION_GOVERNANCE_PHASE2A
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:     lcs.movement_emission_intake  (staging, append-only)
--   Function:  lcs.fn_emit_movement(...)     (sub-hub entry point)
--   Function:  lcs.fn_process_emissions(int) (batch promotion to CID)
--   Role:      lcs_emitter                   (EXECUTE-only access)
--
-- Extends:
--   Table:     lcs.movement_type_registry    (6 governance columns)
--   Constraint: lcs.lcs_errors               (2 new error_stage values)
--
-- Preserves all v0/v1 enforcement. No dropped view references.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 0. CTB PRE-REGISTRATION
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('lcs', 'movement_emission_intake', 'STAGING', FALSE, 'lcs_phase2a', 'Movement emission staging — append-only after processing')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 1. EXTEND movement_type_registry — governance columns
-- ============================================================================

ALTER TABLE lcs.movement_type_registry
    ADD COLUMN IF NOT EXISTS allowed_sources        TEXT[]   NOT NULL DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS payload_schema          JSONB,
    ADD COLUMN IF NOT EXISTS requires_sovereign      BOOLEAN  NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS requires_outreach       BOOLEAN  NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS default_retry_strategy  TEXT     NOT NULL DEFAULT 'manual_fix',
    ADD COLUMN IF NOT EXISTS ttl_days                INTEGER;

-- Seed allowed_sources for existing movement types
UPDATE lcs.movement_type_registry SET allowed_sources = ARRAY['people-intelligence']
WHERE movement_type_code IN ('EXECUTIVE_HIRE', 'EXECUTIVE_DEPARTURE', 'TITLE_CHANGE')
  AND allowed_sources = '{}';

UPDATE lcs.movement_type_registry SET allowed_sources = ARRAY['dol-filings']
WHERE movement_type_code IN ('BROKER_CHANGE', 'CARRIER_CHANGE', 'PLAN_COST_SPIKE', 'RENEWAL_APPROACHING')
  AND allowed_sources = '{}';

UPDATE lcs.movement_type_registry SET allowed_sources = ARRAY['blog-content']
WHERE movement_type_code IN ('FUNDING_EVENT', 'ACQUISITION', 'LEADERSHIP_ANNOUNCE')
  AND allowed_sources = '{}';

-- ============================================================================
-- 2. EXPAND lcs_errors CHECK constraint — add emission stages
-- ============================================================================

ALTER TABLE lcs.lcs_errors DROP CONSTRAINT IF EXISTS chk_lcs_errors_stage;
ALTER TABLE lcs.lcs_errors ADD CONSTRAINT chk_lcs_errors_stage
    CHECK (error_stage IN (
        'cid_processing', 'sid_creation', 'mid_minting',
        'dispatch_finalization', 'canonical_update',
        'emission_validation', 'emission_processing'
    ));

-- ============================================================================
-- 3. CREATE movement_emission_intake — staging table
-- ============================================================================

CREATE TABLE lcs.movement_emission_intake (
    emission_id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_hub          TEXT        NOT NULL,
    movement_type_code  TEXT        NOT NULL
                                    REFERENCES lcs.movement_type_registry(movement_type_code),
    outreach_id         UUID,
    sovereign_id        UUID,
    evidence            JSONB       NOT NULL DEFAULT '{}',
    dedupe_key          TEXT        NOT NULL UNIQUE,
    status              TEXT        NOT NULL DEFAULT 'STAGED',
    promoted_cid        UUID        REFERENCES lcs.cid_intake(cid),
    error_id            UUID        REFERENCES lcs.lcs_errors(error_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at        TIMESTAMPTZ
);

ALTER TABLE lcs.movement_emission_intake ADD CONSTRAINT chk_emission_status
    CHECK (status IN ('STAGED', 'PROMOTED', 'REJECTED', 'ERROR'));

CREATE INDEX idx_emission_intake_staged   ON lcs.movement_emission_intake(created_at) WHERE status = 'STAGED';
CREATE INDEX idx_emission_intake_dedupe   ON lcs.movement_emission_intake(dedupe_key);
CREATE INDEX idx_emission_intake_outreach ON lcs.movement_emission_intake(outreach_id) WHERE outreach_id IS NOT NULL;
CREATE INDEX idx_emission_intake_sovereign ON lcs.movement_emission_intake(sovereign_id) WHERE sovereign_id IS NOT NULL;

-- Append-only after status leaves STAGED (same pattern as cid_intake)
CREATE OR REPLACE FUNCTION lcs.fn_emission_intake_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'lcs.movement_emission_intake is append-only after processing. emission_id=% status=%',
        OLD.emission_id, OLD.status;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_emission_intake_no_update
    BEFORE UPDATE ON lcs.movement_emission_intake
    FOR EACH ROW
    WHEN (OLD.status != 'STAGED')
    EXECUTE FUNCTION lcs.fn_emission_intake_immutable();

CREATE TRIGGER trg_emission_intake_no_delete
    BEFORE DELETE ON lcs.movement_emission_intake
    FOR EACH ROW
    EXECUTE FUNCTION lcs.fn_emission_intake_immutable();

-- ============================================================================
-- 4. fn_emit_movement — Sub-hub entry point
-- ============================================================================
-- Sub-hubs call ONLY this function. No direct table writes.
-- Validates source, movement_type, required fields, payload schema.
-- Computes deterministic dedupe_key. Inserts idempotently.
-- Returns emission_id (or existing emission_id on dedupe hit).
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_emit_movement(
    p_source_hub        TEXT,
    p_movement_type     TEXT,
    p_outreach_id       UUID        DEFAULT NULL,
    p_sovereign_id      UUID        DEFAULT NULL,
    p_evidence          JSONB       DEFAULT '{}'
)
RETURNS UUID AS $$
DECLARE
    v_registry      lcs.movement_type_registry%ROWTYPE;
    v_dedupe_key    TEXT;
    v_emission_id   UUID;
    v_key           TEXT;
BEGIN
    -- 1. Validate movement_type_code exists
    SELECT * INTO v_registry
    FROM lcs.movement_type_registry
    WHERE movement_type_code = p_movement_type;

    IF NOT FOUND THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
        VALUES ('emission_validation', 'validation', 'manual_fix', p_sovereign_id,
                jsonb_build_object('reason', format('unknown movement_type_code: %s', p_movement_type),
                                   'source_hub', p_source_hub));
        RETURN NULL;
    END IF;

    -- 2. Validate movement type is active
    IF NOT v_registry.is_active THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
        VALUES ('emission_validation', 'validation', 'manual_fix', p_sovereign_id,
                jsonb_build_object('reason', format('movement_type_code %s is inactive', p_movement_type),
                                   'source_hub', p_source_hub));
        RETURN NULL;
    END IF;

    -- 3. Validate source is allowed for this movement type
    IF array_length(v_registry.allowed_sources, 1) > 0
       AND NOT (p_source_hub = ANY(v_registry.allowed_sources)) THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
        VALUES ('emission_validation', 'validation', 'manual_fix', p_sovereign_id,
                jsonb_build_object('reason', format('source %s not in allowed_sources for %s', p_source_hub, p_movement_type),
                                   'allowed', to_jsonb(v_registry.allowed_sources),
                                   'source_hub', p_source_hub));
        RETURN NULL;
    END IF;

    -- 4. Validate required fields
    IF v_registry.requires_sovereign AND p_sovereign_id IS NULL THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, error_payload)
        VALUES ('emission_validation', 'validation', 'manual_fix',
                jsonb_build_object('reason', format('%s requires sovereign_id', p_movement_type),
                                   'source_hub', p_source_hub));
        RETURN NULL;
    END IF;

    IF v_registry.requires_outreach AND p_outreach_id IS NULL THEN
        INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
        VALUES ('emission_validation', 'validation', 'manual_fix', p_sovereign_id,
                jsonb_build_object('reason', format('%s requires outreach_id', p_movement_type),
                                   'source_hub', p_source_hub));
        RETURN NULL;
    END IF;

    -- 5. Enforce payload schema (v1 skeleton: check required_keys if defined)
    IF v_registry.payload_schema IS NOT NULL
       AND v_registry.payload_schema ? 'required_keys' THEN
        FOR v_key IN SELECT jsonb_array_elements_text(v_registry.payload_schema -> 'required_keys')
        LOOP
            IF NOT (p_evidence ? v_key) THEN
                INSERT INTO lcs.lcs_errors (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
                VALUES ('emission_validation', 'validation', 'manual_fix', p_sovereign_id,
                        jsonb_build_object('reason', format('evidence missing required key: %s', v_key),
                                           'source_hub', p_source_hub,
                                           'movement_type', p_movement_type));
                RETURN NULL;
            END IF;
        END LOOP;
    END IF;

    -- 6. Compute deterministic dedupe_key
    v_dedupe_key := md5(
        p_source_hub || '::' ||
        p_movement_type || '::' ||
        COALESCE(p_outreach_id::text, 'NULL') || '::' ||
        COALESCE(p_sovereign_id::text, 'NULL') || '::' ||
        md5(COALESCE(p_evidence::text, '{}'))
    );

    -- 7. Insert idempotently
    INSERT INTO lcs.movement_emission_intake
        (source_hub, movement_type_code, outreach_id, sovereign_id, evidence, dedupe_key)
    VALUES
        (p_source_hub, p_movement_type, p_outreach_id, p_sovereign_id, p_evidence, v_dedupe_key)
    ON CONFLICT (dedupe_key) DO NOTHING
    RETURNING emission_id INTO v_emission_id;

    -- Dedupe hit: return existing emission_id
    IF v_emission_id IS NULL THEN
        SELECT emission_id INTO v_emission_id
        FROM lcs.movement_emission_intake
        WHERE dedupe_key = v_dedupe_key;
    END IF;

    RETURN v_emission_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 5. fn_process_emissions — Batch promotion to CID intake
-- ============================================================================
-- Processes STAGED emissions: validates FK targets, promotes to cid_intake,
-- writes deterministic errors, marks status transitions.
-- Returns result set showing what happened to each emission.
-- ============================================================================

CREATE OR REPLACE FUNCTION lcs.fn_process_emissions(p_batch_limit INTEGER DEFAULT 100)
RETURNS TABLE(
    emission_id     UUID,
    result_status   TEXT,
    promoted_cid    UUID,
    result_error_id UUID
) AS $$
DECLARE
    v_emission      lcs.movement_emission_intake%ROWTYPE;
    v_cid           UUID;
    v_error_id      UUID;
BEGIN
    FOR v_emission IN
        SELECT *
        FROM lcs.movement_emission_intake mei
        WHERE mei.status = 'STAGED'
        ORDER BY mei.created_at
        LIMIT p_batch_limit
        FOR UPDATE SKIP LOCKED
    LOOP
        BEGIN
            -- Validate outreach_id FK if present
            IF v_emission.outreach_id IS NOT NULL THEN
                PERFORM 1 FROM outreach.outreach WHERE outreach.outreach_id = v_emission.outreach_id;
                IF NOT FOUND THEN
                    INSERT INTO lcs.lcs_errors
                        (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
                    VALUES
                        ('emission_processing', 'validation', 'manual_fix', v_emission.sovereign_id,
                         jsonb_build_object('reason', 'outreach_id not found in outreach.outreach',
                                            'outreach_id', v_emission.outreach_id::text,
                                            'emission_id', v_emission.emission_id::text))
                    RETURNING lcs.lcs_errors.error_id INTO v_error_id;

                    UPDATE lcs.movement_emission_intake
                    SET status = 'REJECTED', error_id = v_error_id, processed_at = NOW()
                    WHERE lcs.movement_emission_intake.emission_id = v_emission.emission_id;

                    emission_id     := v_emission.emission_id;
                    result_status   := 'REJECTED';
                    promoted_cid    := NULL;
                    result_error_id := v_error_id;
                    RETURN NEXT;
                    CONTINUE;
                END IF;
            END IF;

            -- Validate sovereign_id FK if present
            IF v_emission.sovereign_id IS NOT NULL THEN
                PERFORM 1 FROM cl.company_identity WHERE company_unique_id = v_emission.sovereign_id;
                IF NOT FOUND THEN
                    INSERT INTO lcs.lcs_errors
                        (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
                    VALUES
                        ('emission_processing', 'validation', 'manual_fix', NULL,
                         jsonb_build_object('reason', 'sovereign_id not found in cl.company_identity',
                                            'sovereign_id', v_emission.sovereign_id::text,
                                            'emission_id', v_emission.emission_id::text))
                    RETURNING lcs.lcs_errors.error_id INTO v_error_id;

                    UPDATE lcs.movement_emission_intake
                    SET status = 'REJECTED', error_id = v_error_id, processed_at = NOW()
                    WHERE lcs.movement_emission_intake.emission_id = v_emission.emission_id;

                    emission_id     := v_emission.emission_id;
                    result_status   := 'REJECTED';
                    promoted_cid    := NULL;
                    result_error_id := v_error_id;
                    RETURN NEXT;
                    CONTINUE;
                END IF;
            END IF;

            -- Promote to CID intake
            INSERT INTO lcs.cid_intake
                (outreach_id, sovereign_id, movement_type_code, status,
                 detected_at, source_hub, source_record_id, evidence)
            VALUES
                (v_emission.outreach_id, v_emission.sovereign_id, v_emission.movement_type_code,
                 'PENDING', v_emission.created_at, v_emission.source_hub,
                 v_emission.emission_id::text, v_emission.evidence)
            RETURNING cid INTO v_cid;

            -- Mark as promoted
            UPDATE lcs.movement_emission_intake
            SET status = 'PROMOTED', promoted_cid = v_cid, processed_at = NOW()
            WHERE lcs.movement_emission_intake.emission_id = v_emission.emission_id;

            emission_id     := v_emission.emission_id;
            result_status   := 'PROMOTED';
            promoted_cid    := v_cid;
            result_error_id := NULL;
            RETURN NEXT;

        EXCEPTION WHEN OTHERS THEN
            -- Unexpected error: log and mark ERROR
            INSERT INTO lcs.lcs_errors
                (error_stage, error_type, retry_strategy, sovereign_id, error_payload)
            VALUES
                ('emission_processing', 'external_fail', 'auto_retry', v_emission.sovereign_id,
                 jsonb_build_object('reason', SQLERRM, 'sqlstate', SQLSTATE,
                                    'emission_id', v_emission.emission_id::text))
            RETURNING lcs.lcs_errors.error_id INTO v_error_id;

            UPDATE lcs.movement_emission_intake
            SET status = 'ERROR', error_id = v_error_id, processed_at = NOW()
            WHERE lcs.movement_emission_intake.emission_id = v_emission.emission_id;

            emission_id     := v_emission.emission_id;
            result_status   := 'ERROR';
            promoted_cid    := NULL;
            result_error_id := v_error_id;
            RETURN NEXT;
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 6. PERMISSION LOCKING — EXECUTE-only role for sub-hub callers
-- ============================================================================

DO $$ BEGIN
    CREATE ROLE lcs_emitter NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Sub-hubs may only call the emission function
GRANT EXECUTE ON FUNCTION lcs.fn_emit_movement(TEXT, TEXT, UUID, UUID, JSONB) TO lcs_emitter;

-- No direct table access for sub-hub callers
REVOKE ALL ON lcs.movement_emission_intake FROM lcs_emitter;
REVOKE ALL ON lcs.cid_intake FROM lcs_emitter;
REVOKE ALL ON lcs.lcs_errors FROM lcs_emitter;

-- ============================================================================
-- 7. COMMENTS
-- ============================================================================

COMMENT ON TABLE lcs.movement_emission_intake IS
    'STAGING — Sub-hub movement emissions. Append-only after processing. Promoted to cid_intake via fn_process_emissions.';
COMMENT ON FUNCTION lcs.fn_emit_movement(TEXT, TEXT, UUID, UUID, JSONB) IS
    'Sub-hub entry point for movement emission. Validates source, type, required fields, payload schema. Inserts idempotently via dedupe_key.';
COMMENT ON FUNCTION lcs.fn_process_emissions(INTEGER) IS
    'Batch processor: promotes STAGED emissions to cid_intake, writes errors to lcs_errors, marks status transitions.';

COMMIT;
