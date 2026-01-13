-- ============================================================================
-- MIGRATION 003: Create intake.people_raw_intake table
-- ============================================================================
-- Purpose: Raw staging table for people data before validation
-- Author: Claude Code
-- Date: 2025-11-18
-- Barton ID: 04.04.02.04.50000.003
-- ============================================================================

-- Create intake.people_raw_intake table
-- This is the temporary staging area for people data
-- Goal: This table should be EMPTY when all processing is complete
-- ============================================================================

CREATE TABLE IF NOT EXISTS intake.people_raw_intake (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Person Identification
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    full_name VARCHAR(500),

    -- Contact Information
    email VARCHAR(500),
    work_phone VARCHAR(50),
    personal_phone VARCHAR(50),

    -- Job Information
    title VARCHAR(500),
    seniority VARCHAR(100),
    department VARCHAR(255),

    -- Company Association
    company_name VARCHAR(500),
    company_unique_id VARCHAR(100), -- FK to marketing.company_master

    -- Social & Web Presence
    linkedin_url TEXT,
    twitter_url TEXT,
    facebook_url TEXT,

    -- Professional Details
    bio TEXT,
    skills TEXT[],
    education TEXT,
    certifications TEXT,

    -- Location
    city VARCHAR(255),
    state VARCHAR(100),
    state_abbrev VARCHAR(2),
    country VARCHAR(100),

    -- Source Tracking
    source_system VARCHAR(100),     -- 'csv_upload', 'api_import', 'manual_entry', etc.
    source_record_id VARCHAR(255),  -- Original ID from source system
    import_batch_id VARCHAR(100),   -- Batch import identifier

    -- Validation Tracking
    validated BOOLEAN DEFAULT FALSE,
    validation_notes TEXT,
    validated_at TIMESTAMP,
    validated_by VARCHAR(255),      -- Script name or user

    -- Enrichment Tracking
    enrichment_attempt INTEGER DEFAULT 0,
    chronic_bad BOOLEAN DEFAULT FALSE,
    last_enriched_at TIMESTAMP,
    enriched_by VARCHAR(255),       -- Agent name

    -- B2 Storage Tracking
    b2_file_path TEXT,              -- Path in Backblaze B2
    b2_uploaded_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_email
    ON intake.people_raw_intake(email);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_linkedin
    ON intake.people_raw_intake(linkedin_url);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_company_id
    ON intake.people_raw_intake(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_validated
    ON intake.people_raw_intake(validated);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_enrichment_attempt
    ON intake.people_raw_intake(enrichment_attempt);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_chronic_bad
    ON intake.people_raw_intake(chronic_bad);

CREATE INDEX IF NOT EXISTS idx_people_raw_intake_import_batch
    ON intake.people_raw_intake(import_batch_id);

-- ============================================================================
-- AUTO-UPDATE TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION update_people_raw_intake_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER people_raw_intake_updated_at_trigger
    BEFORE UPDATE ON intake.people_raw_intake
    FOR EACH ROW
    EXECUTE FUNCTION update_people_raw_intake_updated_at();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE intake.people_raw_intake IS
'Temporary staging table for people data before validation and promotion to marketing.people_master. Goal: Keep this table empty by promoting valid records and enriching invalid ones.';

COMMENT ON COLUMN intake.people_raw_intake.validated IS
'TRUE = passed validation, ready for promotion. FALSE = failed validation, needs enrichment.';

COMMENT ON COLUMN intake.people_raw_intake.enrichment_attempt IS
'Counter for enrichment attempts: 0 = not enriched, 1 = first attempt, 2 = second attempt (chronic_bad if still fails)';

COMMENT ON COLUMN intake.people_raw_intake.chronic_bad IS
'TRUE = failed validation 2+ times, needs manual review';

COMMENT ON COLUMN intake.people_raw_intake.b2_file_path IS
'Path to JSON file in Backblaze B2 storage (e.g., people_bad/2025-11-18/person_12345.json)';

-- ============================================================================
-- END MIGRATION 003
-- ============================================================================
