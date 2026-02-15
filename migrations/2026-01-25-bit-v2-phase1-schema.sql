-- ============================================================================
-- ██████╗  ██████╗     ███╗   ██╗ ██████╗ ████████╗    ███╗   ███╗ ██████╗ ██████╗ ██╗███████╗██╗   ██╗
-- ██╔══██╗██╔═══██╗    ████╗  ██║██╔═══██╗╚══██╔══╝    ████╗ ████║██╔═══██╗██╔══██╗██║██╔════╝╚██╗ ██╔╝
-- ██║  ██║██║   ██║    ██╔██╗ ██║██║   ██║   ██║       ██╔████╔██║██║   ██║██║  ██║██║█████╗   ╚████╔╝
-- ██║  ██║██║   ██║    ██║╚██╗██║██║   ██║   ██║       ██║╚██╔╝██║██║   ██║██║  ██║██║██╔══╝    ╚██╔╝
-- ██████╔╝╚██████╔╝    ██║ ╚████║╚██████╔╝   ██║       ██║ ╚═╝ ██║╚██████╔╝██████╔╝██║██║        ██║
-- ╚═════╝  ╚═════╝     ╚═╝  ╚═══╝ ╚═════╝    ╚═╝       ╚═╝     ╚═╝ ╚═════╝ ╚═════╝ ╚═╝╚═╝        ╚═╝
-- ============================================================================
--
-- FROZEN COMPONENTS — CHANGE REQUEST REQUIRED
--
-- The following are FROZEN per doctrine/DO_NOT_MODIFY_REGISTRY.md v1.1.0:
--   - bit.movement_events (structure)
--   - bit.proof_lines (structure)
--   - bit.phase_state (structure)
--   - bit.authorization_log (append-only)
--   - bit.get_current_band() (signature)
--   - bit.authorize_action() (signature)
--   - bit.validate_proof_for_send() (signature)
--
-- Modification requires: ADR amendment, impact analysis, rollback plan, sign-off
-- ============================================================================
-- BIT Authorization System v2.0 — Phase 1: Schema Additions
-- ============================================================================
-- Authority: ADR-017
-- Status: EXECUTED (2026-01-26)
-- Date: 2026-01-25
-- Reversibility: DROP tables (no functional impact on existing system)
--
-- This migration adds new tables for the BIT Authorization System without
-- modifying any existing behavior. Old scoring continues to work unchanged.
-- ============================================================================

-- ============================================================================
-- SECTION 0: SCHEMA CREATION
-- ============================================================================
-- Ensure required schemas exist before creating objects within them.
-- This is idempotent — safe to re-run.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS bit;
CREATE SCHEMA IF NOT EXISTS marketing;

-- ============================================================================
-- SECTION 1: ENUM TYPES
-- ============================================================================

-- Authorization band enum (maps to 0-5 integer bands)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'authorization_band' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'bit')) THEN
        CREATE TYPE bit.authorization_band AS ENUM (
            'SILENT',       -- Band 0: No action permitted
            'WATCH',        -- Band 1: Internal flag only
            'EXPLORATORY',  -- Band 2: Educational content only
            'TARGETED',     -- Band 3: Persona email, proof required
            'ENGAGED',      -- Band 4: Phone allowed, multi-source proof
            'DIRECT'        -- Band 5: Full contact, full-chain proof
        );
    END IF;
END
$$;

-- Pressure class enum (what organizational stress is detected)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'pressure_class' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'bit')) THEN
        CREATE TYPE bit.pressure_class AS ENUM (
            'COST_PRESSURE',                    -- Cost visibility gap, silent drift
            'VENDOR_DISSATISFACTION',           -- Broker churn, manual processes
            'DEADLINE_PROXIMITY',               -- Renewal as event, compressed decisions
            'ORGANIZATIONAL_RECONFIGURATION',   -- Knowledge loss, no continuity
            'OPERATIONAL_CHAOS'                 -- Filing irregularities, compliance gaps
        );
    END IF;
END
$$;

-- Movement domain enum (which intelligence hub detected the movement)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'movement_domain' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'bit')) THEN
        CREATE TYPE bit.movement_domain AS ENUM (
            'STRUCTURAL_PRESSURE',      -- DOL: Slow, highest trust, REQUIRED for authority
            'DECISION_SURFACE',         -- People: Medium velocity, who can act
            'NARRATIVE_VOLATILITY'      -- Blog: Fast, lowest trust, amplifier only
        );
    END IF;
END
$$;

-- Movement direction enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'movement_direction' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'bit')) THEN
        CREATE TYPE bit.movement_direction AS ENUM (
            'INCREASING',   -- Metric rising (e.g., costs up)
            'DECREASING',   -- Metric falling (e.g., headcount down)
            'REVERTING',    -- Metric changed (e.g., broker switch)
            'STABLE'        -- Metric unchanged but notable (e.g., stasis)
        );
    END IF;
END
$$;


-- ============================================================================
-- SECTION 2: MOVEMENT EVENTS TABLE
-- ============================================================================
-- Stores detected organizational movements from all three domains.
-- Each movement has a validity window and traceable evidence.

CREATE TABLE IF NOT EXISTS bit.movement_events (
    -- Primary key
    movement_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company reference
    company_unique_id       TEXT NOT NULL,

    -- Source traceability
    source_hub              TEXT NOT NULL,              -- 'dol-filings', 'people-intelligence', 'blog-content'
    source_table            TEXT NOT NULL,              -- e.g., 'dol.form_5500', 'people.company_slot'
    source_fields           TEXT[] NOT NULL,            -- Fields that triggered detection

    -- Classification
    movement_class          TEXT NOT NULL,              -- e.g., 'BROKER_CHANGE', 'SLOT_VACATED'
    pressure_class          TEXT NOT NULL,              -- e.g., 'VENDOR_DISSATISFACTION'
    domain                  TEXT NOT NULL,              -- 'STRUCTURAL_PRESSURE', 'DECISION_SURFACE', 'NARRATIVE_VOLATILITY'

    -- Measurement
    direction               TEXT NOT NULL,              -- 'INCREASING', 'DECREASING', 'REVERTING', 'STABLE'
    magnitude               NUMERIC(5,2) NOT NULL,      -- Impact score (0-100)

    -- Temporal bounds
    detected_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_from              TIMESTAMPTZ NOT NULL,
    valid_until             TIMESTAMPTZ NOT NULL,
    comparison_period       TEXT,                       -- 'YOY', '3YR', 'CURRENT', etc.

    -- Evidence (machine-readable)
    evidence                JSONB NOT NULL,             -- Detection details
    source_record_ids       JSONB NOT NULL,             -- IDs of source records for traceability

    -- Audit
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_domain CHECK (domain IN (
        'STRUCTURAL_PRESSURE',
        'DECISION_SURFACE',
        'NARRATIVE_VOLATILITY'
    )),
    CONSTRAINT valid_direction CHECK (direction IN (
        'INCREASING', 'DECREASING', 'REVERTING', 'STABLE'
    )),
    CONSTRAINT valid_magnitude CHECK (magnitude >= 0 AND magnitude <= 100),
    CONSTRAINT valid_window CHECK (valid_until > valid_from)
);

-- Indexes for movement_events
CREATE INDEX IF NOT EXISTS idx_movement_company
    ON bit.movement_events(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_movement_domain
    ON bit.movement_events(domain);
CREATE INDEX IF NOT EXISTS idx_movement_pressure
    ON bit.movement_events(pressure_class);
CREATE INDEX IF NOT EXISTS idx_movement_valid
    ON bit.movement_events(valid_until);
CREATE INDEX IF NOT EXISTS idx_movement_detected
    ON bit.movement_events(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_movement_company_valid
    ON bit.movement_events(company_unique_id, valid_until);

COMMENT ON TABLE bit.movement_events IS
    'Stores detected organizational movements from DOL, People, and Blog hubs. Each movement has a validity window and traceable evidence chain.';


-- ============================================================================
-- SECTION 3: PROOF LINES TABLE
-- ============================================================================
-- Stores proof lines that authorize Band 3+ outreach.
-- Proof must exist BEFORE message creation.

CREATE TABLE IF NOT EXISTS bit.proof_lines (
    -- Primary key (human-readable format: prf_xxxxx)
    proof_id                TEXT PRIMARY KEY,

    -- Company reference
    company_unique_id       TEXT NOT NULL,

    -- Authorization level
    band                    INTEGER NOT NULL,

    -- Pressure classification
    pressure_class          TEXT NOT NULL,

    -- Evidence chain
    sources                 TEXT[] NOT NULL,            -- Hub sources: ['dol-filings', 'people-intelligence']
    evidence                JSONB NOT NULL,             -- Structured evidence
    movement_ids            UUID[] NOT NULL,            -- Links to movement_events for traceability

    -- Human-readable proof line
    human_readable          TEXT NOT NULL,              -- The proof line text

    -- Validity window
    generated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until             TIMESTAMPTZ NOT NULL,

    -- Audit
    generated_by            TEXT NOT NULL,              -- 'system', 'agent_xxx', 'human_xxx'

    -- Constraints
    CONSTRAINT valid_band CHECK (band BETWEEN 0 AND 5),
    CONSTRAINT valid_window CHECK (valid_until > generated_at),
    CONSTRAINT band3_requires_sources CHECK (band < 3 OR array_length(sources, 1) >= 1),
    CONSTRAINT band4_requires_multi_source CHECK (band < 4 OR array_length(sources, 1) >= 2)
);

-- Indexes for proof_lines
CREATE INDEX IF NOT EXISTS idx_proof_company
    ON bit.proof_lines(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_proof_valid
    ON bit.proof_lines(valid_until);
CREATE INDEX IF NOT EXISTS idx_proof_company_valid
    ON bit.proof_lines(company_unique_id, valid_until);
CREATE INDEX IF NOT EXISTS idx_proof_band
    ON bit.proof_lines(band);

COMMENT ON TABLE bit.proof_lines IS
    'Stores proof lines that authorize Band 3+ outreach. Each proof traces to movement_events and has a validity window.';


-- ============================================================================
-- SECTION 4: PHASE STATE TABLE
-- ============================================================================
-- Stores current authorization state per company.
-- Updated when movements are detected or expire.

CREATE TABLE IF NOT EXISTS bit.phase_state (
    -- Primary key (one row per company)
    company_unique_id       TEXT PRIMARY KEY,

    -- Current authorization state
    current_band            INTEGER NOT NULL DEFAULT 0,
    phase_status            TEXT NOT NULL DEFAULT 'SILENT',

    -- Domain activation flags
    dol_active              BOOLEAN NOT NULL DEFAULT FALSE,
    people_active           BOOLEAN NOT NULL DEFAULT FALSE,
    blog_active             BOOLEAN NOT NULL DEFAULT FALSE,

    -- Pressure alignment
    primary_pressure        TEXT,                       -- Most common pressure class
    aligned_domains         INTEGER NOT NULL DEFAULT 0, -- Count of domains with same pressure

    -- Timestamps
    last_movement_at        TIMESTAMPTZ,                -- Most recent movement detection
    last_band_change_at     TIMESTAMPTZ,                -- When band last changed
    phase_entered_at        TIMESTAMPTZ,                -- When entered current phase

    -- Stasis tracking (for Blog suppression)
    stasis_start            TIMESTAMPTZ,                -- When stasis began
    stasis_years            NUMERIC(3,1) DEFAULT 0,     -- Years in stasis

    -- Audit
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_band CHECK (current_band BETWEEN 0 AND 5),
    CONSTRAINT valid_phase CHECK (phase_status IN (
        'SILENT', 'WATCH', 'EXPLORATORY', 'TARGETED', 'ENGAGED', 'DIRECT'
    )),
    CONSTRAINT valid_aligned CHECK (aligned_domains BETWEEN 0 AND 3)
);

-- Indexes for phase_state
CREATE INDEX IF NOT EXISTS idx_phase_band
    ON bit.phase_state(current_band);
CREATE INDEX IF NOT EXISTS idx_phase_status
    ON bit.phase_state(phase_status);
CREATE INDEX IF NOT EXISTS idx_phase_dol_active
    ON bit.phase_state(dol_active)
    WHERE dol_active = TRUE;

COMMENT ON TABLE bit.phase_state IS
    'Stores current authorization state per company. One row per company, updated when movements are detected or expire.';


-- ============================================================================
-- SECTION 5: AUTHORIZATION LOG TABLE
-- ============================================================================
-- Audit log for all authorization decisions.
-- Append-only: no updates, no deletes.

CREATE TABLE IF NOT EXISTS bit.authorization_log (
    -- Primary key
    log_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company reference
    company_unique_id       TEXT NOT NULL,

    -- Request details
    requested_action        TEXT NOT NULL,              -- 'send_email', 'phone_warm', etc.
    requested_band          INTEGER NOT NULL,           -- Band required for action

    -- Decision
    authorized              BOOLEAN NOT NULL,
    actual_band             INTEGER NOT NULL,           -- Company's actual band
    denial_reason           TEXT,                       -- If denied, why

    -- Proof (if Band 3+)
    proof_id                TEXT,                       -- FK to proof_lines
    proof_valid             BOOLEAN,                    -- Was proof valid at request time

    -- Context
    requested_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    requested_by            TEXT NOT NULL,              -- 'system', 'campaign_xxx', 'agent_xxx'
    correlation_id          TEXT,                       -- For end-to-end tracing

    -- Constraints
    CONSTRAINT valid_requested_band CHECK (requested_band BETWEEN 0 AND 5),
    CONSTRAINT valid_actual_band CHECK (actual_band BETWEEN 0 AND 5)
);

-- Indexes for authorization_log
CREATE INDEX IF NOT EXISTS idx_authlog_company
    ON bit.authorization_log(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_authlog_time
    ON bit.authorization_log(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_authlog_denied
    ON bit.authorization_log(authorized)
    WHERE authorized = FALSE;
CREATE INDEX IF NOT EXISTS idx_authlog_correlation
    ON bit.authorization_log(correlation_id)
    WHERE correlation_id IS NOT NULL;

-- Prevent updates and deletes (append-only)
CREATE OR REPLACE FUNCTION bit.prevent_authlog_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'bit.authorization_log is append-only. Updates and deletes are prohibited.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_authlog_no_update ON bit.authorization_log;
CREATE TRIGGER trg_authlog_no_update
    BEFORE UPDATE OR DELETE ON bit.authorization_log
    FOR EACH ROW
    EXECUTE FUNCTION bit.prevent_authlog_mutation();

COMMENT ON TABLE bit.authorization_log IS
    'Append-only audit log for all authorization decisions. Records every attempt to perform an outreach action.';


-- ============================================================================
-- SECTION 6: SHADOW COLUMNS ON EXISTING TABLES
-- ============================================================================
-- Add columns for shadow mode comparison (Phase 2).
-- These allow parallel calculation without changing existing behavior.

-- Add movement classification to existing signals (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'bit' AND table_name = 'bit_signal') THEN
        ALTER TABLE bit.bit_signal
            ADD COLUMN IF NOT EXISTS movement_class TEXT,
            ADD COLUMN IF NOT EXISTS pressure_class TEXT,
            ADD COLUMN IF NOT EXISTS domain TEXT;
        RAISE NOTICE 'Added shadow columns to bit.bit_signal';
    ELSE
        RAISE NOTICE 'bit.bit_signal does not exist - skipping shadow columns';
    END IF;
END
$$;

-- Add shadow band to company_master (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'marketing' AND table_name = 'company_master') THEN
        ALTER TABLE marketing.company_master
            ADD COLUMN IF NOT EXISTS bit_band INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS bit_phase TEXT DEFAULT 'SILENT';

        COMMENT ON COLUMN marketing.company_master.bit_band IS
            'Shadow column for BIT v2 band calculation. Not authoritative until Phase 4 cutover.';
        COMMENT ON COLUMN marketing.company_master.bit_phase IS
            'Shadow column for BIT v2 phase status. Not authoritative until Phase 4 cutover.';

        RAISE NOTICE 'Added shadow columns to marketing.company_master';
    ELSE
        RAISE NOTICE 'marketing.company_master does not exist - skipping shadow columns';
    END IF;
END
$$;


-- ============================================================================
-- SECTION 7: HELPER FUNCTIONS
-- ============================================================================

-- Function to get current band for a company
CREATE OR REPLACE FUNCTION bit.get_current_band(p_company_id TEXT)
RETURNS INTEGER AS $$
DECLARE
    v_band INTEGER;
BEGIN
    SELECT current_band INTO v_band
    FROM bit.phase_state
    WHERE company_unique_id = p_company_id;

    -- Return 0 if no phase state exists
    RETURN COALESCE(v_band, 0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION bit.get_current_band IS
    'Returns current authorization band for a company. Returns 0 (SILENT) if no phase state exists.';


-- Function to check if action is authorized
CREATE OR REPLACE FUNCTION bit.authorize_action(
    p_company_id TEXT,
    p_action TEXT,
    p_requested_by TEXT DEFAULT 'system'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_band INTEGER;
    v_required_band INTEGER;
    v_authorized BOOLEAN;
BEGIN
    -- Get current band
    v_band := bit.get_current_band(p_company_id);

    -- Map action to required band
    v_required_band := CASE p_action
        WHEN 'internal_flag' THEN 1
        WHEN 'educational_content' THEN 2
        WHEN 'persona_email' THEN 3
        WHEN 'phone_warm' THEN 4
        WHEN 'phone_cold' THEN 5
        WHEN 'meeting_request' THEN 5
        ELSE 5  -- Unknown actions require highest band
    END;

    -- Check authorization
    v_authorized := v_band >= v_required_band;

    -- Log the decision
    INSERT INTO bit.authorization_log (
        company_unique_id,
        requested_action,
        requested_band,
        authorized,
        actual_band,
        denial_reason,
        requested_by
    ) VALUES (
        p_company_id,
        p_action,
        v_required_band,
        v_authorized,
        v_band,
        CASE WHEN NOT v_authorized
            THEN format('Band %s insufficient for action %s (requires %s)', v_band, p_action, v_required_band)
            ELSE NULL
        END,
        p_requested_by
    );

    RETURN v_authorized;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION bit.authorize_action IS
    'Checks if an action is authorized for a company and logs the decision. Returns TRUE if authorized.';


-- Function to validate proof for send
CREATE OR REPLACE FUNCTION bit.validate_proof_for_send(
    p_proof_id TEXT,
    p_requested_band INTEGER
)
RETURNS BOOLEAN AS $$
DECLARE
    v_proof RECORD;
BEGIN
    -- Get proof
    SELECT * INTO v_proof
    FROM bit.proof_lines
    WHERE proof_id = p_proof_id;

    -- Check proof exists
    IF v_proof IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check proof not expired
    IF v_proof.valid_until < NOW() THEN
        RETURN FALSE;
    END IF;

    -- Check proof band sufficient
    IF v_proof.band < p_requested_band THEN
        RETURN FALSE;
    END IF;

    -- Verify at least one movement still valid
    IF NOT EXISTS (
        SELECT 1 FROM bit.movement_events
        WHERE movement_id = ANY(v_proof.movement_ids)
          AND valid_until > NOW()
    ) THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION bit.validate_proof_for_send IS
    'Validates that a proof line is still valid for the requested band. Checks expiration and evidence chain.';


-- ============================================================================
-- SECTION 8: VIEWS
-- ============================================================================

-- View: Active movements per company
CREATE OR REPLACE VIEW bit.vw_active_movements AS
SELECT
    company_unique_id,
    domain,
    pressure_class,
    movement_class,
    magnitude,
    detected_at,
    valid_until,
    (valid_until - NOW()) AS time_remaining
FROM bit.movement_events
WHERE valid_until > NOW()
ORDER BY company_unique_id, magnitude DESC;

COMMENT ON VIEW bit.vw_active_movements IS
    'Shows all currently active (non-expired) movement events.';


-- View: Company authorization summary
CREATE OR REPLACE VIEW bit.vw_company_authorization AS
SELECT
    ps.company_unique_id,
    ps.current_band,
    ps.phase_status,
    ps.dol_active,
    ps.people_active,
    ps.blog_active,
    ps.primary_pressure,
    ps.aligned_domains,
    ps.last_movement_at,
    (SELECT COUNT(*) FROM bit.movement_events me
     WHERE me.company_unique_id = ps.company_unique_id
       AND me.valid_until > NOW()) AS active_movement_count,
    (SELECT COUNT(*) FROM bit.proof_lines pl
     WHERE pl.company_unique_id = ps.company_unique_id
       AND pl.valid_until > NOW()) AS valid_proof_count
FROM bit.phase_state ps;

COMMENT ON VIEW bit.vw_company_authorization IS
    'Summary view of company authorization state with movement and proof counts.';


-- ============================================================================
-- SECTION 9: GRANTS
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA bit TO PUBLIC;

-- Grant select on views
GRANT SELECT ON bit.vw_active_movements TO PUBLIC;
GRANT SELECT ON bit.vw_company_authorization TO PUBLIC;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION bit.get_current_band TO PUBLIC;
GRANT EXECUTE ON FUNCTION bit.authorize_action TO PUBLIC;
GRANT EXECUTE ON FUNCTION bit.validate_proof_for_send TO PUBLIC;


-- ============================================================================
-- SECTION 10: VERIFICATION
-- ============================================================================

DO $$
DECLARE
    v_table_count INTEGER;
    v_function_count INTEGER;
BEGIN
    -- Count new tables
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'bit'
      AND table_name IN ('movement_events', 'proof_lines', 'phase_state', 'authorization_log');

    -- Count new functions
    SELECT COUNT(*) INTO v_function_count
    FROM information_schema.routines
    WHERE routine_schema = 'bit'
      AND routine_name IN ('get_current_band', 'authorize_action', 'validate_proof_for_send');

    -- Verify
    IF v_table_count = 4 AND v_function_count >= 3 THEN
        RAISE NOTICE 'BIT v2 Phase 1 schema migration SUCCESSFUL';
        RAISE NOTICE 'Tables created: %', v_table_count;
        RAISE NOTICE 'Functions created: %', v_function_count;
    ELSE
        RAISE EXCEPTION 'BIT v2 Phase 1 schema migration INCOMPLETE. Tables: %, Functions: %',
            v_table_count, v_function_count;
    END IF;
END
$$;


-- ============================================================================
-- ROLLBACK SCRIPT (for reference, do not execute)
-- ============================================================================
/*
-- To rollback Phase 1, execute:

DROP VIEW IF EXISTS bit.vw_company_authorization CASCADE;
DROP VIEW IF EXISTS bit.vw_active_movements CASCADE;

DROP FUNCTION IF EXISTS bit.validate_proof_for_send CASCADE;
DROP FUNCTION IF EXISTS bit.authorize_action CASCADE;
DROP FUNCTION IF EXISTS bit.get_current_band CASCADE;
DROP FUNCTION IF EXISTS bit.prevent_authlog_mutation CASCADE;

DROP TABLE IF EXISTS bit.authorization_log CASCADE;
DROP TABLE IF EXISTS bit.phase_state CASCADE;
DROP TABLE IF EXISTS bit.proof_lines CASCADE;
DROP TABLE IF EXISTS bit.movement_events CASCADE;

DROP TYPE IF EXISTS bit.movement_direction CASCADE;
DROP TYPE IF EXISTS bit.movement_domain CASCADE;
DROP TYPE IF EXISTS bit.pressure_class CASCADE;
DROP TYPE IF EXISTS bit.authorization_band CASCADE;

ALTER TABLE bit.bit_signal
    DROP COLUMN IF EXISTS movement_class,
    DROP COLUMN IF EXISTS pressure_class,
    DROP COLUMN IF EXISTS domain;

ALTER TABLE marketing.company_master
    DROP COLUMN IF EXISTS bit_band,
    DROP COLUMN IF EXISTS bit_phase;
*/
