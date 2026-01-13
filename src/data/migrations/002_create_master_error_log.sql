-- ============================================================================
-- MIGRATION 002: Create Master Error Log Infrastructure
-- ============================================================================
-- File: 002_create_master_error_log.sql
-- Created: 2025-12-17
-- Purpose: Create shq_master_error_log table for global error visibility
-- Doctrine: Barton Doctrine / Bicycle Wheel v1.1
--
-- CORE DOCTRINE:
--   1. Local First: Errors written to sub-hub tables FIRST
--   2. Read-Only Global: Append-only, no UPDATE/DELETE
--   3. Correlation Required: Every record MUST have correlation_id
-- ============================================================================

-- ============================================================================
-- STEP 1: Create shq_master_error_log table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.shq_master_error_log (
    -- Primary Key
    error_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Temporal
    timestamp_utc       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Correlation (REQUIRED - per Barton Doctrine)
    correlation_id      UUID NOT NULL,

    -- Location (Hub/Sub-Hub/Process/Phase)
    hub                 VARCHAR(50) NOT NULL,
    sub_hub             VARCHAR(50),
    process_id          VARCHAR(100) NOT NULL,
    pipeline_phase      VARCHAR(50) NOT NULL,

    -- Entity Context
    entity_type         VARCHAR(50) NOT NULL,
    entity_id           VARCHAR(100),

    -- Error Classification
    severity            VARCHAR(20) NOT NULL,
    error_code          VARCHAR(50) NOT NULL,
    error_message       TEXT NOT NULL,

    -- Source Context
    source_tool         VARCHAR(100),
    operating_mode      VARCHAR(20) NOT NULL,

    -- Actionability
    retryable           BOOLEAN NOT NULL DEFAULT false,

    -- Cost Impact
    cost_impact_usd     DECIMAL(10, 4),

    -- Raw Context
    metadata            JSONB,

    -- Constraints
    CONSTRAINT chk_master_error_correlation_id_required
        CHECK (correlation_id IS NOT NULL),
    CONSTRAINT chk_master_error_hub_valid
        CHECK (hub IN ('company', 'people', 'dol', 'blog_news', 'outreach', 'platform')),
    CONSTRAINT chk_master_error_severity_valid
        CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT chk_master_error_entity_type_valid
        CHECK (entity_type IN ('company', 'person', 'filing', 'article', 'batch', 'unknown')),
    CONSTRAINT chk_master_error_operating_mode_valid
        CHECK (operating_mode IN ('BURN_IN', 'STEADY_STATE'))
);

-- ============================================================================
-- STEP 2: Create Indexes for Common Query Patterns
-- ============================================================================

-- Primary lookup: correlation_id (end-to-end tracing)
CREATE INDEX IF NOT EXISTS idx_master_error_correlation
    ON public.shq_master_error_log (correlation_id);

-- Time-based queries (newest first)
CREATE INDEX IF NOT EXISTS idx_master_error_timestamp
    ON public.shq_master_error_log (timestamp_utc DESC);

-- Hub/Sub-Hub filtering
CREATE INDEX IF NOT EXISTS idx_master_error_hub_subhub
    ON public.shq_master_error_log (hub, sub_hub);

-- Process ID lookup
CREATE INDEX IF NOT EXISTS idx_master_error_process_id
    ON public.shq_master_error_log (process_id);

-- High-severity alerting (partial index)
CREATE INDEX IF NOT EXISTS idx_master_error_severity_high_critical
    ON public.shq_master_error_log (severity, timestamp_utc DESC)
    WHERE severity IN ('HIGH', 'CRITICAL');

-- Entity lookup
CREATE INDEX IF NOT EXISTS idx_master_error_entity
    ON public.shq_master_error_log (entity_type, entity_id);

-- Error code aggregation
CREATE INDEX IF NOT EXISTS idx_master_error_error_code
    ON public.shq_master_error_log (error_code);

-- Operating mode + time (burn-in vs steady-state analysis)
CREATE INDEX IF NOT EXISTS idx_master_error_operating_mode
    ON public.shq_master_error_log (operating_mode, timestamp_utc DESC);

-- Composite index for alerting queries
CREATE INDEX IF NOT EXISTS idx_master_error_alerting
    ON public.shq_master_error_log (operating_mode, severity, timestamp_utc DESC);

-- ============================================================================
-- STEP 3: Enable Row-Level Security (Append-Only Enforcement)
-- ============================================================================

ALTER TABLE public.shq_master_error_log ENABLE ROW LEVEL SECURITY;

-- Allow INSERT from all roles (append-only)
DROP POLICY IF EXISTS policy_master_error_insert ON public.shq_master_error_log;
CREATE POLICY policy_master_error_insert ON public.shq_master_error_log
    FOR INSERT
    WITH CHECK (true);

-- Allow SELECT from all roles (read access)
DROP POLICY IF EXISTS policy_master_error_select ON public.shq_master_error_log;
CREATE POLICY policy_master_error_select ON public.shq_master_error_log
    FOR SELECT
    USING (true);

-- NOTE: No UPDATE or DELETE policies = operations denied by RLS

-- ============================================================================
-- STEP 4: Add Table and Column Comments
-- ============================================================================

COMMENT ON TABLE public.shq_master_error_log IS
    'Global error visibility across all hubs/sub-hubs. APPEND-ONLY. Correlation required. See PRD_MASTER_ERROR_LOG.md';

COMMENT ON COLUMN public.shq_master_error_log.error_id IS
    'Primary key, auto-generated UUID';

COMMENT ON COLUMN public.shq_master_error_log.timestamp_utc IS
    'When the error occurred (UTC)';

COMMENT ON COLUMN public.shq_master_error_log.correlation_id IS
    'End-to-end trace ID. REQUIRED. Links to local sub-hub logs for troubleshooting.';

COMMENT ON COLUMN public.shq_master_error_log.hub IS
    'Source hub: company, people, dol, blog_news, outreach, platform';

COMMENT ON COLUMN public.shq_master_error_log.sub_hub IS
    'Specific sub-hub or NULL for hub-level errors';

COMMENT ON COLUMN public.shq_master_error_log.process_id IS
    'Canonical process identifier. Format: hub.subhub.pipeline.phase';

COMMENT ON COLUMN public.shq_master_error_log.pipeline_phase IS
    'Phase name or number (e.g., phase1, phase5, ingest)';

COMMENT ON COLUMN public.shq_master_error_log.entity_type IS
    'Type of entity involved: company, person, filing, article, batch, unknown';

COMMENT ON COLUMN public.shq_master_error_log.entity_id IS
    'ID of the entity (company_id, person_id, filing_id, etc.)';

COMMENT ON COLUMN public.shq_master_error_log.severity IS
    'Error severity: LOW, MEDIUM, HIGH, CRITICAL';

COMMENT ON COLUMN public.shq_master_error_log.error_code IS
    'Machine-readable error code (e.g., PSH-P5-001, DOL-002, PIPE-301)';

COMMENT ON COLUMN public.shq_master_error_log.error_message IS
    'Human-readable error description';

COMMENT ON COLUMN public.shq_master_error_log.source_tool IS
    'Tool or service that failed (e.g., Hunter.io, Firecrawl, dol_parser)';

COMMENT ON COLUMN public.shq_master_error_log.operating_mode IS
    'BURN_IN or STEADY_STATE. Affects alerting thresholds.';

COMMENT ON COLUMN public.shq_master_error_log.retryable IS
    'Can the system retry this operation automatically?';

COMMENT ON COLUMN public.shq_master_error_log.cost_impact_usd IS
    'Estimated cost impact in USD (optional)';

COMMENT ON COLUMN public.shq_master_error_log.metadata IS
    'Additional context as JSONB (stack trace, request/response, etc.)';

-- ============================================================================
-- STEP 5: Create Orphan Errors Table (for rejected events)
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.shq_orphan_errors (
    orphan_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp_utc       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    raw_event           JSONB NOT NULL,
    rejection_reason    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orphan_errors_timestamp
    ON public.shq_orphan_errors (timestamp_utc DESC);

COMMENT ON TABLE public.shq_orphan_errors IS
    'Errors rejected due to missing correlation_id or validation failures. Investigate these.';

-- ============================================================================
-- STEP 6: Create Helper Function for Error Emission
-- ============================================================================

CREATE OR REPLACE FUNCTION public.emit_master_error(
    p_correlation_id    UUID,
    p_hub               VARCHAR(50),
    p_sub_hub           VARCHAR(50),
    p_process_id        VARCHAR(100),
    p_pipeline_phase    VARCHAR(50),
    p_entity_type       VARCHAR(50),
    p_entity_id         VARCHAR(100),
    p_severity          VARCHAR(20),
    p_error_code        VARCHAR(50),
    p_error_message     TEXT,
    p_source_tool       VARCHAR(100) DEFAULT NULL,
    p_operating_mode    VARCHAR(20) DEFAULT 'STEADY_STATE',
    p_retryable         BOOLEAN DEFAULT false,
    p_cost_impact_usd   DECIMAL(10,4) DEFAULT NULL,
    p_metadata          JSONB DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_error_id UUID;
BEGIN
    -- Validate correlation_id (REQUIRED per Barton Doctrine)
    IF p_correlation_id IS NULL THEN
        -- Log to orphan errors and raise exception
        INSERT INTO public.shq_orphan_errors (raw_event, rejection_reason)
        VALUES (
            jsonb_build_object(
                'hub', p_hub,
                'process_id', p_process_id,
                'error_code', p_error_code,
                'error_message', p_error_message
            ),
            'Missing correlation_id - REJECTED per Barton Doctrine'
        );
        RAISE EXCEPTION 'correlation_id is REQUIRED per Barton Doctrine';
    END IF;

    -- Insert error record
    INSERT INTO public.shq_master_error_log (
        correlation_id, hub, sub_hub, process_id, pipeline_phase,
        entity_type, entity_id, severity, error_code, error_message,
        source_tool, operating_mode, retryable, cost_impact_usd, metadata
    ) VALUES (
        p_correlation_id, p_hub, p_sub_hub, p_process_id, p_pipeline_phase,
        p_entity_type, p_entity_id, p_severity, p_error_code, p_error_message,
        p_source_tool, p_operating_mode, p_retryable, p_cost_impact_usd, p_metadata
    )
    RETURNING error_id INTO v_error_id;

    RETURN v_error_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.emit_master_error IS
    'Emits an error event to shq_master_error_log. Validates correlation_id (REQUIRED).';

-- ============================================================================
-- STEP 7: Create Alerting Views
-- ============================================================================

-- View: Recent CRITICAL errors (for immediate alerting)
CREATE OR REPLACE VIEW public.vw_master_error_critical_recent AS
SELECT
    error_id,
    timestamp_utc,
    correlation_id,
    hub,
    sub_hub,
    process_id,
    pipeline_phase,
    entity_type,
    entity_id,
    error_code,
    error_message,
    source_tool,
    operating_mode,
    retryable
FROM public.shq_master_error_log
WHERE
    severity = 'CRITICAL'
    AND timestamp_utc >= NOW() - INTERVAL '1 hour'
ORDER BY timestamp_utc DESC;

COMMENT ON VIEW public.vw_master_error_critical_recent IS
    'CRITICAL errors from the last hour. Use for immediate alerting.';

-- View: Error summary by hub (last 24 hours)
CREATE OR REPLACE VIEW public.vw_master_error_summary_by_hub AS
SELECT
    hub,
    sub_hub,
    operating_mode,
    COUNT(*) as total_errors,
    COUNT(*) FILTER (WHERE severity = 'CRITICAL') as critical_count,
    COUNT(*) FILTER (WHERE severity = 'HIGH') as high_count,
    COUNT(*) FILTER (WHERE severity = 'MEDIUM') as medium_count,
    COUNT(*) FILTER (WHERE severity = 'LOW') as low_count,
    COUNT(*) FILTER (WHERE retryable = true) as retryable_count,
    MAX(timestamp_utc) as last_error_at
FROM public.shq_master_error_log
WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
GROUP BY hub, sub_hub, operating_mode
ORDER BY total_errors DESC;

COMMENT ON VIEW public.vw_master_error_summary_by_hub IS
    'Error summary by hub for the last 24 hours. Use for daily reporting.';

-- View: Error trend by error_code (last 7 days)
CREATE OR REPLACE VIEW public.vw_master_error_trend_by_code AS
SELECT
    error_code,
    hub,
    process_id,
    DATE(timestamp_utc) as error_date,
    COUNT(*) as error_count,
    COUNT(DISTINCT correlation_id) as unique_batches_affected
FROM public.shq_master_error_log
WHERE timestamp_utc >= NOW() - INTERVAL '7 days'
GROUP BY error_code, hub, process_id, DATE(timestamp_utc)
ORDER BY error_date DESC, error_count DESC;

COMMENT ON VIEW public.vw_master_error_trend_by_code IS
    'Error trends by error_code for the last 7 days. Use for pattern detection.';

-- ============================================================================
-- STEP 8: Verify Migration
-- ============================================================================

DO $$
DECLARE
    v_table_exists BOOLEAN;
    v_index_count INTEGER;
    v_function_exists BOOLEAN;
BEGIN
    -- Check table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'shq_master_error_log'
    ) INTO v_table_exists;

    -- Check index count
    SELECT COUNT(*) INTO v_index_count
    FROM pg_indexes
    WHERE tablename = 'shq_master_error_log';

    -- Check function exists
    SELECT EXISTS (
        SELECT FROM pg_proc
        WHERE proname = 'emit_master_error'
    ) INTO v_function_exists;

    -- Report results
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration 002 Verification:';
    RAISE NOTICE '  Table shq_master_error_log: %', CASE WHEN v_table_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '  Index count: %', v_index_count;
    RAISE NOTICE '  Function emit_master_error: %', CASE WHEN v_function_exists THEN 'EXISTS' ELSE 'MISSING' END;
    RAISE NOTICE '========================================';

    IF NOT v_table_exists THEN
        RAISE EXCEPTION 'Migration failed: shq_master_error_log table not created';
    END IF;
END $$;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Update sub-hub error handlers to call emit_master_error()
-- 2. Configure alerting rules per PRD_MASTER_ERROR_LOG.md Section 6
-- 3. Set up Grafana dashboards using the views created above
-- ============================================================================
