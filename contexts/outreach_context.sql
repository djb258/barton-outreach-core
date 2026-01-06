-- =============================================================================
-- OUTREACH CONTEXT - Disposable Execution Context
-- =============================================================================
--
-- PURPOSE:
--   Track outreach executions (runs / epochs / campaigns) for:
--   - Cost accounting
--   - Retry isolation
--   - Audit logs
--   - Single-attempt enforcement for Tier-2 tools
--
-- IMPORTANT:
--   - Outreach Context IDs are DISPOSABLE, not identity
--   - Always scoped to a Company Sovereign ID
--   - TTL-bound and kill-switchable
--
-- ANALOGY:
--   - company_sov_id = VIN (permanent, sovereign)
--   - outreach_id = Work Order (disposable, scoped)
--   - There is ONE VIN, many work orders
--
-- =============================================================================

-- Schema for outreach contexts
CREATE SCHEMA IF NOT EXISTS outreach_ctx;

-- =============================================================================
-- ENUM TYPES
-- =============================================================================

-- Final state enum (immutable once set)
CREATE TYPE outreach_ctx.final_state_enum AS ENUM (
    'PASS',     -- Pipeline completed successfully
    'FAIL',     -- Pipeline failed with blocking error
    'ABORTED'   -- Context killed (manual or SLA expiry)
);

-- =============================================================================
-- OUTREACH CONTEXT TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_ctx.context (
    -- Primary identifier (disposable)
    outreach_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Sovereign company reference (REQUIRED, read-only)
    company_sov_id UUID NOT NULL,

    -- Context metadata
    context_type VARCHAR(50) NOT NULL DEFAULT 'run',  -- run, epoch, campaign
    context_name VARCHAR(255),

    -- Lifecycle gate at creation time
    lifecycle_state_at_creation VARCHAR(50) NOT NULL,

    -- TTL and lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    killed_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- SLA aging (auto-ABORT on expiry)
    sla_expires_at TIMESTAMPTZ,  -- NULL = no SLA, non-NULL = hard deadline

    -- Final state (immutable once set)
    final_state outreach_ctx.final_state_enum,  -- NULL while in-flight
    finalized_at TIMESTAMPTZ,

    -- Cost tracking
    total_cost_credits DECIMAL(12, 4) NOT NULL DEFAULT 0,
    tier0_calls INTEGER NOT NULL DEFAULT 0,
    tier1_calls INTEGER NOT NULL DEFAULT 0,
    tier2_calls INTEGER NOT NULL DEFAULT 0,

    -- Audit
    created_by VARCHAR(100),
    kill_reason TEXT,

    -- Constraints
    CONSTRAINT valid_context_type CHECK (context_type IN ('run', 'epoch', 'campaign')),
    CONSTRAINT valid_lifecycle_state CHECK (lifecycle_state_at_creation IN (
        'INTAKE', 'SOVEREIGN_MINTED', 'ACTIVE', 'TARGETABLE', 'ENGAGED', 'CLIENT', 'DORMANT', 'DEAD'
    )),
    CONSTRAINT expires_after_created CHECK (expires_at > created_at),
    -- Final state can only be set once
    CONSTRAINT final_state_immutable CHECK (
        finalized_at IS NULL OR final_state IS NOT NULL
    ),
    -- SLA must be after creation
    CONSTRAINT sla_after_created CHECK (
        sla_expires_at IS NULL OR sla_expires_at > created_at
    )
);

-- Index for company lookups
CREATE INDEX IF NOT EXISTS idx_context_company
    ON outreach_ctx.context(company_sov_id);

-- Index for active contexts
CREATE INDEX IF NOT EXISTS idx_context_active
    ON outreach_ctx.context(is_active, expires_at);

-- =============================================================================
-- TOOL ATTEMPT TRACKING (Single-Attempt Enforcement)
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_ctx.tool_attempts (
    attempt_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Context reference
    outreach_id UUID NOT NULL REFERENCES outreach_ctx.context(outreach_id),
    company_sov_id UUID NOT NULL,

    -- Tool information
    tool_name VARCHAR(100) NOT NULL,
    tool_tier INTEGER NOT NULL,  -- 0, 1, 2

    -- Attempt tracking
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cost_credits DECIMAL(10, 4) NOT NULL DEFAULT 0,
    success BOOLEAN,
    result_summary TEXT,
    error_message TEXT,

    -- CRITICAL: Enforce single Tier-2 attempt per context
    CONSTRAINT tier2_single_attempt UNIQUE (outreach_id, company_sov_id, tool_name)
        WHERE tool_tier = 2
);

-- Index for tool attempt lookups
CREATE INDEX IF NOT EXISTS idx_tool_attempts_context
    ON outreach_ctx.tool_attempts(outreach_id);

-- Index for company tool history
CREATE INDEX IF NOT EXISTS idx_tool_attempts_company
    ON outreach_ctx.tool_attempts(company_sov_id, tool_name);

-- =============================================================================
-- SPEND LOG (Cost Accounting)
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach_ctx.spend_log (
    spend_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Context and company reference
    outreach_id UUID NOT NULL REFERENCES outreach_ctx.context(outreach_id),
    company_sov_id UUID NOT NULL,

    -- Spend details
    tool_name VARCHAR(100) NOT NULL,
    tool_tier INTEGER NOT NULL,
    cost_credits DECIMAL(10, 4) NOT NULL,

    -- Timestamps
    logged_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Audit trail
    sub_hub VARCHAR(50) NOT NULL,  -- company-target, people-intelligence, etc.
    operation VARCHAR(100)
);

-- Index for spend aggregation
CREATE INDEX IF NOT EXISTS idx_spend_log_context
    ON outreach_ctx.spend_log(outreach_id);

CREATE INDEX IF NOT EXISTS idx_spend_log_company
    ON outreach_ctx.spend_log(company_sov_id);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Create a new outreach context
CREATE OR REPLACE FUNCTION outreach_ctx.create_context(
    p_company_sov_id UUID,
    p_context_type VARCHAR(50) DEFAULT 'run',
    p_lifecycle_state VARCHAR(50) DEFAULT 'ACTIVE',
    p_ttl_hours INTEGER DEFAULT 24,
    p_context_name VARCHAR(255) DEFAULT NULL,
    p_created_by VARCHAR(100) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_context_id UUID;
BEGIN
    INSERT INTO outreach_ctx.context (
        company_sov_id,
        context_type,
        context_name,
        lifecycle_state_at_creation,
        expires_at,
        created_by
    ) VALUES (
        p_company_sov_id,
        p_context_type,
        p_context_name,
        p_lifecycle_state,
        NOW() + (p_ttl_hours || ' hours')::INTERVAL,
        p_created_by
    ) RETURNING outreach_id INTO v_context_id;

    RETURN v_context_id;
END;
$$ LANGUAGE plpgsql;

-- Kill a context (with reason) - sets final_state to ABORTED
CREATE OR REPLACE FUNCTION outreach_ctx.kill_context(
    p_context_id UUID,
    p_reason TEXT DEFAULT 'Manual kill'
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE outreach_ctx.context
    SET is_active = FALSE,
        killed_at = NOW(),
        kill_reason = p_reason,
        final_state = 'ABORTED',
        finalized_at = NOW()
    WHERE outreach_id = p_context_id
      AND is_active = TRUE
      AND final_state IS NULL;  -- Cannot re-finalize

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Finalize a context with PASS state
CREATE OR REPLACE FUNCTION outreach_ctx.finalize_pass(
    p_context_id UUID
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE outreach_ctx.context
    SET is_active = FALSE,
        final_state = 'PASS',
        finalized_at = NOW()
    WHERE outreach_id = p_context_id
      AND is_active = TRUE
      AND final_state IS NULL;  -- Cannot re-finalize

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Finalize a context with FAIL state (called when error emitted)
CREATE OR REPLACE FUNCTION outreach_ctx.finalize_fail(
    p_context_id UUID,
    p_reason TEXT DEFAULT 'Pipeline failure'
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE outreach_ctx.context
    SET is_active = FALSE,
        final_state = 'FAIL',
        finalized_at = NOW(),
        kill_reason = p_reason
    WHERE outreach_id = p_context_id
      AND final_state IS NULL;  -- Cannot re-finalize

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Auto-ABORT contexts that have exceeded SLA
CREATE OR REPLACE FUNCTION outreach_ctx.abort_expired_sla() RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE outreach_ctx.context
    SET is_active = FALSE,
        killed_at = NOW(),
        kill_reason = 'SLA expiry auto-abort',
        final_state = 'ABORTED',
        finalized_at = NOW()
    WHERE sla_expires_at IS NOT NULL
      AND sla_expires_at < NOW()
      AND is_active = TRUE
      AND final_state IS NULL;

    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Check if Tier-2 tool already attempted in context
CREATE OR REPLACE FUNCTION outreach_ctx.can_attempt_tier2(
    p_context_id UUID,
    p_company_sov_id UUID,
    p_tool_name VARCHAR(100)
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN NOT EXISTS (
        SELECT 1 FROM outreach_ctx.tool_attempts
        WHERE outreach_id = p_context_id
          AND company_sov_id = p_company_sov_id
          AND tool_name = p_tool_name
          AND tool_tier = 2
    );
END;
$$ LANGUAGE plpgsql;

-- Log a tool attempt
CREATE OR REPLACE FUNCTION outreach_ctx.log_tool_attempt(
    p_context_id UUID,
    p_company_sov_id UUID,
    p_tool_name VARCHAR(100),
    p_tool_tier INTEGER,
    p_cost_credits DECIMAL(10, 4),
    p_success BOOLEAN,
    p_result_summary TEXT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_sub_hub VARCHAR(50) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_attempt_id UUID;
BEGIN
    -- Insert attempt record
    INSERT INTO outreach_ctx.tool_attempts (
        outreach_id,
        company_sov_id,
        tool_name,
        tool_tier,
        cost_credits,
        success,
        result_summary,
        error_message
    ) VALUES (
        p_context_id,
        p_company_sov_id,
        p_tool_name,
        p_tool_tier,
        p_cost_credits,
        p_success,
        p_result_summary,
        p_error_message
    ) RETURNING attempt_id INTO v_attempt_id;

    -- Log spend
    INSERT INTO outreach_ctx.spend_log (
        outreach_id,
        company_sov_id,
        tool_name,
        tool_tier,
        cost_credits,
        sub_hub,
        operation
    ) VALUES (
        p_context_id,
        p_company_sov_id,
        p_tool_name,
        p_tool_tier,
        p_cost_credits,
        COALESCE(p_sub_hub, 'unknown'),
        'tool_attempt'
    );

    -- Update context totals
    UPDATE outreach_ctx.context
    SET total_cost_credits = total_cost_credits + p_cost_credits,
        tier0_calls = tier0_calls + CASE WHEN p_tool_tier = 0 THEN 1 ELSE 0 END,
        tier1_calls = tier1_calls + CASE WHEN p_tool_tier = 1 THEN 1 ELSE 0 END,
        tier2_calls = tier2_calls + CASE WHEN p_tool_tier = 2 THEN 1 ELSE 0 END
    WHERE outreach_id = p_context_id;

    RETURN v_attempt_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active contexts with spend summary
CREATE OR REPLACE VIEW outreach_ctx.active_contexts AS
SELECT
    c.outreach_id,
    c.company_sov_id,
    c.context_type,
    c.context_name,
    c.lifecycle_state_at_creation,
    c.created_at,
    c.expires_at,
    c.sla_expires_at,
    c.total_cost_credits,
    c.tier0_calls,
    c.tier1_calls,
    c.tier2_calls,
    EXTRACT(EPOCH FROM (c.expires_at - NOW())) / 3600 AS hours_remaining,
    CASE
        WHEN c.sla_expires_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (c.sla_expires_at - NOW())) / 3600
        ELSE NULL
    END AS sla_hours_remaining
FROM outreach_ctx.context c
WHERE c.is_active = TRUE
  AND c.expires_at > NOW()
  AND c.final_state IS NULL;

-- Finalized contexts (PASS/FAIL/ABORTED)
CREATE OR REPLACE VIEW outreach_ctx.finalized_contexts AS
SELECT
    c.outreach_id,
    c.company_sov_id,
    c.context_type,
    c.context_name,
    c.final_state,
    c.finalized_at,
    c.created_at,
    c.total_cost_credits,
    c.tier0_calls,
    c.tier1_calls,
    c.tier2_calls,
    c.kill_reason,
    EXTRACT(EPOCH FROM (c.finalized_at - c.created_at)) / 60 AS duration_minutes
FROM outreach_ctx.context c
WHERE c.final_state IS NOT NULL;

-- Contexts approaching SLA expiry (warning threshold: 1 hour)
CREATE OR REPLACE VIEW outreach_ctx.sla_warning AS
SELECT
    c.outreach_id,
    c.company_sov_id,
    c.sla_expires_at,
    EXTRACT(EPOCH FROM (c.sla_expires_at - NOW())) / 60 AS minutes_until_abort,
    c.total_cost_credits
FROM outreach_ctx.context c
WHERE c.is_active = TRUE
  AND c.final_state IS NULL
  AND c.sla_expires_at IS NOT NULL
  AND c.sla_expires_at < NOW() + INTERVAL '1 hour'
  AND c.sla_expires_at > NOW();

-- Spend by company
CREATE OR REPLACE VIEW outreach_ctx.spend_by_company AS
SELECT
    company_sov_id,
    COUNT(DISTINCT outreach_id) AS context_count,
    SUM(cost_credits) AS total_spend,
    SUM(CASE WHEN tool_tier = 0 THEN cost_credits ELSE 0 END) AS tier0_spend,
    SUM(CASE WHEN tool_tier = 1 THEN cost_credits ELSE 0 END) AS tier1_spend,
    SUM(CASE WHEN tool_tier = 2 THEN cost_credits ELSE 0 END) AS tier2_spend
FROM outreach_ctx.spend_log
GROUP BY company_sov_id;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE outreach_ctx.context IS
    'Disposable outreach execution contexts. NOT identity - just work orders.';

COMMENT ON TABLE outreach_ctx.tool_attempts IS
    'Track tool attempts per context. Enforces single Tier-2 attempt rule.';

COMMENT ON TABLE outreach_ctx.spend_log IS
    'Cost accounting keyed to (company_sov_id + outreach_id).';

COMMENT ON FUNCTION outreach_ctx.can_attempt_tier2 IS
    'Check if Tier-2 tool can be attempted in this context. Returns FALSE if already attempted.';

COMMENT ON FUNCTION outreach_ctx.finalize_pass IS
    'Mark context as PASS. Can only be called once per context.';

COMMENT ON FUNCTION outreach_ctx.finalize_fail IS
    'Mark context as FAIL. Called when blocking error emitted.';

COMMENT ON FUNCTION outreach_ctx.abort_expired_sla IS
    'Auto-ABORT all contexts past SLA deadline. Run on schedule (e.g., every 5 min).';

COMMENT ON VIEW outreach_ctx.finalized_contexts IS
    'All contexts with final_state set (PASS/FAIL/ABORTED).';

COMMENT ON VIEW outreach_ctx.sla_warning IS
    'Contexts within 1 hour of SLA auto-abort. Use for alerting.';
