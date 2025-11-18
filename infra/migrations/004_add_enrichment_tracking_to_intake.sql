-- ============================================================================
-- MIGRATION 004: Add enrichment tracking to intake tables
-- ============================================================================
-- Purpose: Add enrichment attempt tracking, chronic_bad flag, and B2 storage tracking
-- Author: Claude Code
-- Date: 2025-11-18
-- Barton ID: 04.04.02.04.50000.004
-- ============================================================================

-- Add enrichment tracking fields to intake.company_raw_intake
-- ============================================================================

ALTER TABLE intake.company_raw_intake
ADD COLUMN IF NOT EXISTS apollo_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS enrichment_attempt INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS chronic_bad BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS enriched_by VARCHAR(255),
ADD COLUMN IF NOT EXISTS b2_file_path TEXT,
ADD COLUMN IF NOT EXISTS b2_uploaded_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS garage_bay VARCHAR(10),
ADD COLUMN IF NOT EXISTS validation_reasons TEXT;

-- ============================================================================
-- INDEXES for new columns
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_apollo_id
    ON intake.company_raw_intake(apollo_id);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_last_hash
    ON intake.company_raw_intake(last_hash);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_enrichment_attempt
    ON intake.company_raw_intake(enrichment_attempt);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_chronic_bad
    ON intake.company_raw_intake(chronic_bad);

CREATE INDEX IF NOT EXISTS idx_company_raw_intake_garage_bay
    ON intake.company_raw_intake(garage_bay);

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN intake.company_raw_intake.apollo_id IS
'Universal external anchor key from Apollo.io for enrichment tracking and reconciliation';

COMMENT ON COLUMN intake.company_raw_intake.last_hash IS
'SHA256 hash of company_name + domain + linkedin_url + apollo_id + timestamp for deduplication';

COMMENT ON COLUMN intake.company_raw_intake.enrichment_attempt IS
'Counter for enrichment attempts: 0 = not enriched, 1 = first attempt, 2 = second attempt (chronic_bad if still fails)';

COMMENT ON COLUMN intake.company_raw_intake.chronic_bad IS
'TRUE = failed validation 2+ times, needs manual review';

COMMENT ON COLUMN intake.company_raw_intake.b2_file_path IS
'Path to JSON file in Backblaze B2 storage (e.g., companies_bad/2025-11-18/company_12345.json)';

COMMENT ON COLUMN intake.company_raw_intake.last_enriched_at IS
'Timestamp of last enrichment by agent';

COMMENT ON COLUMN intake.company_raw_intake.enriched_by IS
'Name of agent that performed enrichment (e.g., firecrawl, apify, abacus, claude)';

COMMENT ON COLUMN intake.company_raw_intake.garage_bay IS
'Garage 2.0 bay assignment: bay_a (missing fields) or bay_b (contradictions)';

COMMENT ON COLUMN intake.company_raw_intake.validation_reasons IS
'Comma-separated list of validation failure reasons for tracking and debugging';

-- ============================================================================
-- END MIGRATION 004
-- ============================================================================
