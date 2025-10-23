-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-3FCA4296
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Barton Doctrine Migration
-- File: create_company_history.sql
-- Purpose: Company History tracking tables for data provenance and deduplication
-- Requirements: Append-only structure with Barton ID compliance
-- MCP: All access via Composio bridge, no direct connections

-- SCHEMA: company_history
CREATE SCHEMA IF NOT EXISTS company_history;

-- History tracking table for company data discovery events
-- This table maintains a complete audit trail of when, where, and what data was discovered
-- Append-only design prevents data loss and maintains full provenance
CREATE TABLE IF NOT EXISTS company_history.discovery_log (
  -- Primary identifiers
  history_unique_id           TEXT PRIMARY KEY DEFAULT generate_barton_id(),    -- Barton ID for this history entry
  company_id                  TEXT NOT NULL,                                    -- FK to company master record (CMP- or company_ prefix)

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

  -- Timestamps (append-only, never updated)
  timestamp_found             TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), -- When discovered
  created_at                  TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), -- Record creation time

  -- Additional metadata
  metadata                    JSONB,                                            -- Source-specific metadata

  -- Constraints
  CONSTRAINT chk_confidence_score CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
  CONSTRAINT chk_company_id_format CHECK (company_id ~ '^(CMP-|company_).+'),
  CONSTRAINT chk_field_enum CHECK (field IN (
    'domain', 'email', 'phone', 'linkedin_url', 'company_size', 'industry',
    'address', 'description', 'logo_url', 'website', 'founded_year', 'revenue',
    'employees', 'technologies', 'funding', 'headquarters', 'subsidiaries',
    'social_media', 'contact_email', 'sales_email', 'support_email'
  )),
  CONSTRAINT chk_source_enum CHECK (source IN (
    'apify', 'millionverify', 'lindy', 'manual_adjust', 'apollo', 'clearbit',
    'hunter_io', 'enrichment_api', 'linkedin_scraper', 'company_scraper',
    'domain_analyzer', 'email_finder', 'web_scraper', 'manual_input',
    'csv_import', 'api_integration'
  )),
  CONSTRAINT chk_change_reason_enum CHECK (change_reason IS NULL OR change_reason IN (
    'initial_discovery', 'enrichment_update', 'correction', 'verification',
    'manual_override', 'data_refresh', 'source_upgrade'
  ))
);

-- Indexes for efficient querying
CREATE INDEX idx_company_history_company_id ON company_history.discovery_log(company_id);
CREATE INDEX idx_company_history_company_field ON company_history.discovery_log(company_id, field);
CREATE INDEX idx_company_history_timestamp ON company_history.discovery_log(timestamp_found);
CREATE INDEX idx_company_history_source ON company_history.discovery_log(source);
CREATE INDEX idx_company_history_process ON company_history.discovery_log(process_id);
CREATE INDEX idx_company_history_confidence ON company_history.discovery_log(field, confidence_score);
CREATE INDEX idx_company_history_session ON company_history.discovery_log(session_id);

-- Composite index for latest value queries
CREATE INDEX idx_company_history_latest ON company_history.discovery_log(company_id, field, timestamp_found DESC);

-- JSONB index for metadata queries
CREATE INDEX idx_company_history_metadata ON company_history.discovery_log USING GIN(metadata);

-- Comments for documentation
COMMENT ON TABLE company_history.discovery_log IS 'Append-only history tracking for company data discovery events';
COMMENT ON COLUMN company_history.discovery_log.history_unique_id IS 'Barton ID for this history entry';
COMMENT ON COLUMN company_history.discovery_log.company_id IS 'Foreign key to company master record';
COMMENT ON COLUMN company_history.discovery_log.field IS 'Field name that was enriched/discovered';
COMMENT ON COLUMN company_history.discovery_log.value_found IS 'The actual value that was discovered';
COMMENT ON COLUMN company_history.discovery_log.source IS 'Source system that discovered this information';
COMMENT ON COLUMN company_history.discovery_log.confidence_score IS 'Confidence level of discovered information (0.0-1.0)';
COMMENT ON COLUMN company_history.discovery_log.timestamp_found IS 'When this information was discovered';
COMMENT ON COLUMN company_history.discovery_log.metadata IS 'Additional source-specific metadata in JSON format';

-- View for latest discovered values (most recent entry per company/field)
CREATE OR REPLACE VIEW company_history.latest_discoveries AS
SELECT DISTINCT ON (company_id, field)
    company_id,
    field,
    value_found,
    source,
    confidence_score,
    timestamp_found,
    process_id,
    metadata
FROM company_history.discovery_log
ORDER BY company_id, field, timestamp_found DESC;

COMMENT ON VIEW company_history.latest_discoveries IS 'Latest discovered value for each company field combination';

-- Function to get company discovery history
CREATE OR REPLACE FUNCTION company_history.get_field_history(
    p_company_id TEXT,
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
    change_reason TEXT
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
        dl.change_reason
    FROM company_history.discovery_log dl
    WHERE dl.company_id = p_company_id
    AND (p_field IS NULL OR dl.field = p_field)
    ORDER BY dl.timestamp_found DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION company_history.get_field_history IS 'Retrieve history entries for a company, optionally filtered by field';

-- Function to check if a field has been discovered recently
CREATE OR REPLACE FUNCTION company_history.check_recent_discovery(
    p_company_id TEXT,
    p_field TEXT,
    p_hours_threshold INTEGER DEFAULT 24
)
RETURNS BOOLEAN AS $$
DECLARE
    discovery_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO discovery_count
    FROM company_history.discovery_log
    WHERE company_id = p_company_id
    AND field = p_field
    AND timestamp_found > NOW() - INTERVAL '1 hour' * p_hours_threshold;

    RETURN discovery_count > 0;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION company_history.check_recent_discovery IS 'Check if a field was discovered within the specified time threshold';