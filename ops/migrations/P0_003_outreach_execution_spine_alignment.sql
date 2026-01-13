-- =============================================================================
-- P0 MIGRATION: OUTREACH EXECUTION SPINE ALIGNMENT
-- =============================================================================
-- Migration ID: P0_003
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
-- Mode: SAFE MODE - No application code changes, reversible
--
-- PURPOSE:
--   Create and/or update Outreach Execution tables to comply with Spine-First
--   Architecture v1.1. Ensures campaigns and send_log tables FK to outreach_id.
--
-- TABLES AFFECTED:
--   1. outreach.campaigns (CREATE IF NOT EXISTS, add outreach_id FK)
--   2. outreach.send_log (CREATE IF NOT EXISTS, add outreach_id FK)
--
-- DOCTRINE COMPLIANCE:
--   - All sub-hubs FK to outreach.outreach.outreach_id
--   - sovereign_id is hidden from sub-hubs
--   - Legacy columns LEFT IN PLACE (do NOT drop yet)
--
-- ROLLBACK: See P0_003_outreach_execution_spine_alignment_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- SECTION A: Create outreach.campaigns table
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.campaigns (
    campaign_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference (PRIMARY FK)
    outreach_id UUID NOT NULL,

    -- Campaign metadata
    campaign_name VARCHAR(255) NOT NULL,
    campaign_type VARCHAR(50) NOT NULL CHECK (campaign_type IN ('cold', 'warm', 'talentflow', 'reengagement')),
    campaign_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (campaign_status IN ('draft', 'active', 'paused', 'completed', 'cancelled')),

    -- Sequence configuration
    sequence_id UUID,
    sequence_step INTEGER DEFAULT 1,
    max_steps INTEGER DEFAULT 5,

    -- Timing
    scheduled_start TIMESTAMPTZ,
    actual_start TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metrics (denormalized for performance)
    total_contacts INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    open_count INTEGER DEFAULT 0,
    click_count INTEGER DEFAULT 0,
    reply_count INTEGER DEFAULT 0,
    bounce_count INTEGER DEFAULT 0,
    unsubscribe_count INTEGER DEFAULT 0,

    -- Legacy reference (DO NOT USE for new code)
    company_unique_id TEXT,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT DEFAULT 'system',

    -- FK to spine
    CONSTRAINT fk_campaigns_outreach
        FOREIGN KEY (outreach_id)
        REFERENCES outreach.outreach(outreach_id)
        ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_outreach_id
ON outreach.campaigns(outreach_id);

CREATE INDEX IF NOT EXISTS idx_campaigns_status
ON outreach.campaigns(campaign_status);

CREATE INDEX IF NOT EXISTS idx_campaigns_type
ON outreach.campaigns(campaign_type);

CREATE INDEX IF NOT EXISTS idx_campaigns_scheduled_start
ON outreach.campaigns(scheduled_start)
WHERE campaign_status = 'active';

-- Table comment
COMMENT ON TABLE outreach.campaigns IS
'OUT.EXEC.CAMP.001 | Campaign execution table for Outreach Execution sub-hub.
FKs to outreach_id (NOT directly to CL).
Part of waterfall: Company Target -> DOL -> People -> Blog -> Execution
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.';

COMMENT ON COLUMN outreach.campaigns.outreach_id IS
'OUT.EXEC.CAMP.FK | Primary FK to outreach.outreach.outreach_id.
All campaigns must reference the spine. Required.';

COMMENT ON COLUMN outreach.campaigns.company_unique_id IS
'OUT.EXEC.CAMP.LEGACY | Legacy company reference. DO NOT USE for new code.
Retained temporarily for backward compatibility. Will be dropped in Phase 2.';

-- =============================================================================
-- SECTION B: Create outreach.send_log table
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.send_log (
    send_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference (PRIMARY FK)
    outreach_id UUID NOT NULL,

    -- Campaign reference
    campaign_id UUID,

    -- Contact reference
    person_id UUID,

    -- Send details
    email_address TEXT NOT NULL,
    subject_line TEXT,
    send_status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (send_status IN ('pending', 'sent', 'delivered', 'bounced', 'failed')),

    -- Timing
    scheduled_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,

    -- Engagement tracking
    opened_at TIMESTAMPTZ,
    open_count INTEGER DEFAULT 0,
    clicked_at TIMESTAMPTZ,
    click_count INTEGER DEFAULT 0,
    replied_at TIMESTAMPTZ,
    bounced_at TIMESTAMPTZ,
    unsubscribed_at TIMESTAMPTZ,

    -- Email service provider reference
    esp_message_id TEXT,
    esp_status TEXT,

    -- Legacy reference (DO NOT USE for new code)
    company_unique_id TEXT,

    -- Traceability
    correlation_id UUID DEFAULT gen_random_uuid(),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- FK to spine
    CONSTRAINT fk_send_log_outreach
        FOREIGN KEY (outreach_id)
        REFERENCES outreach.outreach(outreach_id)
        ON DELETE CASCADE,

    -- FK to campaign (optional)
    CONSTRAINT fk_send_log_campaign
        FOREIGN KEY (campaign_id)
        REFERENCES outreach.campaigns(campaign_id)
        ON DELETE SET NULL,

    -- FK to person (optional)
    CONSTRAINT fk_send_log_person
        FOREIGN KEY (person_id)
        REFERENCES outreach.people(person_id)
        ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_send_log_outreach_id
ON outreach.send_log(outreach_id);

CREATE INDEX IF NOT EXISTS idx_send_log_campaign_id
ON outreach.send_log(campaign_id);

CREATE INDEX IF NOT EXISTS idx_send_log_person_id
ON outreach.send_log(person_id);

CREATE INDEX IF NOT EXISTS idx_send_log_email
ON outreach.send_log(email_address);

CREATE INDEX IF NOT EXISTS idx_send_log_status
ON outreach.send_log(send_status);

CREATE INDEX IF NOT EXISTS idx_send_log_sent_at
ON outreach.send_log(sent_at DESC);

CREATE INDEX IF NOT EXISTS idx_send_log_correlation_id
ON outreach.send_log(correlation_id);

-- Table comment
COMMENT ON TABLE outreach.send_log IS
'OUT.EXEC.SEND.001 | Send log table for email tracking in Outreach Execution.
Immutable record of every email send attempt.
FKs to outreach_id (NOT directly to CL).
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.';

COMMENT ON COLUMN outreach.send_log.outreach_id IS
'OUT.EXEC.SEND.FK | Primary FK to outreach.outreach.outreach_id.
All sends must reference the spine. Required.';

COMMENT ON COLUMN outreach.send_log.company_unique_id IS
'OUT.EXEC.SEND.LEGACY | Legacy company reference. DO NOT USE for new code.
Retained temporarily for backward compatibility. Will be dropped in Phase 2.';

-- =============================================================================
-- SECTION C: Create outreach.execution_errors table
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.execution_errors (
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine reference
    outreach_id UUID,

    -- Context
    campaign_id UUID,
    send_id UUID,
    person_id UUID,

    -- Error details
    pipeline_stage VARCHAR(50) NOT NULL,
    failure_code VARCHAR(50) NOT NULL,
    blocking_reason TEXT,
    severity VARCHAR(20) DEFAULT 'ERROR' CHECK (severity IN ('ERROR', 'WARNING', 'CRITICAL')),

    -- Processing
    retry_allowed BOOLEAN DEFAULT FALSE,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Traceability
    correlation_id UUID,
    raw_input JSONB,
    stack_trace TEXT,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,
    resolution_note TEXT,

    -- FK to spine (optional - may fail before outreach_id known)
    CONSTRAINT fk_exec_errors_outreach
        FOREIGN KEY (outreach_id)
        REFERENCES outreach.outreach(outreach_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_exec_errors_campaign
        FOREIGN KEY (campaign_id)
        REFERENCES outreach.campaigns(campaign_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_exec_errors_send
        FOREIGN KEY (send_id)
        REFERENCES outreach.send_log(send_id)
        ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_exec_errors_outreach_id
ON outreach.execution_errors(outreach_id);

CREATE INDEX IF NOT EXISTS idx_exec_errors_campaign_id
ON outreach.execution_errors(campaign_id);

CREATE INDEX IF NOT EXISTS idx_exec_errors_pipeline_stage
ON outreach.execution_errors(pipeline_stage);

CREATE INDEX IF NOT EXISTS idx_exec_errors_failure_code
ON outreach.execution_errors(failure_code);

CREATE INDEX IF NOT EXISTS idx_exec_errors_unresolved
ON outreach.execution_errors(resolved_at)
WHERE resolved_at IS NULL;

-- Table comment
COMMENT ON TABLE outreach.execution_errors IS
'OUT.EXEC.ERR.001 | Error persistence table for Outreach Execution sub-hub.
Per Error Persistence Doctrine: failures are work items, not states.
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.';

-- =============================================================================
-- SECTION D: Add triggers
-- =============================================================================

-- Auto-update updated_at for campaigns
DROP TRIGGER IF EXISTS set_updated_at ON outreach.campaigns;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.campaigns
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

-- Auto-update updated_at for send_log
DROP TRIGGER IF EXISTS set_updated_at ON outreach.send_log;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.send_log
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

-- =============================================================================
-- SECTION E: Create views for execution monitoring
-- =============================================================================

CREATE OR REPLACE VIEW outreach.v_campaign_summary AS
SELECT
    c.campaign_id,
    c.outreach_id,
    c.campaign_name,
    c.campaign_type,
    c.campaign_status,
    c.total_contacts,
    c.sent_count,
    c.open_count,
    c.click_count,
    c.reply_count,
    CASE
        WHEN c.sent_count > 0 THEN ROUND(100.0 * c.open_count / c.sent_count, 1)
        ELSE 0
    END AS open_rate_pct,
    CASE
        WHEN c.open_count > 0 THEN ROUND(100.0 * c.click_count / c.open_count, 1)
        ELSE 0
    END AS click_to_open_rate_pct,
    c.scheduled_start,
    c.actual_start,
    c.completed_at,
    c.created_at
FROM outreach.campaigns c
ORDER BY c.created_at DESC;

COMMENT ON VIEW outreach.v_campaign_summary IS
'OUT.EXEC.VIEW.001 | Campaign performance summary view.
Shows key metrics and rates for each campaign.';

CREATE OR REPLACE VIEW outreach.v_send_activity AS
SELECT
    sl.send_id,
    sl.outreach_id,
    sl.campaign_id,
    sl.email_address,
    sl.send_status,
    sl.sent_at,
    sl.opened_at,
    sl.clicked_at,
    sl.replied_at,
    sl.bounced_at,
    CASE
        WHEN sl.replied_at IS NOT NULL THEN 'ENGAGED_REPLY'
        WHEN sl.clicked_at IS NOT NULL THEN 'ENGAGED_CLICK'
        WHEN sl.opened_at IS NOT NULL THEN 'OPENED'
        WHEN sl.bounced_at IS NOT NULL THEN 'BOUNCED'
        WHEN sl.sent_at IS NOT NULL THEN 'DELIVERED'
        ELSE 'PENDING'
    END AS engagement_status,
    sl.correlation_id
FROM outreach.send_log sl
ORDER BY sl.sent_at DESC NULLS LAST;

COMMENT ON VIEW outreach.v_send_activity IS
'OUT.EXEC.VIEW.002 | Send activity view with engagement status.
Shows current engagement status for each send.';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Check tables created:
-- SELECT tablename FROM pg_tables WHERE schemaname = 'outreach'
-- AND tablename IN ('campaigns', 'send_log', 'execution_errors');
--
-- 2. Check FK constraints:
-- SELECT conname, confrelid::regclass AS references_table
-- FROM pg_constraint
-- WHERE conrelid = 'outreach.campaigns'::regclass AND contype = 'f';
--
-- 3. Check indexes created:
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'outreach'
-- AND tablename IN ('campaigns', 'send_log', 'execution_errors');
--
-- 4. Check views created:
-- SELECT viewname FROM pg_views WHERE schemaname = 'outreach'
-- AND viewname IN ('v_campaign_summary', 'v_send_activity');

-- =============================================================================
-- MIGRATION P0_003 COMPLETE
-- =============================================================================
-- CREATED:
--   - outreach.campaigns table (with outreach_id FK)
--   - outreach.send_log table (with outreach_id FK)
--   - outreach.execution_errors table
--   - outreach.v_campaign_summary view
--   - outreach.v_send_activity view
--   - 14 indexes
--   - 2 triggers
--
-- FK COMPLIANCE:
--   - campaigns.outreach_id -> outreach.outreach(outreach_id)
--   - send_log.outreach_id -> outreach.outreach(outreach_id)
--
-- LEGACY COLUMNS (DO NOT USE):
--   - campaigns.company_unique_id (for backward compatibility)
--   - send_log.company_unique_id (for backward compatibility)
--
-- NEXT STEPS:
--   1. Phase 2: Remove legacy company_unique_id columns
--   2. Phase 2: Update application code to use outreach_id
-- =============================================================================
