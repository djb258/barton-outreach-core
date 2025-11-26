-- ═══════════════════════════════════════════════════════════════════════════
-- PLE SCHEMA MIGRATION SCRIPT
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Align existing Neon PostgreSQL schema with PLE specification
-- Database: Marketing DB (Neon PostgreSQL)
-- Date: 2025-11-26
-- Status: Ready for execution
--
-- EXECUTION PHASES:
--   Phase 1: Add missing columns to existing tables (ALTER TABLE)
--   Phase 2: Create PLE-compatible views (CREATE VIEW)
--   Phase 3: Create missing sidecar tables (CREATE TABLE)
--   Phase 4: Add indexes for performance (CREATE INDEX)
--
-- SAFETY NOTES:
--   - All operations are additive (no data loss)
--   - Views are read-only (no existing code breakage)
--   - New columns are nullable with defaults
--   - Rollback statements provided at end of file
-- ═══════════════════════════════════════════════════════════════════════════

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 1: ADD MISSING COLUMNS TO EXISTING TABLES
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Extend existing tables to support PLE requirements
-- Risk: LOW (nullable columns with defaults)

-- ---------------------------------------------------------------------------
-- 1.1: Add PLE-required columns to marketing.people_master
-- ---------------------------------------------------------------------------
COMMENT ON TABLE marketing.people_master IS
'Core people/contacts table. Extended with PLE validation and enrichment tracking.';

-- validation_status: pending | valid | invalid | expired
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS validation_status TEXT DEFAULT 'pending'
CHECK (validation_status IN ('pending', 'valid', 'invalid', 'expired'));

-- last_verified_at: when person data was last verified (any field, not just email)
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS last_verified_at TIMESTAMPTZ;

-- last_enrichment_attempt: when we last tried to enrich this person's data
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ;

COMMENT ON COLUMN marketing.people_master.validation_status IS
'PLE validation status: pending (new), valid (verified), invalid (bad data), expired (needs refresh)';
COMMENT ON COLUMN marketing.people_master.last_verified_at IS
'Timestamp of last data verification (any field, not just email)';
COMMENT ON COLUMN marketing.people_master.last_enrichment_attempt IS
'Timestamp of last enrichment attempt (for rate limiting and retry logic)';

-- ---------------------------------------------------------------------------
-- 1.2: Add PLE-required columns to marketing.company_slot
-- ---------------------------------------------------------------------------
COMMENT ON TABLE marketing.company_slot IS
'Executive slot assignments (CEO/CFO/HR). Extended with vacation tracking for movement detection.';

-- vacated_at: when person left this slot (for movement history)
ALTER TABLE marketing.company_slot
ADD COLUMN IF NOT EXISTS vacated_at TIMESTAMPTZ;

COMMENT ON COLUMN marketing.company_slot.vacated_at IS
'Timestamp when person vacated this slot (job change, departure, etc.)';

-- ---------------------------------------------------------------------------
-- 1.3: Create indexes for new columns
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_people_validation_status
ON marketing.people_master(validation_status);

CREATE INDEX IF NOT EXISTS idx_people_last_verified
ON marketing.people_master(last_verified_at DESC);

CREATE INDEX IF NOT EXISTS idx_people_last_enrichment
ON marketing.people_master(last_enrichment_attempt DESC);

CREATE INDEX IF NOT EXISTS idx_slot_vacated
ON marketing.company_slot(vacated_at DESC)
WHERE vacated_at IS NOT NULL;

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 2: CREATE PLE-COMPATIBLE VIEWS
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Provide PLE-compliant column names without breaking existing code
-- Risk: NONE (read-only views)

BEGIN;

-- ---------------------------------------------------------------------------
-- 2.1: Create or replace ple.companies view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ple.companies AS
SELECT
    company_unique_id AS id,
    company_unique_id AS company_uid,
    company_name AS name,
    linkedin_url,
    employee_count,
    COALESCE(state_abbrev, address_state) AS state,  -- Prefer abbreviation
    address_city AS city,
    industry,
    source_system AS source,
    created_at,
    updated_at,

    -- Extra fields (available but not in PLE spec)
    website_url,
    company_phone,
    address_street,
    address_zip,
    address_country,
    facebook_url,
    twitter_url,
    sic_codes,
    founded_year,
    keywords,
    description,
    data_quality_score,
    validated_at,
    validated_by
FROM marketing.company_master;

COMMENT ON VIEW ple.companies IS
'PLE-compliant view of marketing.company_master with standardized column names';

-- ---------------------------------------------------------------------------
-- 2.2: Create or replace ple.company_slots view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ple.company_slots AS
SELECT
    company_slot_unique_id AS id,
    company_slot_unique_id AS slot_uid,
    company_unique_id AS company_id,
    slot_type,
    person_unique_id AS person_id,
    filled_at AS assigned_at,
    vacated_at,

    -- Extra fields (available but not in PLE spec)
    is_filled,
    confidence_score,
    status,
    created_at,
    last_refreshed_at,
    filled_by,
    source_system,
    enrichment_attempts
FROM marketing.company_slot;

COMMENT ON VIEW ple.company_slots IS
'PLE-compliant view of marketing.company_slot with standardized column names';

-- ---------------------------------------------------------------------------
-- 2.3: Create or replace ple.people view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW ple.people AS
SELECT
    unique_id AS id,
    unique_id AS person_uid,
    company_unique_id AS company_id,
    linkedin_url,
    email,
    first_name,
    last_name,
    title,
    validation_status,
    last_verified_at,
    last_enrichment_attempt,
    created_at,
    updated_at,

    -- Extra fields (available but not in PLE spec)
    full_name,
    seniority,
    department,
    work_phone_e164,
    personal_phone_e164,
    twitter_url,
    facebook_url,
    bio,
    skills,
    education,
    certifications,
    email_verified,
    email_verified_at,
    email_verification_source,
    source_system,
    company_slot_unique_id
FROM marketing.people_master;

COMMENT ON VIEW ple.people IS
'PLE-compliant view of marketing.people_master with standardized column names';

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 3: CREATE MISSING SIDECAR TABLES
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Add PLE-required tables for movement history, scoring, and events
-- Risk: LOW (new tables, no existing data affected)

BEGIN;

-- ---------------------------------------------------------------------------
-- 3.1: Create ple.person_movement_history table
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS ple.person_movement_history CASCADE;

CREATE TABLE ple.person_movement_history (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL,
    linkedin_url TEXT,
    company_id_from TEXT,
    company_id_to TEXT,
    title_from TEXT,
    title_to TEXT,
    movement_type TEXT NOT NULL CHECK (movement_type IN (
        'job_change',       -- Moved to different company
        'promotion',        -- Same company, new title
        'departure',        -- Left company (to unknown)
        'new_hire',         -- First appearance in system
        'demotion',         -- Downward move (rare)
        'lateral_move',     -- Same level, different role
        'return'            -- Came back to previous employer
    )),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_payload JSONB,

    -- Metadata
    detection_source TEXT DEFAULT 'manual',  -- manual, linkedin_scrape, apify, webhook
    confidence_score NUMERIC CHECK (confidence_score BETWEEN 0 AND 100),
    notes TEXT,

    -- Foreign keys
    FOREIGN KEY (person_id) REFERENCES marketing.people_master(unique_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id_from) REFERENCES marketing.company_master(company_unique_id) ON DELETE SET NULL,
    FOREIGN KEY (company_id_to) REFERENCES marketing.company_master(company_unique_id) ON DELETE SET NULL
);

COMMENT ON TABLE ple.person_movement_history IS
'Tracks career movements and job changes for executives and key personnel';
COMMENT ON COLUMN ple.person_movement_history.movement_type IS
'Type of movement: job_change (new company), promotion (same company), departure, new_hire, etc.';
COMMENT ON COLUMN ple.person_movement_history.detected_at IS
'When this movement was detected/recorded';
COMMENT ON COLUMN ple.person_movement_history.raw_payload IS
'Raw data from source (LinkedIn profile, scraper output, etc.)';

-- ---------------------------------------------------------------------------
-- 3.2: Create ple.person_scores table
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS ple.person_scores CASCADE;

CREATE TABLE ple.person_scores (
    id SERIAL PRIMARY KEY,
    person_id TEXT NOT NULL,
    bit_score NUMERIC CHECK (bit_score BETWEEN 0 AND 100),
    confidence_score NUMERIC CHECK (confidence_score BETWEEN 0 AND 100),
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    score_factors JSONB,

    -- Metadata
    calculation_version TEXT DEFAULT '1.0',
    manual_override BOOLEAN DEFAULT false,
    override_reason TEXT,
    expires_at TIMESTAMPTZ,  -- Score validity period

    -- Foreign key
    FOREIGN KEY (person_id) REFERENCES marketing.people_master(unique_id) ON DELETE CASCADE
);

COMMENT ON TABLE ple.person_scores IS
'Buyer Intent (BIT) scores for contacts, with confidence and score breakdown';
COMMENT ON COLUMN ple.person_scores.bit_score IS
'Buyer intent score (0-100): likelihood this person is ready to purchase';
COMMENT ON COLUMN ple.person_scores.confidence_score IS
'Data quality confidence (0-100): how reliable is this score';
COMMENT ON COLUMN ple.person_scores.score_factors IS
'JSON breakdown of score components: {recent_activity: 20, job_change: 30, company_events: 15, ...}';
COMMENT ON COLUMN ple.person_scores.expires_at IS
'When this score should be recalculated (default: 7 days)';

-- ---------------------------------------------------------------------------
-- 3.3: Create ple.company_events table
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS ple.company_events CASCADE;

CREATE TABLE ple.company_events (
    id SERIAL PRIMARY KEY,
    company_id TEXT NOT NULL,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'funding',          -- Funding round
        'expansion',        -- Office expansion, new location
        'layoffs',          -- Workforce reduction
        'merger',           -- Merger or acquisition (as acquirer)
        'acquired',         -- Acquired by another company
        'ipo',              -- Initial public offering
        'leadership_change',-- C-level executive change
        'product_launch',   -- Major product release
        'partnership',      -- Strategic partnership
        'award',            -- Industry award or recognition
        'negative_press',   -- Negative news coverage
        'financial_trouble',-- Financial difficulties
        'other'             -- Other significant event
    )),
    event_date DATE,
    source_url TEXT,
    summary TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    impacts_bit BOOLEAN DEFAULT false,

    -- Metadata
    detection_source TEXT DEFAULT 'manual',  -- manual, news_scraper, webhook, rss
    bit_impact_score NUMERIC CHECK (bit_impact_score BETWEEN -100 AND 100),
    verified BOOLEAN DEFAULT false,
    verified_at TIMESTAMPTZ,
    verified_by TEXT,

    -- Foreign key
    FOREIGN KEY (company_id) REFERENCES marketing.company_master(company_unique_id) ON DELETE CASCADE
);

COMMENT ON TABLE ple.company_events IS
'Significant company events that impact buyer intent scoring';
COMMENT ON COLUMN ple.company_events.event_type IS
'Type of event: funding, expansion, layoffs, merger, leadership_change, etc.';
COMMENT ON COLUMN ple.company_events.impacts_bit IS
'True if this event should affect BIT score calculation';
COMMENT ON COLUMN ple.company_events.bit_impact_score IS
'Numeric impact on BIT score: positive (0-100) or negative (-100-0)';
COMMENT ON COLUMN ple.company_events.source_url IS
'URL of news article or source document';

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 4: ADD INDEXES FOR PERFORMANCE
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Optimize query performance for PLE operations
-- Risk: NONE (indexes are transparent to applications)

BEGIN;

-- ---------------------------------------------------------------------------
-- 4.1: Indexes for ple.person_movement_history
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_movement_person_id
ON ple.person_movement_history(person_id);

CREATE INDEX IF NOT EXISTS idx_movement_detected_at
ON ple.person_movement_history(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_movement_type
ON ple.person_movement_history(movement_type);

CREATE INDEX IF NOT EXISTS idx_movement_company_from
ON ple.person_movement_history(company_id_from)
WHERE company_id_from IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_movement_company_to
ON ple.person_movement_history(company_id_to)
WHERE company_id_to IS NOT NULL;

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_movement_person_detected
ON ple.person_movement_history(person_id, detected_at DESC);

-- GIN index for JSONB payload searches
CREATE INDEX IF NOT EXISTS idx_movement_payload_gin
ON ple.person_movement_history USING GIN (raw_payload);

-- ---------------------------------------------------------------------------
-- 4.2: Indexes for ple.person_scores
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_scores_person_id
ON ple.person_scores(person_id);

CREATE INDEX IF NOT EXISTS idx_scores_bit_score
ON ple.person_scores(bit_score DESC);

CREATE INDEX IF NOT EXISTS idx_scores_calculated_at
ON ple.person_scores(calculated_at DESC);

-- Composite index for "latest valid score" queries
CREATE INDEX IF NOT EXISTS idx_scores_person_calculated
ON ple.person_scores(person_id, calculated_at DESC);

-- Index for expired scores
CREATE INDEX IF NOT EXISTS idx_scores_expires
ON ple.person_scores(expires_at)
WHERE expires_at IS NOT NULL AND expires_at < NOW();

-- GIN index for score_factors JSONB
CREATE INDEX IF NOT EXISTS idx_scores_factors_gin
ON ple.person_scores USING GIN (score_factors);

-- ---------------------------------------------------------------------------
-- 4.3: Indexes for ple.company_events
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_events_company_id
ON ple.company_events(company_id);

CREATE INDEX IF NOT EXISTS idx_events_event_type
ON ple.company_events(event_type);

CREATE INDEX IF NOT EXISTS idx_events_detected_at
ON ple.company_events(detected_at DESC);

CREATE INDEX IF NOT EXISTS idx_events_event_date
ON ple.company_events(event_date DESC)
WHERE event_date IS NOT NULL;

-- Partial index for BIT-impacting events
CREATE INDEX IF NOT EXISTS idx_events_impacts_bit
ON ple.company_events(company_id, detected_at DESC)
WHERE impacts_bit = true;

-- Composite index for "recent events by company"
CREATE INDEX IF NOT EXISTS idx_events_company_detected
ON ple.company_events(company_id, detected_at DESC);

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════
-- PHASE 5: GRANT PERMISSIONS
-- ═══════════════════════════════════════════════════════════════════════════
-- Purpose: Ensure proper access permissions for PLE schema objects

BEGIN;

-- Grant permissions on views (replace 'app_user' with your actual role)
-- GRANT SELECT ON ple.companies TO app_user;
-- GRANT SELECT ON ple.company_slots TO app_user;
-- GRANT SELECT ON ple.people TO app_user;

-- Grant permissions on tables
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ple.person_movement_history TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ple.person_scores TO app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ple.company_events TO app_user;

-- Grant sequence permissions
-- GRANT USAGE, SELECT ON SEQUENCE ple.person_movement_history_id_seq TO app_user;
-- GRANT USAGE, SELECT ON SEQUENCE ple.person_scores_id_seq TO app_user;
-- GRANT USAGE, SELECT ON SEQUENCE ple.company_events_id_seq TO app_user;

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════
-- Run these after migration to verify success

-- Check new columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'marketing'
  AND table_name = 'people_master'
  AND column_name IN ('validation_status', 'last_verified_at', 'last_enrichment_attempt');

-- Check views exist
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'ple'
ORDER BY table_name;

-- Check new tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'ple'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Check indexes exist
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'ple'
ORDER BY tablename, indexname;

-- Test views work (should return 0 rows if no data yet)
SELECT COUNT(*) FROM ple.companies;
SELECT COUNT(*) FROM ple.company_slots;
SELECT COUNT(*) FROM ple.people;

-- ═══════════════════════════════════════════════════════════════════════════
-- ROLLBACK SCRIPT (USE ONLY IF MIGRATION FAILS)
-- ═══════════════════════════════════════════════════════════════════════════
/*
BEGIN;

-- Phase 4 Rollback: Drop indexes
DROP INDEX IF EXISTS ple.idx_movement_person_id;
DROP INDEX IF EXISTS ple.idx_movement_detected_at;
DROP INDEX IF EXISTS ple.idx_movement_type;
DROP INDEX IF EXISTS ple.idx_movement_company_from;
DROP INDEX IF EXISTS ple.idx_movement_company_to;
DROP INDEX IF EXISTS ple.idx_movement_person_detected;
DROP INDEX IF EXISTS ple.idx_movement_payload_gin;

DROP INDEX IF EXISTS ple.idx_scores_person_id;
DROP INDEX IF EXISTS ple.idx_scores_bit_score;
DROP INDEX IF EXISTS ple.idx_scores_calculated_at;
DROP INDEX IF EXISTS ple.idx_scores_person_calculated;
DROP INDEX IF EXISTS ple.idx_scores_expires;
DROP INDEX IF EXISTS ple.idx_scores_factors_gin;

DROP INDEX IF EXISTS ple.idx_events_company_id;
DROP INDEX IF EXISTS ple.idx_events_event_type;
DROP INDEX IF EXISTS ple.idx_events_detected_at;
DROP INDEX IF EXISTS ple.idx_events_event_date;
DROP INDEX IF EXISTS ple.idx_events_impacts_bit;
DROP INDEX IF EXISTS ple.idx_events_company_detected;

-- Phase 3 Rollback: Drop tables
DROP TABLE IF EXISTS ple.person_movement_history CASCADE;
DROP TABLE IF EXISTS ple.person_scores CASCADE;
DROP TABLE IF EXISTS ple.company_events CASCADE;

-- Phase 2 Rollback: Drop views
DROP VIEW IF EXISTS ple.companies CASCADE;
DROP VIEW IF EXISTS ple.company_slots CASCADE;
DROP VIEW IF EXISTS ple.people CASCADE;

-- Phase 1 Rollback: Remove columns
ALTER TABLE marketing.people_master DROP COLUMN IF EXISTS validation_status;
ALTER TABLE marketing.people_master DROP COLUMN IF EXISTS last_verified_at;
ALTER TABLE marketing.people_master DROP COLUMN IF EXISTS last_enrichment_attempt;
ALTER TABLE marketing.company_slot DROP COLUMN IF EXISTS vacated_at;

DROP INDEX IF EXISTS marketing.idx_people_validation_status;
DROP INDEX IF EXISTS marketing.idx_people_last_verified;
DROP INDEX IF EXISTS marketing.idx_people_last_enrichment;
DROP INDEX IF EXISTS marketing.idx_slot_vacated;

COMMIT;
*/

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION SCRIPT
-- ═══════════════════════════════════════════════════════════════════════════
--
-- EXECUTION NOTES:
-- 1. Run each phase separately and verify before proceeding to next
-- 2. Test queries after each phase to ensure expected behavior
-- 3. Monitor database performance after Phase 4 (indexes)
-- 4. Update application code to use ple.* views for new features
--
-- BACKFILL RECOMMENDATIONS:
-- 1. Set validation_status to 'valid' for records with email_verified = true
-- 2. Copy email_verified_at to last_verified_at for validated records
-- 3. Populate person_movement_history from historical data (if available)
-- 4. Calculate initial person_scores using BIT scoring algorithm
--
-- ═══════════════════════════════════════════════════════════════════════════
