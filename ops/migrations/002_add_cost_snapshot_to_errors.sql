-- =============================================================================
-- MIGRATION 002: Add Cost Snapshot Columns to Error Tables
-- =============================================================================
--
-- PURPOSE:
--   Add cost visibility at failure time to all error tables.
--   When a pipeline fails, we capture:
--   - Which tool was being used
--   - The tool's tier
--   - Cumulative cost up to that point
--   - Total call count at failure
--
-- DOCTRINE:
--   "Cost visibility at failure is mandatory. You cannot debug spend
--    without knowing exactly where the money went when things broke."
--
-- =============================================================================

-- -----------------------------------------------------------------------------
-- COMPANY TARGET ERRORS
-- -----------------------------------------------------------------------------

ALTER TABLE outreach_errors.company_target_errors
    ADD COLUMN IF NOT EXISTS tool_at_failure VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tool_tier_at_failure INTEGER,
    ADD COLUMN IF NOT EXISTS cumulative_cost_usd DECIMAL(12, 4) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS call_count_at_failure INTEGER DEFAULT 0;

COMMENT ON COLUMN outreach_errors.company_target_errors.tool_at_failure IS
    'Tool being used when failure occurred (NULL if not tool-related)';
COMMENT ON COLUMN outreach_errors.company_target_errors.tool_tier_at_failure IS
    'Tier of tool at failure (0, 1, or 2)';
COMMENT ON COLUMN outreach_errors.company_target_errors.cumulative_cost_usd IS
    'Total spend on this context up to failure point';
COMMENT ON COLUMN outreach_errors.company_target_errors.call_count_at_failure IS
    'Total tool calls in context up to failure point';

-- -----------------------------------------------------------------------------
-- PEOPLE INTELLIGENCE ERRORS
-- -----------------------------------------------------------------------------

ALTER TABLE outreach_errors.people_intelligence_errors
    ADD COLUMN IF NOT EXISTS tool_at_failure VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tool_tier_at_failure INTEGER,
    ADD COLUMN IF NOT EXISTS cumulative_cost_usd DECIMAL(12, 4) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS call_count_at_failure INTEGER DEFAULT 0;

COMMENT ON COLUMN outreach_errors.people_intelligence_errors.tool_at_failure IS
    'Tool being used when failure occurred (NULL if not tool-related)';
COMMENT ON COLUMN outreach_errors.people_intelligence_errors.tool_tier_at_failure IS
    'Tier of tool at failure (0, 1, or 2)';
COMMENT ON COLUMN outreach_errors.people_intelligence_errors.cumulative_cost_usd IS
    'Total spend on this context up to failure point';
COMMENT ON COLUMN outreach_errors.people_intelligence_errors.call_count_at_failure IS
    'Total tool calls in context up to failure point';

-- -----------------------------------------------------------------------------
-- DOL FILINGS ERRORS
-- -----------------------------------------------------------------------------

ALTER TABLE outreach_errors.dol_filings_errors
    ADD COLUMN IF NOT EXISTS tool_at_failure VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tool_tier_at_failure INTEGER,
    ADD COLUMN IF NOT EXISTS cumulative_cost_usd DECIMAL(12, 4) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS call_count_at_failure INTEGER DEFAULT 0;

COMMENT ON COLUMN outreach_errors.dol_filings_errors.tool_at_failure IS
    'Tool being used when failure occurred (NULL if not tool-related)';
COMMENT ON COLUMN outreach_errors.dol_filings_errors.tool_tier_at_failure IS
    'Tier of tool at failure (0, 1, or 2)';
COMMENT ON COLUMN outreach_errors.dol_filings_errors.cumulative_cost_usd IS
    'Total spend on this context up to failure point';
COMMENT ON COLUMN outreach_errors.dol_filings_errors.call_count_at_failure IS
    'Total tool calls in context up to failure point';

-- -----------------------------------------------------------------------------
-- OUTREACH EXECUTION ERRORS
-- -----------------------------------------------------------------------------

ALTER TABLE outreach_errors.outreach_execution_errors
    ADD COLUMN IF NOT EXISTS tool_at_failure VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tool_tier_at_failure INTEGER,
    ADD COLUMN IF NOT EXISTS cumulative_cost_usd DECIMAL(12, 4) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS call_count_at_failure INTEGER DEFAULT 0;

COMMENT ON COLUMN outreach_errors.outreach_execution_errors.tool_at_failure IS
    'Tool being used when failure occurred (NULL if not tool-related)';
COMMENT ON COLUMN outreach_errors.outreach_execution_errors.tool_tier_at_failure IS
    'Tier of tool at failure (0, 1, or 2)';
COMMENT ON COLUMN outreach_errors.outreach_execution_errors.cumulative_cost_usd IS
    'Total spend on this context up to failure point';
COMMENT ON COLUMN outreach_errors.outreach_execution_errors.call_count_at_failure IS
    'Total tool calls in context up to failure point';

-- -----------------------------------------------------------------------------
-- BLOG CONTENT ERRORS
-- -----------------------------------------------------------------------------

ALTER TABLE outreach_errors.blog_content_errors
    ADD COLUMN IF NOT EXISTS tool_at_failure VARCHAR(100),
    ADD COLUMN IF NOT EXISTS tool_tier_at_failure INTEGER,
    ADD COLUMN IF NOT EXISTS cumulative_cost_usd DECIMAL(12, 4) DEFAULT 0,
    ADD COLUMN IF NOT EXISTS call_count_at_failure INTEGER DEFAULT 0;

COMMENT ON COLUMN outreach_errors.blog_content_errors.tool_at_failure IS
    'Tool being used when failure occurred (NULL if not tool-related)';
COMMENT ON COLUMN outreach_errors.blog_content_errors.tool_tier_at_failure IS
    'Tier of tool at failure (0, 1, or 2)';
COMMENT ON COLUMN outreach_errors.blog_content_errors.cumulative_cost_usd IS
    'Total spend on this context up to failure point';
COMMENT ON COLUMN outreach_errors.blog_content_errors.call_count_at_failure IS
    'Total tool calls in context up to failure point';

-- -----------------------------------------------------------------------------
-- UPDATED EMIT ERROR FUNCTION WITH COST SNAPSHOT
-- -----------------------------------------------------------------------------

-- Helper function to emit error with cost snapshot
CREATE OR REPLACE FUNCTION outreach_errors.emit_error_with_cost(
    p_hub_name VARCHAR(50),
    p_company_sov_id UUID,
    p_context_id UUID,
    p_stage VARCHAR(100),
    p_failure_code VARCHAR(50),
    p_reason TEXT,
    p_severity outreach_errors.severity_level DEFAULT 'blocking',
    p_tool_name VARCHAR(100) DEFAULT NULL,
    p_tool_tier INTEGER DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_error_id UUID;
    v_cost DECIMAL(12, 4);
    v_call_count INTEGER;
    v_sql TEXT;
BEGIN
    -- Get current cost snapshot from context
    SELECT total_cost_credits, (tier0_calls + tier1_calls + tier2_calls)
    INTO v_cost, v_call_count
    FROM outreach_ctx.context
    WHERE outreach_context_id = p_context_id;

    -- Build dynamic insert
    v_sql := format(
        'INSERT INTO outreach_errors.%I_errors (
            company_sov_id, outreach_context_id, hub_name, pipeline_stage,
            failure_code, blocking_reason, severity,
            tool_at_failure, tool_tier_at_failure, cumulative_cost_usd, call_count_at_failure
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING error_id',
        p_hub_name
    );

    EXECUTE v_sql
    INTO v_error_id
    USING p_company_sov_id, p_context_id, p_hub_name, p_stage,
          p_failure_code, p_reason, p_severity,
          p_tool_name, p_tool_tier, COALESCE(v_cost, 0), COALESCE(v_call_count, 0);

    -- If blocking, finalize context as FAIL
    IF p_severity = 'blocking' THEN
        PERFORM outreach_ctx.finalize_fail(p_context_id, p_failure_code || ': ' || p_reason);
    END IF;

    RETURN v_error_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach_errors.emit_error_with_cost IS
    'Emit error with automatic cost snapshot. If blocking, finalizes context as FAIL.';

-- -----------------------------------------------------------------------------
-- VIEW: Errors with cost analysis
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW outreach_errors.errors_with_cost AS
SELECT
    hub_name,
    failure_code,
    tool_at_failure,
    tool_tier_at_failure,
    cumulative_cost_usd,
    call_count_at_failure,
    created_at,
    severity::TEXT,
    resolved_at IS NOT NULL AS is_resolved
FROM outreach_errors.company_target_errors
UNION ALL
SELECT
    hub_name,
    failure_code,
    tool_at_failure,
    tool_tier_at_failure,
    cumulative_cost_usd,
    call_count_at_failure,
    created_at,
    severity::TEXT,
    resolved_at IS NOT NULL AS is_resolved
FROM outreach_errors.people_intelligence_errors
UNION ALL
SELECT
    hub_name,
    failure_code,
    tool_at_failure,
    tool_tier_at_failure,
    cumulative_cost_usd,
    call_count_at_failure,
    created_at,
    severity::TEXT,
    resolved_at IS NOT NULL AS is_resolved
FROM outreach_errors.dol_filings_errors
UNION ALL
SELECT
    hub_name,
    failure_code,
    tool_at_failure,
    tool_tier_at_failure,
    cumulative_cost_usd,
    call_count_at_failure,
    created_at,
    severity::TEXT,
    resolved_at IS NOT NULL AS is_resolved
FROM outreach_errors.outreach_execution_errors
UNION ALL
SELECT
    hub_name,
    failure_code,
    tool_at_failure,
    tool_tier_at_failure,
    cumulative_cost_usd,
    call_count_at_failure,
    created_at,
    severity::TEXT,
    resolved_at IS NOT NULL AS is_resolved
FROM outreach_errors.blog_content_errors;

COMMENT ON VIEW outreach_errors.errors_with_cost IS
    'All errors across hubs with cost snapshot for spend analysis.';

-- -----------------------------------------------------------------------------
-- VIEW: Cost burn by failure
-- -----------------------------------------------------------------------------

CREATE OR REPLACE VIEW outreach_errors.cost_burn_by_failure AS
SELECT
    hub_name,
    failure_code,
    COUNT(*) AS occurrence_count,
    SUM(cumulative_cost_usd) AS total_cost_at_failures,
    AVG(cumulative_cost_usd) AS avg_cost_at_failure,
    MAX(cumulative_cost_usd) AS max_cost_at_failure
FROM outreach_errors.errors_with_cost
GROUP BY hub_name, failure_code
ORDER BY total_cost_at_failures DESC;

COMMENT ON VIEW outreach_errors.cost_burn_by_failure IS
    'Aggregate cost burned per failure type. Use for prioritizing fixes.';
