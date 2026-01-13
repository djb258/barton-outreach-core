-- ==============================================================================
-- OUTREACH EXECUTION TABLES COMPLETION MIGRATION
-- ==============================================================================
-- Date: 2026-01-13
-- Purpose: Complete outreach.* schema with missing execution tables
--
-- EXISTING (from 2025-12-26-outreach-schema-creation.sql):
--   - outreach.company_target
--   - outreach.people
--   - outreach.engagement_events
--   - outreach.column_registry
--
-- MISSING (to be created):
--   - outreach.campaigns
--   - outreach.sequences
--   - outreach.send_log
--
-- HARDENING PASS: Creates ONLY tables referenced by existing code.
-- Pattern: Reuses patterns from 2025-12-26-outreach-schema-creation.sql
-- ==============================================================================

-- ==============================================================================
-- PHASE 1: CREATE CAMPAIGNS TABLE
-- ==============================================================================
-- Based on usage in:
--   - hubs/outreach-execution/imo/middle/outreach_hub.py (CampaignTarget class)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.campaigns (
    -- Primary key
    campaign_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Campaign identity
    campaign_name           VARCHAR(255) NOT NULL,
    campaign_type           VARCHAR(50) NOT NULL DEFAULT 'cold'
        CHECK (campaign_type IN ('cold', 'warm', 'reengagement', 'talentflow', 'manual')),

    -- Status
    campaign_status         VARCHAR(50) NOT NULL DEFAULT 'draft'
        CHECK (campaign_status IN ('draft', 'active', 'paused', 'completed', 'archived')),

    -- Targeting
    target_bit_score_min    INTEGER DEFAULT 25 CHECK (target_bit_score_min >= 0 AND target_bit_score_min <= 100),
    target_outreach_state   VARCHAR(50),

    -- Limits
    daily_send_limit        INTEGER DEFAULT 100,
    total_send_limit        INTEGER,

    -- Tracking
    total_targeted          INTEGER NOT NULL DEFAULT 0,
    total_sent              INTEGER NOT NULL DEFAULT 0,
    total_opened            INTEGER NOT NULL DEFAULT 0,
    total_clicked           INTEGER NOT NULL DEFAULT 0,
    total_replied           INTEGER NOT NULL DEFAULT 0,

    -- Dates
    start_date              DATE,
    end_date                DATE,

    -- Metadata
    created_by              VARCHAR(100),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_status
    ON outreach.campaigns(campaign_status);
CREATE INDEX IF NOT EXISTS idx_campaigns_type
    ON outreach.campaigns(campaign_type);
CREATE INDEX IF NOT EXISTS idx_campaigns_active
    ON outreach.campaigns(campaign_status, start_date, end_date)
    WHERE campaign_status = 'active';

COMMENT ON TABLE outreach.campaigns IS
'OUT.TABLE.004 | Campaign definitions for Outreach Execution Hub.
Tracks campaign configuration, targeting rules, and aggregate metrics.
Individual sends tracked in outreach.send_log.';

COMMENT ON COLUMN outreach.campaigns.campaign_id IS
'OUT.CAMP.001 | Primary key - unique identifier for each campaign.';

COMMENT ON COLUMN outreach.campaigns.campaign_type IS
'OUT.CAMP.002 | Type of campaign: cold (new prospects), warm (engaged),
reengagement (cold re-warm), talentflow (job changers), manual (ad-hoc).';

COMMENT ON COLUMN outreach.campaigns.campaign_status IS
'OUT.CAMP.003 | Campaign lifecycle state.
draft: Not yet started
active: Currently sending
paused: Temporarily stopped
completed: All sends finished
archived: Historical only';

COMMENT ON COLUMN outreach.campaigns.target_bit_score_min IS
'OUT.CAMP.004 | Minimum BIT score required for campaign eligibility.
Default 25 (WARM threshold). Range 0-100.';

-- ==============================================================================
-- PHASE 2: CREATE SEQUENCES TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.sequences (
    -- Primary key
    sequence_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to campaign
    campaign_id             UUID REFERENCES outreach.campaigns(campaign_id) ON DELETE CASCADE,

    -- Sequence identity
    sequence_name           VARCHAR(255) NOT NULL,
    sequence_order          INTEGER NOT NULL DEFAULT 1,

    -- Content
    subject_template        TEXT,
    body_template           TEXT,
    template_type           VARCHAR(50) DEFAULT 'email'
        CHECK (template_type IN ('email', 'linkedin', 'phone', 'sms')),

    -- Timing
    delay_days              INTEGER NOT NULL DEFAULT 0,
    delay_hours             INTEGER NOT NULL DEFAULT 0,
    send_time_preference    VARCHAR(20) DEFAULT 'business_hours'
        CHECK (send_time_preference IN ('business_hours', 'morning', 'afternoon', 'any')),

    -- Status
    sequence_status         VARCHAR(50) NOT NULL DEFAULT 'active'
        CHECK (sequence_status IN ('active', 'paused', 'archived')),

    -- Metadata
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sequences_campaign
    ON outreach.sequences(campaign_id);
CREATE INDEX IF NOT EXISTS idx_sequences_order
    ON outreach.sequences(campaign_id, sequence_order);
CREATE INDEX IF NOT EXISTS idx_sequences_status
    ON outreach.sequences(sequence_status);

COMMENT ON TABLE outreach.sequences IS
'OUT.TABLE.005 | Sequence steps within campaigns.
Defines multi-touch outreach sequences with timing and content templates.
Linked to campaigns, tracks individual step configuration.';

COMMENT ON COLUMN outreach.sequences.sequence_order IS
'OUT.SEQ.001 | Order within campaign (1 = first touch, 2 = follow-up, etc.).';

COMMENT ON COLUMN outreach.sequences.delay_days IS
'OUT.SEQ.002 | Days to wait after previous step before sending.
Combined with delay_hours for precise timing.';

-- ==============================================================================
-- PHASE 3: CREATE SEND_LOG TABLE
-- ==============================================================================
-- Based on usage in:
--   - hubs/outreach-execution/imo/middle/outreach_hub.py
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.send_log (
    -- Primary key
    send_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links
    campaign_id             UUID REFERENCES outreach.campaigns(campaign_id) ON DELETE SET NULL,
    sequence_id             UUID REFERENCES outreach.sequences(sequence_id) ON DELETE SET NULL,
    person_id               UUID REFERENCES outreach.people(person_id) ON DELETE SET NULL,
    target_id               UUID REFERENCES outreach.company_target(target_id) ON DELETE SET NULL,

    -- Denormalized for query performance
    company_unique_id       TEXT,

    -- Send details
    email_to                VARCHAR(255) NOT NULL,
    email_subject           TEXT,
    sequence_step           INTEGER NOT NULL DEFAULT 1,

    -- Status
    send_status             VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (send_status IN ('pending', 'scheduled', 'sent', 'delivered', 'bounced', 'failed')),

    -- Timestamps
    scheduled_at            TIMESTAMPTZ,
    sent_at                 TIMESTAMPTZ,
    delivered_at            TIMESTAMPTZ,
    bounced_at              TIMESTAMPTZ,

    -- Engagement (updated by events)
    opened_at               TIMESTAMPTZ,
    clicked_at              TIMESTAMPTZ,
    replied_at              TIMESTAMPTZ,

    -- Tracking
    open_count              INTEGER NOT NULL DEFAULT 0,
    click_count             INTEGER NOT NULL DEFAULT 0,

    -- Error handling
    error_message           TEXT,
    retry_count             INTEGER NOT NULL DEFAULT 0,

    -- Metadata
    source_system           VARCHAR(100),
    external_id             VARCHAR(255),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_send_log_campaign
    ON outreach.send_log(campaign_id);
CREATE INDEX IF NOT EXISTS idx_send_log_person
    ON outreach.send_log(person_id);
CREATE INDEX IF NOT EXISTS idx_send_log_target
    ON outreach.send_log(target_id);
CREATE INDEX IF NOT EXISTS idx_send_log_company
    ON outreach.send_log(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_send_log_status
    ON outreach.send_log(send_status);
CREATE INDEX IF NOT EXISTS idx_send_log_email
    ON outreach.send_log(email_to);
CREATE INDEX IF NOT EXISTS idx_send_log_scheduled
    ON outreach.send_log(scheduled_at)
    WHERE send_status = 'scheduled';
CREATE INDEX IF NOT EXISTS idx_send_log_sent
    ON outreach.send_log(sent_at)
    WHERE sent_at IS NOT NULL;

COMMENT ON TABLE outreach.send_log IS
'OUT.TABLE.006 | Individual send records for outreach delivery.
Tracks every email/message sent, with status and engagement.
Source of truth for delivery and engagement metrics.';

COMMENT ON COLUMN outreach.send_log.send_id IS
'OUT.SEND.001 | Primary key - unique identifier for each send.';

COMMENT ON COLUMN outreach.send_log.send_status IS
'OUT.SEND.002 | Delivery status.
pending: Not yet scheduled
scheduled: Queued for delivery
sent: Handed off to email provider
delivered: Confirmed delivery
bounced: Hard bounce (suppressed)
failed: Send error (may retry)';

COMMENT ON COLUMN outreach.send_log.sequence_step IS
'OUT.SEND.003 | Which step in the sequence this send represents.
1 = initial outreach, 2+ = follow-ups.';

-- ==============================================================================
-- PHASE 4: AUTO-UPDATE TRIGGERS
-- ==============================================================================

-- Apply to new tables (trigger function already exists from prior migration)
DROP TRIGGER IF EXISTS set_updated_at ON outreach.campaigns;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.campaigns
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON outreach.sequences;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.sequences
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON outreach.send_log;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.send_log
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

-- ==============================================================================
-- PHASE 5: VERIFICATION
-- ==============================================================================

DO $$
DECLARE
    v_table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_table_count
    FROM information_schema.tables
    WHERE table_schema = 'outreach';

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Outreach Execution Tables Complete:';
    RAISE NOTICE '  Tables in outreach schema: % (expected 7)', v_table_count;
    RAISE NOTICE '  Existing:';
    RAISE NOTICE '    - outreach.company_target';
    RAISE NOTICE '    - outreach.people';
    RAISE NOTICE '    - outreach.engagement_events';
    RAISE NOTICE '    - outreach.column_registry';
    RAISE NOTICE '  New:';
    RAISE NOTICE '    - outreach.campaigns';
    RAISE NOTICE '    - outreach.sequences';
    RAISE NOTICE '    - outreach.send_log';
    RAISE NOTICE '========================================';

    IF v_table_count < 7 THEN
        RAISE WARNING 'Expected 7 tables, found %', v_table_count;
    END IF;
END $$;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- CREATED:
--   - outreach.campaigns (campaign definitions)
--   - outreach.sequences (multi-touch steps)
--   - outreach.send_log (delivery tracking)
--   - 14 indexes
--   - 3 auto-update triggers
--
-- DOCTRINE COMPLIANCE:
--   - All FK references use UUID
--   - company_unique_id denormalized for query performance
--   - No analytics tables, no derived fields
--   - Operational tracking only, not BI
-- ==============================================================================
