-- ============================================================================
-- Migration: 0004_create_warm_universe.sql
-- Description: Create warm_universe table (Funnel 3: Warm/Engaged Universe)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- TABLE: warm_universe
-- Purpose: Track contacts who have demonstrated engagement (Funnel 3)
-- Entry: Via email reply, 3+ opens, 2+ clicks, or BIT threshold
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.warm_universe (
    -- Primary key
    warm_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- Warm qualification
    warm_reason             VARCHAR(50) NOT NULL,  -- 'reply', 'opens_x3', 'clicks_x2', 'bit_threshold'
    warm_score              INTEGER NOT NULL DEFAULT 0,  -- Engagement score at time of promotion
    qualifying_event_id     UUID REFERENCES funnel.engagement_events(event_id),

    -- Timestamps
    first_warm_ts           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_engagement_ts      TIMESTAMPTZ,

    -- Engagement metrics at promotion time
    opens_at_promotion      INTEGER NOT NULL DEFAULT 0,
    clicks_at_promotion     INTEGER NOT NULL DEFAULT 0,
    replies_at_promotion    INTEGER NOT NULL DEFAULT 0,
    bit_score_at_promotion  INTEGER NOT NULL DEFAULT 0,

    -- Current engagement tracking
    current_opens           INTEGER NOT NULL DEFAULT 0,
    current_clicks          INTEGER NOT NULL DEFAULT 0,
    current_replies         INTEGER NOT NULL DEFAULT 0,

    -- TalentFlow overlay
    has_talentflow_signal   BOOLEAN NOT NULL DEFAULT FALSE,
    talentflow_signal_id    UUID,

    -- Nurture sequence tracking
    nurture_sequence_id     VARCHAR(100),
    nurture_step            INTEGER DEFAULT 0,
    nurture_started_at      TIMESTAMPTZ,

    -- Lifecycle tracking
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    demoted_to_reengagement BOOLEAN NOT NULL DEFAULT FALSE,
    demoted_at              TIMESTAMPTZ,
    promoted_to_appointment BOOLEAN NOT NULL DEFAULT FALSE,
    promoted_at             TIMESTAMPTZ,

    -- Metadata
    source                  VARCHAR(100),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_warm_person UNIQUE (person_id),
    CONSTRAINT chk_warm_reason CHECK (warm_reason IN ('reply', 'opens_x3', 'clicks_x2', 'bit_threshold', 'manual'))
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_warm_company_id ON funnel.warm_universe(company_id);
CREATE INDEX idx_warm_person_id ON funnel.warm_universe(person_id);
CREATE INDEX idx_warm_suspect_id ON funnel.warm_universe(suspect_id);

-- Warm reason index
CREATE INDEX idx_warm_reason ON funnel.warm_universe(warm_reason);
CREATE INDEX idx_warm_score ON funnel.warm_universe(warm_score);

-- Time-based indexes
CREATE INDEX idx_warm_first_ts ON funnel.warm_universe(first_warm_ts);
CREATE INDEX idx_warm_last_engagement ON funnel.warm_universe(last_engagement_ts);
CREATE INDEX idx_warm_created_at ON funnel.warm_universe(created_at);

-- Composite indexes
CREATE INDEX idx_warm_company_reason ON funnel.warm_universe(company_id, warm_reason);
CREATE INDEX idx_warm_active_company ON funnel.warm_universe(is_active, company_id);

-- Status indexes
CREATE INDEX idx_warm_active ON funnel.warm_universe(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_warm_talentflow ON funnel.warm_universe(has_talentflow_signal)
    WHERE has_talentflow_signal = TRUE;
CREATE INDEX idx_warm_demoted ON funnel.warm_universe(demoted_to_reengagement)
    WHERE demoted_to_reengagement = TRUE;
CREATE INDEX idx_warm_promoted ON funnel.warm_universe(promoted_to_appointment)
    WHERE promoted_to_appointment = TRUE;

-- Nurture sequence tracking
CREATE INDEX idx_warm_nurture_sequence ON funnel.warm_universe(nurture_sequence_id)
    WHERE nurture_sequence_id IS NOT NULL;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER trg_warm_updated_at
    BEFORE UPDATE ON funnel.warm_universe
    FOR EACH ROW
    EXECUTE FUNCTION funnel.update_suspect_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.warm_universe IS 'Funnel 3: Warm Universe - Contacts with demonstrated engagement';
COMMENT ON COLUMN funnel.warm_universe.warm_id IS 'Primary key - unique identifier for warm entry';
COMMENT ON COLUMN funnel.warm_universe.warm_reason IS 'How contact qualified for warm status';
COMMENT ON COLUMN funnel.warm_universe.warm_score IS 'Engagement score at time of promotion to warm';
COMMENT ON COLUMN funnel.warm_universe.first_warm_ts IS 'When contact first achieved warm status';
COMMENT ON COLUMN funnel.warm_universe.has_talentflow_signal IS 'Whether contact also has TalentFlow signal (dual qualification)';
COMMENT ON COLUMN funnel.warm_universe.nurture_sequence_id IS 'Current nurture sequence assignment';
