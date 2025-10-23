-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-8509FF04
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

/**
 * Enrichment Router Database Schema
 * Step 2B of Barton Doctrine Pipeline - Validation Failure Enrichment
 * Templated for flexible schema/table configuration
 */

-- Create enrichment tracking table
CREATE TABLE IF NOT EXISTS intake.validation_failed (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL, -- FK to intake.company_raw_intake.id
    error_type TEXT NOT NULL, -- missing_state, bad_phone_format, invalid_url, etc.
    error_field TEXT NOT NULL, -- column name that failed validation
    raw_value TEXT, -- original value that failed validation
    expected_format TEXT, -- description of expected format
    batch_id TEXT, -- processing batch identifier
    attempts INTEGER DEFAULT 0,
    last_attempt_source TEXT CHECK (last_attempt_source IN ('auto_fix', 'apify', 'abacus', 'human')),
    last_attempt_at TIMESTAMPTZ,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'fixed', 'escalated', 'human_review')),
    fixed_value TEXT, -- value after successful enrichment
    metadata JSONB DEFAULT '{}', -- additional context and tracking data
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Create indexes for performance
    CONSTRAINT validation_failed_record_error_unique UNIQUE(record_id, error_type, error_field),
    FOREIGN KEY (record_id) REFERENCES intake.company_raw_intake(id) ON DELETE CASCADE
);

-- Create validation audit log
CREATE TABLE IF NOT EXISTS intake.validation_audit_log (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    error_field TEXT NOT NULL,
    attempt_source TEXT NOT NULL CHECK (attempt_source IN ('auto_fix', 'apify', 'abacus', 'human')),
    result TEXT NOT NULL CHECK (result IN ('success', 'fail', 'retry', 'escalate')),
    original_value TEXT,
    enriched_value TEXT,
    details JSONB DEFAULT '{}', -- handler-specific details
    processing_time_ms INTEGER,
    confidence_score NUMERIC(3,2), -- 0.00 to 1.00
    barton_metadata JSONB DEFAULT '{}', -- Barton Doctrine compliance data
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Reference the validation_failed record
    validation_failed_id INTEGER REFERENCES intake.validation_failed(id) ON DELETE CASCADE,

    -- Barton Doctrine compliance
    altitude INTEGER DEFAULT 10000,
    doctrine TEXT DEFAULT 'STAMPED',
    process_id TEXT DEFAULT 'enrichment_router_step_2b'
);

-- Create human firebreak queue table
CREATE TABLE IF NOT EXISTS intake.human_firebreak_queue (
    id SERIAL PRIMARY KEY,
    record_id INTEGER NOT NULL,
    error_type TEXT NOT NULL,
    error_field TEXT NOT NULL,
    raw_value TEXT,
    attempts_made INTEGER DEFAULT 0,
    handlers_tried TEXT[], -- array of handler types attempted
    escalation_reason TEXT,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    assigned_to TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'resolved', 'deferred')),
    resolution_notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,

    -- Reference original validation failure
    validation_failed_id INTEGER REFERENCES intake.validation_failed(id) ON DELETE CASCADE,

    -- Barton Doctrine compliance
    altitude INTEGER DEFAULT 10000,
    doctrine TEXT DEFAULT 'STAMPED'
);

-- Create enrichment handler registry (tracks handler capabilities)
CREATE TABLE IF NOT EXISTS intake.enrichment_handler_registry (
    id SERIAL PRIMARY KEY,
    handler_name TEXT UNIQUE NOT NULL,
    handler_type TEXT NOT NULL CHECK (handler_type IN ('auto_fix', 'apify', 'abacus', 'human')),
    error_types TEXT[] NOT NULL, -- array of error types this handler can process
    error_fields TEXT[] NOT NULL, -- array of fields this handler can fix
    priority_order INTEGER DEFAULT 100,
    enabled BOOLEAN DEFAULT true,
    config JSONB DEFAULT '{}', -- handler-specific configuration
    success_rate NUMERIC(5,2) DEFAULT 0.00, -- percentage success rate
    avg_processing_time_ms INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_validation_failed_status ON intake.validation_failed(status);
CREATE INDEX IF NOT EXISTS idx_validation_failed_error_type ON intake.validation_failed(error_type);
CREATE INDEX IF NOT EXISTS idx_validation_failed_batch_id ON intake.validation_failed(batch_id);
CREATE INDEX IF NOT EXISTS idx_validation_failed_attempts ON intake.validation_failed(attempts);
CREATE INDEX IF NOT EXISTS idx_validation_failed_record_id ON intake.validation_failed(record_id);

CREATE INDEX IF NOT EXISTS idx_audit_log_record_id ON intake.validation_audit_log(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON intake.validation_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_result ON intake.validation_audit_log(result);

CREATE INDEX IF NOT EXISTS idx_firebreak_status ON intake.human_firebreak_queue(status);
CREATE INDEX IF NOT EXISTS idx_firebreak_priority ON intake.human_firebreak_queue(priority);

-- Create update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_validation_failed_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validation_failed_updated
    BEFORE UPDATE ON intake.validation_failed
    FOR EACH ROW
    EXECUTE FUNCTION update_validation_failed_timestamp();

CREATE OR REPLACE FUNCTION update_handler_registry_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_handler_registry_updated
    BEFORE UPDATE ON intake.enrichment_handler_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_handler_registry_timestamp();

-- Insert default handler registry entries
INSERT INTO intake.enrichment_handler_registry (
    handler_name, handler_type, error_types, error_fields, priority_order, config
) VALUES
(
    'state_normalizer',
    'auto_fix',
    ARRAY['missing_state', 'invalid_state', 'bad_state_format'],
    ARRAY['company_state', 'state', 'location_state'],
    10,
    '{"patterns": ["full_name_to_code", "case_normalization"], "confidence_threshold": 0.8}'::jsonb
),
(
    'url_formatter',
    'auto_fix',
    ARRAY['invalid_url', 'missing_protocol', 'bad_url_format'],
    ARRAY['website_url', 'website', 'company_website'],
    20,
    '{"protocols": ["https", "http"], "validation": "strict", "auto_protocol": true}'::jsonb
),
(
    'phone_normalizer',
    'auto_fix',
    ARRAY['bad_phone_format', 'invalid_phone'],
    ARRAY['company_phone', 'phone', 'phone_number'],
    30,
    '{"format": "E164", "country_default": "US", "strip_formatting": true}'::jsonb
),
(
    'linkedin_scraper',
    'apify',
    ARRAY['missing_linkedin', 'invalid_linkedin'],
    ARRAY['company_linkedin_url', 'linkedin_url'],
    100,
    '{"actor_id": "apify/linkedin-company-scraper", "timeout": 30, "retry_count": 2}'::jsonb
),
(
    'website_discoverer',
    'apify',
    ARRAY['missing_website', 'website_not_found'],
    ARRAY['website_url', 'website', 'company_website'],
    110,
    '{"actor_id": "apify/website-content-crawler", "timeout": 45, "retry_count": 3}'::jsonb
),
(
    'company_data_enricher',
    'apify',
    ARRAY['missing_ein', 'missing_permit', 'missing_revenue'],
    ARRAY['ein', 'tax_id', 'permit_number', 'annual_revenue'],
    120,
    '{"actor_id": "apify/company-data-scraper", "timeout": 60, "retry_count": 2}'::jsonb
),
(
    'abacus_escalator',
    'abacus',
    ARRAY['complex_validation_failure', 'multiple_field_failure', 'data_inconsistency'],
    ARRAY['*'], -- can handle any field
    200,
    '{"endpoint": "/api/abacus/data-enrichment", "confidence_requirement": 0.75}'::jsonb
),
(
    'human_reviewer',
    'human',
    ARRAY['*'], -- can handle any error type
    ARRAY['*'], -- can handle any field
    1000,
    '{"queue": "human_firebreak_queue", "priority_escalation": true}'::jsonb
)
ON CONFLICT (handler_name) DO NOTHING;

-- Insert audit log entry for schema creation
INSERT INTO intake.validation_audit_log (
    record_id, error_type, error_field, attempt_source, result,
    details, barton_metadata, validation_failed_id
) VALUES (
    -1, 'schema_creation', 'enrichment_tables', 'human', 'success',
    '{"message": "Enrichment router database schema created successfully"}'::jsonb,
    '{"altitude": 10000, "doctrine": "STAMPED", "process_id": "enrichment_router_step_2b", "schema_version": "1.0"}'::jsonb,
    NULL
);

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA intake TO your_enrichment_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA intake TO your_enrichment_user;