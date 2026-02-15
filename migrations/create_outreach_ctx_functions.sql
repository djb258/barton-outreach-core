-- outreach_ctx Functions
-- Execute after schema and tables are created

-- Function: can_attempt_tier2()
-- Single-shot fuse per outreach_context_id
CREATE OR REPLACE FUNCTION outreach_ctx.can_attempt_tier2(p_context_id TEXT)
RETURNS BOOLEAN
LANGUAGE sql
AS $$
    SELECT NOT EXISTS (
        SELECT 1
        FROM outreach_ctx.tool_attempts
        WHERE outreach_context_id = p_context_id
          AND tier = 2
    );
$$;

-- Function: log_tool_attempt()
-- Used by context_manager.py after any paid call
CREATE OR REPLACE FUNCTION outreach_ctx.log_tool_attempt(
    p_context_id TEXT,
    p_company_sov_id UUID,
    p_tool_name TEXT,
    p_tier INTEGER,
    p_cost_credits NUMERIC
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO outreach_ctx.tool_attempts (
        outreach_context_id, tool_name, tier
    ) VALUES (
        p_context_id, p_tool_name, p_tier
    ) ON CONFLICT DO NOTHING;

    INSERT INTO outreach_ctx.spend_log (
        outreach_context_id,
        company_sov_id,
        tool_name,
        tier,
        cost_credits
    ) VALUES (
        p_context_id,
        p_company_sov_id,
        p_tool_name,
        p_tier,
        p_cost_credits
    );
END;
$$;
