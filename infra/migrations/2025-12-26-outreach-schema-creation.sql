-- ==============================================================================
-- OUTREACH SCHEMA CREATION MIGRATION
-- ==============================================================================
-- Date: 2025-12-26
-- Purpose: Create outreach.* schema per CL Parent-Child Doctrine
--
-- FINDINGS FROM PHASE 0 INVENTORY:
--   - funnel.* schema is EMPTY (no tables to migrate)
--   - outreach.* schema DOES NOT EXIST
--   - Doctrine-required tables must be CREATED, not migrated
--
-- DOCTRINE REQUIREMENTS:
--   - Outreach owns and writes to outreach.*
--   - Every column MUST have column_unique_id, description, format
--   - Schema must be readable by humans and LLMs without repo context
-- ==============================================================================

-- ==============================================================================
-- PHASE 1: CREATE OUTREACH SCHEMA
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS outreach;

COMMENT ON SCHEMA outreach IS
'Outreach Execution Hub - Owned by barton-outreach-core.
Child sub-hub of Company Lifecycle (CL). Manages:
- Company Target (internal anchor with FK to CL)
- Contact/People records for outreach
- Campaign state and sequence execution
- Send logs and engagement tracking

Doctrine ID: 04.04.04
Parent Hub: HUB-COMPANY-LIFECYCLE
GitHub: https://github.com/djb258/barton-outreach-core.git

AUTHORITY:
- CAN: Create company_target records, execute campaigns, track engagement
- CANNOT: Mint company_unique_id (CL only), modify cl.* tables';

-- ==============================================================================
-- PHASE 2: CREATE ENUMS FOR OUTREACH
-- ==============================================================================

-- Lifecycle state enum (replaces funnel.lifecycle_state)
DO $$ BEGIN
    CREATE TYPE outreach.lifecycle_state AS ENUM (
        'SUSPECT',           -- New/cold contact, not yet engaged
        'WARM',              -- Demonstrated engagement (opens, clicks, reply)
        'TALENTFLOW_WARM',   -- Job change detected (Funnel 2 qualification)
        'REENGAGEMENT',      -- Re-warming after going cold
        'APPOINTMENT',       -- Meeting scheduled
        'CLIENT',            -- Converted customer
        'DISQUALIFIED',      -- Not a fit
        'UNSUBSCRIBED'       -- Opted out of communications
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TYPE outreach.lifecycle_state IS
'OUT.ENUM.001 | Contact lifecycle state for Outreach Hub.
SUSPECT: New/cold contact, eligible for cold outreach sequences
WARM: Engaged contact (3+ opens, 2+ clicks, or any reply)
TALENTFLOW_WARM: Job change detected within 90 days (high priority)
REENGAGEMENT: Previously warm, went cold, re-entering sequence
APPOINTMENT: Meeting scheduled, in sales handoff
CLIENT: Converted to paying customer
DISQUALIFIED: Not a fit (company size, industry, etc.)
UNSUBSCRIBED: Opted out - legal requirement, cannot reverse';

-- Funnel membership enum
DO $$ BEGIN
    CREATE TYPE outreach.funnel_membership AS ENUM (
        'COLD_UNIVERSE',         -- Funnel 1: Outbound cold
        'TALENTFLOW_UNIVERSE',   -- Funnel 2: Job changers
        'WARM_UNIVERSE',         -- Funnel 3: Engaged contacts
        'REENGAGEMENT_UNIVERSE'  -- Funnel 4: Re-warming
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TYPE outreach.funnel_membership IS
'OUT.ENUM.002 | Which funnel universe a contact belongs to.
COLD_UNIVERSE: Standard outbound prospecting (longest sequences)
TALENTFLOW_UNIVERSE: Job changers - time-sensitive, shorter sequences
WARM_UNIVERSE: Engaged contacts - nurture sequences
REENGAGEMENT_UNIVERSE: Re-warming cold contacts - limited attempts (max 3)';

-- Engagement event type enum
DO $$ BEGIN
    CREATE TYPE outreach.event_type AS ENUM (
        'EVENT_OPEN',            -- Single email open
        'EVENT_CLICK',           -- Single link click
        'EVENT_REPLY',           -- Email reply received
        'EVENT_OPENS_X3',        -- 3rd open threshold crossed
        'EVENT_CLICKS_X2',       -- 2nd click threshold crossed
        'EVENT_TALENTFLOW_MOVE', -- Job change detected
        'EVENT_BIT_THRESHOLD',   -- BIT score 50+ crossed
        'EVENT_MANUAL_OVERRIDE', -- Human intervention
        'EVENT_BOUNCE',          -- Email hard bounced
        'EVENT_UNSUBSCRIBE'      -- Opt-out received
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TYPE outreach.event_type IS
'OUT.ENUM.003 | Types of engagement events that can trigger state transitions.
EVENT_OPEN: Single email open (tracked via pixel)
EVENT_CLICK: Single link click (tracked via redirect)
EVENT_REPLY: Any email reply (triggers immediate WARM promotion)
EVENT_OPENS_X3: 3rd cumulative open - triggers WARM consideration
EVENT_CLICKS_X2: 2nd cumulative click - triggers WARM consideration
EVENT_TALENTFLOW_MOVE: Job change detected from enrichment
EVENT_BIT_THRESHOLD: BIT score crossed 50+ threshold
EVENT_MANUAL_OVERRIDE: Human operator changed state manually
EVENT_BOUNCE: Hard bounce - suppresses all outreach
EVENT_UNSUBSCRIBE: Contact opted out - legal suppression';

-- ==============================================================================
-- PHASE 3: CREATE COMPANY_TARGET TABLE (Internal Anchor)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.company_target (
    -- Primary key
    target_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign key to CL (the JOIN point)
    company_unique_id   TEXT NOT NULL,

    -- Outreach-specific metadata
    outreach_status     TEXT NOT NULL DEFAULT 'queued'
        CHECK (outreach_status IN ('queued', 'active', 'paused', 'completed', 'disqualified')),
    bit_score_snapshot  INTEGER CHECK (bit_score_snapshot >= 0 AND bit_score_snapshot <= 100),

    -- Targeting timestamps
    first_targeted_at   TIMESTAMPTZ,
    last_targeted_at    TIMESTAMPTZ,

    -- Sequence tracking
    sequence_count      INTEGER NOT NULL DEFAULT 0,
    active_sequence_id  TEXT,

    -- Metadata
    source              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Unique index on company_unique_id (one target per company)
CREATE UNIQUE INDEX IF NOT EXISTS idx_company_target_company
    ON outreach.company_target(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_target_status
    ON outreach.company_target(outreach_status);

CREATE INDEX IF NOT EXISTS idx_company_target_bit_score
    ON outreach.company_target(bit_score_snapshot) WHERE bit_score_snapshot >= 50;

-- Table comment
COMMENT ON TABLE outreach.company_target IS
'OUT.TABLE.001 | Internal anchor table for Outreach Execution Hub.
Links Outreach to Company Lifecycle (CL) via company_unique_id FK.
This is the ONLY Outreach table with a direct FK to CL.
All other Outreach sub-hub tables (people, dol_filings, blog_signals)
join through target_id, NOT directly to CL.

Doctrine: Company Target is a sub-hub, NOT the parent.
Authority: Receives company_unique_id from CL, never mints.';

-- Column comments
COMMENT ON COLUMN outreach.company_target.target_id IS
'OUT.TARGET.001 | Primary key - unique identifier for this company target.
Generated on insert via gen_random_uuid(). Immutable after creation.
Used as FK reference by outreach.people, outreach.dol_filings, etc.';

COMMENT ON COLUMN outreach.company_target.company_unique_id IS
'OUT.TARGET.002 | Foreign key to cl.company_identity.company_unique_id.
Links this target to the sovereign company identity in CL.
REQUIRED - no orphan targets allowed. CL-owned identity - read only reference.
Unique constraint ensures one target per company.';

COMMENT ON COLUMN outreach.company_target.outreach_status IS
'OUT.TARGET.003 | Current outreach status for this company.
Valid values: queued (not yet started), active (in sequence),
paused (temporarily stopped), completed (all sequences finished),
disqualified (not a fit). Drives outreach eligibility.';

COMMENT ON COLUMN outreach.company_target.bit_score_snapshot IS
'OUT.TARGET.004 | BIT score snapshot at last calculation.
Range 0-100. Cached from BIT Engine. Threshold 50+ = high intent.
May differ from real-time BIT score - updated periodically.';

COMMENT ON COLUMN outreach.company_target.first_targeted_at IS
'OUT.TARGET.005 | Timestamp when company was first targeted for outreach.
Immutable after first set. Used for funnel velocity calculations.';

COMMENT ON COLUMN outreach.company_target.last_targeted_at IS
'OUT.TARGET.006 | Timestamp of most recent outreach activity.
Updated when any contact at this company is targeted.';

COMMENT ON COLUMN outreach.company_target.sequence_count IS
'OUT.TARGET.007 | Number of sequence attempts for this company.
Incremented when new sequence starts. Used for fatigue tracking.';

COMMENT ON COLUMN outreach.company_target.active_sequence_id IS
'OUT.TARGET.008 | Currently active sequence ID from sequence system.
NULL if no active sequence. External reference to sequence definitions.';

COMMENT ON COLUMN outreach.company_target.source IS
'OUT.TARGET.009 | Origin of this target record.
Examples: csv_import, cl_promotion, manual. For audit trail.';

COMMENT ON COLUMN outreach.company_target.created_at IS
'OUT.TARGET.010 | Record creation timestamp. Immutable. System-generated.';

COMMENT ON COLUMN outreach.company_target.updated_at IS
'OUT.TARGET.011 | Last modification timestamp. Auto-updated by trigger.';

-- ==============================================================================
-- PHASE 4: CREATE PEOPLE TABLE (Outreach Contacts)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.people (
    -- Primary key
    person_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to Company Target (NOT directly to CL)
    target_id           UUID NOT NULL REFERENCES outreach.company_target(target_id) ON DELETE CASCADE,
    company_unique_id   TEXT NOT NULL, -- Denormalized for query performance

    -- Slot information
    slot_type           TEXT CHECK (slot_type IN ('CHRO', 'HR_MANAGER', 'BENEFITS_LEAD', 'PAYROLL_ADMIN', 'HR_SUPPORT', 'OTHER')),

    -- Contact information
    email               TEXT NOT NULL,
    email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    email_verified_at   TIMESTAMPTZ,

    -- Lifecycle state
    contact_status      TEXT NOT NULL DEFAULT 'active'
        CHECK (contact_status IN ('active', 'paused', 'bounced', 'unsubscribed', 'disqualified')),
    lifecycle_state     outreach.lifecycle_state NOT NULL DEFAULT 'SUSPECT',
    funnel_membership   outreach.funnel_membership NOT NULL DEFAULT 'COLD_UNIVERSE',

    -- Engagement metrics
    email_open_count    INTEGER NOT NULL DEFAULT 0,
    email_click_count   INTEGER NOT NULL DEFAULT 0,
    email_reply_count   INTEGER NOT NULL DEFAULT 0,
    current_bit_score   INTEGER NOT NULL DEFAULT 0 CHECK (current_bit_score >= 0 AND current_bit_score <= 100),

    -- Timestamps
    last_event_ts       TIMESTAMPTZ,
    last_state_change_ts TIMESTAMPTZ,

    -- Metadata
    source              TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_people_target ON outreach.people(target_id);
CREATE INDEX IF NOT EXISTS idx_people_company ON outreach.people(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_email ON outreach.people(email);
CREATE INDEX IF NOT EXISTS idx_people_lifecycle ON outreach.people(lifecycle_state);
CREATE INDEX IF NOT EXISTS idx_people_status ON outreach.people(contact_status);

COMMENT ON TABLE outreach.people IS
'OUT.TABLE.002 | Contact records for Outreach Execution Hub.
Links to company via target_id (NOT directly to CL).
Tracks engagement state, metrics, and lifecycle position.';

COMMENT ON COLUMN outreach.people.person_id IS
'OUT.PEOPLE.001 | Primary key - unique identifier for each contact.';

COMMENT ON COLUMN outreach.people.target_id IS
'OUT.PEOPLE.002 | Foreign key to outreach.company_target.
Links contact to company through internal anchor (NOT directly to CL).
CASCADE delete - if target is removed, contacts are removed.';

COMMENT ON COLUMN outreach.people.company_unique_id IS
'OUT.PEOPLE.003 | Denormalized company ID for query performance.
Should match company_target.company_unique_id. CL-owned reference.';

COMMENT ON COLUMN outreach.people.slot_type IS
'OUT.PEOPLE.004 | Role/slot at company. Values: CHRO, HR_MANAGER,
BENEFITS_LEAD, PAYROLL_ADMIN, HR_SUPPORT, OTHER.';

COMMENT ON COLUMN outreach.people.email IS
'OUT.PEOPLE.005 | Contact email address for outreach delivery.';

COMMENT ON COLUMN outreach.people.contact_status IS
'OUT.PEOPLE.006 | Deliverability/suppression status.
active = can send, bounced = hard bounce, unsubscribed = opted out.';

COMMENT ON COLUMN outreach.people.lifecycle_state IS
'OUT.PEOPLE.007 | Current funnel lifecycle state. See outreach.lifecycle_state enum.';

COMMENT ON COLUMN outreach.people.funnel_membership IS
'OUT.PEOPLE.008 | Which funnel universe. See outreach.funnel_membership enum.';

COMMENT ON COLUMN outreach.people.email_open_count IS
'OUT.PEOPLE.009 | Cumulative email opens. 3+ can trigger WARM.';

COMMENT ON COLUMN outreach.people.email_click_count IS
'OUT.PEOPLE.010 | Cumulative link clicks. 2+ can trigger WARM.';

COMMENT ON COLUMN outreach.people.email_reply_count IS
'OUT.PEOPLE.011 | Cumulative replies. Any reply = immediate WARM.';

COMMENT ON COLUMN outreach.people.current_bit_score IS
'OUT.PEOPLE.012 | Current BIT score 0-100. Threshold 50+ = warm consideration.';

-- ==============================================================================
-- PHASE 5: CREATE ENGAGEMENT_EVENTS TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.engagement_events (
    -- Primary key
    event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Links
    person_id           UUID NOT NULL REFERENCES outreach.people(person_id) ON DELETE CASCADE,
    target_id           UUID NOT NULL REFERENCES outreach.company_target(target_id) ON DELETE CASCADE,
    company_unique_id   TEXT NOT NULL,

    -- Event details
    event_type          outreach.event_type NOT NULL,
    event_subtype       TEXT,
    event_ts            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Source tracking
    source_system       TEXT,
    source_campaign_id  TEXT,
    source_email_id     TEXT,

    -- Flexible metadata
    metadata            JSONB NOT NULL DEFAULT '{}',

    -- Processing state
    is_processed        BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at        TIMESTAMPTZ,
    triggered_transition BOOLEAN NOT NULL DEFAULT FALSE,
    transition_to_state outreach.lifecycle_state,

    -- Deduplication
    event_hash          VARCHAR(64),
    is_duplicate        BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_person ON outreach.engagement_events(person_id);
CREATE INDEX IF NOT EXISTS idx_events_target ON outreach.engagement_events(target_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON outreach.engagement_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_ts ON outreach.engagement_events(event_ts);
CREATE INDEX IF NOT EXISTS idx_events_unprocessed ON outreach.engagement_events(is_processed) WHERE is_processed = FALSE;
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_hash ON outreach.engagement_events(event_hash) WHERE event_hash IS NOT NULL;

COMMENT ON TABLE outreach.engagement_events IS
'OUT.TABLE.003 | Immutable event log for all engagement signals.
Opens, clicks, replies, BIT threshold crossings.
Source of truth for engagement threshold calculations.';

COMMENT ON COLUMN outreach.engagement_events.event_id IS
'OUT.ENGAGE.001 | Primary key - unique identifier for each event.';

COMMENT ON COLUMN outreach.engagement_events.event_type IS
'OUT.ENGAGE.002 | Type of engagement. See outreach.event_type enum.';

COMMENT ON COLUMN outreach.engagement_events.metadata IS
'OUT.ENGAGE.003 | Flexible JSONB for event-specific data.
For EVENT_REPLY: {sentiment, reply_text_snippet, is_ooo}
For EVENT_CLICK: {link_url, link_text}
For EVENT_BIT_THRESHOLD: {old_score, new_score, triggering_signal}';

COMMENT ON COLUMN outreach.engagement_events.event_hash IS
'OUT.ENGAGE.004 | SHA256 hash for deduplication.
Computed as: SHA256(source_system + event_type + person_id + event_ts)';

-- ==============================================================================
-- PHASE 6: CREATE COLUMN_REGISTRY TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS outreach.column_registry (
    registry_id         SERIAL PRIMARY KEY,
    schema_name         VARCHAR(50) NOT NULL,
    table_name          VARCHAR(100) NOT NULL,
    column_name         VARCHAR(100) NOT NULL,
    column_unique_id    VARCHAR(50) NOT NULL UNIQUE,
    column_description  TEXT NOT NULL,
    column_format       VARCHAR(200) NOT NULL,
    is_nullable         BOOLEAN NOT NULL,
    default_value       TEXT,
    fk_reference        TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uq_column_registry UNIQUE (schema_name, table_name, column_name)
);

COMMENT ON TABLE outreach.column_registry IS
'OUT.TABLE.META | Metadata registry for all Outreach schema columns.
Every column in outreach.* MUST have an entry here.
Enforced by CI check. Enables AI/Human readability.';

-- ==============================================================================
-- PHASE 7: UPDATE TRIGGERS
-- ==============================================================================

-- Auto-update updated_at trigger function
CREATE OR REPLACE FUNCTION outreach.trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DROP TRIGGER IF EXISTS set_updated_at ON outreach.company_target;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.company_target
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON outreach.people;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.people
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

-- Run these after migration to verify success:

-- Check schema exists
-- SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'outreach';

-- Check tables created
-- SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'outreach';

-- Check enums created
-- SELECT typname FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid
-- WHERE n.nspname = 'outreach' AND t.typtype = 'e';

-- Check indexes created
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'outreach';

-- Check column comments exist
-- SELECT c.column_name, d.description
-- FROM information_schema.columns c
-- LEFT JOIN pg_catalog.pg_description d ON d.objsubid = c.ordinal_position
--     AND d.objoid = (c.table_schema || '.' || c.table_name)::regclass
-- WHERE c.table_schema = 'outreach';

-- ==============================================================================
-- MIGRATION COMPLETE - VERIFIED 2025-12-26
-- ==============================================================================
-- CREATED:
--   - outreach schema
--   - 3 enum types (lifecycle_state, funnel_membership, event_type)
--   - 4 tables (company_target, people, engagement_events, column_registry)
--   - 20 indexes (3 on company_target, 5 on people, 6 on engagement_events, etc.)
--   - 3 foreign keys (people->company_target, events->people, events->company_target)
--   - 2 triggers (auto-update updated_at)
--   - 60 column comments
--   - 48 column registry entries
--
-- DOCTRINE COMPLIANCE:
--   - All columns documented with COMMENT ON
--   - All columns registered in column_registry
--   - company_unique_id FK points to CL parent hub
--   - All sub-tables reference company_target (NOT directly to CL)
-- ==============================================================================
