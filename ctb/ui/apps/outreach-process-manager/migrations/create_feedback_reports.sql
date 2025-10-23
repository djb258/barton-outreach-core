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
    segment4 := '08'; -- Fixed segment for feedback reports
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

/**
 * Feedback Reports Migration - Step 8 Feedback Loop
 * File: create_feedback_reports
 * Purpose: Continuous improvement through error pattern analysis
 * Requirements: Store structured feedback reports for process tuning
 * MCP: All access via Composio bridge, no direct connections
 */

/**
 * Feedback Reports Migration - Step 8 Feedback Loop
 * Creates marketing.feedback_reports for continuous improvement analysis
 * Analyzes error patterns from error_log + validation_failed tables
 * Generates actionable insights for process optimization
 *
 * Barton Doctrine Rules:
 * - Every report must have doctrine ID and timestamp
 * - Structured JSON + human-readable format
 * - Tagged error patterns for trend analysis
 * - Actionable recommendations for improvement
 *
 * Data Sources Analyzed:
 * 1. marketing.unified_audit_log (error_log entries)
 * 2. intake.validation_failed (validation error patterns)
 * 3. intake.validation_audit_log (enrichment attempt results)
 * 4. intake.human_firebreak_queue (escalated issues)
 */

-- ==============================================================================
-- MARKETING.FEEDBACK_REPORTS - Continuous Improvement Analytics
-- ==============================================================================

/**
 * Feedback Reports Table - Central repository for process improvement insights
 * Analyzes error patterns and generates actionable feedback
 * Drives continuous optimization of the data pipeline
 */
CREATE TABLE IF NOT EXISTS marketing.feedback_reports (
    id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: Required unique identifiers
    report_id TEXT NOT NULL UNIQUE DEFAULT generate_barton_id(), -- Report Barton ID
    report_name TEXT NOT NULL, -- Human-readable report name

    -- REPORT METADATA
    report_type TEXT NOT NULL CHECK (report_type IN ('daily', 'weekly', 'monthly', 'ad_hoc', 'incident')),
    report_period_start TIMESTAMPTZ NOT NULL, -- Analysis period start
    report_period_end TIMESTAMPTZ NOT NULL, -- Analysis period end
    generated_by TEXT NOT NULL, -- Who/what generated the report (never anonymous)
    generation_trigger TEXT NOT NULL, -- What triggered report generation

    -- ANALYSIS SCOPE
    data_sources TEXT[] NOT NULL DEFAULT ARRAY['unified_audit_log', 'validation_failed'], -- Sources analyzed
    record_types TEXT[] NOT NULL DEFAULT ARRAY['company', 'people'], -- Record types included
    total_records_analyzed INTEGER NOT NULL DEFAULT 0,
    analysis_depth TEXT NOT NULL DEFAULT 'standard' CHECK (analysis_depth IN ('basic', 'standard', 'deep')),

    -- ERROR PATTERN ANALYSIS
    error_patterns JSONB NOT NULL DEFAULT '{}', -- Structured error pattern analysis
    recurring_errors JSONB NOT NULL DEFAULT '{}', -- Frequently occurring errors
    error_trends JSONB NOT NULL DEFAULT '{}', -- Error trend analysis over time
    critical_issues JSONB NOT NULL DEFAULT '{}', -- High-priority issues requiring attention

    -- PERFORMANCE METRICS
    total_errors_found INTEGER NOT NULL DEFAULT 0,
    error_categories_count INTEGER NOT NULL DEFAULT 0,
    avg_resolution_time_hours NUMERIC(10,2), -- Average time to resolve issues
    success_rate_improvement NUMERIC(5,2), -- Improvement in success rates
    processing_efficiency JSONB DEFAULT '{}', -- Performance efficiency metrics

    -- ACTIONABLE INSIGHTS
    recommendations JSONB NOT NULL DEFAULT '{}', -- Structured improvement recommendations
    quick_wins TEXT[], -- Easy to implement improvements
    long_term_improvements TEXT[], -- Strategic improvements requiring planning
    process_adjustments JSONB DEFAULT '{}', -- Specific process change recommendations

    -- HUMAN-READABLE REPORT
    executive_summary TEXT, -- Brief overview for leadership
    detailed_findings TEXT, -- Comprehensive analysis details
    methodology_notes TEXT, -- How the analysis was conducted
    data_quality_notes TEXT, -- Notes on data quality and limitations

    -- IMPACT TRACKING
    previous_report_id TEXT, -- Reference to previous report for comparison
    improvements_implemented JSONB DEFAULT '{}', -- What was actually implemented
    impact_measured JSONB DEFAULT '{}', -- Measured impact of previous improvements
    roi_analysis JSONB DEFAULT '{}', -- Return on investment analysis

    -- TAGS AND CATEGORIZATION
    tags TEXT[] DEFAULT ARRAY[]::TEXT[], -- Searchable tags for categorization
    priority_level TEXT DEFAULT 'medium' CHECK (priority_level IN ('low', 'medium', 'high', 'critical')),
    stakeholders TEXT[] DEFAULT ARRAY[]::TEXT[], -- Who should review this report
    follow_up_required BOOLEAN DEFAULT false,
    follow_up_by TIMESTAMPTZ, -- When follow-up is needed

    -- STATUS TRACKING
    status TEXT DEFAULT 'generated' CHECK (status IN ('generated', 'reviewed', 'acted_upon', 'archived')),
    reviewed_by TEXT, -- Who reviewed the report
    reviewed_at TIMESTAMPTZ,
    action_plan JSONB DEFAULT '{}', -- What actions will be taken
    completion_status JSONB DEFAULT '{}', -- Status of recommended actions

    -- BARTON DOCTRINE: Metadata and compliance
    altitude INTEGER DEFAULT 10000, -- Execution level
    doctrine TEXT DEFAULT 'STAMPED', -- Doctrine compliance status
    doctrine_version TEXT DEFAULT 'v2.1.0', -- Version of doctrine applied
    session_id TEXT, -- Analysis session identifier
    correlation_id TEXT, -- Cross-system correlation ID

    -- AUDIT METADATA
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- FEEDBACK PATTERN TAGS - Error Classification System
-- ==============================================================================

/**
 * Pattern Tags Table - Standardized error pattern classification
 * Enables consistent tagging and trend analysis across reports
 */
CREATE TABLE IF NOT EXISTS marketing.feedback_pattern_tags (
    id SERIAL PRIMARY KEY,

    -- TAG IDENTIFICATION
    tag_name TEXT NOT NULL UNIQUE, -- Standardized tag name
    tag_category TEXT NOT NULL, -- Category (data_quality, process, system, etc.)
    tag_description TEXT NOT NULL, -- Human-readable description
    tag_severity TEXT NOT NULL CHECK (tag_severity IN ('info', 'warning', 'error', 'critical')),

    -- PATTERN MATCHING
    error_types TEXT[] DEFAULT ARRAY[]::TEXT[], -- Error types this tag applies to
    error_fields TEXT[] DEFAULT ARRAY[]::TEXT[], -- Fields this tag commonly affects
    pattern_regex TEXT, -- Regex pattern for automatic tagging
    keywords TEXT[] DEFAULT ARRAY[]::TEXT[], -- Keywords for pattern matching

    -- METADATA
    created_by TEXT NOT NULL,
    usage_count INTEGER DEFAULT 0, -- How many times this tag has been used
    last_used_at TIMESTAMPTZ,

    -- STATUS
    active BOOLEAN DEFAULT true,
    review_required BOOLEAN DEFAULT false,

    -- BARTON DOCTRINE
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- FEEDBACK REPORT ACTIONS - Track Implementation of Recommendations
-- ==============================================================================

/**
 * Report Actions Table - Track implementation of feedback recommendations
 * Enables measurement of improvement impact and ROI
 */
CREATE TABLE IF NOT EXISTS marketing.feedback_report_actions (
    id SERIAL PRIMARY KEY,

    -- REFERENCE TO REPORT
    report_id TEXT NOT NULL, -- Reference to feedback_reports.report_id
    recommendation_id TEXT NOT NULL, -- ID of specific recommendation within report

    -- ACTION DETAILS
    action_title TEXT NOT NULL,
    action_description TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (action_type IN ('process_change', 'system_update', 'training', 'automation', 'configuration')),
    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high', 'critical')),

    -- ASSIGNMENT AND OWNERSHIP
    assigned_to TEXT NOT NULL,
    assigned_by TEXT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date TIMESTAMPTZ,

    -- IMPLEMENTATION TRACKING
    status TEXT DEFAULT 'assigned' CHECK (status IN ('assigned', 'in_progress', 'completed', 'cancelled', 'deferred')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    implementation_notes TEXT,
    blockers JSONB DEFAULT '{}', -- What's preventing completion
    resources_required JSONB DEFAULT '{}', -- Resources needed

    -- IMPACT MEASUREMENT
    expected_impact TEXT,
    measured_impact JSONB DEFAULT '{}', -- Actual measured improvement
    success_metrics JSONB DEFAULT '{}', -- How success will be measured
    roi_estimate NUMERIC(10,2), -- Estimated return on investment
    roi_actual NUMERIC(10,2), -- Actual measured ROI

    -- COMPLETION TRACKING
    completed_at TIMESTAMPTZ,
    validated_by TEXT, -- Who validated the completion
    validation_notes TEXT,

    -- BARTON DOCTRINE
    altitude INTEGER DEFAULT 10000,
    doctrine TEXT DEFAULT 'STAMPED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- FOREIGN KEY
    FOREIGN KEY (report_id) REFERENCES marketing.feedback_reports(report_id) ON DELETE CASCADE
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - Doctrine Requirements
-- ==============================================================================

-- Primary lookup indexes for feedback_reports
CREATE INDEX IF NOT EXISTS idx_feedback_reports_report_id
    ON marketing.feedback_reports(report_id);

CREATE INDEX IF NOT EXISTS idx_feedback_reports_type_period
    ON marketing.feedback_reports(report_type, report_period_start DESC);

CREATE INDEX IF NOT EXISTS idx_feedback_reports_status
    ON marketing.feedback_reports(status);

CREATE INDEX IF NOT EXISTS idx_feedback_reports_priority
    ON marketing.feedback_reports(priority_level);

CREATE INDEX IF NOT EXISTS idx_feedback_reports_generated_by
    ON marketing.feedback_reports(generated_by);

CREATE INDEX IF NOT EXISTS idx_feedback_reports_tags
    ON marketing.feedback_reports USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_feedback_reports_created_at
    ON marketing.feedback_reports(created_at DESC);

-- Pattern tags indexes
CREATE INDEX IF NOT EXISTS idx_pattern_tags_category
    ON marketing.feedback_pattern_tags(tag_category);

CREATE INDEX IF NOT EXISTS idx_pattern_tags_severity
    ON marketing.feedback_pattern_tags(tag_severity);

CREATE INDEX IF NOT EXISTS idx_pattern_tags_active
    ON marketing.feedback_pattern_tags(active);

-- Report actions indexes
CREATE INDEX IF NOT EXISTS idx_report_actions_report_id
    ON marketing.feedback_report_actions(report_id);

CREATE INDEX IF NOT EXISTS idx_report_actions_assigned_to
    ON marketing.feedback_report_actions(assigned_to);

CREATE INDEX IF NOT EXISTS idx_report_actions_status
    ON marketing.feedback_report_actions(status);

CREATE INDEX IF NOT EXISTS idx_report_actions_due_date
    ON marketing.feedback_report_actions(due_date);

-- ==============================================================================
-- TRIGGERS - Automatic Timestamp Management
-- ==============================================================================

/**
 * Automatic updated_at timestamp triggers
 * Ensures doctrine compliance for change tracking
 */
CREATE TRIGGER trigger_feedback_reports_updated_at
    BEFORE UPDATE ON marketing.feedback_reports
    FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

CREATE TRIGGER trigger_pattern_tags_updated_at
    BEFORE UPDATE ON marketing.feedback_pattern_tags
    FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

CREATE TRIGGER trigger_report_actions_updated_at
    BEFORE UPDATE ON marketing.feedback_report_actions
    FOR EACH ROW EXECUTE FUNCTION trigger_updated_at();

-- ==============================================================================
-- FEEDBACK ANALYTICS HELPER VIEWS
-- ==============================================================================

/**
 * Recent Feedback Reports View
 * Shows latest feedback reports with key metrics
 */
CREATE OR REPLACE VIEW marketing.recent_feedback_reports AS
SELECT
    report_id,
    report_name,
    report_type,
    report_period_start,
    report_period_end,
    generated_by,
    total_errors_found,
    error_categories_count,
    priority_level,
    status,
    tags,
    created_at,
    CASE
        WHEN follow_up_required AND follow_up_by < NOW() THEN 'Overdue'
        WHEN follow_up_required AND follow_up_by > NOW() THEN 'Pending'
        ELSE 'None'
    END as follow_up_status
FROM marketing.feedback_reports
ORDER BY created_at DESC
LIMIT 100;

/**
 * Error Pattern Trends View
 * Aggregates error patterns across reports for trend analysis
 */
CREATE OR REPLACE VIEW marketing.error_pattern_trends AS
SELECT
    unnest(tags) as error_pattern,
    COUNT(*) as occurrence_count,
    AVG(total_errors_found) as avg_errors_per_report,
    MAX(created_at) as last_seen,
    MIN(created_at) as first_seen,
    ARRAY_AGG(DISTINCT priority_level) as priority_levels,
    ARRAY_AGG(DISTINCT report_type) as report_types
FROM marketing.feedback_reports
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY unnest(tags)
HAVING COUNT(*) > 1
ORDER BY occurrence_count DESC, last_seen DESC;

/**
 * Action Implementation Status View
 * Shows status of feedback recommendations implementation
 */
CREATE OR REPLACE VIEW marketing.action_implementation_status AS
SELECT
    fr.report_name,
    fr.report_type,
    fr.created_at as report_date,
    fra.action_title,
    fra.action_type,
    fra.priority,
    fra.assigned_to,
    fra.status,
    fra.progress_percentage,
    fra.due_date,
    CASE
        WHEN fra.due_date < NOW() AND fra.status NOT IN ('completed', 'cancelled') THEN 'Overdue'
        WHEN fra.due_date < NOW() + INTERVAL '7 days' AND fra.status NOT IN ('completed', 'cancelled') THEN 'Due Soon'
        ELSE 'On Track'
    END as timeline_status
FROM marketing.feedback_reports fr
JOIN marketing.feedback_report_actions fra ON fr.report_id = fra.report_id
WHERE fra.status IN ('assigned', 'in_progress')
ORDER BY fra.due_date ASC NULLS LAST;

-- ==============================================================================
-- INITIAL PATTERN TAGS - Common Error Patterns
-- ==============================================================================

/**
 * Seed common error pattern tags for immediate use
 */
INSERT INTO marketing.feedback_pattern_tags (
    tag_name, tag_category, tag_description, tag_severity, error_types, error_fields, keywords
) VALUES
-- Data Quality Issues
('invalid_phone_format', 'data_quality', 'Phone numbers not in E.164 format', 'error',
 ARRAY['bad_phone_format', 'invalid_phone'], ARRAY['company_phone', 'work_phone_e164'],
 ARRAY['phone', 'format', 'e164']),

('missing_required_fields', 'data_quality', 'Required fields are empty or null', 'error',
 ARRAY['missing_state', 'missing_linkedin', 'missing_website'], ARRAY['address_state', 'linkedin_url', 'website_url'],
 ARRAY['missing', 'required', 'empty']),

('invalid_url_format', 'data_quality', 'URLs missing protocol or malformed', 'error',
 ARRAY['invalid_url', 'bad_url_format', 'missing_protocol'], ARRAY['website_url', 'linkedin_url'],
 ARRAY['url', 'protocol', 'format']),

('invalid_state_code', 'data_quality', 'State codes not in standard format', 'warning',
 ARRAY['invalid_state'], ARRAY['address_state'],
 ARRAY['state', 'code', 'abbreviation']),

-- Process Issues
('csv_format_errors', 'process', 'Issues with CSV file structure and formatting', 'error',
 ARRAY['bad_csv_format'], ARRAY[],
 ARRAY['csv', 'format', 'delimiter']),

('linkedin_extraction_failure', 'process', 'Failed to extract or validate LinkedIn profiles', 'warning',
 ARRAY['invalid_linkedin', 'linkedin_not_found'], ARRAY['linkedin_url'],
 ARRAY['linkedin', 'extraction', 'profile']),

('enrichment_timeout', 'system', 'Enrichment processes timing out', 'error',
 ARRAY['enrichment_timeout'], ARRAY[],
 ARRAY['timeout', 'enrichment', 'performance']),

-- System Issues
('database_connection_errors', 'system', 'Database connectivity or query issues', 'critical',
 ARRAY['db_connection_error'], ARRAY[],
 ARRAY['database', 'connection', 'query']),

('api_rate_limits', 'system', 'External API rate limiting issues', 'warning',
 ARRAY['rate_limit_exceeded'], ARRAY[],
 ARRAY['api', 'rate', 'limit']),

-- Validation Issues
('complex_validation_failure', 'validation', 'Complex multi-field validation failures', 'error',
 ARRAY['complex_validation_failure', 'multiple_field_failure'], ARRAY[],
 ARRAY['complex', 'validation', 'multiple']),

('data_inconsistency', 'validation', 'Inconsistent data across related fields', 'warning',
 ARRAY['data_inconsistency'], ARRAY[],
 ARRAY['inconsistent', 'related', 'fields'])

ON CONFLICT (tag_name) DO NOTHING;

-- ==============================================================================
-- INITIAL FEEDBACK REPORT ENTRY - Schema Creation
-- ==============================================================================

/**
 * Log schema creation for doctrine compliance
 * Every major operation must be documented
 */
INSERT INTO marketing.feedback_reports (
    report_id,
    report_name,
    report_type,
    report_period_start,
    report_period_end,
    generated_by,
    generation_trigger,
    data_sources,
    record_types,
    total_records_analyzed,
    error_patterns,
    recommendations,
    executive_summary,
    status,
    tags,
    altitude,
    doctrine,
    doctrine_version
) VALUES (
    generate_barton_id(),
    'Schema Initialization Report',
    'ad_hoc',
    NOW() - INTERVAL '1 minute',
    NOW(),
    'system_migration',
    'schema_creation',
    ARRAY['schema_migration'],
    ARRAY['system'],
    0,
    '{"schema_created": {"tables": ["feedback_reports", "feedback_pattern_tags", "feedback_report_actions"], "views": ["recent_feedback_reports", "error_pattern_trends", "action_implementation_status"], "initial_tags": 11}}'::jsonb,
    '{"immediate": ["Begin collecting error patterns for analysis"], "short_term": ["Generate first weekly feedback report"], "long_term": ["Implement automated feedback loop triggers"]}'::jsonb,
    'Feedback loop infrastructure has been successfully established. The system is now ready to collect, analyze, and report on error patterns across the data pipeline for continuous improvement.',
    'generated',
    ARRAY['system_initialization', 'schema_setup'],
    10000,
    'STAMPED',
    'v2.1.0'
);

-- ==============================================================================
-- GRANT PERMISSIONS - Doctrine Access Control
-- ==============================================================================

-- Grant appropriate permissions for application access
-- GRANT SELECT, INSERT, UPDATE ON marketing.feedback_reports TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON marketing.feedback_pattern_tags TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON marketing.feedback_report_actions TO app_user;
-- GRANT SELECT ON marketing.recent_feedback_reports TO app_user;
-- GRANT SELECT ON marketing.error_pattern_trends TO app_user;
-- GRANT SELECT ON marketing.action_implementation_status TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.feedback_reports_id_seq TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.feedback_pattern_tags_id_seq TO app_user;
-- GRANT USAGE ON SEQUENCE marketing.feedback_report_actions_id_seq TO app_user;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * Feedback Reports Migration Complete
 *
 * Created:
 * - marketing.feedback_reports (central report repository)
 * - marketing.feedback_pattern_tags (error pattern classification)
 * - marketing.feedback_report_actions (implementation tracking)
 * - Helper views for analytics and monitoring
 * - Initial pattern tags for common error types
 * - Performance indexes and constraints
 * - Automatic triggers and validation
 *
 * Next Steps:
 * 1. Create feedbackLoopOperations.js utility functions
 * 2. Build error pattern recognition algorithms
 * 3. Generate structured feedback reports
 * 4. Create React dashboard components
 * 5. Integrate with pipeline monitoring systems
 */