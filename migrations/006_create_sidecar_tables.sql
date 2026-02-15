-- ============================================================================
-- Migration 006: Create Sidecar Tables for Optional Enrichment Data
-- ============================================================================
-- Purpose: Create marketing.company_sidecar and marketing.people_sidecar
--          tables to hold optional enrichment data that should not be part
--          of core validation schema (Clay tags, EIN, D&B, social profiles)
-- Author: Claude Code
-- Created: 2025-11-18
-- Barton ID: 04.04.02.04.50000.006
-- ============================================================================

-- ============================================================================
-- TABLE: marketing.company_sidecar
-- ============================================================================
-- Optional enrichment data for companies (EIN, D&B, Clay metadata)

CREATE TABLE IF NOT EXISTS marketing.company_sidecar (
    company_unique_id VARCHAR(50) PRIMARY KEY,
    ein_number VARCHAR(20),
    dun_and_bradstreet_number VARCHAR(20),
    clay_tags TEXT[],
    clay_segments TEXT[],
    enrichment_payload JSONB,
    last_enriched_at TIMESTAMP,
    enrichment_source TEXT,
    confidence_score NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key to company_master
    CONSTRAINT fk_company_sidecar_company
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE
);

-- Indexes for company_sidecar
CREATE INDEX IF NOT EXISTS idx_company_sidecar_ein ON marketing.company_sidecar(ein_number);
CREATE INDEX IF NOT EXISTS idx_company_sidecar_duns ON marketing.company_sidecar(dun_and_bradstreet_number);
CREATE INDEX IF NOT EXISTS idx_company_sidecar_enriched ON marketing.company_sidecar(last_enriched_at DESC);
CREATE INDEX IF NOT EXISTS idx_company_sidecar_source ON marketing.company_sidecar(enrichment_source);
CREATE INDEX IF NOT EXISTS idx_company_sidecar_confidence ON marketing.company_sidecar(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_company_sidecar_payload ON marketing.company_sidecar USING GIN (enrichment_payload);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_company_sidecar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER company_sidecar_updated_at
    BEFORE UPDATE ON marketing.company_sidecar
    FOR EACH ROW
    EXECUTE FUNCTION update_company_sidecar_updated_at();

-- Table and column comments
COMMENT ON TABLE marketing.company_sidecar IS 'Optional enrichment data for companies (EIN, D&B, Clay metadata) - not part of core validation';
COMMENT ON COLUMN marketing.company_sidecar.company_unique_id IS 'Foreign key to company_master (Barton ID: 04.04.01.XX.XXXXX.XXX)';
COMMENT ON COLUMN marketing.company_sidecar.ein_number IS 'Employer Identification Number (IRS tax ID)';
COMMENT ON COLUMN marketing.company_sidecar.dun_and_bradstreet_number IS 'Dun & Bradstreet DUNS number';
COMMENT ON COLUMN marketing.company_sidecar.clay_tags IS 'Array of Clay.com tags for categorization';
COMMENT ON COLUMN marketing.company_sidecar.clay_segments IS 'Array of Clay.com segments for grouping';
COMMENT ON COLUMN marketing.company_sidecar.enrichment_payload IS 'Full JSON payload from enrichment source (Clay, Apify, etc.)';
COMMENT ON COLUMN marketing.company_sidecar.last_enriched_at IS 'Timestamp of last enrichment update';
COMMENT ON COLUMN marketing.company_sidecar.enrichment_source IS 'Source of enrichment data (clay, apify, firecrawl, abacus, etc.)';
COMMENT ON COLUMN marketing.company_sidecar.confidence_score IS 'Data confidence score (0-100) from enrichment source';

-- ============================================================================
-- TABLE: marketing.people_sidecar
-- ============================================================================
-- Optional enrichment data for people (Clay insights, social profiles)

CREATE TABLE IF NOT EXISTS marketing.people_sidecar (
    person_unique_id VARCHAR(50) PRIMARY KEY,
    clay_insight_summary TEXT,
    clay_segments TEXT[],
    social_profiles JSONB,
    enrichment_payload JSONB,
    last_enriched_at TIMESTAMP,
    enrichment_source TEXT,
    confidence_score NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key to people_master
    CONSTRAINT fk_people_sidecar_person
        FOREIGN KEY (person_unique_id)
        REFERENCES marketing.people_master(unique_id)
        ON DELETE CASCADE
);

-- Indexes for people_sidecar
CREATE INDEX IF NOT EXISTS idx_people_sidecar_enriched ON marketing.people_sidecar(last_enriched_at DESC);
CREATE INDEX IF NOT EXISTS idx_people_sidecar_source ON marketing.people_sidecar(enrichment_source);
CREATE INDEX IF NOT EXISTS idx_people_sidecar_confidence ON marketing.people_sidecar(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_people_sidecar_social ON marketing.people_sidecar USING GIN (social_profiles);
CREATE INDEX IF NOT EXISTS idx_people_sidecar_payload ON marketing.people_sidecar USING GIN (enrichment_payload);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_people_sidecar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER people_sidecar_updated_at
    BEFORE UPDATE ON marketing.people_sidecar
    FOR EACH ROW
    EXECUTE FUNCTION update_people_sidecar_updated_at();

-- Table and column comments
COMMENT ON TABLE marketing.people_sidecar IS 'Optional enrichment data for people (Clay insights, social profiles) - not part of core validation';
COMMENT ON COLUMN marketing.people_sidecar.person_unique_id IS 'Foreign key to people_master (Barton ID: 04.04.02.XX.XXXXX.XXX)';
COMMENT ON COLUMN marketing.people_sidecar.clay_insight_summary IS 'Clay.com AI-generated insight summary about the person';
COMMENT ON COLUMN marketing.people_sidecar.clay_segments IS 'Array of Clay.com segments for grouping (e.g., "VP-Engineering", "Series-B-Founders")';
COMMENT ON COLUMN marketing.people_sidecar.social_profiles IS 'JSON object with social media profiles (Twitter, GitHub, personal website, etc.)';
COMMENT ON COLUMN marketing.people_sidecar.enrichment_payload IS 'Full JSON payload from enrichment source (Clay, Apify, LinkedIn scraper, etc.)';
COMMENT ON COLUMN marketing.people_sidecar.last_enriched_at IS 'Timestamp of last enrichment update';
COMMENT ON COLUMN marketing.people_sidecar.enrichment_source IS 'Source of enrichment data (clay, apify, linkedin_scraper, etc.)';
COMMENT ON COLUMN marketing.people_sidecar.confidence_score IS 'Data confidence score (0-100) from enrichment source';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 006 Complete:';
    RAISE NOTICE '  ✓ Created table: marketing.company_sidecar';
    RAISE NOTICE '  ✓ Created table: marketing.people_sidecar';
    RAISE NOTICE '  ✓ Created 6 indexes on company_sidecar';
    RAISE NOTICE '  ✓ Created 5 indexes on people_sidecar';
    RAISE NOTICE '  ✓ Created foreign key constraints';
    RAISE NOTICE '  ✓ Created auto-update triggers';
    RAISE NOTICE '  ✓ Added table and column comments';
END $$;
