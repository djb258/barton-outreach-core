-- ============================================================================
-- Migration: 0003_create_engagement_events.sql
-- Description: Create engagement_events table (event log for all engagement signals)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- TABLE: engagement_events
-- Purpose: Immutable log of all engagement events (opens, clicks, replies, etc.)
-- Usage: Source of truth for engagement history and threshold calculations
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.engagement_events (
    -- Primary key
    event_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- Event classification
    event_type              funnel.event_type NOT NULL,
    event_subtype           VARCHAR(50),  -- e.g., 'positive_reply', 'ooo_reply', 'link_click'

    -- Event timestamp
    event_ts                TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Event source
    source_system           VARCHAR(100),  -- e.g., 'email_tracking', 'crm', 'manual'
    source_campaign_id      VARCHAR(100),  -- Email campaign ID if applicable
    source_email_id         VARCHAR(100),  -- Specific email ID if applicable

    -- Event metadata (flexible JSON for event-specific data)
    metadata                JSONB NOT NULL DEFAULT '{}',

    -- Processing status
    is_processed            BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at            TIMESTAMPTZ,
    triggered_transition    BOOLEAN NOT NULL DEFAULT FALSE,
    transition_to_state     funnel.lifecycle_state,

    -- Deduplication
    event_hash              VARCHAR(64),  -- SHA256 hash for deduplication
    is_duplicate            BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_event_hash UNIQUE (event_hash)
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_engagement_company_id ON funnel.engagement_events(company_id);
CREATE INDEX idx_engagement_person_id ON funnel.engagement_events(person_id);
CREATE INDEX idx_engagement_suspect_id ON funnel.engagement_events(suspect_id);

-- Event type indexes
CREATE INDEX idx_engagement_event_type ON funnel.engagement_events(event_type);
CREATE INDEX idx_engagement_event_subtype ON funnel.engagement_events(event_subtype);

-- Time-based indexes
CREATE INDEX idx_engagement_event_ts ON funnel.engagement_events(event_ts);
CREATE INDEX idx_engagement_created_at ON funnel.engagement_events(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_engagement_person_type ON funnel.engagement_events(person_id, event_type);
CREATE INDEX idx_engagement_person_ts ON funnel.engagement_events(person_id, event_ts);
CREATE INDEX idx_engagement_company_type ON funnel.engagement_events(company_id, event_type);
CREATE INDEX idx_engagement_type_ts ON funnel.engagement_events(event_type, event_ts);

-- Processing indexes
CREATE INDEX idx_engagement_unprocessed ON funnel.engagement_events(is_processed, event_ts)
    WHERE is_processed = FALSE;
CREATE INDEX idx_engagement_triggered ON funnel.engagement_events(triggered_transition)
    WHERE triggered_transition = TRUE;

-- Source tracking indexes
CREATE INDEX idx_engagement_source_system ON funnel.engagement_events(source_system);
CREATE INDEX idx_engagement_campaign ON funnel.engagement_events(source_campaign_id)
    WHERE source_campaign_id IS NOT NULL;

-- Deduplication index
CREATE INDEX idx_engagement_hash ON funnel.engagement_events(event_hash);

-- JSONB metadata index for flexible queries
CREATE INDEX idx_engagement_metadata ON funnel.engagement_events USING GIN (metadata);

-- ============================================================================
-- PARTITIONING (Optional - for high-volume systems)
-- Uncomment if event volume is expected to be very high
-- ============================================================================

-- Note: If partitioning is needed, recreate table with:
-- CREATE TABLE funnel.engagement_events (...) PARTITION BY RANGE (event_ts);
-- CREATE TABLE funnel.engagement_events_2025_q1 PARTITION OF funnel.engagement_events
--     FOR VALUES FROM ('2025-01-01') TO ('2025-04-01');

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.engagement_events IS 'Immutable event log for all engagement signals. Used for threshold calculations and audit trail.';
COMMENT ON COLUMN funnel.engagement_events.event_id IS 'Primary key - unique identifier for each event';
COMMENT ON COLUMN funnel.engagement_events.event_type IS 'Type of event (EVENT_REPLY, EVENT_CLICKS_X2, etc.)';
COMMENT ON COLUMN funnel.engagement_events.event_subtype IS 'Subtype for more granular classification';
COMMENT ON COLUMN funnel.engagement_events.metadata IS 'Flexible JSON storage for event-specific data';
COMMENT ON COLUMN funnel.engagement_events.event_hash IS 'SHA256 hash for deduplication (source+type+person+ts)';
COMMENT ON COLUMN funnel.engagement_events.triggered_transition IS 'Whether this event triggered a state transition';
