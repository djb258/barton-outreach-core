-- ============================================================================
-- Migration: 0006_create_bit_signal_log.sql
-- Description: Create bit_signal_log table (BIT - Buyer Intent Tool signals)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- TABLE: bit_signal_log
-- Purpose: Log of all BIT (Buyer Intent Tool) score changes and signals
-- Usage: Track intent signals and score calculations for state transitions
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.bit_signal_log (
    -- Primary key
    bit_log_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- BIT score data
    bit_score               INTEGER NOT NULL,
    previous_score          INTEGER,
    score_delta             INTEGER GENERATED ALWAYS AS (bit_score - COALESCE(previous_score, 0)) STORED,

    -- Score components (for debugging/analysis)
    open_points             INTEGER NOT NULL DEFAULT 0,
    click_points            INTEGER NOT NULL DEFAULT 0,
    reply_points            INTEGER NOT NULL DEFAULT 0,
    website_points          INTEGER NOT NULL DEFAULT 0,
    content_points          INTEGER NOT NULL DEFAULT 0,
    webinar_points          INTEGER NOT NULL DEFAULT 0,
    talentflow_points       INTEGER NOT NULL DEFAULT 0,
    recency_decay           INTEGER NOT NULL DEFAULT 0,

    -- Threshold tracking
    crossed_warm_threshold  BOOLEAN NOT NULL DEFAULT FALSE,
    crossed_hot_threshold   BOOLEAN NOT NULL DEFAULT FALSE,
    crossed_priority_threshold BOOLEAN NOT NULL DEFAULT FALSE,

    -- Reason for score change
    bit_reason              VARCHAR(255) NOT NULL,  -- e.g., 'email_open', 'daily_decay', 'reply_received'
    triggering_event_id     UUID REFERENCES funnel.engagement_events(event_id),

    -- Detection timestamp
    detected_ts             TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Processing
    triggered_state_change  BOOLEAN NOT NULL DEFAULT FALSE,
    new_state               funnel.lifecycle_state,

    -- Metadata
    calculation_details     JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_bit_score CHECK (bit_score >= 0),
    CONSTRAINT chk_threshold_order CHECK (
        (crossed_priority_threshold = FALSE OR crossed_hot_threshold = TRUE) AND
        (crossed_hot_threshold = FALSE OR crossed_warm_threshold = TRUE)
    )
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_bit_company_id ON funnel.bit_signal_log(company_id);
CREATE INDEX idx_bit_person_id ON funnel.bit_signal_log(person_id);
CREATE INDEX idx_bit_suspect_id ON funnel.bit_signal_log(suspect_id);

-- Score indexes
CREATE INDEX idx_bit_score ON funnel.bit_signal_log(bit_score);
CREATE INDEX idx_bit_score_delta ON funnel.bit_signal_log(score_delta);

-- Reason index
CREATE INDEX idx_bit_reason ON funnel.bit_signal_log(bit_reason);

-- Time-based indexes
CREATE INDEX idx_bit_detected_ts ON funnel.bit_signal_log(detected_ts);
CREATE INDEX idx_bit_created_at ON funnel.bit_signal_log(created_at);

-- Composite indexes
CREATE INDEX idx_bit_person_ts ON funnel.bit_signal_log(person_id, detected_ts);
CREATE INDEX idx_bit_company_ts ON funnel.bit_signal_log(company_id, detected_ts);
CREATE INDEX idx_bit_person_score ON funnel.bit_signal_log(person_id, bit_score);

-- Threshold crossing indexes
CREATE INDEX idx_bit_warm_crossed ON funnel.bit_signal_log(crossed_warm_threshold)
    WHERE crossed_warm_threshold = TRUE;
CREATE INDEX idx_bit_hot_crossed ON funnel.bit_signal_log(crossed_hot_threshold)
    WHERE crossed_hot_threshold = TRUE;
CREATE INDEX idx_bit_priority_crossed ON funnel.bit_signal_log(crossed_priority_threshold)
    WHERE crossed_priority_threshold = TRUE;

-- State change tracking
CREATE INDEX idx_bit_triggered ON funnel.bit_signal_log(triggered_state_change)
    WHERE triggered_state_change = TRUE;

-- Event linkage
CREATE INDEX idx_bit_event ON funnel.bit_signal_log(triggering_event_id)
    WHERE triggering_event_id IS NOT NULL;

-- JSONB index for calculation details
CREATE INDEX idx_bit_calculation ON funnel.bit_signal_log USING GIN (calculation_details);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Current BIT score per person (latest entry)
CREATE OR REPLACE VIEW funnel.v_current_bit_scores AS
SELECT DISTINCT ON (person_id)
    person_id,
    company_id,
    suspect_id,
    bit_score,
    bit_reason,
    detected_ts,
    crossed_warm_threshold,
    crossed_hot_threshold,
    crossed_priority_threshold
FROM funnel.bit_signal_log
ORDER BY person_id, detected_ts DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.bit_signal_log IS 'BIT (Buyer Intent Tool) signal log. Tracks intent scores and threshold crossings.';
COMMENT ON COLUMN funnel.bit_signal_log.bit_log_id IS 'Primary key - unique identifier for each BIT log entry';
COMMENT ON COLUMN funnel.bit_signal_log.bit_score IS 'Current BIT score after this event';
COMMENT ON COLUMN funnel.bit_signal_log.previous_score IS 'BIT score before this event';
COMMENT ON COLUMN funnel.bit_signal_log.score_delta IS 'Computed: change in score from previous';
COMMENT ON COLUMN funnel.bit_signal_log.bit_reason IS 'What triggered this score calculation';
COMMENT ON COLUMN funnel.bit_signal_log.recency_decay IS 'Points lost due to recency decay (-1/day, max 30)';
COMMENT ON COLUMN funnel.bit_signal_log.crossed_warm_threshold IS 'TRUE if this event crossed WARM threshold (25)';
COMMENT ON COLUMN funnel.bit_signal_log.crossed_hot_threshold IS 'TRUE if this event crossed HOT threshold (50)';
COMMENT ON COLUMN funnel.bit_signal_log.crossed_priority_threshold IS 'TRUE if this event crossed PRIORITY threshold (75)';
COMMENT ON VIEW funnel.v_current_bit_scores IS 'Current BIT score for each person (latest entry)';
