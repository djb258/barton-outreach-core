-- ============================================================================
-- SRC 2 — Outreach Identity Resolution Governor
-- ============================================================================
-- WORK_PACKET: WP_20260224T0740_SRC2_OUTREACH_IDENTITY_RESOLUTION_GOVERNOR
-- Doctrine:    2.8.0
-- Date:        2026-02-24
--
-- Creates:
--   Table:     outreach.identity_resolution_errors (append-only ERROR)
--   Function:  outreach.fn_resolve_identity(text, text, text, jsonb) → jsonb
--   Role:      identity_resolver (EXECUTE-only)
--
-- Resolution paths: outreach_id, sovereign_id, domain, ein.
-- Hard-fail on ambiguity, missing anchor, invalid input.
-- Errors log to outreach.identity_resolution_errors, NOT lcs.
-- ============================================================================

BEGIN;

-- ============================================================================
-- 0. CTB PRE-REGISTRATION
-- ============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, is_frozen, registered_by, notes)
VALUES ('outreach', 'identity_resolution_errors', 'ERROR', FALSE, 'src2_identity_governor', 'Identity resolution error capture — append-only')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ============================================================================
-- 1. outreach.identity_resolution_errors — ERROR table
-- ============================================================================

CREATE TABLE outreach.identity_resolution_errors (
    error_id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_schema       TEXT        NOT NULL,
    source_table        TEXT        NOT NULL,
    source_row_pk       TEXT        NOT NULL,
    resolution_stage    TEXT        NOT NULL,
    error_type          TEXT        NOT NULL,
    error_payload       JSONB       NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ
);

ALTER TABLE outreach.identity_resolution_errors ADD CONSTRAINT chk_ire_stage
    CHECK (resolution_stage IN ('input_validation', 'outreach_lookup', 'sovereign_lookup', 'domain_lookup', 'ein_lookup', 'cross_validation'));

ALTER TABLE outreach.identity_resolution_errors ADD CONSTRAINT chk_ire_type
    CHECK (error_type IN ('not_found', 'ambiguity', 'missing_anchor', 'invalid_input'));

CREATE INDEX idx_ire_unresolved ON outreach.identity_resolution_errors(created_at) WHERE resolved_at IS NULL;
CREATE INDEX idx_ire_source     ON outreach.identity_resolution_errors(source_schema, source_table);

-- Append-only: only resolved_at may be updated
CREATE OR REPLACE FUNCTION outreach.fn_ire_guard()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.error_id         != OLD.error_id         OR
       NEW.source_schema    != OLD.source_schema    OR
       NEW.source_table     != OLD.source_table     OR
       NEW.source_row_pk    != OLD.source_row_pk    OR
       NEW.resolution_stage != OLD.resolution_stage OR
       NEW.error_type       != OLD.error_type       OR
       NEW.error_payload    != OLD.error_payload    OR
       NEW.created_at       != OLD.created_at       THEN
        RAISE EXCEPTION 'outreach.identity_resolution_errors is append-only. Only resolved_at may be updated. error_id=%', OLD.error_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ire_guard
    BEFORE UPDATE ON outreach.identity_resolution_errors
    FOR EACH ROW
    EXECUTE FUNCTION outreach.fn_ire_guard();

CREATE OR REPLACE FUNCTION outreach.fn_ire_no_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'outreach.identity_resolution_errors rows cannot be deleted. error_id=%', OLD.error_id;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ire_no_delete
    BEFORE DELETE ON outreach.identity_resolution_errors
    FOR EACH ROW
    EXECUTE FUNCTION outreach.fn_ire_no_delete();

-- ============================================================================
-- 2. outreach.fn_resolve_identity — Deterministic identity resolver
-- ============================================================================
-- Resolution priority: outreach_id > sovereign_id > domain > ein
-- Hard-fails: NULL return + error row on any failure path.
-- Returns: {"outreach_id": "<uuid>", "sovereign_id": "<uuid>"}
-- ============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_resolve_identity(
    p_source_schema TEXT,
    p_source_table  TEXT,
    p_source_row_pk TEXT,
    p_identifiers   JSONB
)
RETURNS JSONB AS $$
DECLARE
    v_outreach_id   UUID;
    v_sovereign_id  UUID;
    v_count         INTEGER;
    v_provided_sid  UUID;
BEGIN
    -- ----------------------------------------------------------------
    -- Path 1: outreach_id provided (highest priority)
    -- ----------------------------------------------------------------
    IF p_identifiers ? 'outreach_id' THEN
        BEGIN
            v_outreach_id := (p_identifiers ->> 'outreach_id')::UUID;
        EXCEPTION WHEN OTHERS THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'input_validation', 'invalid_input',
                    jsonb_build_object('reason', 'outreach_id is not a valid UUID',
                                       'value', p_identifiers ->> 'outreach_id'));
            RETURN NULL;
        END;

        SELECT sovereign_id INTO v_sovereign_id
        FROM outreach.outreach WHERE outreach_id = v_outreach_id;

        IF NOT FOUND THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'outreach_lookup', 'not_found',
                    jsonb_build_object('reason', 'outreach_id not found in outreach.outreach',
                                       'outreach_id', v_outreach_id::text));
            RETURN NULL;
        END IF;

        -- Cross-validate sovereign_id if also provided
        IF p_identifiers ? 'sovereign_id' THEN
            BEGIN
                v_provided_sid := (p_identifiers ->> 'sovereign_id')::UUID;
            EXCEPTION WHEN OTHERS THEN
                v_provided_sid := NULL;
            END;
            IF v_provided_sid IS NOT NULL AND v_sovereign_id != v_provided_sid THEN
                INSERT INTO outreach.identity_resolution_errors
                    (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
                VALUES (p_source_schema, p_source_table, p_source_row_pk,
                        'cross_validation', 'ambiguity',
                        jsonb_build_object('reason', 'outreach_id resolves to different sovereign_id than provided',
                                           'outreach_id', v_outreach_id::text,
                                           'resolved_sovereign_id', v_sovereign_id::text,
                                           'provided_sovereign_id', v_provided_sid::text));
                RETURN NULL;
            END IF;
        END IF;

        RETURN jsonb_build_object('outreach_id', v_outreach_id, 'sovereign_id', v_sovereign_id);
    END IF;

    -- ----------------------------------------------------------------
    -- Path 2: sovereign_id provided
    -- ----------------------------------------------------------------
    IF p_identifiers ? 'sovereign_id' THEN
        BEGIN
            v_sovereign_id := (p_identifiers ->> 'sovereign_id')::UUID;
        EXCEPTION WHEN OTHERS THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'input_validation', 'invalid_input',
                    jsonb_build_object('reason', 'sovereign_id is not a valid UUID',
                                       'value', p_identifiers ->> 'sovereign_id'));
            RETURN NULL;
        END;

        -- Verify sovereign exists in CL
        PERFORM 1 FROM cl.company_identity WHERE company_unique_id = v_sovereign_id;
        IF NOT FOUND THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'sovereign_lookup', 'not_found',
                    jsonb_build_object('reason', 'sovereign_id not found in cl.company_identity',
                                       'sovereign_id', v_sovereign_id::text));
            RETURN NULL;
        END IF;

        -- Find outreach_id via spine
        SELECT outreach_id INTO v_outreach_id
        FROM outreach.outreach WHERE sovereign_id = v_sovereign_id;

        IF NOT FOUND THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'sovereign_lookup', 'missing_anchor',
                    jsonb_build_object('reason', 'sovereign_id exists in CL but has no outreach_id in spine',
                                       'sovereign_id', v_sovereign_id::text));
            RETURN NULL;
        END IF;

        RETURN jsonb_build_object('outreach_id', v_outreach_id, 'sovereign_id', v_sovereign_id);
    END IF;

    -- ----------------------------------------------------------------
    -- Path 3: domain provided
    -- ----------------------------------------------------------------
    IF p_identifiers ? 'domain' THEN
        SELECT count(*) INTO v_count
        FROM outreach.outreach WHERE domain = p_identifiers ->> 'domain';

        IF v_count = 0 THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'domain_lookup', 'not_found',
                    jsonb_build_object('reason', 'domain not found in outreach.outreach',
                                       'domain', p_identifiers ->> 'domain'));
            RETURN NULL;
        ELSIF v_count > 1 THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'domain_lookup', 'ambiguity',
                    jsonb_build_object('reason', format('domain resolves to %s records', v_count),
                                       'domain', p_identifiers ->> 'domain',
                                       'match_count', v_count));
            RETURN NULL;
        END IF;

        SELECT outreach_id, sovereign_id INTO v_outreach_id, v_sovereign_id
        FROM outreach.outreach WHERE domain = p_identifiers ->> 'domain';

        RETURN jsonb_build_object('outreach_id', v_outreach_id, 'sovereign_id', v_sovereign_id);
    END IF;

    -- ----------------------------------------------------------------
    -- Path 4: ein provided
    -- ----------------------------------------------------------------
    IF p_identifiers ? 'ein' THEN
        SELECT count(*) INTO v_count
        FROM outreach.outreach WHERE ein = p_identifiers ->> 'ein';

        IF v_count = 0 THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'ein_lookup', 'not_found',
                    jsonb_build_object('reason', 'EIN not found in outreach.outreach',
                                       'ein', p_identifiers ->> 'ein'));
            RETURN NULL;
        ELSIF v_count > 1 THEN
            INSERT INTO outreach.identity_resolution_errors
                (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
            VALUES (p_source_schema, p_source_table, p_source_row_pk,
                    'ein_lookup', 'ambiguity',
                    jsonb_build_object('reason', format('EIN resolves to %s records', v_count),
                                       'ein', p_identifiers ->> 'ein',
                                       'match_count', v_count));
            RETURN NULL;
        END IF;

        SELECT outreach_id, sovereign_id INTO v_outreach_id, v_sovereign_id
        FROM outreach.outreach WHERE ein = p_identifiers ->> 'ein';

        RETURN jsonb_build_object('outreach_id', v_outreach_id, 'sovereign_id', v_sovereign_id);
    END IF;

    -- ----------------------------------------------------------------
    -- No usable identifiers
    -- ----------------------------------------------------------------
    INSERT INTO outreach.identity_resolution_errors
        (source_schema, source_table, source_row_pk, resolution_stage, error_type, error_payload)
    VALUES (p_source_schema, p_source_table, p_source_row_pk,
            'input_validation', 'invalid_input',
            jsonb_build_object('reason', 'No usable identifier found',
                               'identifiers', p_identifiers,
                               'supported', '["outreach_id", "sovereign_id", "domain", "ein"]'));
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 3. PERMISSION LOCKING
-- ============================================================================

DO $$ BEGIN
    CREATE ROLE identity_resolver NOLOGIN;
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

GRANT EXECUTE ON FUNCTION outreach.fn_resolve_identity(TEXT, TEXT, TEXT, JSONB) TO identity_resolver;

REVOKE ALL ON outreach.outreach FROM identity_resolver;
REVOKE ALL ON cl.company_identity FROM identity_resolver;
REVOKE ALL ON outreach.identity_resolution_errors FROM identity_resolver;

-- ============================================================================
-- 4. COMMENTS
-- ============================================================================

COMMENT ON TABLE outreach.identity_resolution_errors IS
    'ERROR — Identity resolution failures. Append-only except resolved_at. Errors log here, not to lcs.lcs_errors.';
COMMENT ON FUNCTION outreach.fn_resolve_identity(TEXT, TEXT, TEXT, JSONB) IS
    'Deterministic identity resolver. Input: source context + identifiers JSONB. Output: {"outreach_id","sovereign_id"} or NULL on hard-fail. Resolution priority: outreach_id > sovereign_id > domain > ein.';

COMMIT;
