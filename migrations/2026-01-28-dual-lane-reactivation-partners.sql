-- ============================================================================
-- MIGRATION: Dual Lane - Appointment Reactivation + Fractional CFO Partners
-- ============================================================================
-- Authority: ADR-018 (pending)
-- Created: 2026-01-28
-- Status: READY FOR EXECUTION
--
-- DOCTRINE COMPLIANCE:
--   - Immutable fact tables (write-once enforced)
--   - Scoring/intent lives ONLY in BIT
--   - Full auditability via shq.audit_log
--   - No schema pollution (isolated schemas)
--   - Kill switch ready via eligibility_status
--
-- LANES:
--   A) Appointment Reactivation (sales.appointment_history → bit.reactivation_intent)
--   B) Fractional CFO Partners (partners.* → bit.partner_intent)
--
-- ============================================================================

-- ============================================================================
-- SECTION 0: SCHEMA CREATION
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS sales;
CREATE SCHEMA IF NOT EXISTS partners;
CREATE SCHEMA IF NOT EXISTS shq;

-- ============================================================================
-- SECTION 1: AUDIT LOG TABLE (if not exists)
-- ============================================================================

CREATE TABLE IF NOT EXISTS shq.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    record_id TEXT NOT NULL,  -- Primary key of affected record
    old_values JSONB,
    new_values JSONB,
    performed_by TEXT NOT NULL DEFAULT current_user,
    performed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id UUID,
    metadata JSONB DEFAULT '{}'::JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table ON shq.audit_log(schema_name, table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_time ON shq.audit_log(performed_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_record ON shq.audit_log(table_name, record_id);

-- Make audit log append-only
CREATE OR REPLACE FUNCTION shq.fn_audit_log_immutable()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'shq.audit_log is append-only. Updates and deletes are prohibited per Barton Doctrine.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_log_immutable ON shq.audit_log;
CREATE TRIGGER trg_audit_log_immutable
    BEFORE UPDATE OR DELETE ON shq.audit_log
    FOR EACH ROW EXECUTE FUNCTION shq.fn_audit_log_immutable();

COMMENT ON TABLE shq.audit_log IS 'Immutable audit log for all tracked operations. Append-only per Barton Doctrine.';


-- ============================================================================
-- SECTION 2: LANE A - APPOINTMENT REACTIVATION ENUMS
-- ============================================================================

-- Meeting type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meeting_type_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'sales')) THEN
        CREATE TYPE sales.meeting_type_enum AS ENUM (
            'discovery',    -- Initial discovery call
            'systems',      -- Systems/process review
            'numbers',      -- Numbers/pricing discussion
            'other'         -- Other meeting type
        );
    END IF;
END $$;

-- Meeting outcome enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'meeting_outcome_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'sales')) THEN
        CREATE TYPE sales.meeting_outcome_enum AS ENUM (
            'progressed',   -- Moved to next stage
            'stalled',      -- Stuck, no movement
            'ghosted',      -- Lost contact
            'lost'          -- Closed-lost
        );
    END IF;
END $$;

-- Appointment source enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'appointment_source_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'sales')) THEN
        CREATE TYPE sales.appointment_source_enum AS ENUM (
            'calendar',     -- Calendar sync
            'crm',          -- CRM import
            'manual'        -- Manual entry
        );
    END IF;
END $$;

-- Reactivation channel enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reactivation_channel_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'bit')) THEN
        CREATE TYPE bit.reactivation_channel_enum AS ENUM (
            'linkedin',     -- LinkedIn outreach
            'email'         -- Email outreach
        );
    END IF;
END $$;

-- Eligibility status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'eligibility_status_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'bit')) THEN
        CREATE TYPE bit.eligibility_status_enum AS ENUM (
            'eligible',     -- Ready for outreach
            'excluded',     -- Permanently excluded
            'cooling_off'   -- Temporarily excluded
        );
    END IF;
END $$;


-- ============================================================================
-- SECTION 3: LANE A - APPOINTMENT HISTORY (FACT TABLE)
-- ============================================================================
-- This is a FACT table. No scores. No intent. Write-once enforced.

CREATE TABLE IF NOT EXISTS sales.appointment_history (
    -- Primary key (deterministic for deduplication)
    appointment_uid TEXT PRIMARY KEY,  -- Format: company_id|people_id|meeting_date

    -- Foreign keys (nullable for flexibility)
    company_id UUID,
    people_id UUID,
    outreach_id UUID,

    -- Meeting details
    meeting_date DATE NOT NULL,
    meeting_type sales.meeting_type_enum NOT NULL,
    meeting_outcome sales.meeting_outcome_enum NOT NULL,
    stalled_reason TEXT,  -- Nullable, only populated if outcome = 'stalled'

    -- Source tracking
    source sales.appointment_source_enum NOT NULL DEFAULT 'manual',
    source_record_id TEXT,  -- External ID from source system

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_appointment_uid_format CHECK (
        appointment_uid ~ '^[a-zA-Z0-9_-]+\|[a-zA-Z0-9_-]+\|[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        OR appointment_uid ~ '^[a-f0-9-]{36}\|[a-f0-9-]{36}\|[0-9]{4}-[0-9]{2}-[0-9]{2}$'
        OR LENGTH(appointment_uid) >= 10  -- Fallback for other formats
    ),
    CONSTRAINT chk_stalled_reason CHECK (
        (meeting_outcome != 'stalled') OR (stalled_reason IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_appointment_history_company ON sales.appointment_history(company_id);
CREATE INDEX IF NOT EXISTS idx_appointment_history_people ON sales.appointment_history(people_id);
CREATE INDEX IF NOT EXISTS idx_appointment_history_outreach ON sales.appointment_history(outreach_id);
CREATE INDEX IF NOT EXISTS idx_appointment_history_date ON sales.appointment_history(meeting_date DESC);
CREATE INDEX IF NOT EXISTS idx_appointment_history_outcome ON sales.appointment_history(meeting_outcome);
CREATE INDEX IF NOT EXISTS idx_appointment_history_type_outcome ON sales.appointment_history(meeting_type, meeting_outcome);

-- Write-once trigger
CREATE OR REPLACE FUNCTION sales.fn_appointment_history_write_once()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'UPDATE BLOCKED: sales.appointment_history is write-once per Barton Doctrine. Record appointment_uid: %', OLD.appointment_uid;
    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'DELETE BLOCKED: sales.appointment_history is write-once per Barton Doctrine. Record appointment_uid: %', OLD.appointment_uid;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_appointment_history_write_once ON sales.appointment_history;
CREATE TRIGGER trg_appointment_history_write_once
    BEFORE UPDATE OR DELETE ON sales.appointment_history
    FOR EACH ROW EXECUTE FUNCTION sales.fn_appointment_history_write_once();

-- Audit trigger
CREATE OR REPLACE FUNCTION sales.fn_appointment_history_audit()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO shq.audit_log (schema_name, table_name, operation, record_id, new_values)
    VALUES ('sales', 'appointment_history', TG_OP, NEW.appointment_uid, to_jsonb(NEW));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_appointment_history_audit ON sales.appointment_history;
CREATE TRIGGER trg_appointment_history_audit
    AFTER INSERT ON sales.appointment_history
    FOR EACH ROW EXECUTE FUNCTION sales.fn_appointment_history_audit();

COMMENT ON TABLE sales.appointment_history IS 'Immutable fact table for past appointments. Write-once enforced. No scores - intent lives in BIT.';


-- ============================================================================
-- SECTION 4: LANE A - REACTIVATION INTENT (BIT TABLE)
-- ============================================================================
-- Scoring and intent ONLY live here, not in fact tables.

CREATE TABLE IF NOT EXISTS bit.reactivation_intent (
    -- Primary key
    reactivation_bit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to fact table
    appointment_uid TEXT NOT NULL REFERENCES sales.appointment_history(appointment_uid),

    -- BIT scoring (nullable for scaffold - computed later)
    bit_score NUMERIC(5,2),
    bit_reason_codes TEXT[],

    -- Recommended action
    recommended_channel bit.reactivation_channel_enum,
    message_variant_id TEXT,

    -- Kill switch support
    eligibility_status bit.eligibility_status_enum NOT NULL DEFAULT 'eligible',
    exclusion_reason TEXT,  -- If excluded, why
    cooling_off_until TIMESTAMPTZ,  -- If cooling_off, until when

    -- Timestamps
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_touched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Audit
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Constraints
    CONSTRAINT chk_reactivation_score CHECK (bit_score IS NULL OR (bit_score >= 0 AND bit_score <= 100)),
    CONSTRAINT chk_cooling_off CHECK (
        eligibility_status != 'cooling_off' OR cooling_off_until IS NOT NULL
    ),
    CONSTRAINT chk_exclusion_reason CHECK (
        eligibility_status != 'excluded' OR exclusion_reason IS NOT NULL
    ),

    -- Unique constraint: one intent per appointment
    CONSTRAINT uq_reactivation_appointment UNIQUE (appointment_uid)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_reactivation_intent_appointment ON bit.reactivation_intent(appointment_uid);
CREATE INDEX IF NOT EXISTS idx_reactivation_intent_score ON bit.reactivation_intent(bit_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_reactivation_intent_status ON bit.reactivation_intent(eligibility_status);
CREATE INDEX IF NOT EXISTS idx_reactivation_intent_eligible ON bit.reactivation_intent(bit_score DESC)
    WHERE eligibility_status = 'eligible';

-- Update last_touched_at on any change
CREATE OR REPLACE FUNCTION bit.fn_reactivation_intent_touch()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_touched_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_reactivation_intent_touch ON bit.reactivation_intent;
CREATE TRIGGER trg_reactivation_intent_touch
    BEFORE UPDATE ON bit.reactivation_intent
    FOR EACH ROW EXECUTE FUNCTION bit.fn_reactivation_intent_touch();

COMMENT ON TABLE bit.reactivation_intent IS 'BIT scoring for appointment reactivation. Intent and scores live here, not in fact tables.';


-- ============================================================================
-- SECTION 5: LANE A - REACTIVATION READY VIEW
-- ============================================================================

CREATE OR REPLACE VIEW bit.v_reactivation_ready AS
SELECT
    ri.reactivation_bit_id,
    ri.appointment_uid,
    ah.company_id,
    ah.people_id,
    ah.outreach_id,
    ah.meeting_date,
    ah.meeting_type,
    ah.meeting_outcome,
    ah.stalled_reason,
    ri.bit_score,
    ri.bit_reason_codes,
    ri.recommended_channel,
    ri.message_variant_id,
    ri.eligibility_status,
    ri.computed_at,
    ri.last_touched_at,
    -- Days since meeting
    (CURRENT_DATE - ah.meeting_date) AS days_since_meeting,
    -- Reactivation tier based on score
    CASE
        WHEN ri.bit_score >= 80 THEN 'hot'
        WHEN ri.bit_score >= 60 THEN 'warm'
        WHEN ri.bit_score >= 40 THEN 'cool'
        ELSE 'cold'
    END AS reactivation_tier
FROM bit.reactivation_intent ri
JOIN sales.appointment_history ah ON ri.appointment_uid = ah.appointment_uid
WHERE ri.eligibility_status = 'eligible'
  AND (ri.bit_score IS NULL OR ri.bit_score >= 40)  -- Threshold filter (adjustable)
ORDER BY ri.bit_score DESC NULLS LAST, ah.meeting_date DESC;

COMMENT ON VIEW bit.v_reactivation_ready IS 'Eligible appointments ready for reactivation outreach. Use this view - never bypass to underlying tables.';


-- ============================================================================
-- SECTION 6: LANE B - FRACTIONAL CFO PARTNER ENUMS
-- ============================================================================

-- Partner status enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'partner_status_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'partners')) THEN
        CREATE TYPE partners.partner_status_enum AS ENUM (
            'prospect',     -- Initial identification
            'contacted',    -- Outreach initiated
            'engaged',      -- Active dialogue
            'partner'       -- Formal partnership
        );
    END IF;
END $$;

-- Partner meeting type enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'partner_meeting_type_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'partners')) THEN
        CREATE TYPE partners.partner_meeting_type_enum AS ENUM (
            'intro',        -- Introduction call
            'followup'      -- Follow-up meeting
        );
    END IF;
END $$;

-- Partner meeting outcome enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'partner_meeting_outcome_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'partners')) THEN
        CREATE TYPE partners.partner_meeting_outcome_enum AS ENUM (
            'warm',         -- Positive reception
            'neutral',      -- No clear direction
            'cold'          -- Negative reception
        );
    END IF;
END $$;


-- ============================================================================
-- SECTION 7: LANE B - FRACTIONAL CFO MASTER TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS partners.fractional_cfo_master (
    -- Primary key
    fractional_cfo_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identity
    firm_name TEXT NOT NULL,
    primary_contact_name TEXT NOT NULL,
    linkedin_url TEXT,
    email TEXT,

    -- Segmentation
    geography TEXT,  -- e.g., 'Mid-Atlantic', 'Northeast', 'National'
    niche_focus TEXT,  -- e.g., 'Healthcare', 'SaaS', 'Manufacturing'

    -- Source tracking
    source TEXT NOT NULL,  -- e.g., 'LinkedIn', 'Referral', 'Conference'
    source_detail TEXT,  -- Additional source info

    -- Status
    status partners.partner_status_enum NOT NULL DEFAULT 'prospect',

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_linkedin_url CHECK (
        linkedin_url IS NULL OR linkedin_url ~ '^https?://(www\.)?linkedin\.com/'
    ),
    CONSTRAINT chk_email_format CHECK (
        email IS NULL OR email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_fractional_cfo_status ON partners.fractional_cfo_master(status);
CREATE INDEX IF NOT EXISTS idx_fractional_cfo_geography ON partners.fractional_cfo_master(geography);
CREATE INDEX IF NOT EXISTS idx_fractional_cfo_niche ON partners.fractional_cfo_master(niche_focus);
CREATE INDEX IF NOT EXISTS idx_fractional_cfo_source ON partners.fractional_cfo_master(source);
CREATE INDEX IF NOT EXISTS idx_fractional_cfo_linkedin ON partners.fractional_cfo_master(linkedin_url) WHERE linkedin_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_fractional_cfo_email ON partners.fractional_cfo_master(email) WHERE email IS NOT NULL;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION partners.fn_fractional_cfo_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_fractional_cfo_updated ON partners.fractional_cfo_master;
CREATE TRIGGER trg_fractional_cfo_updated
    BEFORE UPDATE ON partners.fractional_cfo_master
    FOR EACH ROW EXECUTE FUNCTION partners.fn_fractional_cfo_updated();

-- Audit trigger
CREATE OR REPLACE FUNCTION partners.fn_fractional_cfo_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO shq.audit_log (schema_name, table_name, operation, record_id, new_values)
        VALUES ('partners', 'fractional_cfo_master', TG_OP, NEW.fractional_cfo_id::TEXT, to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO shq.audit_log (schema_name, table_name, operation, record_id, old_values, new_values)
        VALUES ('partners', 'fractional_cfo_master', TG_OP, NEW.fractional_cfo_id::TEXT, to_jsonb(OLD), to_jsonb(NEW));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_fractional_cfo_audit ON partners.fractional_cfo_master;
CREATE TRIGGER trg_fractional_cfo_audit
    AFTER INSERT OR UPDATE ON partners.fractional_cfo_master
    FOR EACH ROW EXECUTE FUNCTION partners.fn_fractional_cfo_audit();

COMMENT ON TABLE partners.fractional_cfo_master IS 'Master table for fractional CFO partners. Status can be updated, full audit trail maintained.';


-- ============================================================================
-- SECTION 8: LANE B - PARTNER APPOINTMENTS (FACT TABLE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS partners.partner_appointments (
    -- Primary key
    partner_appointment_uid TEXT PRIMARY KEY,  -- Format: cfo_id|meeting_date|seq

    -- Foreign key
    fractional_cfo_id UUID NOT NULL REFERENCES partners.fractional_cfo_master(fractional_cfo_id),

    -- Meeting details
    meeting_date DATE NOT NULL,
    meeting_type partners.partner_meeting_type_enum NOT NULL,
    outcome partners.partner_meeting_outcome_enum NOT NULL,
    notes TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_partner_appointment_uid_format CHECK (
        LENGTH(partner_appointment_uid) >= 10
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_partner_appointments_cfo ON partners.partner_appointments(fractional_cfo_id);
CREATE INDEX IF NOT EXISTS idx_partner_appointments_date ON partners.partner_appointments(meeting_date DESC);
CREATE INDEX IF NOT EXISTS idx_partner_appointments_outcome ON partners.partner_appointments(outcome);

-- Write-once trigger
CREATE OR REPLACE FUNCTION partners.fn_partner_appointments_write_once()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'UPDATE BLOCKED: partners.partner_appointments is write-once per Barton Doctrine. Record partner_appointment_uid: %', OLD.partner_appointment_uid;
    ELSIF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'DELETE BLOCKED: partners.partner_appointments is write-once per Barton Doctrine. Record partner_appointment_uid: %', OLD.partner_appointment_uid;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_partner_appointments_write_once ON partners.partner_appointments;
CREATE TRIGGER trg_partner_appointments_write_once
    BEFORE UPDATE OR DELETE ON partners.partner_appointments
    FOR EACH ROW EXECUTE FUNCTION partners.fn_partner_appointments_write_once();

-- Audit trigger
CREATE OR REPLACE FUNCTION partners.fn_partner_appointments_audit()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO shq.audit_log (schema_name, table_name, operation, record_id, new_values)
    VALUES ('partners', 'partner_appointments', TG_OP, NEW.partner_appointment_uid, to_jsonb(NEW));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_partner_appointments_audit ON partners.partner_appointments;
CREATE TRIGGER trg_partner_appointments_audit
    AFTER INSERT ON partners.partner_appointments
    FOR EACH ROW EXECUTE FUNCTION partners.fn_partner_appointments_audit();

COMMENT ON TABLE partners.partner_appointments IS 'Immutable fact table for partner appointments. Write-once enforced.';


-- ============================================================================
-- SECTION 9: LANE B - PARTNER INTENT (BIT TABLE)
-- ============================================================================

CREATE TABLE IF NOT EXISTS bit.partner_intent (
    -- Primary key
    partner_bit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key
    fractional_cfo_id UUID NOT NULL REFERENCES partners.fractional_cfo_master(fractional_cfo_id),

    -- BIT scoring (nullable for scaffold)
    leverage_score NUMERIC(5,2),
    leverage_factors TEXT[],

    -- Recommended action
    recommended_next_action TEXT,
    message_variant_id TEXT,

    -- Status tracking
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, active, paused, completed

    -- Timestamps
    computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Audit
    metadata JSONB DEFAULT '{}'::JSONB,

    -- Constraints
    CONSTRAINT chk_partner_leverage_score CHECK (leverage_score IS NULL OR (leverage_score >= 0 AND leverage_score <= 100)),
    CONSTRAINT chk_partner_intent_status CHECK (status IN ('pending', 'active', 'paused', 'completed')),

    -- Unique constraint: one active intent per partner
    CONSTRAINT uq_partner_intent_cfo UNIQUE (fractional_cfo_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_partner_intent_cfo ON bit.partner_intent(fractional_cfo_id);
CREATE INDEX IF NOT EXISTS idx_partner_intent_score ON bit.partner_intent(leverage_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_partner_intent_status ON bit.partner_intent(status);
CREATE INDEX IF NOT EXISTS idx_partner_intent_active ON bit.partner_intent(leverage_score DESC)
    WHERE status = 'active';

COMMENT ON TABLE bit.partner_intent IS 'BIT scoring for partner outreach. Leverage scores and recommended actions live here.';


-- ============================================================================
-- SECTION 10: LANE B - PARTNER OUTREACH VIEW
-- ============================================================================

CREATE OR REPLACE VIEW bit.v_partner_outreach_ready AS
SELECT
    pi.partner_bit_id,
    pi.fractional_cfo_id,
    fcm.firm_name,
    fcm.primary_contact_name,
    fcm.linkedin_url,
    fcm.email,
    fcm.geography,
    fcm.niche_focus,
    fcm.status AS partner_status,
    pi.leverage_score,
    pi.leverage_factors,
    pi.recommended_next_action,
    pi.message_variant_id,
    pi.status AS intent_status,
    pi.computed_at,
    -- Last meeting info
    (
        SELECT json_build_object(
            'meeting_date', pa.meeting_date,
            'meeting_type', pa.meeting_type,
            'outcome', pa.outcome
        )
        FROM partners.partner_appointments pa
        WHERE pa.fractional_cfo_id = fcm.fractional_cfo_id
        ORDER BY pa.meeting_date DESC
        LIMIT 1
    ) AS last_meeting,
    -- Days since last meeting
    (
        SELECT (CURRENT_DATE - MAX(pa.meeting_date))
        FROM partners.partner_appointments pa
        WHERE pa.fractional_cfo_id = fcm.fractional_cfo_id
    ) AS days_since_last_meeting,
    -- Meeting count
    (
        SELECT COUNT(*)
        FROM partners.partner_appointments pa
        WHERE pa.fractional_cfo_id = fcm.fractional_cfo_id
    ) AS total_meetings
FROM bit.partner_intent pi
JOIN partners.fractional_cfo_master fcm ON pi.fractional_cfo_id = fcm.fractional_cfo_id
WHERE pi.status = 'active'
ORDER BY pi.leverage_score DESC NULLS LAST;

COMMENT ON VIEW bit.v_partner_outreach_ready IS 'Partners ready for outreach. Use this view for LinkedIn/email campaigns.';


-- ============================================================================
-- SECTION 11: HELPER FUNCTIONS
-- ============================================================================

-- Generate deterministic appointment_uid
CREATE OR REPLACE FUNCTION sales.fn_generate_appointment_uid(
    p_company_id UUID,
    p_people_id UUID,
    p_meeting_date DATE
) RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(p_company_id::TEXT, 'UNKNOWN') || '|' ||
           COALESCE(p_people_id::TEXT, 'UNKNOWN') || '|' ||
           p_meeting_date::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Generate partner appointment_uid
CREATE OR REPLACE FUNCTION partners.fn_generate_partner_appointment_uid(
    p_fractional_cfo_id UUID,
    p_meeting_date DATE,
    p_seq INTEGER DEFAULT 1
) RETURNS TEXT AS $$
BEGIN
    RETURN p_fractional_cfo_id::TEXT || '|' || p_meeting_date::TEXT || '|' || p_seq::TEXT;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Initialize reactivation intent for appointment
CREATE OR REPLACE FUNCTION bit.fn_init_reactivation_intent(
    p_appointment_uid TEXT
) RETURNS UUID AS $$
DECLARE
    v_reactivation_bit_id UUID;
BEGIN
    INSERT INTO bit.reactivation_intent (appointment_uid)
    VALUES (p_appointment_uid)
    ON CONFLICT (appointment_uid) DO NOTHING
    RETURNING reactivation_bit_id INTO v_reactivation_bit_id;

    RETURN v_reactivation_bit_id;
END;
$$ LANGUAGE plpgsql;

-- Initialize partner intent
CREATE OR REPLACE FUNCTION bit.fn_init_partner_intent(
    p_fractional_cfo_id UUID
) RETURNS UUID AS $$
DECLARE
    v_partner_bit_id UUID;
BEGIN
    INSERT INTO bit.partner_intent (fractional_cfo_id, status)
    VALUES (p_fractional_cfo_id, 'pending')
    ON CONFLICT (fractional_cfo_id) DO NOTHING
    RETURNING partner_bit_id INTO v_partner_bit_id;

    RETURN v_partner_bit_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- SECTION 12: GRANTS
-- ============================================================================

GRANT USAGE ON SCHEMA sales TO PUBLIC;
GRANT USAGE ON SCHEMA partners TO PUBLIC;
GRANT USAGE ON SCHEMA shq TO PUBLIC;

GRANT SELECT ON bit.v_reactivation_ready TO PUBLIC;
GRANT SELECT ON bit.v_partner_outreach_ready TO PUBLIC;

GRANT EXECUTE ON FUNCTION sales.fn_generate_appointment_uid TO PUBLIC;
GRANT EXECUTE ON FUNCTION partners.fn_generate_partner_appointment_uid TO PUBLIC;
GRANT EXECUTE ON FUNCTION bit.fn_init_reactivation_intent TO PUBLIC;
GRANT EXECUTE ON FUNCTION bit.fn_init_partner_intent TO PUBLIC;


-- ============================================================================
-- SECTION 13: VERIFICATION
-- ============================================================================

DO $$
DECLARE
    v_lane_a_tables INTEGER;
    v_lane_b_tables INTEGER;
    v_bit_tables INTEGER;
    v_triggers INTEGER;
BEGIN
    -- Count Lane A tables
    SELECT COUNT(*) INTO v_lane_a_tables
    FROM information_schema.tables
    WHERE table_schema = 'sales' AND table_name = 'appointment_history';

    -- Count Lane B tables
    SELECT COUNT(*) INTO v_lane_b_tables
    FROM information_schema.tables
    WHERE table_schema = 'partners' AND table_name IN ('fractional_cfo_master', 'partner_appointments');

    -- Count BIT tables
    SELECT COUNT(*) INTO v_bit_tables
    FROM information_schema.tables
    WHERE table_schema = 'bit' AND table_name IN ('reactivation_intent', 'partner_intent');

    -- Count write-once triggers
    SELECT COUNT(*) INTO v_triggers
    FROM pg_trigger
    WHERE tgname LIKE '%write_once%';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Dual Lane Migration Verification:';
    RAISE NOTICE '  Lane A tables (sales): % (expected 1)', v_lane_a_tables;
    RAISE NOTICE '  Lane B tables (partners): % (expected 2)', v_lane_b_tables;
    RAISE NOTICE '  BIT tables: % (expected 2)', v_bit_tables;
    RAISE NOTICE '  Write-once triggers: % (expected 2)', v_triggers;
    RAISE NOTICE '========================================';

    IF v_lane_a_tables = 1 AND v_lane_b_tables = 2 AND v_bit_tables = 2 THEN
        RAISE NOTICE 'Dual Lane Migration SUCCESSFUL';
    ELSE
        RAISE WARNING 'Dual Lane Migration may be incomplete';
    END IF;
END $$;


-- ============================================================================
-- ROLLBACK SCRIPT (for reference, do not execute)
-- ============================================================================
/*
-- To rollback this migration, execute:

DROP VIEW IF EXISTS bit.v_partner_outreach_ready CASCADE;
DROP VIEW IF EXISTS bit.v_reactivation_ready CASCADE;

DROP FUNCTION IF EXISTS bit.fn_init_partner_intent CASCADE;
DROP FUNCTION IF EXISTS bit.fn_init_reactivation_intent CASCADE;
DROP FUNCTION IF EXISTS partners.fn_generate_partner_appointment_uid CASCADE;
DROP FUNCTION IF EXISTS sales.fn_generate_appointment_uid CASCADE;

DROP TABLE IF EXISTS bit.partner_intent CASCADE;
DROP TABLE IF EXISTS bit.reactivation_intent CASCADE;
DROP TABLE IF EXISTS partners.partner_appointments CASCADE;
DROP TABLE IF EXISTS partners.fractional_cfo_master CASCADE;
DROP TABLE IF EXISTS sales.appointment_history CASCADE;

DROP TYPE IF EXISTS partners.partner_meeting_outcome_enum CASCADE;
DROP TYPE IF EXISTS partners.partner_meeting_type_enum CASCADE;
DROP TYPE IF EXISTS partners.partner_status_enum CASCADE;
DROP TYPE IF EXISTS bit.eligibility_status_enum CASCADE;
DROP TYPE IF EXISTS bit.reactivation_channel_enum CASCADE;
DROP TYPE IF EXISTS sales.appointment_source_enum CASCADE;
DROP TYPE IF EXISTS sales.meeting_outcome_enum CASCADE;
DROP TYPE IF EXISTS sales.meeting_type_enum CASCADE;

-- Keep shq.audit_log (shared infrastructure)
*/
