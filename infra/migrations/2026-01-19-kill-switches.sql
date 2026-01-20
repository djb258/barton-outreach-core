-- =============================================================================
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--                         DO NOT MODIFY WITHOUT CHANGE REQUEST
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--
-- STATUS: FROZEN (v1.0 Operational Baseline)
-- FREEZE DATE: 2026-01-20
-- REFERENCE: docs/GO-LIVE_STATE_v1.0.md
--
-- This file contains AUTHORITATIVE views and logic that are FROZEN at v1.0.
-- Any modification requires:
--   1. Formal Change Request with justification
--   2. Impact analysis on all dependent systems
--   3. Full re-certification after changes
--   4. Technical lead sign-off
--
-- AUTHORITATIVE COMPONENTS IN THIS FILE:
--   - outreach.vw_marketing_eligibility_with_overrides (THE source of truth)
--   - outreach.manual_overrides (Kill switch enforcement)
--   - Override enum types and audit tables
--
-- =============================================================================
-- KILL SWITCHES - Manual Override System
-- =============================================================================
--
-- PURPOSE:
--   Prevent any company from receiving marketing outreach, regardless of 
--   computed eligibility. Takes precedence over all automated decisions.
--
-- DOCTRINE:
--   - Kill switches MUST be implemented BEFORE UI
--   - No visual bypass possible - data layer enforcement
--   - Full audit trail required
--   - TTL support for temporary disablements
--
-- USAGE:
--   -- Disable marketing for a company
--   INSERT INTO outreach.manual_overrides (company_unique_id, override_type, reason)
--   VALUES ('...', 'marketing_disabled', 'Customer requested opt-out');
--
--   -- Check if company is disabled
--   SELECT * FROM outreach.vw_marketing_eligibility_with_overrides WHERE company_unique_id = '...';
--
-- =============================================================================

-- =============================================================================
-- OVERRIDE TYPES ENUM
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'override_type_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'outreach')) THEN
        CREATE TYPE outreach.override_type_enum AS ENUM (
            'marketing_disabled',       -- Complete marketing blackout
            'tier_cap',                  -- Cap to specific tier (use metadata for tier number)
            'hub_bypass',                -- Skip specific hub (use metadata for hub_id)
            'cooldown',                  -- Temporary pause (use expires_at)
            'legal_hold',                -- Legal/compliance freeze
            'customer_requested'         -- Customer opt-out
        );
    END IF;
END$$;

-- =============================================================================
-- MANUAL OVERRIDES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.manual_overrides (
    override_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_unique_id UUID NOT NULL,
    override_type outreach.override_type_enum NOT NULL,
    
    -- Override details
    reason TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    
    -- TTL support
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_by TEXT NOT NULL DEFAULT current_user,
    expires_at TIMESTAMPTZ,  -- NULL = permanent
    
    -- Deactivation tracking
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    deactivated_at TIMESTAMPTZ,
    deactivated_by TEXT,
    deactivation_reason TEXT,
    
    CONSTRAINT manual_overrides_company_fk 
        FOREIGN KEY (company_unique_id) 
        REFERENCES outreach.company_target(company_unique_id)
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_manual_overrides_company 
ON outreach.manual_overrides(company_unique_id) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_manual_overrides_type 
ON outreach.manual_overrides(override_type) WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_manual_overrides_expires 
ON outreach.manual_overrides(expires_at) WHERE is_active = TRUE AND expires_at IS NOT NULL;

-- =============================================================================
-- OVERRIDE AUDIT LOG
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.override_audit_log (
    audit_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    override_id UUID NOT NULL,
    company_unique_id UUID NOT NULL,
    action TEXT NOT NULL,  -- 'created', 'deactivated', 'expired', 'modified'
    old_values JSONB,
    new_values JSONB,
    performed_by TEXT NOT NULL DEFAULT current_user,
    performed_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    ip_address INET,
    user_agent TEXT
);

CREATE INDEX IF NOT EXISTS idx_override_audit_company 
ON outreach.override_audit_log(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_override_audit_override 
ON outreach.override_audit_log(override_id);

-- =============================================================================
-- AUDIT TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_override_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO outreach.override_audit_log (
            override_id, company_unique_id, action, new_values
        ) VALUES (
            NEW.override_id, 
            NEW.company_unique_id, 
            'created',
            jsonb_build_object(
                'override_type', NEW.override_type,
                'reason', NEW.reason,
                'expires_at', NEW.expires_at,
                'metadata', NEW.metadata
            )
        );
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Track deactivation
        IF OLD.is_active = TRUE AND NEW.is_active = FALSE THEN
            INSERT INTO outreach.override_audit_log (
                override_id, company_unique_id, action, old_values, new_values
            ) VALUES (
                NEW.override_id, 
                NEW.company_unique_id, 
                'deactivated',
                jsonb_build_object(
                    'override_type', OLD.override_type,
                    'reason', OLD.reason
                ),
                jsonb_build_object(
                    'deactivated_by', NEW.deactivated_by,
                    'deactivation_reason', NEW.deactivation_reason
                )
            );
        ELSE
            INSERT INTO outreach.override_audit_log (
                override_id, company_unique_id, action, old_values, new_values
            ) VALUES (
                NEW.override_id, 
                NEW.company_unique_id, 
                'modified',
                to_jsonb(OLD),
                to_jsonb(NEW)
            );
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_override_audit ON outreach.manual_overrides;
CREATE TRIGGER trg_override_audit
AFTER INSERT OR UPDATE ON outreach.manual_overrides
FOR EACH ROW EXECUTE FUNCTION outreach.fn_override_audit_trigger();

-- =============================================================================
-- TTL EXPIRATION FUNCTION
-- =============================================================================

CREATE OR REPLACE FUNCTION outreach.fn_expire_overrides()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    -- Deactivate expired overrides
    WITH expired AS (
        UPDATE outreach.manual_overrides
        SET 
            is_active = FALSE,
            deactivated_at = NOW(),
            deactivated_by = 'system:ttl_expiration',
            deactivation_reason = 'TTL expired'
        WHERE is_active = TRUE 
        AND expires_at IS NOT NULL 
        AND expires_at <= NOW()
        RETURNING override_id, company_unique_id
    )
    SELECT COUNT(*) INTO expired_count FROM expired;
    
    -- Log expirations
    INSERT INTO outreach.override_audit_log (
        override_id, company_unique_id, action, performed_by
    )
    SELECT override_id, company_unique_id, 'expired', 'system:ttl_expiration'
    FROM outreach.manual_overrides
    WHERE deactivated_by = 'system:ttl_expiration'
    AND deactivated_at >= NOW() - INTERVAL '1 minute';
    
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.fn_expire_overrides() IS 
'Expires overrides past their TTL. Call periodically via cron or application timer.';

-- =============================================================================
-- MARKETING ELIGIBILITY WITH OVERRIDES VIEW
-- =============================================================================
-- This is the AUTHORITATIVE view that respects kill switches

CREATE OR REPLACE VIEW outreach.vw_marketing_eligibility_with_overrides AS
WITH active_overrides AS (
    SELECT 
        company_unique_id,
        override_type,
        reason,
        metadata,
        expires_at
    FROM outreach.manual_overrides
    WHERE is_active = TRUE
    AND (expires_at IS NULL OR expires_at > NOW())
),

-- Check for marketing-blocking overrides
blocking_overrides AS (
    SELECT 
        company_unique_id,
        array_agg(override_type::text) AS override_types,
        array_agg(reason) AS override_reasons
    FROM active_overrides
    WHERE override_type IN ('marketing_disabled', 'legal_hold', 'customer_requested', 'cooldown')
    GROUP BY company_unique_id
),

-- Check for tier caps
tier_caps AS (
    SELECT 
        company_unique_id,
        MIN((metadata->>'tier_cap')::int) AS max_tier
    FROM active_overrides
    WHERE override_type = 'tier_cap'
    AND metadata ? 'tier_cap'
    GROUP BY company_unique_id
)

SELECT 
    me.company_unique_id,
    me.overall_status,
    me.company_target_status,
    me.dol_status,
    me.people_status,
    me.talent_flow_status,
    me.bit_gate_status,
    me.bit_score,
    
    -- Original computed tier
    me.marketing_tier AS computed_tier,
    
    -- Effective tier (after kill switches)
    CASE
        -- Any blocking override = INELIGIBLE
        WHEN bo.company_unique_id IS NOT NULL THEN -1
        -- Tier cap applies
        WHEN tc.max_tier IS NOT NULL AND me.marketing_tier > tc.max_tier THEN tc.max_tier
        -- No overrides
        ELSE me.marketing_tier
    END AS effective_tier,
    
    -- Override status
    CASE
        WHEN bo.company_unique_id IS NOT NULL THEN TRUE
        WHEN tc.max_tier IS NOT NULL AND me.marketing_tier > tc.max_tier THEN TRUE
        ELSE FALSE
    END AS has_active_override,
    
    -- Override details
    bo.override_types,
    bo.override_reasons,
    tc.max_tier AS tier_cap,
    
    -- Effective tier explanation
    CASE
        WHEN bo.company_unique_id IS NOT NULL THEN 
            'BLOCKED: ' || array_to_string(bo.override_types, ', ')
        WHEN tc.max_tier IS NOT NULL AND me.marketing_tier > tc.max_tier THEN 
            'CAPPED: Tier limited to ' || tc.max_tier
        ELSE me.tier_explanation
    END AS effective_tier_explanation,
    
    me.next_tier_requirement,
    me.missing_requirements
    
FROM outreach.vw_marketing_eligibility me
LEFT JOIN blocking_overrides bo ON me.company_unique_id = bo.company_unique_id
LEFT JOIN tier_caps tc ON me.company_unique_id = tc.company_unique_id;

COMMENT ON VIEW outreach.vw_marketing_eligibility_with_overrides IS 
'Marketing eligibility with kill switch enforcement. USE THIS VIEW for all marketing decisions - never bypass to underlying views.';

-- =============================================================================
-- HELPER FUNCTIONS FOR OVERRIDE MANAGEMENT
-- =============================================================================

-- Disable marketing for a company
CREATE OR REPLACE FUNCTION outreach.fn_disable_marketing(
    p_company_id UUID,
    p_reason TEXT,
    p_expires_at TIMESTAMPTZ DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_override_id UUID;
BEGIN
    INSERT INTO outreach.manual_overrides (
        company_unique_id, override_type, reason, expires_at
    ) VALUES (
        p_company_id, 'marketing_disabled', p_reason, p_expires_at
    ) RETURNING override_id INTO v_override_id;
    
    RETURN v_override_id;
END;
$$ LANGUAGE plpgsql;

-- Re-enable marketing
CREATE OR REPLACE FUNCTION outreach.fn_enable_marketing(
    p_company_id UUID,
    p_deactivation_reason TEXT DEFAULT 'Manually re-enabled'
) RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE outreach.manual_overrides
    SET 
        is_active = FALSE,
        deactivated_at = NOW(),
        deactivated_by = current_user,
        deactivation_reason = p_deactivation_reason
    WHERE company_unique_id = p_company_id
    AND is_active = TRUE
    AND override_type IN ('marketing_disabled', 'cooldown');
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Set tier cap
CREATE OR REPLACE FUNCTION outreach.fn_set_tier_cap(
    p_company_id UUID,
    p_max_tier INTEGER,
    p_reason TEXT,
    p_expires_at TIMESTAMPTZ DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_override_id UUID;
BEGIN
    -- Validate tier
    IF p_max_tier < 0 OR p_max_tier > 3 THEN
        RAISE EXCEPTION 'Invalid tier cap: %. Must be 0-3.', p_max_tier;
    END IF;
    
    INSERT INTO outreach.manual_overrides (
        company_unique_id, 
        override_type, 
        reason, 
        metadata,
        expires_at
    ) VALUES (
        p_company_id, 
        'tier_cap', 
        p_reason, 
        jsonb_build_object('tier_cap', p_max_tier),
        p_expires_at
    ) RETURNING override_id INTO v_override_id;
    
    RETURN v_override_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- RLS POLICIES
-- =============================================================================

ALTER TABLE outreach.manual_overrides ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach.override_audit_log ENABLE ROW LEVEL SECURITY;

-- Overrides: service role full access
CREATE POLICY manual_overrides_service_policy ON outreach.manual_overrides
    FOR ALL USING (current_user = 'service_role');

-- Audit log: service role full access, others read-only
CREATE POLICY override_audit_service_policy ON outreach.override_audit_log
    FOR ALL USING (current_user = 'service_role');

CREATE POLICY override_audit_read_policy ON outreach.override_audit_log
    FOR SELECT USING (TRUE);

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE outreach.manual_overrides IS 
'Kill switch table - manual overrides that take precedence over computed eligibility. Full audit trail required.';

COMMENT ON TABLE outreach.override_audit_log IS 
'Immutable audit log for all override changes. Never delete from this table.';

COMMENT ON FUNCTION outreach.fn_disable_marketing(UUID, TEXT, TIMESTAMPTZ) IS 
'Disable marketing for a company. Returns override_id. Pass expires_at for temporary disable.';

COMMENT ON FUNCTION outreach.fn_enable_marketing(UUID, TEXT) IS 
'Re-enable marketing by deactivating blocking overrides. Returns count of deactivated overrides.';

COMMENT ON FUNCTION outreach.fn_set_tier_cap(UUID, INTEGER, TEXT, TIMESTAMPTZ) IS 
'Cap marketing tier for a company. Max tier must be 0-3.';
