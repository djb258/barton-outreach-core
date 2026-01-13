-- ==============================================================================
-- DOL FILINGS HUB SCHEMA CREATION MIGRATION
-- ==============================================================================
-- Date: 2026-01-13
-- Purpose: Create dol.* schema for DOL Filings Hub (04.04.03)
--
-- HARDENING PASS: Creates ONLY tables referenced by existing code.
-- Pattern: Reuses RLS/trigger patterns from 003_enforce_master_error_immutability.sql
--
-- DOCTRINE REQUIREMENTS:
--   - DOL Hub owns and writes to dol.*
--   - FK to cl.company_identity (external parent) OR company_unique_id TEXT
--   - No bloat - minimal columns from existing importers
-- ==============================================================================

-- ==============================================================================
-- PHASE 1: CREATE DOL SCHEMA
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS dol;

COMMENT ON SCHEMA dol IS
'DOL Filings Hub - Owned by barton-outreach-core.
Sub-hub of Outreach Program (child of CL).
Manages:
- Form 5500 filings (large plans)
- Form 5500-SF filings (small plans)
- Schedule A (insurance broker data)
- Renewal calendar (plan renewal dates)

Doctrine ID: 04.04.03
Core Metric: FILING_MATCH_RATE
GitHub: https://github.com/djb258/barton-outreach-core.git

AUTHORITY:
- CAN: Store DOL filings, match EINs, emit filing signals
- CANNOT: Mint company_unique_id (CL only), modify cl.* tables';

-- ==============================================================================
-- PHASE 2: CREATE FORM_5500 TABLE
-- ==============================================================================
-- Based on columns used in:
--   - hubs/dol-filings/imo/middle/importers/import_5500.py
--   - hubs/dol-filings/imo/middle/dol_hub.py
--   - hubs/dol-filings/imo/middle/ein_matcher.py
-- ==============================================================================

CREATE TABLE IF NOT EXISTS dol.form_5500 (
    -- Primary key
    filing_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Unique DOL identifier
    ack_id                  VARCHAR(255) NOT NULL UNIQUE,

    -- Company linkage (join to CL or outreach.company_target)
    company_unique_id       TEXT,  -- FK populated by EIN matching

    -- Core filing fields (from DOL data)
    sponsor_dfe_ein         VARCHAR(20) NOT NULL,
    sponsor_dfe_name        VARCHAR(500) NOT NULL,
    spons_dfe_dba_name      VARCHAR(500),

    -- Plan info
    plan_name               VARCHAR(500),
    plan_number             VARCHAR(20),
    plan_eff_date           VARCHAR(20),

    -- Address (for matching)
    spons_dfe_mail_us_city  VARCHAR(100),
    spons_dfe_mail_us_state VARCHAR(10),
    spons_dfe_mail_us_zip   VARCHAR(20),

    -- Participant counts (for signal emission)
    tot_active_partcp_cnt   INTEGER,
    tot_partcp_boy_cnt      INTEGER,

    -- Schedule indicators
    sch_a_attached_ind      VARCHAR(5),
    num_sch_a_attached_cnt  INTEGER,

    -- Admin info
    admin_name              VARCHAR(255),
    admin_ein               VARCHAR(20),

    -- Filing metadata
    form_plan_year_begin_date VARCHAR(20),
    form_year               VARCHAR(10),
    filing_status           VARCHAR(50),
    date_received           VARCHAR(30),

    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for EIN matching and lookups
CREATE INDEX IF NOT EXISTS idx_form_5500_ein
    ON dol.form_5500(sponsor_dfe_ein);
CREATE INDEX IF NOT EXISTS idx_form_5500_company
    ON dol.form_5500(company_unique_id) WHERE company_unique_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_form_5500_state_city
    ON dol.form_5500(spons_dfe_mail_us_state, spons_dfe_mail_us_city);
CREATE INDEX IF NOT EXISTS idx_form_5500_year
    ON dol.form_5500(form_year);
CREATE INDEX IF NOT EXISTS idx_form_5500_participants
    ON dol.form_5500(tot_active_partcp_cnt) WHERE tot_active_partcp_cnt >= 500;

COMMENT ON TABLE dol.form_5500 IS
'DOL.TABLE.001 | Form 5500 filings from Department of Labor.
Large plan filings (>=100 participants). Used for:
- EIN resolution to company_master
- Filing signals to BIT Engine
- Renewal calendar population';

COMMENT ON COLUMN dol.form_5500.filing_id IS
'DOL.5500.001 | Primary key - internal UUID for this filing record.';

COMMENT ON COLUMN dol.form_5500.ack_id IS
'DOL.5500.002 | DOL acknowledgment ID. Unique per filing. From DOL data.';

COMMENT ON COLUMN dol.form_5500.company_unique_id IS
'DOL.5500.003 | FK to CL company identity. Populated by EIN matching.
NULL until matched. DOCTRINE: Never mint - only receive from CL.';

COMMENT ON COLUMN dol.form_5500.sponsor_dfe_ein IS
'DOL.5500.004 | Employer Identification Number. Primary match key.';

-- ==============================================================================
-- PHASE 3: CREATE FORM_5500_SF TABLE (Small Plan Filings)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS dol.form_5500_sf (
    -- Primary key
    filing_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Unique DOL identifier
    ack_id                  VARCHAR(255) NOT NULL UNIQUE,

    -- Company linkage
    company_unique_id       TEXT,

    -- Core filing fields
    sponsor_dfe_ein         VARCHAR(20) NOT NULL,
    sponsor_dfe_name        VARCHAR(500) NOT NULL,
    spons_dfe_dba_name      VARCHAR(500),

    -- Plan info
    plan_name               VARCHAR(500),
    plan_number             VARCHAR(20),
    plan_eff_date           VARCHAR(20),

    -- Address
    spons_dfe_mail_us_city  VARCHAR(100),
    spons_dfe_mail_us_state VARCHAR(10),
    spons_dfe_mail_us_zip   VARCHAR(20),

    -- Participant counts (small plans <100)
    tot_partcp_boy_cnt      INTEGER,

    -- Filing metadata
    form_plan_year_begin_date VARCHAR(20),
    form_year               VARCHAR(10),
    filing_status           VARCHAR(50),

    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_form_5500_sf_ein
    ON dol.form_5500_sf(sponsor_dfe_ein);
CREATE INDEX IF NOT EXISTS idx_form_5500_sf_company
    ON dol.form_5500_sf(company_unique_id) WHERE company_unique_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_form_5500_sf_year
    ON dol.form_5500_sf(form_year);

COMMENT ON TABLE dol.form_5500_sf IS
'DOL.TABLE.002 | Form 5500-SF filings (short form for small plans).
Small plan filings (<100 participants). Same structure as Form 5500
but separate table for data isolation.';

-- ==============================================================================
-- PHASE 4: CREATE SCHEDULE_A TABLE
-- ==============================================================================
-- Based on columns used in:
--   - hubs/dol-filings/imo/middle/importers/import_schedule_a.py
--   - hubs/dol-filings/imo/middle/dol_hub.py (broker change detection)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS dol.schedule_a (
    -- Primary key
    schedule_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to parent Form 5500
    ack_id                  VARCHAR(255) NOT NULL,
    filing_id               UUID REFERENCES dol.form_5500(filing_id) ON DELETE SET NULL,

    -- Company linkage (denormalized for query performance)
    company_unique_id       TEXT,

    -- Insurance carrier info
    insurance_company_name  VARCHAR(500),
    insurance_company_ein   VARCHAR(20),
    insurance_company_phone_num VARCHAR(30),
    contract_number         VARCHAR(100),

    -- Coverage info
    covered_lives           INTEGER,

    -- Policy dates (for renewal calendar)
    policy_year_begin_date  VARCHAR(20),
    policy_year_end_date    VARCHAR(20),

    -- Plan year
    sch_a_plan_year_begin_date VARCHAR(20),
    sch_a_plan_year_end_date   VARCHAR(20),
    form_year               VARCHAR(10),

    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_schedule_a_ack
    ON dol.schedule_a(ack_id);
CREATE INDEX IF NOT EXISTS idx_schedule_a_company
    ON dol.schedule_a(company_unique_id) WHERE company_unique_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_schedule_a_carrier
    ON dol.schedule_a(insurance_company_name);
CREATE INDEX IF NOT EXISTS idx_schedule_a_year
    ON dol.schedule_a(form_year);
CREATE INDEX IF NOT EXISTS idx_schedule_a_policy_end
    ON dol.schedule_a(policy_year_end_date);

COMMENT ON TABLE dol.schedule_a IS
'DOL.TABLE.003 | Schedule A insurance/broker data from Form 5500.
Used for:
- Broker change detection (YoY comparison)
- Renewal calendar population
- Insurance carrier signals to BIT Engine';

COMMENT ON COLUMN dol.schedule_a.insurance_company_name IS
'DOL.SCHA.001 | Insurance carrier name. Used for broker change detection.
Normalized for YoY comparison.';

-- ==============================================================================
-- PHASE 5: CREATE RENEWAL_CALENDAR TABLE
-- ==============================================================================
-- Derived from Schedule A policy dates
-- ==============================================================================

CREATE TABLE IF NOT EXISTS dol.renewal_calendar (
    -- Primary key
    renewal_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Company linkage
    company_unique_id       TEXT NOT NULL,

    -- Source reference
    schedule_id             UUID REFERENCES dol.schedule_a(schedule_id) ON DELETE SET NULL,
    filing_id               UUID REFERENCES dol.form_5500(filing_id) ON DELETE SET NULL,

    -- Renewal info
    renewal_month           INTEGER CHECK (renewal_month >= 1 AND renewal_month <= 12),
    renewal_year            INTEGER,
    renewal_date            DATE,

    -- Plan info
    plan_name               VARCHAR(500),
    carrier_name            VARCHAR(500),

    -- Status
    is_upcoming             BOOLEAN NOT NULL DEFAULT TRUE,
    days_until_renewal      INTEGER,

    -- Timestamps
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one renewal per company per year
    CONSTRAINT uq_renewal_company_year UNIQUE (company_unique_id, renewal_year)
);

CREATE INDEX IF NOT EXISTS idx_renewal_company
    ON dol.renewal_calendar(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_renewal_date
    ON dol.renewal_calendar(renewal_date);
CREATE INDEX IF NOT EXISTS idx_renewal_upcoming
    ON dol.renewal_calendar(is_upcoming, renewal_date) WHERE is_upcoming = TRUE;
CREATE INDEX IF NOT EXISTS idx_renewal_month
    ON dol.renewal_calendar(renewal_month);

COMMENT ON TABLE dol.renewal_calendar IS
'DOL.TABLE.004 | Plan renewal calendar derived from Schedule A policy dates.
Used for:
- Renewal timing signals to BIT Engine
- Outreach campaign timing
- Funnel prioritization';

-- ==============================================================================
-- PHASE 6: AUTO-UPDATE TRIGGERS
-- ==============================================================================

-- Trigger function (reuse pattern from existing migrations)
CREATE OR REPLACE FUNCTION dol.trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all DOL tables
DROP TRIGGER IF EXISTS set_updated_at ON dol.form_5500;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON dol.form_5500
    FOR EACH ROW EXECUTE FUNCTION dol.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON dol.form_5500_sf;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON dol.form_5500_sf
    FOR EACH ROW EXECUTE FUNCTION dol.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON dol.schedule_a;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON dol.schedule_a
    FOR EACH ROW EXECUTE FUNCTION dol.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON dol.renewal_calendar;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON dol.renewal_calendar
    FOR EACH ROW EXECUTE FUNCTION dol.trigger_set_updated_at();

-- ==============================================================================
-- PHASE 7: VERIFICATION
-- ==============================================================================

DO $$
DECLARE
    v_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'dol';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'DOL Schema Migration Complete:';
    RAISE NOTICE '  Tables created: % (expected 4)', v_table_count;
    RAISE NOTICE '  - dol.form_5500';
    RAISE NOTICE '  - dol.form_5500_sf';
    RAISE NOTICE '  - dol.schedule_a';
    RAISE NOTICE '  - dol.renewal_calendar';
    RAISE NOTICE '========================================';

    IF v_table_count < 4 THEN
        RAISE WARNING 'Expected 4 tables, found %', v_table_count;
    END IF;
END $$;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- CREATED:
--   - dol schema
--   - 4 tables: form_5500, form_5500_sf, schedule_a, renewal_calendar
--   - 16 indexes (lookup + FK optimization)
--   - 4 auto-update triggers
--
-- DOCTRINE COMPLIANCE:
--   - company_unique_id is TEXT (join to CL, not FK constraint per existing pattern)
--   - Minimal columns from existing importers only
--   - No analytics tables, no derived fields
-- ==============================================================================
