-- =============================================================================
-- OUTREACH SUB-HUB ERROR TABLES
-- =============================================================================
--
-- DOCTRINE:
--   A pipeline never "pauses." It either PASSes or FAILs.
--   FAIL = emit error row + exit.
--   Failures are WORK ITEMS, not states.
--
-- ENFORCEMENT:
--   - Any pipeline failure MUST write to its hub's error table
--   - Writing an error TERMINATES execution
--   - Error rows FREEZE spend for that context
--   - Resolution requires manual intervention OR new outreach_context_id
--
-- NO silent failures. NO retries inside the same context.
--
-- =============================================================================

-- Schema for outreach errors
CREATE SCHEMA IF NOT EXISTS outreach_errors;

-- =============================================================================
-- SHARED ENUM TYPES
-- =============================================================================

-- Severity levels
CREATE TYPE outreach_errors.severity_level AS ENUM (
    'info',      -- Informational, non-blocking
    'warning',   -- Needs attention, may proceed
    'blocking'   -- STOP execution immediately
);

-- =============================================================================
-- COMPANY TARGET ERROR TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_errors.company_target_errors (
    -- Primary key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Required identity keys
    company_sov_id UUID NOT NULL,
    outreach_context_id UUID NOT NULL,

    -- Hub identification
    hub_name VARCHAR(50) NOT NULL DEFAULT 'company-target',
    pipeline_stage VARCHAR(100) NOT NULL,

    -- Failure details
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,

    -- Control flags
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    severity outreach_errors.severity_level NOT NULL DEFAULT 'blocking',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    resolved_by VARCHAR(100),

    -- Additional context
    raw_input JSONB,
    stack_trace TEXT,

    -- Constraints
    CONSTRAINT ct_valid_stage CHECK (pipeline_stage IN (
        'upstream_cl_gate',
        'phase1_company_matching',
        'phase1b_unmatched_hold',
        'phase2_domain_resolution',
        'phase3_email_pattern_waterfall',
        'phase4_pattern_verification',
        'bit_scoring',
        'neon_write'
    )),
    CONSTRAINT ct_valid_failure_code CHECK (failure_code IN (
        -- Upstream gate failures
        'CT_UPSTREAM_CL_NOT_VERIFIED',
        -- Phase 1 failures
        'CT_MATCH_NO_COMPANY',
        'CT_MATCH_AMBIGUOUS',
        'CT_MATCH_COLLISION',
        -- Phase 2 failures
        'CT_DOMAIN_UNRESOLVED',
        'CT_DOMAIN_DNS_FAIL',
        'CT_DOMAIN_MX_FAIL',
        -- Phase 3 failures
        'CT_PATTERN_NOT_FOUND',
        'CT_TIER2_EXHAUSTED',
        'CT_PROVIDER_ERROR',
        'CT_LIFECYCLE_GATE_FAIL',
        'CT_BIT_THRESHOLD_FAIL',
        -- Phase 4 failures
        'CT_VERIFICATION_FAIL',
        'CT_SMTP_REJECT',
        -- General failures
        'CT_MISSING_SOV_ID',
        'CT_MISSING_CONTEXT_ID',
        'CT_NEON_WRITE_FAIL',
        'CT_UNKNOWN_ERROR'
    ))
);

-- Indexes for company-target errors
CREATE INDEX IF NOT EXISTS idx_ct_errors_company ON outreach_errors.company_target_errors(company_sov_id);
CREATE INDEX IF NOT EXISTS idx_ct_errors_context ON outreach_errors.company_target_errors(outreach_context_id);
CREATE INDEX IF NOT EXISTS idx_ct_errors_unresolved ON outreach_errors.company_target_errors(resolved_at) WHERE resolved_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_ct_errors_severity ON outreach_errors.company_target_errors(severity) WHERE severity = 'blocking';

COMMENT ON TABLE outreach_errors.company_target_errors IS
    'Error table for Company Target sub-hub. Failures are work items, not states.';

-- =============================================================================
-- PEOPLE INTELLIGENCE ERROR TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_errors.people_intelligence_errors (
    -- Primary key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Required identity keys
    company_sov_id UUID NOT NULL,
    outreach_context_id UUID NOT NULL,
    person_id UUID,  -- May be NULL if failure before person identification

    -- Hub identification
    hub_name VARCHAR(50) NOT NULL DEFAULT 'people-intelligence',
    pipeline_stage VARCHAR(100) NOT NULL,

    -- Failure details
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,

    -- Control flags
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    severity outreach_errors.severity_level NOT NULL DEFAULT 'blocking',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    resolved_by VARCHAR(100),

    -- Additional context
    raw_input JSONB,
    stack_trace TEXT,

    -- Constraints
    CONSTRAINT pi_valid_stage CHECK (pipeline_stage IN (
        'phase5_email_generation',
        'phase6_slot_assignment',
        'phase7_enrichment_queue',
        'phase8_output_writer',
        'email_verification',
        'movement_detection'
    )),
    CONSTRAINT pi_valid_failure_code CHECK (failure_code IN (
        -- Phase 5 failures
        'PI_NO_PATTERN_AVAILABLE',
        'PI_EMAIL_GEN_FAIL',
        'PI_INVALID_NAME',
        -- Phase 6 failures
        'PI_SLOT_COLLISION',
        'PI_NO_SLOTS_DEFINED',
        'PI_INVALID_TITLE',
        -- Phase 7 failures
        'PI_ENRICHMENT_NO_DEFICIT',
        'PI_TIER2_EXHAUSTED',
        'PI_LIFECYCLE_GATE_FAIL',
        -- Phase 8 failures
        'PI_OUTPUT_WRITE_FAIL',
        'PI_CSV_FORMAT_ERROR',
        -- Verification failures
        'PI_VERIFICATION_FAIL',
        'PI_MILLIONVERIFIER_ERROR',
        'PI_BATCH_LIMIT_EXCEEDED',
        -- General failures
        'PI_MISSING_COMPANY_ANCHOR',
        'PI_MISSING_CONTEXT_ID',
        'PI_UNKNOWN_ERROR'
    ))
);

-- Indexes for people-intelligence errors
CREATE INDEX IF NOT EXISTS idx_pi_errors_company ON outreach_errors.people_intelligence_errors(company_sov_id);
CREATE INDEX IF NOT EXISTS idx_pi_errors_context ON outreach_errors.people_intelligence_errors(outreach_context_id);
CREATE INDEX IF NOT EXISTS idx_pi_errors_person ON outreach_errors.people_intelligence_errors(person_id) WHERE person_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pi_errors_unresolved ON outreach_errors.people_intelligence_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach_errors.people_intelligence_errors IS
    'Error table for People Intelligence sub-hub. Failures are work items, not states.';

-- =============================================================================
-- DOL FILINGS ERROR TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_errors.dol_filings_errors (
    -- Primary key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Required identity keys
    company_sov_id UUID,  -- May be NULL if EIN match failed
    outreach_context_id UUID NOT NULL,
    ein VARCHAR(20),  -- EIN from filing
    filing_id VARCHAR(50),  -- DOL filing identifier

    -- Hub identification
    hub_name VARCHAR(50) NOT NULL DEFAULT 'dol-filings',
    pipeline_stage VARCHAR(100) NOT NULL,

    -- Failure details
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,

    -- Control flags
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    severity outreach_errors.severity_level NOT NULL DEFAULT 'blocking',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    resolved_by VARCHAR(100),

    -- Additional context
    raw_input JSONB,
    stack_trace TEXT,

    -- Constraints
    CONSTRAINT dol_valid_stage CHECK (pipeline_stage IN (
        'csv_ingest',
        'record_parse',
        'ein_matching',
        'filing_attach',
        'signal_emit'
    )),
    CONSTRAINT dol_valid_failure_code CHECK (failure_code IN (
        -- Ingest failures
        'DOL_CSV_NOT_FOUND',
        'DOL_CSV_FORMAT_ERROR',
        'DOL_CSV_ENCODING_ERROR',
        -- Parse failures
        'DOL_MISSING_EIN',
        'DOL_INVALID_EIN_FORMAT',
        'DOL_MISSING_REQUIRED_FIELD',
        -- Match failures
        'DOL_EIN_NO_MATCH',
        'DOL_EIN_MULTIPLE_MATCH',
        'DOL_LIFECYCLE_GATE_FAIL',
        -- Attach failures
        'DOL_ATTACH_DUPLICATE',
        'DOL_NEON_WRITE_FAIL',
        -- General failures
        'DOL_MISSING_CONTEXT_ID',
        'DOL_UNKNOWN_ERROR'
    ))
);

-- Indexes for dol-filings errors
CREATE INDEX IF NOT EXISTS idx_dol_errors_company ON outreach_errors.dol_filings_errors(company_sov_id) WHERE company_sov_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dol_errors_context ON outreach_errors.dol_filings_errors(outreach_context_id);
CREATE INDEX IF NOT EXISTS idx_dol_errors_ein ON outreach_errors.dol_filings_errors(ein) WHERE ein IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dol_errors_unresolved ON outreach_errors.dol_filings_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach_errors.dol_filings_errors IS
    'Error table for DOL Filings sub-hub. Failures are work items, not states.';

-- =============================================================================
-- OUTREACH EXECUTION ERROR TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_errors.outreach_execution_errors (
    -- Primary key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Required identity keys
    company_sov_id UUID NOT NULL,
    outreach_context_id UUID NOT NULL,
    campaign_id UUID,  -- May be NULL if failure before campaign creation

    -- Hub identification
    hub_name VARCHAR(50) NOT NULL DEFAULT 'outreach-execution',
    pipeline_stage VARCHAR(100) NOT NULL,

    -- Failure details
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,

    -- Control flags
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    severity outreach_errors.severity_level NOT NULL DEFAULT 'blocking',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    resolved_by VARCHAR(100),

    -- Additional context
    raw_input JSONB,
    stack_trace TEXT,

    -- Constraints
    CONSTRAINT oe_valid_stage CHECK (pipeline_stage IN (
        'golden_rule_validation',
        'bit_evaluation',
        'contact_selection',
        'campaign_creation',
        'sequence_execution',
        'send_execution',
        'engagement_tracking'
    )),
    CONSTRAINT oe_valid_failure_code CHECK (failure_code IN (
        -- Golden Rule failures
        'OE_MISSING_SOV_ID',
        'OE_MISSING_DOMAIN',
        'OE_MISSING_PATTERN',
        'OE_LIFECYCLE_GATE_FAIL',
        -- BIT failures
        'OE_BIT_BELOW_THRESHOLD',
        'OE_BIT_ENGINE_ERROR',
        -- Contact failures
        'OE_NO_CONTACTS_AVAILABLE',
        'OE_COOLING_OFF_ACTIVE',
        'OE_RATE_LIMIT_EXCEEDED',
        -- Campaign failures
        'OE_CAMPAIGN_CREATE_FAIL',
        'OE_SEQUENCE_NOT_FOUND',
        -- Send failures
        'OE_SEND_FAIL',
        'OE_BOUNCE_DETECTED',
        'OE_SPAM_FLAGGED',
        -- General failures
        'OE_MISSING_CONTEXT_ID',
        'OE_UNKNOWN_ERROR'
    ))
);

-- Indexes for outreach-execution errors
CREATE INDEX IF NOT EXISTS idx_oe_errors_company ON outreach_errors.outreach_execution_errors(company_sov_id);
CREATE INDEX IF NOT EXISTS idx_oe_errors_context ON outreach_errors.outreach_execution_errors(outreach_context_id);
CREATE INDEX IF NOT EXISTS idx_oe_errors_campaign ON outreach_errors.outreach_execution_errors(campaign_id) WHERE campaign_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_oe_errors_unresolved ON outreach_errors.outreach_execution_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach_errors.outreach_execution_errors IS
    'Error table for Outreach Execution sub-hub. Failures are work items, not states.';

-- =============================================================================
-- BLOG CONTENT ERROR TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_errors.blog_content_errors (
    -- Primary key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Required identity keys
    company_sov_id UUID,  -- May be NULL if company match failed
    outreach_context_id UUID NOT NULL,
    content_source VARCHAR(100),  -- Source of the content

    -- Hub identification
    hub_name VARCHAR(50) NOT NULL DEFAULT 'blog-content',
    pipeline_stage VARCHAR(100) NOT NULL,

    -- Failure details
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT NOT NULL,

    -- Control flags
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,
    severity outreach_errors.severity_level NOT NULL DEFAULT 'blocking',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,
    resolved_by VARCHAR(100),

    -- Additional context
    raw_input JSONB,
    stack_trace TEXT,

    -- Constraints
    CONSTRAINT bc_valid_stage CHECK (pipeline_stage IN (
        'content_ingest',
        'company_match',
        'event_classification',
        'lifecycle_check',
        'signal_emit'
    )),
    CONSTRAINT bc_valid_failure_code CHECK (failure_code IN (
        -- Ingest failures
        'BC_SOURCE_UNAVAILABLE',
        'BC_PARSE_ERROR',
        -- Match failures
        'BC_COMPANY_NOT_FOUND',
        'BC_AMBIGUOUS_COMPANY',
        -- Classification failures
        'BC_UNKNOWN_EVENT_TYPE',
        'BC_CLASSIFICATION_ERROR',
        -- Gate failures
        'BC_LIFECYCLE_GATE_FAIL',
        'BC_COMPANY_NOT_ACTIVE',
        -- Signal failures
        'BC_SIGNAL_EMIT_FAIL',
        'BC_BIT_ENGINE_ERROR',
        -- General failures
        'BC_MISSING_CONTEXT_ID',
        'BC_UNKNOWN_ERROR'
    ))
);

-- Indexes for blog-content errors
CREATE INDEX IF NOT EXISTS idx_bc_errors_company ON outreach_errors.blog_content_errors(company_sov_id) WHERE company_sov_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bc_errors_context ON outreach_errors.blog_content_errors(outreach_context_id);
CREATE INDEX IF NOT EXISTS idx_bc_errors_source ON outreach_errors.blog_content_errors(content_source) WHERE content_source IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_bc_errors_unresolved ON outreach_errors.blog_content_errors(resolved_at) WHERE resolved_at IS NULL;

COMMENT ON TABLE outreach_errors.blog_content_errors IS
    'Error table for Blog Content sub-hub. Failures are work items, not states.';

-- =============================================================================
-- ERROR RESOLUTION FUNCTIONS
-- =============================================================================

-- Resolve an error (generic function that works across tables)
CREATE OR REPLACE FUNCTION outreach_errors.resolve_error(
    p_table_name VARCHAR(50),
    p_error_id UUID,
    p_resolution_note TEXT,
    p_resolved_by VARCHAR(100) DEFAULT 'system'
) RETURNS BOOLEAN AS $$
DECLARE
    v_sql TEXT;
BEGIN
    v_sql := format(
        'UPDATE outreach_errors.%I SET resolved_at = NOW(), resolution_note = $1, resolved_by = $2 WHERE error_id = $3 AND resolved_at IS NULL',
        p_table_name
    );
    EXECUTE v_sql USING p_resolution_note, p_resolved_by, p_error_id;
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Check if context has blocking errors
CREATE OR REPLACE FUNCTION outreach_errors.context_has_blocking_errors(
    p_context_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_has_errors BOOLEAN := FALSE;
BEGIN
    -- Check all error tables for unresolved blocking errors
    SELECT EXISTS (
        SELECT 1 FROM outreach_errors.company_target_errors
        WHERE outreach_context_id = p_context_id
          AND severity = 'blocking'
          AND resolved_at IS NULL
        UNION ALL
        SELECT 1 FROM outreach_errors.people_intelligence_errors
        WHERE outreach_context_id = p_context_id
          AND severity = 'blocking'
          AND resolved_at IS NULL
        UNION ALL
        SELECT 1 FROM outreach_errors.dol_filings_errors
        WHERE outreach_context_id = p_context_id
          AND severity = 'blocking'
          AND resolved_at IS NULL
        UNION ALL
        SELECT 1 FROM outreach_errors.outreach_execution_errors
        WHERE outreach_context_id = p_context_id
          AND severity = 'blocking'
          AND resolved_at IS NULL
        UNION ALL
        SELECT 1 FROM outreach_errors.blog_content_errors
        WHERE outreach_context_id = p_context_id
          AND severity = 'blocking'
          AND resolved_at IS NULL
    ) INTO v_has_errors;

    RETURN v_has_errors;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- All unresolved errors across all sub-hubs
CREATE OR REPLACE VIEW outreach_errors.all_unresolved_errors AS
SELECT
    error_id, company_sov_id, outreach_context_id, hub_name,
    pipeline_stage, failure_code, blocking_reason, severity, created_at
FROM outreach_errors.company_target_errors WHERE resolved_at IS NULL
UNION ALL
SELECT
    error_id, company_sov_id, outreach_context_id, hub_name,
    pipeline_stage, failure_code, blocking_reason, severity, created_at
FROM outreach_errors.people_intelligence_errors WHERE resolved_at IS NULL
UNION ALL
SELECT
    error_id, company_sov_id, outreach_context_id, hub_name,
    pipeline_stage, failure_code, blocking_reason, severity, created_at
FROM outreach_errors.dol_filings_errors WHERE resolved_at IS NULL
UNION ALL
SELECT
    error_id, company_sov_id, outreach_context_id, hub_name,
    pipeline_stage, failure_code, blocking_reason, severity, created_at
FROM outreach_errors.outreach_execution_errors WHERE resolved_at IS NULL
UNION ALL
SELECT
    error_id, company_sov_id, outreach_context_id, hub_name,
    pipeline_stage, failure_code, blocking_reason, severity, created_at
FROM outreach_errors.blog_content_errors WHERE resolved_at IS NULL;

-- Error counts by hub and severity
CREATE OR REPLACE VIEW outreach_errors.error_summary AS
SELECT
    hub_name,
    severity::TEXT,
    COUNT(*) AS error_count,
    COUNT(*) FILTER (WHERE resolved_at IS NULL) AS unresolved_count
FROM (
    SELECT hub_name, severity, resolved_at FROM outreach_errors.company_target_errors
    UNION ALL
    SELECT hub_name, severity, resolved_at FROM outreach_errors.people_intelligence_errors
    UNION ALL
    SELECT hub_name, severity, resolved_at FROM outreach_errors.dol_filings_errors
    UNION ALL
    SELECT hub_name, severity, resolved_at FROM outreach_errors.outreach_execution_errors
    UNION ALL
    SELECT hub_name, severity, resolved_at FROM outreach_errors.blog_content_errors
) AS all_errors
GROUP BY hub_name, severity
ORDER BY hub_name, severity;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON SCHEMA outreach_errors IS
    'Per-sub-hub error tables. Failures are work items, not states. No retries in same context.';

COMMENT ON FUNCTION outreach_errors.resolve_error IS
    'Resolve an error row. Requires manual intervention or new context.';

COMMENT ON FUNCTION outreach_errors.context_has_blocking_errors IS
    'Check if a context has unresolved blocking errors. If TRUE, spend is frozen.';

COMMENT ON VIEW outreach_errors.all_unresolved_errors IS
    'All unresolved errors across all sub-hubs. Use for monitoring and triage.';
