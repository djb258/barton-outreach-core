-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-4FF7AE20
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Barton Doctrine Migration
-- File: create_person_history.sql
-- Purpose: Person History tracking tables for data provenance and deduplication
-- Requirements: Append-only structure with Barton ID compliance
-- MCP: All access via Composio bridge, no direct connections

-- SCHEMA: person_history
CREATE SCHEMA IF NOT EXISTS person_history;

-- History tracking table for person data discovery events
-- This table maintains a complete audit trail of when, where, and what data was discovered
-- Append-only design prevents data loss and maintains full provenance
CREATE TABLE IF NOT EXISTS person_history.discovery_log (
  -- Primary identifiers
  history_unique_id           TEXT PRIMARY KEY DEFAULT generate_barton_id(),    -- Barton ID for this history entry
  person_id                   TEXT NOT NULL,                                    -- FK to person master record (PER- or person_ prefix)

  -- Discovery metadata
  field                       TEXT NOT NULL,                                    -- Field that was enriched/discovered
  value_found                 TEXT NOT NULL,                                    -- The actual value discovered
  source                      TEXT NOT NULL,                                    -- Source of discovery (apify, millionverify, etc)

  -- Confidence and validation
  confidence_score            DECIMAL(3,2) NOT NULL DEFAULT 1.0,               -- 0.0 to 1.0 confidence level
  previous_value              TEXT,                                             -- Previous value if this is an update
  change_reason               TEXT,                                             -- Reason for change

  -- Process tracking
  process_id                  TEXT,                                             -- Process that discovered this information
  session_id                  TEXT,                                             -- Session grouping for related discoveries
  related_company_id          TEXT,                                             -- Associated company ID if applicable

  -- Timestamps (append-only, never updated)
  timestamp_found             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), -- When discovered
  created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), -- Record creation time

  -- Additional metadata
  metadata                    JSONB,                                            -- Source-specific metadata

  -- Constraints
  CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  CONSTRAINT chk_person_id_format CHECK (person_id ~ '^(PER-|person_).+'),
  CONSTRAINT chk_field_enum CHECK (field IN (
    'email', 'phone', 'linkedin_url', 'first_name', 'last_name', 'full_name',
    'title', 'department', 'seniority_level', 'company_email', 'personal_email',
    'work_phone', 'mobile_phone', 'social_profiles', 'bio', 'skills', 'education',
    'experience', 'location', 'timezone', 'profile_picture', 'contact_preference',
    'email_status', 'phone_status', 'engagement_score', 'lead_score'
  )),
  CONSTRAINT chk_source_enum CHECK (source IN (
    'apify', 'millionverify', 'lindy', 'manual_adjust', 'apollo', 'clearbit',
    'hunter_io', 'enrichment_api', 'linkedin_scraper', 'people_scraper',
    'email_verifier', 'phone_verifier', 'social_scraper', 'manual_input',
    'csv_import', 'api_integration', 'lead_scoring_engine'
  )),
  CONSTRAINT chk_change_reason_enum CHECK (change_reason IS NULL OR change_reason IN (
    'initial_discovery', 'enrichment_update', 'correction', 'verification',
    'manual_override', 'data_refresh', 'source_upgrade'
  ))
);

-- Indexes for efficient querying
CREATE INDEX idx_person_history_person_id ON person_history.discovery_log(person_id);
CREATE INDEX idx_person_history_person_field ON person_history.discovery_log(person_id, field);
CREATE INDEX idx_person_history_timestamp ON person_history.discovery_log(timestamp_found);
CREATE INDEX idx_person_history_source ON person_history.discovery_log(source);
CREATE INDEX idx_person_history_process ON person_history.discovery_log(process_id);
CREATE INDEX idx_person_history_confidence ON person_history.discovery_log(field, confidence_score);
CREATE INDEX idx_person_history_session ON person_history.discovery_log(session_id);
CREATE INDEX idx_person_history_company ON person_history.discovery_log(related_company_id);

-- Composite index for latest value queries
CREATE INDEX idx_person_history_latest ON person_history.discovery_log(person_id, field, timestamp_found DESC);

-- JSONB index for metadata queries
CREATE INDEX idx_person_history_metadata ON person_history.discovery_log USING GIN(metadata);

-- Comments for documentation
COMMENT ON TABLE person_history.discovery_log IS 'Append-only history tracking for person data discovery events';
COMMENT ON COLUMN person_history.discovery_log.history_unique_id IS 'Barton ID for this history entry';
COMMENT ON COLUMN person_history.discovery_log.person_id IS 'Foreign key to person master record';
COMMENT ON COLUMN person_history.discovery_log.field IS 'Field name that was enriched/discovered';
COMMENT ON COLUMN person_history.discovery_log.value_found IS 'The actual value that was discovered';
COMMENT ON COLUMN person_history.discovery_log.source IS 'Source system that discovered this information';
COMMENT ON COLUMN person_history.discovery_log.confidence_score IS 'Confidence level of discovered information (0.0-1.0)';
COMMENT ON COLUMN person_history.discovery_log.timestamp_found IS 'When this information was discovered';
COMMENT ON COLUMN person_history.discovery_log.related_company_id IS 'Associated company ID for person-company relationships';
COMMENT ON COLUMN person_history.discovery_log.metadata IS 'Additional source-specific metadata in JSON format';

-- View for latest discovered values (most recent entry per person/field)
CREATE OR REPLACE VIEW person_history.latest_discoveries AS
SELECT DISTINCT ON (person_id, field)
    person_id,
    field,
    value_found,
    source,
    confidence_score,
    timestamp_found,
    process_id,
    related_company_id,
    metadata
FROM person_history.discovery_log
ORDER BY person_id, field, timestamp_found DESC;

COMMENT ON VIEW person_history.latest_discoveries IS 'Latest discovered value for each person field combination';

-- Function to get person discovery history
CREATE OR REPLACE FUNCTION person_history.get_field_history(
    p_person_id TEXT,
    p_field TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    history_unique_id TEXT,
    field TEXT,
    value_found TEXT,
    source TEXT,
    confidence_score DECIMAL,
    timestamp_found TIMESTAMP WITH TIME ZONE,
    previous_value TEXT,
    change_reason TEXT,
    related_company_id TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dl.history_unique_id,
        dl.field,
        dl.value_found,
        dl.source,
        dl.confidence_score,
        dl.timestamp_found,
        dl.previous_value,
        dl.change_reason,
        dl.related_company_id
    FROM person_history.discovery_log dl
    WHERE dl.person_id = p_person_id
    AND (p_field IS NULL OR dl.field = p_field)
    ORDER BY dl.timestamp_found DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION person_history.get_field_history IS 'Retrieve history entries for a person, optionally filtered by field';

-- Function to check if a field has been discovered recently
CREATE OR REPLACE FUNCTION person_history.check_recent_discovery(
    p_person_id TEXT,
    p_field TEXT,
    p_hours_threshold INTEGER DEFAULT 24
)
RETURNS BOOLEAN AS $$
DECLARE
    discovery_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO discovery_count
    FROM person_history.discovery_log
    WHERE person_id = p_person_id
    AND field = p_field
    AND timestamp_found > NOW() - INTERVAL '1 hour' * p_hours_threshold;

    RETURN discovery_count > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION person_history.check_recent_discovery IS 'Check if a field was discovered within the specified time threshold';

-- Function to get person discovery stats by company
CREATE OR REPLACE FUNCTION person_history.get_company_discovery_stats(
    p_company_id TEXT,
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    person_id TEXT,
    total_discoveries INTEGER,
    unique_fields INTEGER,
    latest_discovery TIMESTAMP WITH TIME ZONE,
    top_source TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dl.person_id,
        COUNT(*)::INTEGER as total_discoveries,
        COUNT(DISTINCT dl.field)::INTEGER as unique_fields,
        MAX(dl.timestamp_found) as latest_discovery,
        MODE() WITHIN GROUP (ORDER BY dl.source) as top_source
    FROM person_history.discovery_log dl
    WHERE dl.related_company_id = p_company_id
    AND dl.timestamp_found > NOW() - INTERVAL '1 day' * p_days_back
    GROUP BY dl.person_id
    ORDER BY total_discoveries DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION person_history.get_company_discovery_stats IS 'Get discovery statistics for people associated with a company';