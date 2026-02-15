-- =============================================================================
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--                         DO NOT MODIFY WITHOUT CHANGE REQUEST
-- !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
--
-- STATUS: FROZEN (v1.0 Operational Baseline)
-- FREEZE DATE: 2026-01-20
-- REFERENCE: docs/GO-LIVE_STATE_v1.0.md
--
-- This file contains AUTHORITATIVE audit logging that is FROZEN at v1.0.
-- The send_attempt_audit table is APPEND-ONLY by design.
-- Any modification requires:
--   1. Formal Change Request with justification
--   2. Impact analysis on audit trail integrity
--   3. Full re-certification after changes
--   4. Technical lead sign-off
--
-- FROZEN COMPONENTS IN THIS FILE:
--   - outreach.send_attempt_audit (Append-only audit log)
--   - Protective triggers preventing updates/deletes
--
-- =============================================================================
-- SEND ATTEMPT AUDIT TABLE - Append-Only Audit Logging
-- =============================================================================
--
-- PURPOSE:
--   Append-only audit log for ALL marketing send attempts.
--   Every attempt MUST be logged BEFORE the send occurs.
--   This provides complete traceability for compliance and debugging.
--
-- DOCTRINE:
--   - Append-only: NO updates, NO deletes
--   - Every send attempt MUST be logged
--   - Includes full override snapshot at time of attempt
--   - Supports compliance auditing and incident investigation
--
-- USAGE:
--   Automatically populated by MarketingSafetyGate before any send.
--
-- =============================================================================

-- =============================================================================
-- SEND ATTEMPT AUDIT TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.send_attempt_audit (
    -- Primary key
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was attempted
    company_unique_id UUID NOT NULL,
    campaign_id TEXT NOT NULL,

    -- Eligibility snapshot at time of attempt
    effective_tier INTEGER NOT NULL,
    computed_tier INTEGER NOT NULL,
    override_snapshot JSONB NOT NULL DEFAULT '{}'::JSONB,

    -- Result
    status TEXT NOT NULL,  -- blocked_ineligible, blocked_disabled, blocked_override, allowed, sent, send_failed
    failure_reason TEXT,

    -- Traceability
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT send_attempt_audit_status_check CHECK (
        status IN (
            'blocked_ineligible',
            'blocked_disabled',
            'blocked_override',
            'blocked_check_failed',
            'allowed',
            'sent',
            'send_failed'
        )
    )
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Fast lookup by company
CREATE INDEX IF NOT EXISTS idx_send_attempt_audit_company
ON outreach.send_attempt_audit(company_unique_id);

-- Fast lookup by campaign
CREATE INDEX IF NOT EXISTS idx_send_attempt_audit_campaign
ON outreach.send_attempt_audit(campaign_id);

-- Time-based queries for compliance
CREATE INDEX IF NOT EXISTS idx_send_attempt_audit_created
ON outreach.send_attempt_audit(created_at DESC);

-- Filter by status (for finding blocks)
CREATE INDEX IF NOT EXISTS idx_send_attempt_audit_status
ON outreach.send_attempt_audit(status) WHERE status LIKE 'blocked%';

-- Correlation ID for tracing
CREATE INDEX IF NOT EXISTS idx_send_attempt_audit_correlation
ON outreach.send_attempt_audit(correlation_id) WHERE correlation_id IS NOT NULL;

-- =============================================================================
-- APPEND-ONLY ENFORCEMENT
-- =============================================================================

-- Prevent UPDATE on send_attempt_audit (append-only)
CREATE OR REPLACE FUNCTION outreach.fn_prevent_audit_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'send_attempt_audit is append-only. Updates are not permitted.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_audit_update ON outreach.send_attempt_audit;
CREATE TRIGGER trg_prevent_audit_update
BEFORE UPDATE ON outreach.send_attempt_audit
FOR EACH ROW EXECUTE FUNCTION outreach.fn_prevent_audit_update();

-- Prevent DELETE on send_attempt_audit (append-only)
CREATE OR REPLACE FUNCTION outreach.fn_prevent_audit_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'send_attempt_audit is append-only. Deletes are not permitted.';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_audit_delete ON outreach.send_attempt_audit;
CREATE TRIGGER trg_prevent_audit_delete
BEFORE DELETE ON outreach.send_attempt_audit
FOR EACH ROW EXECUTE FUNCTION outreach.fn_prevent_audit_delete();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE outreach.send_attempt_audit IS
'Append-only audit log for all marketing send attempts. Every attempt must be logged before send. NO updates, NO deletes.';

COMMENT ON COLUMN outreach.send_attempt_audit.audit_id IS
'Unique identifier for this audit record';

COMMENT ON COLUMN outreach.send_attempt_audit.company_unique_id IS
'Company that was targeted for send';

COMMENT ON COLUMN outreach.send_attempt_audit.campaign_id IS
'Campaign identifier';

COMMENT ON COLUMN outreach.send_attempt_audit.effective_tier IS
'Effective marketing tier at time of attempt (-1 = ineligible)';

COMMENT ON COLUMN outreach.send_attempt_audit.computed_tier IS
'Computed tier before overrides applied';

COMMENT ON COLUMN outreach.send_attempt_audit.override_snapshot IS
'Full snapshot of override state at time of attempt';

COMMENT ON COLUMN outreach.send_attempt_audit.status IS
'Result of the attempt: blocked_*, allowed, sent, or send_failed';

COMMENT ON COLUMN outreach.send_attempt_audit.failure_reason IS
'Reason for block or failure (NULL if allowed/sent)';

COMMENT ON COLUMN outreach.send_attempt_audit.correlation_id IS
'End-to-end trace ID for debugging';

COMMENT ON COLUMN outreach.send_attempt_audit.created_at IS
'When this attempt was made';
