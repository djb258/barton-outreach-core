-- ============================================================================
-- Clay.com Intake Tables Migration
-- ============================================================================
-- Purpose: Create intake tables for Clay.com direct Postgres integration
-- Date: 2025-11-27
--
-- Clay connects directly to Neon and writes enriched data to these tables.
-- Two separate tables: one for companies, one for people.
-- ============================================================================

BEGIN;

-- ============================================================================
-- TABLE 1: intake.company_raw_from_clay
-- ============================================================================
-- Receives enriched company data from Clay
-- Clay reads from marketing.company_master, enriches, writes here

CREATE TABLE IF NOT EXISTS intake.company_raw_from_clay (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Reference to source record
    company_unique_id TEXT NOT NULL,

    -- Original data sent to Clay
    company_name TEXT NOT NULL,
    website_original TEXT,
    city TEXT,
    state TEXT,

    -- Enriched data from Clay
    website_enriched TEXT,
    employee_count_enriched INT,
    industry_enriched TEXT,
    linkedin_company_url TEXT,
    founded_year INT,
    company_type TEXT,  -- public, private, nonprofit, etc.
    revenue_range TEXT,  -- e.g., "$10M-$50M"
    tech_stack JSONB,  -- Array of technologies detected
    funding_total TEXT,
    funding_stage TEXT,  -- seed, series_a, series_b, etc.
    headquarters_address TEXT,

    -- Clay metadata
    clay_table_id TEXT,  -- Clay's internal table reference
    clay_row_id TEXT,  -- Clay's internal row reference
    clay_enriched_at TIMESTAMPTZ,
    clay_credits_used INT DEFAULT 0,
    clay_providers_used JSONB,  -- Which enrichment providers were used

    -- Processing status
    enrichment_status TEXT DEFAULT 'received' CHECK (enrichment_status IN (
        'received', 'processing', 'promoted', 'failed', 'duplicate'
    )),
    promoted_to_master_at TIMESTAMPTZ,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for company_raw_from_clay
CREATE INDEX IF NOT EXISTS idx_clay_company_unique_id
    ON intake.company_raw_from_clay(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_clay_company_status
    ON intake.company_raw_from_clay(enrichment_status);

CREATE INDEX IF NOT EXISTS idx_clay_company_created
    ON intake.company_raw_from_clay(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_clay_company_not_promoted
    ON intake.company_raw_from_clay(enrichment_status)
    WHERE enrichment_status = 'received';

-- ============================================================================
-- TABLE 2: intake.people_raw_from_clay
-- ============================================================================
-- Receives enriched people/contact data from Clay
-- Clay reads from marketing.people_master or company_slot, enriches, writes here

CREATE TABLE IF NOT EXISTS intake.people_raw_from_clay (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Reference to source records
    person_unique_id TEXT,  -- May be NULL if new person discovered
    company_unique_id TEXT NOT NULL,
    slot_type TEXT,  -- CEO, CFO, HR (if from company_slot)

    -- Original data sent to Clay
    full_name_original TEXT,
    title_original TEXT,
    linkedin_url_original TEXT,
    email_original TEXT,

    -- Enriched data from Clay
    full_name_enriched TEXT,
    first_name TEXT,
    last_name TEXT,
    title_enriched TEXT,
    title_normalized TEXT,  -- Standardized title (CEO, CFO, etc.)

    -- Contact enrichment
    work_email TEXT,
    work_email_verified BOOLEAN,
    work_email_verification_date TIMESTAMPTZ,
    personal_email TEXT,
    linkedin_url_enriched TEXT,
    phone_direct TEXT,
    phone_mobile TEXT,
    phone_verified BOOLEAN,

    -- Professional info
    linkedin_headline TEXT,
    linkedin_summary TEXT,
    years_in_role INT,
    years_at_company INT,
    previous_companies JSONB,  -- Array of previous employers
    education JSONB,  -- Array of education entries
    skills JSONB,  -- Array of skills

    -- Clay metadata
    clay_table_id TEXT,
    clay_row_id TEXT,
    clay_enriched_at TIMESTAMPTZ,
    clay_credits_used INT DEFAULT 0,
    clay_providers_used JSONB,  -- Which providers found what

    -- Processing status
    enrichment_status TEXT DEFAULT 'received' CHECK (enrichment_status IN (
        'received', 'processing', 'promoted', 'failed', 'duplicate', 'no_match'
    )),
    promoted_to_master_at TIMESTAMPTZ,
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for people_raw_from_clay
CREATE INDEX IF NOT EXISTS idx_clay_people_person_id
    ON intake.people_raw_from_clay(person_unique_id);

CREATE INDEX IF NOT EXISTS idx_clay_people_company_id
    ON intake.people_raw_from_clay(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_clay_people_status
    ON intake.people_raw_from_clay(enrichment_status);

CREATE INDEX IF NOT EXISTS idx_clay_people_created
    ON intake.people_raw_from_clay(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_clay_people_slot_type
    ON intake.people_raw_from_clay(slot_type)
    WHERE slot_type IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_clay_people_work_email
    ON intake.people_raw_from_clay(work_email)
    WHERE work_email IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_clay_people_not_promoted
    ON intake.people_raw_from_clay(enrichment_status)
    WHERE enrichment_status = 'received';

-- ============================================================================
-- AUTO-UPDATE TRIGGERS
-- ============================================================================

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION intake.update_clay_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for company_raw_from_clay
DROP TRIGGER IF EXISTS trg_clay_company_updated ON intake.company_raw_from_clay;
CREATE TRIGGER trg_clay_company_updated
    BEFORE UPDATE ON intake.company_raw_from_clay
    FOR EACH ROW
    EXECUTE FUNCTION intake.update_clay_timestamp();

-- Trigger for people_raw_from_clay
DROP TRIGGER IF EXISTS trg_clay_people_updated ON intake.people_raw_from_clay;
CREATE TRIGGER trg_clay_people_updated
    BEFORE UPDATE ON intake.people_raw_from_clay
    FOR EACH ROW
    EXECUTE FUNCTION intake.update_clay_timestamp();

-- ============================================================================
-- VIEWS FOR CLAY INTEGRATION
-- ============================================================================

-- View: Companies ready for Clay enrichment
-- Clay can SELECT from this view to get companies needing enrichment
CREATE OR REPLACE VIEW intake.v_companies_for_clay AS
SELECT
    cm.company_unique_id,
    cm.company_name,
    cm.website_url,
    cm.address_city,
    cm.address_state,
    cm.employee_count,
    cm.industry,
    cm.linkedin_url AS company_linkedin,
    cm.created_at,
    cm.updated_at
FROM marketing.company_master cm
LEFT JOIN intake.company_raw_from_clay crc
    ON cm.company_unique_id = crc.company_unique_id
    AND crc.enrichment_status IN ('received', 'promoted')
    AND crc.created_at > NOW() - INTERVAL '30 days'  -- Re-enrich after 30 days
WHERE crc.id IS NULL  -- Not recently enriched
ORDER BY cm.created_at DESC;

-- View: People ready for Clay enrichment
-- Clay can SELECT from this view to get people needing enrichment
CREATE OR REPLACE VIEW intake.v_people_for_clay AS
SELECT
    pm.unique_id AS person_unique_id,
    pm.company_unique_id,
    cs.slot_type,
    pm.full_name,
    pm.title,
    pm.linkedin_url,
    pm.email,
    pm.created_at,
    pm.updated_at
FROM marketing.people_master pm
LEFT JOIN marketing.company_slot cs
    ON pm.unique_id = cs.person_unique_id
LEFT JOIN intake.people_raw_from_clay prc
    ON pm.unique_id = prc.person_unique_id
    AND prc.enrichment_status IN ('received', 'promoted')
    AND prc.created_at > NOW() - INTERVAL '30 days'
WHERE prc.id IS NULL
ORDER BY pm.created_at DESC;

-- View: Clay enrichment stats
CREATE OR REPLACE VIEW intake.v_clay_enrichment_stats AS
SELECT
    'companies' AS table_type,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE enrichment_status = 'received') AS pending,
    COUNT(*) FILTER (WHERE enrichment_status = 'promoted') AS promoted,
    COUNT(*) FILTER (WHERE enrichment_status = 'failed') AS failed,
    SUM(clay_credits_used) AS total_credits_used,
    MAX(created_at) AS last_enrichment
FROM intake.company_raw_from_clay
UNION ALL
SELECT
    'people' AS table_type,
    COUNT(*) AS total_records,
    COUNT(*) FILTER (WHERE enrichment_status = 'received') AS pending,
    COUNT(*) FILTER (WHERE enrichment_status = 'promoted') AS promoted,
    COUNT(*) FILTER (WHERE enrichment_status = 'failed') AS failed,
    SUM(clay_credits_used) AS total_credits_used,
    MAX(created_at) AS last_enrichment
FROM intake.people_raw_from_clay;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE intake.company_raw_from_clay IS
    'Raw company data enriched by Clay.com - staging before promotion to company_master';

COMMENT ON TABLE intake.people_raw_from_clay IS
    'Raw people/contact data enriched by Clay.com - staging before promotion to people_master';

COMMENT ON VIEW intake.v_companies_for_clay IS
    'Companies eligible for Clay enrichment (not enriched in last 30 days)';

COMMENT ON VIEW intake.v_people_for_clay IS
    'People eligible for Clay enrichment (not enriched in last 30 days)';

COMMENT ON VIEW intake.v_clay_enrichment_stats IS
    'Summary statistics for Clay enrichment pipeline';

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================
-- Run these queries to verify the migration succeeded:
--
-- SELECT * FROM intake.v_clay_enrichment_stats;
-- SELECT COUNT(*) FROM intake.v_companies_for_clay;
-- SELECT COUNT(*) FROM intake.v_people_for_clay;
-- \d intake.company_raw_from_clay
-- \d intake.people_raw_from_clay
-- ============================================================================
