-- =============================================================================
-- PROMOTION GATE FUNCTIONS
-- =============================================================================
--
-- PURPOSE:
--   Functions to check if an entity can progress to the next hub/phase
--   based on DONE state criteria and blocking errors
--
-- FUNCTIONS CREATED:
--   - shq.fn_check_company_target_done(outreach_id) -> BOOLEAN
--   - shq.fn_check_dol_done(outreach_id) -> BOOLEAN
--   - shq.fn_check_people_done(outreach_id) -> BOOLEAN
--   - shq.fn_check_blog_done(outreach_id) -> BOOLEAN
--   - shq.fn_check_bit_done(outreach_id) -> BOOLEAN
--   - shq.fn_get_promotion_blockers(outreach_id) -> TABLE
--   - shq.fn_can_promote_to_hub(outreach_id, target_hub) -> BOOLEAN
--
-- AUTHORITY: DONE_STATE_DEFINITIONS.md v1.0
-- =============================================================================

-- =============================================================================
-- DONE STATE CHECKERS
-- =============================================================================

-- Company Target (04.04.01) DONE Check
CREATE OR REPLACE FUNCTION shq.fn_check_company_target_done(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.company_target
        WHERE outreach_id = p_outreach_id
          AND execution_status = 'ready'
          AND email_method IS NOT NULL
          AND confidence_score IS NOT NULL
          AND imo_completed_at IS NOT NULL
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_check_company_target_done IS 'Returns TRUE if Company Target sub-hub is DONE for given outreach_id';

-- DOL Filings (04.04.03) DONE Check
CREATE OR REPLACE FUNCTION shq.fn_check_dol_done(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.dol
        WHERE outreach_id = p_outreach_id
          AND ein IS NOT NULL
          AND filing_present = TRUE
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_check_dol_done IS 'Returns TRUE if DOL sub-hub is DONE for given outreach_id';

-- People Intelligence (04.04.02) DONE Check (Slot-Level)
CREATE OR REPLACE FUNCTION shq.fn_check_people_done(p_outreach_id UUID, p_min_slots INTEGER DEFAULT 3)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM people.company_slot
        WHERE outreach_id = p_outreach_id
          AND is_filled = TRUE
        GROUP BY outreach_id
        HAVING COUNT(*) >= p_min_slots
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_check_people_done IS 'Returns TRUE if People sub-hub is DONE (has >= min_slots filled)';

-- Blog Content (04.04.05) DONE Check
CREATE OR REPLACE FUNCTION shq.fn_check_blog_done(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.blog
        WHERE outreach_id = p_outreach_id
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_check_blog_done IS 'Returns TRUE if Blog sub-hub is DONE (record exists)';

-- BIT Scores DONE Check
CREATE OR REPLACE FUNCTION shq.fn_check_bit_done(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.bit_scores
        WHERE outreach_id = p_outreach_id
          AND score IS NOT NULL
          AND signal_count > 0
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_check_bit_done IS 'Returns TRUE if BIT scoring is DONE';

-- =============================================================================
-- BLOCKING ERROR CHECKERS
-- =============================================================================

-- Check if outreach_id has blocking errors in DOL
CREATE OR REPLACE FUNCTION shq.fn_has_blocking_dol_errors(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.dol_errors
        WHERE outreach_id = p_outreach_id
          AND disposition IN ('RETRY', 'PARKED')
          AND archived_at IS NULL
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Check if outreach_id has blocking errors in Company Target
CREATE OR REPLACE FUNCTION shq.fn_has_blocking_company_target_errors(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.company_target_errors
        WHERE outreach_id = p_outreach_id
          AND disposition IN ('RETRY', 'PARKED')
          AND archived_at IS NULL
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Check if outreach_id has blocking errors in People
CREATE OR REPLACE FUNCTION shq.fn_has_blocking_people_errors(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM people.people_errors
        WHERE outreach_id = p_outreach_id
          AND disposition IN ('RETRY', 'PARKED')
          AND archived_at IS NULL
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- =============================================================================
-- PROMOTION BLOCKER SUMMARY
-- =============================================================================

-- Get all promotion blockers for an outreach_id
CREATE OR REPLACE FUNCTION shq.fn_get_promotion_blockers(p_outreach_id UUID)
RETURNS TABLE (
    blocker_type TEXT,
    blocker_reason TEXT,
    blocker_severity TEXT,
    blocks_hub TEXT
) AS $$
BEGIN
    -- Check Company Target DONE state
    IF NOT shq.fn_check_company_target_done(p_outreach_id) THEN
        blocker_type := 'DONE_STATE';
        blocker_reason := 'Company Target not DONE: missing execution_status=ready, email_method, confidence_score, or imo_completed_at';
        blocker_severity := 'CRITICAL';
        blocks_hub := 'ALL (anchor hub)';
        RETURN NEXT;
    END IF;

    -- Check Company Target blocking errors
    IF shq.fn_has_blocking_company_target_errors(p_outreach_id) THEN
        blocker_type := 'BLOCKING_ERROR';
        blocker_reason := 'Company Target has RETRY or PARKED errors';
        blocker_severity := 'HIGH';
        blocks_hub := 'ALL (anchor hub)';
        RETURN NEXT;
    END IF;

    -- Check DOL DONE state
    IF NOT shq.fn_check_dol_done(p_outreach_id) THEN
        blocker_type := 'DONE_STATE';
        blocker_reason := 'DOL not DONE: missing ein or filing_present=false';
        blocker_severity := 'MEDIUM';
        blocks_hub := 'Outreach Execution';
        RETURN NEXT;
    END IF;

    -- Check DOL blocking errors
    IF shq.fn_has_blocking_dol_errors(p_outreach_id) THEN
        blocker_type := 'BLOCKING_ERROR';
        blocker_reason := 'DOL has RETRY or PARKED errors';
        blocker_severity := 'HIGH';
        blocks_hub := 'Outreach Execution';
        RETURN NEXT;
    END IF;

    -- Check People DONE state
    IF NOT shq.fn_check_people_done(p_outreach_id) THEN
        blocker_type := 'DONE_STATE';
        blocker_reason := 'People not DONE: fewer than 3 filled slots';
        blocker_severity := 'MEDIUM';
        blocks_hub := 'Outreach Execution';
        RETURN NEXT;
    END IF;

    -- Check People blocking errors
    IF shq.fn_has_blocking_people_errors(p_outreach_id) THEN
        blocker_type := 'BLOCKING_ERROR';
        blocker_reason := 'People has RETRY or PARKED errors';
        blocker_severity := 'HIGH';
        blocks_hub := 'Outreach Execution';
        RETURN NEXT;
    END IF;

    RETURN;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_get_promotion_blockers IS 'Returns all promotion blockers for an outreach_id (DONE state failures and blocking errors)';

-- =============================================================================
-- PROMOTION GATE CHECKER
-- =============================================================================

-- Check if outreach_id can promote to a specific hub
CREATE OR REPLACE FUNCTION shq.fn_can_promote_to_hub(
    p_outreach_id UUID,
    p_target_hub TEXT  -- 'DOL', 'PEOPLE', 'BLOG', 'BIT', 'OUTREACH'
)
RETURNS BOOLEAN AS $$
DECLARE
    v_can_promote BOOLEAN := TRUE;
BEGIN
    -- All hubs require Company Target DONE
    IF NOT shq.fn_check_company_target_done(p_outreach_id) THEN
        RETURN FALSE;
    END IF;

    -- All hubs blocked if Company Target has blocking errors
    IF shq.fn_has_blocking_company_target_errors(p_outreach_id) THEN
        RETURN FALSE;
    END IF;

    CASE UPPER(p_target_hub)
        WHEN 'DOL' THEN
            -- DOL only requires Company Target DONE (already checked)
            RETURN TRUE;

        WHEN 'PEOPLE' THEN
            -- People requires Company Target DONE (already checked)
            RETURN TRUE;

        WHEN 'BLOG' THEN
            -- Blog can run in parallel, only needs Company Target
            RETURN TRUE;

        WHEN 'BIT' THEN
            -- BIT requires signals from multiple hubs
            -- For now, just require Company Target
            RETURN TRUE;

        WHEN 'OUTREACH' THEN
            -- Outreach Execution requires all upstream hubs DONE
            -- and no blocking errors

            -- DOL must be DONE (but DOL errors block promotion)
            IF NOT shq.fn_check_dol_done(p_outreach_id) THEN
                RETURN FALSE;
            END IF;
            IF shq.fn_has_blocking_dol_errors(p_outreach_id) THEN
                RETURN FALSE;
            END IF;

            -- People must be DONE
            IF NOT shq.fn_check_people_done(p_outreach_id) THEN
                RETURN FALSE;
            END IF;
            IF shq.fn_has_blocking_people_errors(p_outreach_id) THEN
                RETURN FALSE;
            END IF;

            RETURN TRUE;

        ELSE
            -- Unknown hub, default to false
            RETURN FALSE;
    END CASE;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_can_promote_to_hub IS 'Returns TRUE if outreach_id can promote to target hub. Checks DONE states and blocking errors.';

-- =============================================================================
-- COMPOSITE TIER FUNCTIONS
-- =============================================================================

-- Tier 1: Marketing-Ready (Company Target DONE with high confidence)
CREATE OR REPLACE FUNCTION shq.fn_is_tier1_marketing_ready(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM outreach.company_target
        WHERE outreach_id = p_outreach_id
          AND execution_status = 'ready'
          AND email_method IS NOT NULL
          AND confidence_score >= 0.8
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Tier 2: Enrichment Complete (All sub-hubs DONE)
CREATE OR REPLACE FUNCTION shq.fn_is_tier2_enrichment_complete(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN shq.fn_check_company_target_done(p_outreach_id)
       AND shq.fn_check_blog_done(p_outreach_id)
       AND shq.fn_check_dol_done(p_outreach_id)
       AND shq.fn_check_bit_done(p_outreach_id);
END;
$$ LANGUAGE plpgsql STABLE;

-- Tier 3: Campaign-Ready (People verified and slots filled)
CREATE OR REPLACE FUNCTION shq.fn_is_tier3_campaign_ready(p_outreach_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN shq.fn_check_company_target_done(p_outreach_id)
       AND shq.fn_check_people_done(p_outreach_id)
       AND EXISTS (
           SELECT 1
           FROM outreach.people
           WHERE outreach_id = p_outreach_id
             AND email_verified = TRUE
       );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION shq.fn_is_tier1_marketing_ready IS 'Tier 1: Company has email pattern with high confidence (>=0.8)';
COMMENT ON FUNCTION shq.fn_is_tier2_enrichment_complete IS 'Tier 2: All sub-hubs (CT, Blog, DOL, BIT) have completed';
COMMENT ON FUNCTION shq.fn_is_tier3_campaign_ready IS 'Tier 3: People verified and slots filled, ready for campaigns';

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View: Promotion readiness for all outreach records
CREATE OR REPLACE VIEW shq.vw_promotion_readiness AS
SELECT
    o.outreach_id,
    shq.fn_check_company_target_done(o.outreach_id) AS company_target_done,
    shq.fn_check_dol_done(o.outreach_id) AS dol_done,
    shq.fn_check_people_done(o.outreach_id) AS people_done,
    shq.fn_check_blog_done(o.outreach_id) AS blog_done,
    shq.fn_check_bit_done(o.outreach_id) AS bit_done,
    shq.fn_has_blocking_company_target_errors(o.outreach_id) AS has_ct_blocking_errors,
    shq.fn_has_blocking_dol_errors(o.outreach_id) AS has_dol_blocking_errors,
    shq.fn_has_blocking_people_errors(o.outreach_id) AS has_people_blocking_errors,
    shq.fn_can_promote_to_hub(o.outreach_id, 'OUTREACH') AS can_promote_to_outreach,
    CASE
        WHEN shq.fn_is_tier3_campaign_ready(o.outreach_id) THEN 'TIER_3_CAMPAIGN_READY'
        WHEN shq.fn_is_tier2_enrichment_complete(o.outreach_id) THEN 'TIER_2_ENRICHMENT_COMPLETE'
        WHEN shq.fn_is_tier1_marketing_ready(o.outreach_id) THEN 'TIER_1_MARKETING_READY'
        WHEN shq.fn_check_company_target_done(o.outreach_id) THEN 'TIER_0_ANCHOR_DONE'
        ELSE 'NOT_READY'
    END AS readiness_tier
FROM outreach.outreach o;

-- View: Summary counts by readiness tier
CREATE OR REPLACE VIEW shq.vw_promotion_readiness_summary AS
SELECT
    readiness_tier,
    COUNT(*) AS count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM shq.vw_promotion_readiness
GROUP BY readiness_tier
ORDER BY
    CASE readiness_tier
        WHEN 'TIER_3_CAMPAIGN_READY' THEN 1
        WHEN 'TIER_2_ENRICHMENT_COMPLETE' THEN 2
        WHEN 'TIER_1_MARKETING_READY' THEN 3
        WHEN 'TIER_0_ANCHOR_DONE' THEN 4
        ELSE 5
    END;

COMMENT ON VIEW shq.vw_promotion_readiness IS 'Shows DONE states and blocking errors for each outreach_id';
COMMENT ON VIEW shq.vw_promotion_readiness_summary IS 'Summary counts by readiness tier';

-- =============================================================================
-- USAGE
-- =============================================================================
--
-- Check if single outreach_id can promote:
--   SELECT shq.fn_can_promote_to_hub('uuid-here', 'OUTREACH');
--
-- Get all blockers for an outreach_id:
--   SELECT * FROM shq.fn_get_promotion_blockers('uuid-here');
--
-- Check readiness tier:
--   SELECT readiness_tier FROM shq.vw_promotion_readiness WHERE outreach_id = 'uuid-here';
--
-- Get summary of all outreach records:
--   SELECT * FROM shq.vw_promotion_readiness_summary;
--
-- =============================================================================
