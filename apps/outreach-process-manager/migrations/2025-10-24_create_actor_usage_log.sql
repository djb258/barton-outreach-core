-- ============================================================================
-- Migration: Create marketing.actor_usage_log
-- Date: 2025-10-24
-- Purpose: Track Apify actor usage and costs for governance and budgeting
-- ============================================================================

-- ============================================================================
-- TABLE: marketing.actor_usage_log
-- ============================================================================
-- Tracks every Apify actor run with cost estimation and item counts
-- Purpose: Cost governance, budget tracking, usage analytics
-- Integration: Composio MCP apify_run_actor_sync_get_dataset_items
-- ============================================================================

CREATE TABLE IF NOT EXISTS marketing.actor_usage_log (
    id SERIAL PRIMARY KEY,

    -- Apify Identifiers
    run_id TEXT NOT NULL,                          -- Apify run ID (unique per execution)
    actor_id TEXT NOT NULL,                        -- Apify actor ID (e.g., code_crafter~leads-finder)
    dataset_id TEXT,                               -- Apify dataset ID (result storage)

    -- Tool Information
    tool_name TEXT DEFAULT 'apify_run_actor_sync_get_dataset_items',

    -- Cost Tracking
    estimated_cost NUMERIC(6,2) DEFAULT 0.00       -- Estimated cost in USD
        CHECK (estimated_cost >= 0.00),

    -- Usage Metrics
    total_items INTEGER DEFAULT 0                   -- Number of items returned/processed
        CHECK (total_items >= 0),

    -- Execution Timing
    run_started_at TIMESTAMPTZ DEFAULT NOW(),      -- Run start timestamp
    run_completed_at TIMESTAMPTZ,                  -- Run completion timestamp

    -- Status
    status TEXT DEFAULT 'running'
        CHECK (status IN ('running', 'success', 'failed', 'aborted')),

    -- Additional Information
    notes TEXT,                                     -- Human-readable notes
    metadata JSONB DEFAULT '{}',                    -- Additional run metadata

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE marketing.actor_usage_log IS
    'Apify actor usage tracking table for cost governance and budgeting.
    Records every actor run with estimated costs and item counts.

    Use Cases:
    - Track monthly Apify costs
    - Budget forecasting and alerts
    - Usage analytics by actor
    - Identify cost optimization opportunities
    - Audit actor executions';

COMMENT ON COLUMN marketing.actor_usage_log.run_id IS
    'Apify run ID (unique per execution). Links to Apify console.';

COMMENT ON COLUMN marketing.actor_usage_log.actor_id IS
    'Apify actor ID (e.g., code_crafter~leads-finder, apify~linkedin-profile-scraper).';

COMMENT ON COLUMN marketing.actor_usage_log.dataset_id IS
    'Apify dataset ID containing result data. NULL if run failed.';

COMMENT ON COLUMN marketing.actor_usage_log.tool_name IS
    'Composio MCP tool name used to execute actor.';

COMMENT ON COLUMN marketing.actor_usage_log.estimated_cost IS
    'Estimated cost in USD for this run. Based on actor pricing and item count.';

COMMENT ON COLUMN marketing.actor_usage_log.total_items IS
    'Number of items returned or processed by the actor.';

COMMENT ON COLUMN marketing.actor_usage_log.status IS
    'Run status: running (in progress), success (completed), failed (error), aborted (cancelled).';

COMMENT ON COLUMN marketing.actor_usage_log.notes IS
    'Human-readable notes about the run (e.g., "Monthly LinkedIn refresh", "Trial enrichment").';

COMMENT ON COLUMN marketing.actor_usage_log.metadata IS
    'Additional run metadata (JSONB): input parameters, error details, performance metrics, etc.';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index on run_id for lookup
CREATE INDEX IF NOT EXISTS idx_actor_usage_log_run_id
    ON marketing.actor_usage_log(run_id);

-- Index on actor_id for filtering by actor
CREATE INDEX IF NOT EXISTS idx_actor_usage_log_actor_id
    ON marketing.actor_usage_log(actor_id);

-- Index on status for filtering active/failed runs
CREATE INDEX IF NOT EXISTS idx_actor_usage_log_status
    ON marketing.actor_usage_log(status);

-- Index on run_started_at for chronological queries
CREATE INDEX IF NOT EXISTS idx_actor_usage_log_started_at
    ON marketing.actor_usage_log(run_started_at DESC);

-- Index on run_completed_at for completion tracking
CREATE INDEX IF NOT EXISTS idx_actor_usage_log_completed_at
    ON marketing.actor_usage_log(run_completed_at DESC NULLS LAST);

-- Composite index on actor_id + run_started_at for actor-specific queries
CREATE INDEX IF NOT EXISTS idx_actor_usage_log_actor_started
    ON marketing.actor_usage_log(actor_id, run_started_at DESC);

-- ============================================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.update_actor_usage_log_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_actor_usage_log_updated_at
    BEFORE UPDATE ON marketing.actor_usage_log
    FOR EACH ROW
    EXECUTE FUNCTION marketing.update_actor_usage_log_timestamp();

COMMENT ON TRIGGER trg_actor_usage_log_updated_at ON marketing.actor_usage_log IS
    'Automatically updates updated_at timestamp on row modification.';

-- ============================================================================
-- HELPER FUNCTION: generate_actor_usage_report()
-- ============================================================================
-- Generates usage summary report for specified date range
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.generate_actor_usage_report(
    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    actor_id TEXT,
    total_runs BIGINT,
    successful_runs BIGINT,
    failed_runs BIGINT,
    total_items BIGINT,
    total_cost NUMERIC,
    avg_cost_per_run NUMERIC,
    avg_items_per_run NUMERIC,
    first_run_date TIMESTAMPTZ,
    last_run_date TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        aul.actor_id,
        COUNT(*)::BIGINT AS total_runs,
        COUNT(*) FILTER (WHERE aul.status = 'success')::BIGINT AS successful_runs,
        COUNT(*) FILTER (WHERE aul.status = 'failed')::BIGINT AS failed_runs,
        SUM(aul.total_items)::BIGINT AS total_items,
        SUM(aul.estimated_cost)::NUMERIC AS total_cost,
        ROUND(AVG(aul.estimated_cost), 2) AS avg_cost_per_run,
        ROUND(AVG(aul.total_items), 2) AS avg_items_per_run,
        MIN(aul.run_started_at) AS first_run_date,
        MAX(aul.run_completed_at) AS last_run_date
    FROM marketing.actor_usage_log aul
    WHERE aul.run_started_at::DATE >= start_date
      AND aul.run_started_at::DATE <= end_date
    GROUP BY aul.actor_id
    ORDER BY SUM(aul.estimated_cost) DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.generate_actor_usage_report(DATE, DATE) IS
    'Generates usage summary report for Apify actors within date range.

    Returns per-actor aggregates:
    - total_runs: Total executions
    - successful_runs: Completed successfully
    - failed_runs: Failed executions
    - total_items: Total items processed
    - total_cost: Total estimated cost (USD)
    - avg_cost_per_run: Average cost per execution
    - avg_items_per_run: Average items per execution
    - first_run_date: First run in period
    - last_run_date: Last run in period

    Example:
      SELECT * FROM marketing.generate_actor_usage_report(
        ''2025-10-01''::DATE,
        ''2025-10-31''::DATE
      );';

-- ============================================================================
-- HELPER FUNCTION: get_monthly_cost_summary()
-- ============================================================================
-- Returns monthly cost breakdown for all actors
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.get_monthly_cost_summary(
    months_back INTEGER DEFAULT 6
)
RETURNS TABLE (
    month TEXT,
    actor_id TEXT,
    total_runs BIGINT,
    total_cost NUMERIC,
    total_items BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        TO_CHAR(aul.run_started_at, 'YYYY-MM') AS month,
        aul.actor_id,
        COUNT(*)::BIGINT AS total_runs,
        SUM(aul.estimated_cost)::NUMERIC AS total_cost,
        SUM(aul.total_items)::BIGINT AS total_items
    FROM marketing.actor_usage_log aul
    WHERE aul.run_started_at >= NOW() - (months_back || ' months')::INTERVAL
      AND aul.status = 'success'
    GROUP BY TO_CHAR(aul.run_started_at, 'YYYY-MM'), aul.actor_id
    ORDER BY month DESC, total_cost DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.get_monthly_cost_summary(INTEGER) IS
    'Returns monthly cost breakdown for all actors over specified period.
    Useful for budget tracking and trend analysis.';

-- ============================================================================
-- HELPER FUNCTION: get_actor_run_details()
-- ============================================================================
-- Returns detailed run information for specific actor
-- ============================================================================

CREATE OR REPLACE FUNCTION marketing.get_actor_run_details(
    p_actor_id TEXT,
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    run_id TEXT,
    dataset_id TEXT,
    status TEXT,
    total_items INTEGER,
    estimated_cost NUMERIC,
    run_started_at TIMESTAMPTZ,
    run_completed_at TIMESTAMPTZ,
    duration_minutes NUMERIC,
    notes TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        aul.run_id,
        aul.dataset_id,
        aul.status,
        aul.total_items,
        aul.estimated_cost,
        aul.run_started_at,
        aul.run_completed_at,
        CASE
            WHEN aul.run_completed_at IS NOT NULL THEN
                ROUND(EXTRACT(EPOCH FROM (aul.run_completed_at - aul.run_started_at)) / 60.0, 2)
            ELSE NULL
        END AS duration_minutes,
        aul.notes
    FROM marketing.actor_usage_log aul
    WHERE aul.actor_id = p_actor_id
      AND aul.run_started_at >= NOW() - (p_days_back || ' days')::INTERVAL
    ORDER BY aul.run_started_at DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION marketing.get_actor_run_details(TEXT, INTEGER) IS
    'Returns detailed run history for specific actor.
    Includes duration calculation and all run metadata.';

-- ============================================================================
-- USAGE EXAMPLES
-- ============================================================================

-- Example 1: Log a new actor run
-- INSERT INTO marketing.actor_usage_log (
--     run_id,
--     actor_id,
--     dataset_id,
--     estimated_cost,
--     total_items,
--     status,
--     notes
-- ) VALUES (
--     'run_abc123xyz',
--     'code_crafter~leads-finder',
--     'dataset_def456',
--     15.75,
--     1500,
--     'success',
--     'Monthly executive enrichment for 3 companies'
-- );

-- Example 2: Update run status after completion
-- UPDATE marketing.actor_usage_log
-- SET status = 'success',
--     run_completed_at = NOW(),
--     total_items = 1500,
--     estimated_cost = 15.75
-- WHERE run_id = 'run_abc123xyz';

-- Example 3: Generate monthly usage report
-- SELECT * FROM marketing.generate_actor_usage_report(
--     '2025-10-01'::DATE,
--     '2025-10-31'::DATE
-- );

-- Example 4: Get 6-month cost trend
-- SELECT * FROM marketing.get_monthly_cost_summary(6);

-- Example 5: Check recent runs for specific actor
-- SELECT * FROM marketing.get_actor_run_details(
--     'apify~linkedin-profile-scraper',
--     30
-- );

-- Example 6: Calculate total cost year-to-date
-- SELECT
--     SUM(estimated_cost) as ytd_total_cost,
--     COUNT(*) as ytd_total_runs,
--     AVG(estimated_cost) as ytd_avg_cost_per_run
-- FROM marketing.actor_usage_log
-- WHERE EXTRACT(YEAR FROM run_started_at) = EXTRACT(YEAR FROM NOW())
--   AND status = 'success';

-- Example 7: Find most expensive runs
-- SELECT
--     run_id,
--     actor_id,
--     estimated_cost,
--     total_items,
--     run_started_at,
--     notes
-- FROM marketing.actor_usage_log
-- WHERE status = 'success'
-- ORDER BY estimated_cost DESC
-- LIMIT 10;

-- Example 8: Budget alert - runs exceeding threshold
-- SELECT
--     run_id,
--     actor_id,
--     estimated_cost,
--     notes
-- FROM marketing.actor_usage_log
-- WHERE estimated_cost > 50.00
--   AND run_started_at >= NOW() - INTERVAL '7 days'
-- ORDER BY estimated_cost DESC;

-- ============================================================================
-- GRANTS (adjust as needed for your security model)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON marketing.actor_usage_log TO authenticated;
-- GRANT USAGE, SELECT ON SEQUENCE marketing.actor_usage_log_id_seq TO authenticated;
-- GRANT EXECUTE ON FUNCTION marketing.generate_actor_usage_report(DATE, DATE) TO authenticated;
-- GRANT EXECUTE ON FUNCTION marketing.get_monthly_cost_summary(INTEGER) TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Table: marketing.actor_usage_log (created)
-- Functions: generate_actor_usage_report(), get_monthly_cost_summary(), get_actor_run_details() (created)
-- Indexes: 6 performance indexes (created)
-- Trigger: Auto-update updated_at timestamp (created)
-- Purpose: Apify cost governance and budget tracking
-- Integration: Composio MCP actor executions
-- ============================================================================

-- ============================================================================
-- IMPLEMENTATION NOTES
-- ============================================================================
--
-- 1. Cost Estimation:
--    - Costs are estimates based on actor pricing
--    - Actual costs from Apify billing may vary
--    - Review monthly Apify invoices for accuracy
--    - Adjust cost factors as needed
--
-- 2. Logging Strategy:
--    - INSERT when actor run starts (status='running')
--    - UPDATE when run completes (status='success'/'failed'/'aborted')
--    - Include run_id, actor_id, dataset_id from Apify response
--    - Store estimated_cost based on actor pricing × item count
--
-- 3. Integration with Composio MCP:
--    - Log all apify_run_actor_sync_get_dataset_items calls
--    - Extract run metadata from Composio response
--    - Store in metadata JSONB field for audit trail
--
-- 4. Cost Governance:
--    - Set budget alerts using estimated_cost thresholds
--    - Monitor monthly costs via get_monthly_cost_summary()
--    - Identify expensive actors for optimization
--    - Track cost trends over time
--
-- 5. Reporting:
--    - Monthly summaries for budget reviews
--    - Per-actor cost breakdowns
--    - YTD cost tracking
--    - Budget vs actual analysis
--
-- 6. Optimization Opportunities:
--    - Identify actors with low item counts (high cost per item)
--    - Track failed runs for debugging
--    - Monitor run durations for performance
--    - Compare cost efficiency across actors
--
-- 7. Future Enhancements:
--    - Add budget_limit column for alerts
--    - Implement cost forecasting
--    - Add cost allocation by department/project
--    - Create materialized view for dashboard
--    - Add webhook notifications for budget overruns
--    - Integrate with Apify billing API for actual costs
--
-- 8. Audit Trail:
--    - Comprehensive run history
--    - Cost tracking per execution
--    - Metadata storage for debugging
--    - Status tracking for reliability metrics
--
-- ============================================================================
