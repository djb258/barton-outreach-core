
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
    segment4 := '07'; -- Fixed segment for database records
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

-- Barton Doctrine Migration
-- File: create_enrichment_audit_log
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

/**
 * Enrichment Audit Log Migration - Barton Doctrine Step 2B
 * Creates intake.enrichment_audit_log for tracking all enrichment attempts
 *
 * Barton Doctrine Rules:
 * - Every enrichment attempt must be logged
 * - No data advances until Step 2A validation is passed
 * - Enrichment may only fill/repair fields — Barton IDs must never change
 * - Altitude 10000 operational level enforcement
 */

-- ==============================================================================
-- INTAKE.ENRICHMENT_AUDIT_LOG - Enrichment Tracking Table
-- ==============================================================================

/**
 * Enrichment Audit Log Table
 * Tracks all enrichment attempts with before/after values
 * Required for Barton Doctrine compliance in Step 2B
 */
CREATE TABLE IF NOT EXISTS intake.enrichment_audit_log (id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: ID for the row being enriched (NEVER changes)
    unique_id TEXT NOT NULL,

    -- ENRICHMENT ACTION DETAILS
    action TEXT NOT NULL CHECK (action IN ('enrich', 're-validate')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    source TEXT NOT NULL, -- e.g. Apollo, Apify, internal heuristics

    -- ERROR HANDLING AND CHANGE TRACKING
    error_log JSONB DEFAULT NULL, -- structured details on failure
    before_values JSONB DEFAULT NULL, -- original values before enrichment
    after_values JSONB DEFAULT NULL, -- values after enrichment

    -- BARTON DOCTRINE: Metadata requirements
    altitude INTEGER DEFAULT 10000, -- operational level
    process_id TEXT, -- specific process identifier
    session_id TEXT, -- batch/session grouping

    -- TIMING
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - Enrichment Lookups
-- ==============================================================================

/**
 * Primary lookup indexes for enrichment audit queries
 */
CREATE INDEX IF NOT EXISTS idx_enrichment_audit_log_unique_id
    ON intake.enrichment_audit_log(unique_id);

CREATE INDEX IF NOT EXISTS idx_enrichment_audit_log_status
    ON intake.enrichment_audit_log(status);

CREATE INDEX IF NOT EXISTS idx_enrichment_audit_log_created_at
    ON intake.enrichment_audit_log(created_at);

CREATE INDEX IF NOT EXISTS idx_enrichment_audit_log_action_status
    ON intake.enrichment_audit_log(action, status);

CREATE INDEX IF NOT EXISTS idx_enrichment_audit_log_source
    ON intake.enrichment_audit_log(source);

CREATE INDEX IF NOT EXISTS idx_enrichment_audit_log_session
    ON intake.enrichment_audit_log(session_id);

-- ==============================================================================
-- HELPER FUNCTIONS - Enrichment Audit Operations
-- ==============================================================================

/**
 * Log enrichment attempt with structured data
 * Ensures consistent audit trail format
 */
CREATE OR REPLACE FUNCTION log_enrichment_attempt(
    p_unique_id TEXT,
    p_action TEXT,
    p_status TEXT,
    p_source TEXT,
    p_before_values JSONB DEFAULT NULL,
    p_after_values JSONB DEFAULT NULL,
    p_error_log JSONB DEFAULT NULL,
    p_process_id TEXT DEFAULT NULL,
    p_session_id TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    audit_id INTEGER;
BEGIN
    -- Validate action
    IF p_action NOT IN ('enrich', 're-validate') THEN
        RAISE EXCEPTION 'Invalid action: %. Must be enrich or re-validate', p_action;
    END IF;

    -- Validate status
    IF p_status NOT IN ('success', 'failed', 'partial') THEN
        RAISE EXCEPTION 'Invalid status: %. Must be success, failed, or partial', p_status;
    END IF;

    -- Insert audit log entry
    INSERT INTO intake.enrichment_audit_log (
        unique_id,
        action,
        status,
        source,
        error_log,
        before_values,
        after_values,
        altitude,
        process_id,
        session_id
    ) VALUES (
        p_unique_id,
        p_action,
        p_status,
        p_source,
        p_error_log,
        p_before_values,
        p_after_values,
        10000,
        p_process_id,
        p_session_id
    ) RETURNING id INTO audit_id;

    RETURN audit_id;
END;
$$ LANGUAGE plpgsql;

/**
 * Get enrichment history for a specific record
 * Returns chronological enrichment attempts
 */
CREATE OR REPLACE FUNCTION get_enrichment_history(p_unique_id TEXT)
RETURNS TABLE (
    audit_id INTEGER,
    action TEXT,
    status TEXT,
    source TEXT,
    before_values JSONB,
    after_values JSONB,
    error_log JSONB,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.id,
        e.action,
        e.status,
        e.source,
        e.before_values,
        e.after_values,
        e.error_log,
        e.created_at
    FROM intake.enrichment_audit_log e
    WHERE e.unique_id = p_unique_id
    ORDER BY e.created_at DESC;
END;
$$ LANGUAGE plpgsql;

/**
 * Get enrichment statistics by status and source
 * Used for dashboard and monitoring
 */
CREATE OR REPLACE FUNCTION get_enrichment_stats(
    p_start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '24 hours',
    p_end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    source TEXT,
    action TEXT,
    status TEXT,
    record_count BIGINT,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.source,
        e.action,
        e.status,
        COUNT(*) as record_count,
        ROUND(
            CASE
                WHEN COUNT(*) > 0 THEN
                    (COUNT(*) FILTER (WHERE e.status = 'success')::NUMERIC / COUNT(*)::NUMERIC) * 100
                ELSE 0
            END, 2
        ) as success_rate
    FROM intake.enrichment_audit_log e
    WHERE e.created_at BETWEEN p_start_date AND p_end_date
    GROUP BY e.source, e.action, e.status
    ORDER BY e.source, e.action, e.status;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- VIEWS FOR ENRICHMENT MONITORING
-- ==============================================================================

/**
 * Current enrichment status summary
 * Shows pending, successful, and failed enrichment counts
 */
CREATE OR REPLACE VIEW intake.enrichment_status_summary AS
SELECT
    'companies' as record_type,
    COUNT(*) FILTER (WHERE status = 'failed') as pending_enrichment,
    COUNT(*) FILTER (WHERE status = 'success') as successful_enrichment,
    COUNT(*) FILTER (WHERE status = 'partial') as partial_enrichment,
    COUNT(*) as total_attempts
FROM intake.enrichment_audit_log
WHERE unique_id LIKE '04.04.01.%' -- company records
AND created_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'people' as record_type,
    COUNT(*) FILTER (WHERE status = 'failed') as pending_enrichment,
    COUNT(*) FILTER (WHERE status = 'success') as successful_enrichment,
    COUNT(*) FILTER (WHERE status = 'partial') as partial_enrichment,
    COUNT(*) as total_attempts
FROM intake.enrichment_audit_log
WHERE unique_id LIKE '04.04.02.%' -- people records
AND created_at > NOW() - INTERVAL '24 hours';

/**
 * Recent enrichment activity view
 * Shows latest enrichment attempts with details
 */
CREATE OR REPLACE VIEW intake.recent_enrichment_activity AS
SELECT
    e.unique_id,
    CASE
        WHEN e.unique_id LIKE '04.04.01.%' THEN 'company'
        WHEN e.unique_id LIKE '04.04.02.%' THEN 'people'
        ELSE 'unknown'
    END as record_type,
    e.action,
    e.status,
    e.source,
    e.before_values,
    e.after_values,
    e.error_log,
    e.created_at
FROM intake.enrichment_audit_log e
WHERE e.created_at > NOW() - INTERVAL '1 hour'
ORDER BY e.created_at DESC
LIMIT 100;

-- ==============================================================================
-- PERMISSIONS AND SECURITY
-- ==============================================================================

-- Grant appropriate permissions for application access
-- GRANT SELECT, INSERT ON intake.enrichment_audit_log TO app_user;
-- GRANT USAGE ON SEQUENCE intake.enrichment_audit_log_id_seq TO app_user;
-- GRANT SELECT ON intake.enrichment_status_summary TO app_user;
-- GRANT SELECT ON intake.recent_enrichment_activity TO app_user;

-- ==============================================================================
-- INITIAL AUDIT LOG ENTRY - Schema Creation
-- ==============================================================================

/**
 * Log schema creation for doctrine compliance
 */
INSERT INTO intake.enrichment_audit_log (
    unique_id,
    action,
    status,
    source,
    error_log,
    altitude,
    process_id,
    session_id
) VALUES (
    '04.04.00.04.10000.000', -- system/schema creation ID
    'enrich',
    'success',
    'schema_migration',
    '{"message": "Enrichment audit log schema created successfully", "schema_version": "1.0.0"}'::jsonb,
    10000,
    'create_enrichment_audit_log_migration',
    'schema_init_' || EXTRACT(epoch FROM NOW())::TEXT
);

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * Enrichment Audit Log Migration Complete
 *
 * Created:
 * - intake.enrichment_audit_log (with full audit trail tracking)
 * - Enrichment helper functions for logging and history
 * - Performance indexes for efficient queries
 * - Monitoring views for dashboard display
 * - Statistics functions for reporting
 *
 * Barton Doctrine Compliance:
 * - Every enrichment attempt logged with before/after values
 * - Barton IDs preserved (never changed during enrichment)
 * - Altitude 10000 operational level enforcement
 * - Structured error handling with JSONB details
 * - Process and session tracking for batch operations
 *
 * Next Steps:
 * 1. Build enrichment APIs (/api/enrich-companies.ts, /api/enrich-people.ts)
 * 2. Update validation console with Step 2B enrichment view
 * 3. Implement enrichment rules and re-validation triggers
 */
-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();
