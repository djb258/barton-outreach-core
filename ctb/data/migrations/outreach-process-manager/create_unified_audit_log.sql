-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-F93DF3D2
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

-- Updated At Trigger Function
CREATE OR REPLACE FUNCTION trigger_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Barton ID Generator Function
-- Generates format: NN.NN.NN.NN.NNNNN.NNN
CREATE OR REPLACE FUNCTION generate_barton_id()
RETURNS VARCHAR(23) AS $$
DECLARE
    segment1 VARCHAR(2);
    segment2 VARCHAR(2);
    segment3 VARCHAR(2);
    segment4 VARCHAR(2);
    segment5 VARCHAR(5);
    segment6 VARCHAR(3);
BEGIN
    -- Use timestamp and random for uniqueness
    segment1 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment2 := LPAD((EXTRACT(MICROSECONDS FROM NOW()) % 100)::TEXT, 2, '0');
    segment3 := LPAD((RANDOM() * 100)::INT::TEXT, 2, '0');
    segment4 := '05'; -- Fixed segment for audit records
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

/**
 * Unified Audit Log Migration - Barton Doctrine Step 5
 * File: create_unified_audit_log
 * Purpose: Central audit trail for all pipeline actions (Steps 1-4)
 * Requirements: Standardized schema with Barton Doctrine compliance
 * MCP: All access via Composio bridge, no direct connections
 */

/**
 * Unified Audit Log Migration - Step 5 Audit Trail Integration
 * Creates marketing.unified_audit_log for tracking all pipeline actions
 * Enforces Barton Doctrine compliance with mandatory fields
 *
 * Barton Doctrine Rules:
 * - Every action must have doctrine ID and unique_id
 * - No anonymous actions (always tie to agent/human/system)
 * - Standardized schema across all pipeline steps
 * - Full traceability from ingest to promotion
 *
 * Pipeline Steps Tracked:
 * 1. Ingest (data ingestion from sources)
 * 2. Validate (data validation and error detection)
 * 3. Enrich (data enrichment via external sources)
 * 4. Adjust (human adjustments and corrections)
 * 5. Promote (movement to master tables)
 */

-- ==============================================================================
-- MARKETING.UNIFIED_AUDIT_LOG - Central Audit Trail
-- ==============================================================================

/**
 * Unified Audit Log Table - Central tracking for all pipeline actions
 * Captures events from Steps 1-4 with standardized schema
 * Enforces Barton Doctrine with required fields and compliance
 */
CREATE TABLE IF NOT EXISTS marketing.unified_audit_log (
    id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: Required unique identifiers
    unique_id TEXT NOT NULL, -- Subject of the action (company/person Barton ID)
    audit_id TEXT NOT NULL UNIQUE DEFAULT generate_barton_id(), -- Audit entry Barton ID

    -- STANDARDIZED LOG SCHEMA: Core required fields
    process_id TEXT NOT NULL, -- Process identifier (step_1_ingest, step_2_validate, etc.)
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'warning', 'pending', 'skipped')),
    actor TEXT NOT NULL, -- Who/what performed the action (never anonymous)
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL, -- Source system/component that generated the log

    -- ACTION DETAILS
    action TEXT NOT NULL, -- Specific action taken (ingest, validate, enrich, adjust, promote)
    step TEXT NOT NULL CHECK (step IN ('step_1_ingest', 'step_2_validate', 'step_2b_enrich', 'step_3_adjust', 'step_4_promote')),
    sub_action TEXT, -- Detailed sub-action (phone_validation, linkedin_enrichment, etc.)

    -- DATA CONTEXT
    record_type TEXT NOT NULL CHECK (record_type IN ('company', 'people', 'campaign', 'attribution', 'general')),
    record_id INTEGER, -- FK to the actual record (if applicable)

    -- CHANGE TRACKING
    before_values JSONB DEFAULT NULL, -- State before the action
    after_values JSONB DEFAULT NULL, -- State after the action
    field_changes TEXT[], -- Array of fields that were modified

    -- ERROR HANDLING
    error_log JSONB DEFAULT NULL, -- Structured error details when status = 'failed'
    error_code TEXT, -- Error classification code
    retry_count INTEGER DEFAULT 0, -- Number of retries attempted

    -- PERFORMANCE METRICS
    processing_time_ms INTEGER, -- Time taken to complete the action
    confidence_score NUMERIC(3,2), -- Confidence in the action (0.00 to 1.00)

    -- BARTON DOCTRINE: Metadata and compliance
    altitude INTEGER DEFAULT 10000, -- Execution level
    doctrine TEXT DEFAULT 'STAMPED', -- Doctrine compliance status
    doctrine_version TEXT DEFAULT 'v2.1.0', -- Version of doctrine applied
    session_id TEXT, -- Batch/session grouping identifier
    correlation_id TEXT, -- Cross-system correlation ID

    -- AUDIT METADATA
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - Doctrine Requirements
-- ==============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_unified_audit_log_unique_id
    ON marketing.unified_audit_log(unique_id);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_audit_id
    ON marketing.unified_audit_log(audit_id);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_timestamp
    ON marketing.unified_audit_log(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_process_id
    ON marketing.unified_audit_log(process_id);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_step
    ON marketing.unified_audit_log(step);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_action
    ON marketing.unified_audit_log(action);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_status
    ON marketing.unified_audit_log(status);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_actor
    ON marketing.unified_audit_log(actor);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_source
    ON marketing.unified_audit_log(source);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_record_type
    ON marketing.unified_audit_log(record_type);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_session_id
    ON marketing.unified_audit_log(session_id);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_correlation_id
    ON marketing.unified_audit_log(correlation_id);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_unified_audit_log_step_status
    ON marketing.unified_audit_log(step, status);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_unique_id_step
    ON marketing.unified_audit_log(unique_id, step);

CREATE INDEX IF NOT EXISTS idx_unified_audit_log_action_timestamp
    ON marketing.unified_audit_log(action, timestamp DESC);

-- ==============================================================================
-- TRIGGERS - Automatic Timestamp Management
-- ==============================================================================

/**
 * Automatic updated_at timestamp trigger
 * Ensures doctrine compliance for change tracking
 */
CREATE OR REPLACE FUNCTION update_unified_audit_log_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_unified_audit_log_updated_at
    BEFORE UPDATE ON marketing.unified_audit_log
    FOR EACH ROW EXECUTE FUNCTION update_unified_audit_log_timestamp();

-- ==============================================================================
-- BARTON DOCTRINE VALIDATION FUNCTIONS
-- ==============================================================================

/**
 * Validate Barton ID format for audit entries
 * Ensures all audit IDs conform to 6-part specification
 */
CREATE OR REPLACE FUNCTION validate_audit_barton_id(audit_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    -- Check format: XX.XX.XX.XX.XXXXX.XXX
    IF audit_id !~ '^[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$' THEN
        RETURN FALSE;
    END IF;

    -- Additional validation: must use segment4 = '05' for audit records
    IF NOT audit_id LIKE '%.%.%.05.%.%' THEN
        RETURN FALSE;
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Add check constraint to ensure Barton ID format compliance
ALTER TABLE marketing.unified_audit_log
    ADD CONSTRAINT chk_unified_audit_log_barton_id_format
    CHECK (validate_audit_barton_id(audit_id));

-- ==============================================================================
-- AUDIT LOG HELPER VIEWS
-- ==============================================================================

/**
 * Recent Audit Activity View
 * Shows last 1000 audit entries with formatted data
 */
CREATE OR REPLACE VIEW marketing.recent_audit_activity AS
SELECT
    audit_id,
    unique_id,
    step,
    action,
    status,
    actor,
    source,
    record_type,
    processing_time_ms,
    confidence_score,
    session_id,
    timestamp,
    CASE
        WHEN error_log IS NOT NULL THEN 'Has Errors'
        ELSE 'Clean'
    END as error_status,
    CASE
        WHEN field_changes IS NOT NULL AND array_length(field_changes, 1) > 0
        THEN array_length(field_changes, 1)
        ELSE 0
    END as fields_changed
FROM marketing.unified_audit_log
ORDER BY timestamp DESC
LIMIT 1000;

/**
 * Audit Summary by Step View
 * Aggregates audit activity by pipeline step
 */
CREATE OR REPLACE VIEW marketing.audit_summary_by_step AS
SELECT
    step,
    COUNT(*) as total_actions,
    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_actions,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_actions,
    COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning_actions,
    AVG(processing_time_ms) as avg_processing_time_ms,
    AVG(confidence_score) as avg_confidence_score,
    MIN(timestamp) as first_action,
    MAX(timestamp) as last_action
FROM marketing.unified_audit_log
GROUP BY step
ORDER BY step;

-- ==============================================================================
-- INITIAL AUDIT LOG ENTRY - Schema Creation
-- ==============================================================================

/**
 * Log schema creation for doctrine compliance
 * Every major operation must be audited
 */
INSERT INTO marketing.unified_audit_log (
    unique_id,
    audit_id,
    process_id,
    status,
    actor,
    source,
    action,
    step,
    record_type,
    session_id,
    error_log,
    altitude,
    doctrine,
    doctrine_version
) VALUES (
    '05.05.05.05.10000.000', -- system/schema creation ID
    generate_barton_id(),
    'create_unified_audit_log_migration',
    'success',
    'system_migration',
    'schema_migration',
    'create_table',
    'step_1_ingest', -- Schema creation is part of initial setup
    'general',
    'schema_init_' || EXTRACT(epoch FROM NOW())::TEXT,
    '{"message": "Unified audit log table created successfully", "schema_version": "1.0.0", "tables_created": ["marketing.unified_audit_log"], "views_created": ["marketing.recent_audit_activity", "marketing.audit_summary_by_step"]}'::jsonb,
    10000,
    'STAMPED',
    'v2.1.0'
);

-- ==============================================================================
-- GRANT PERMISSIONS - Doctrine Access Control
-- ==============================================================================

-- Grant appropriate permissions for application access
-- GRANT SELECT, INSERT, UPDATE ON marketing.unified_audit_log TO app_user;
-- GRANT SELECT ON marketing.recent_audit_activity TO app_user;
-- GRANT SELECT ON marketing.audit_summary_by_step TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.unified_audit_log_id_seq TO app_user;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * Unified Audit Log Migration Complete
 *
 * Created:
 * - marketing.unified_audit_log (with Barton ID enforcement)
 * - Helper views for audit activity monitoring
 * - Barton ID validation functions
 * - Performance indexes
 * - Validation constraints
 * - Automatic triggers
 *
 * Next Steps:
 * 1. Create auditOperations.js utility functions
 * 2. Integrate audit hooks into all pipeline steps
 * 3. Migrate existing audit data to unified format
 * 4. Update audit trail viewing interface
 */