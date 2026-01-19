-- =============================================================================
-- SOVEREIGN COMPLETION VIEW - Read-Only, Authoritative, Dumb
-- =============================================================================
--
-- PURPOSE:
--   Single source of truth for company completion status.
--   Aggregates hub statuses to compute marketing eligibility.
--
-- DOCTRINE:
--   - This view is READ-ONLY - no triggers, no propagation logic inside
--   - All mutation logic belongs in hub-specific tables/triggers
--   - Computes "What's Missing" automatically from hub statuses
--   - Required hubs gate "Complete" status forever
--
-- USAGE:
--   SELECT * FROM outreach.vw_sovereign_completion WHERE company_unique_id = '...';
--
-- =============================================================================

-- First, ensure we have the tables we need
-- (This migration depends on 2026-01-19-hub-registry.sql)

-- =============================================================================
-- SOVEREIGN COMPLETION VIEW
-- =============================================================================

CREATE OR REPLACE VIEW outreach.vw_sovereign_completion AS
WITH 
-- Get all required hubs
required_hubs AS (
    SELECT hub_id, hub_name, waterfall_order
    FROM outreach.hub_registry
    WHERE classification = 'required' AND gates_completion = TRUE
    ORDER BY waterfall_order
),

-- Get hub status per company (with defaults for missing)
hub_statuses AS (
    SELECT 
        ct.company_unique_id,
        rh.hub_id,
        rh.hub_name,
        rh.waterfall_order,
        COALESCE(chs.status, 'IN_PROGRESS'::outreach.hub_status_enum) AS status,
        chs.metric_value,
        chs.last_processed_at
    FROM outreach.company_target ct
    CROSS JOIN required_hubs rh
    LEFT JOIN outreach.company_hub_status chs 
        ON ct.company_unique_id = chs.company_unique_id 
        AND rh.hub_id = chs.hub_id
),

-- Aggregate hub statuses per company
company_summary AS (
    SELECT 
        company_unique_id,
        
        -- Individual hub statuses
        MAX(CASE WHEN hub_id = 'company-target' THEN status END) AS company_target_status,
        MAX(CASE WHEN hub_id = 'dol-filings' THEN status END) AS dol_status,
        MAX(CASE WHEN hub_id = 'people-intelligence' THEN status END) AS people_status,
        MAX(CASE WHEN hub_id = 'talent-flow' THEN status END) AS talent_flow_status,
        
        -- Count statuses
        COUNT(*) FILTER (WHERE status = 'PASS') AS pass_count,
        COUNT(*) FILTER (WHERE status = 'FAIL') AS fail_count,
        COUNT(*) FILTER (WHERE status = 'BLOCKED') AS blocked_count,
        COUNT(*) FILTER (WHERE status = 'IN_PROGRESS') AS in_progress_count,
        COUNT(*) AS total_required_hubs
        
    FROM hub_statuses
    GROUP BY company_unique_id
),

-- Get BIT score for gate evaluation
bit_scores AS (
    SELECT 
        company_unique_id,
        bit_score
    FROM outreach.company_target
)

SELECT 
    cs.company_unique_id,
    
    -- Individual hub statuses
    COALESCE(cs.company_target_status, 'IN_PROGRESS') AS company_target_status,
    COALESCE(cs.dol_status, 'IN_PROGRESS') AS dol_status,
    COALESCE(cs.people_status, 'IN_PROGRESS') AS people_status,
    COALESCE(cs.talent_flow_status, 'IN_PROGRESS') AS talent_flow_status,
    
    -- BIT gate status (not a hub, but a gate)
    CASE 
        WHEN COALESCE(bs.bit_score, 0) >= 25 THEN 'PASS'
        ELSE 'FAIL'
    END AS bit_gate_status,
    
    COALESCE(bs.bit_score, 0) AS bit_score,
    
    -- Overall status (computed from required hubs)
    CASE
        -- Any required hub FAIL or BLOCKED = BLOCKED
        WHEN cs.fail_count > 0 OR cs.blocked_count > 0 THEN 'BLOCKED'
        -- All required hubs PASS = COMPLETE
        WHEN cs.pass_count = cs.total_required_hubs THEN 'COMPLETE'
        -- Otherwise = IN_PROGRESS
        ELSE 'IN_PROGRESS'
    END AS overall_status,
    
    -- Counts for debugging
    cs.pass_count,
    cs.fail_count,
    cs.blocked_count,
    cs.in_progress_count,
    cs.total_required_hubs,
    
    -- Missing requirements (JSONB array of what's not PASS)
    (
        SELECT jsonb_agg(jsonb_build_object(
            'hub_id', hub_id,
            'hub_name', hub_name,
            'status', status::text,
            'reason', CASE 
                WHEN status = 'FAIL' THEN 'Hub failed validation'
                WHEN status = 'BLOCKED' THEN 'Blocked by upstream dependency'
                WHEN status = 'IN_PROGRESS' THEN 'Processing not complete'
                ELSE 'Unknown'
            END
        ) ORDER BY waterfall_order)
        FROM hub_statuses hs
        WHERE hs.company_unique_id = cs.company_unique_id
        AND hs.status != 'PASS'
    ) AS missing_requirements
    
FROM company_summary cs
LEFT JOIN bit_scores bs ON cs.company_unique_id = bs.company_unique_id;

COMMENT ON VIEW outreach.vw_sovereign_completion IS 
'Read-only, authoritative view of company completion status. No triggers, no mutation logic. Aggregates hub statuses from company_hub_status table.';

-- =============================================================================
-- MARKETING ELIGIBILITY VIEW
-- =============================================================================
-- Derived from vw_sovereign_completion, computes marketing tier

CREATE OR REPLACE VIEW outreach.vw_marketing_eligibility AS
SELECT 
    company_unique_id,
    overall_status,
    company_target_status,
    dol_status,
    people_status,
    talent_flow_status,
    bit_gate_status,
    bit_score,
    
    -- Marketing tier (computed, not stored)
    CASE
        -- INELIGIBLE: Any blocker
        WHEN overall_status = 'BLOCKED' THEN -1
        
        -- Tier 3 (Aggressive): ALL required hubs PASS + BIT >= 50
        WHEN overall_status = 'COMPLETE' AND bit_score >= 50 THEN 3
        
        -- Tier 2 (Trigger-based): Talent Flow PASS
        WHEN talent_flow_status = 'PASS' THEN 2
        
        -- Tier 1 (Persona-aware): People PASS
        WHEN people_status = 'PASS' THEN 1
        
        -- Tier 0 (Cold allowed): Company Target PASS only
        WHEN company_target_status = 'PASS' THEN 0
        
        -- Default: INELIGIBLE
        ELSE -1
    END AS marketing_tier,
    
    -- Tier explanation (for UI)
    CASE
        WHEN overall_status = 'BLOCKED' THEN 
            'INELIGIBLE: One or more required hubs failed or blocked'
        WHEN overall_status = 'COMPLETE' AND bit_score >= 50 THEN 
            'Tier 3: All hubs PASS + BIT >= 50 (Aggressive outreach allowed)'
        WHEN talent_flow_status = 'PASS' THEN 
            'Tier 2: Talent Flow signals available (Trigger-based outreach)'
        WHEN people_status = 'PASS' THEN 
            'Tier 1: People data available (Persona-aware outreach)'
        WHEN company_target_status = 'PASS' THEN 
            'Tier 0: Company anchor only (Cold outreach allowed)'
        ELSE 
            'INELIGIBLE: No hubs have passed'
    END AS tier_explanation,
    
    -- What's needed for next tier
    CASE
        WHEN overall_status = 'BLOCKED' THEN 
            'Fix blocked/failed hubs'
        WHEN overall_status = 'COMPLETE' AND bit_score >= 50 THEN 
            'Already at max tier'
        WHEN overall_status = 'COMPLETE' AND bit_score < 50 THEN 
            'Increase BIT score to 50+ for Tier 3'
        WHEN talent_flow_status = 'PASS' THEN 
            'Complete remaining required hubs + BIT >= 50 for Tier 3'
        WHEN people_status = 'PASS' THEN 
            'Complete Talent Flow for Tier 2'
        WHEN company_target_status = 'PASS' THEN 
            'Complete People Intelligence for Tier 1'
        ELSE 
            'Complete Company Target for Tier 0'
    END AS next_tier_requirement,
    
    missing_requirements
    
FROM outreach.vw_sovereign_completion;

COMMENT ON VIEW outreach.vw_marketing_eligibility IS 
'Read-only view computing marketing tier from hub completion status. Tier -1=INELIGIBLE, 0=Cold, 1=Persona, 2=Trigger, 3=Aggressive.';

-- =============================================================================
-- HELPER FUNCTION: Get completion for a single company
-- =============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_get_completion(p_company_id UUID)
RETURNS TABLE (
    company_unique_id UUID,
    overall_status TEXT,
    marketing_tier INTEGER,
    tier_explanation TEXT,
    missing_requirements JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        me.company_unique_id,
        me.overall_status::TEXT,
        me.marketing_tier,
        me.tier_explanation,
        me.missing_requirements
    FROM outreach.vw_marketing_eligibility me
    WHERE me.company_unique_id = p_company_id;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION outreach.fn_get_completion(UUID) IS 
'Get completion status and marketing tier for a single company. Returns NULL if company not found.';

-- =============================================================================
-- INDEX RECOMMENDATIONS
-- =============================================================================
-- These indexes support the views above

CREATE INDEX IF NOT EXISTS idx_company_target_company_id 
ON outreach.company_target(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_target_bit_score 
ON outreach.company_target(bit_score);
