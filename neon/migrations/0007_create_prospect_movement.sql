-- ============================================================================
-- Migration: 0007_create_prospect_movement.sql
-- Description: Create prospect_movement table (State transition audit log)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- TABLE: prospect_movement
-- Purpose: Immutable audit log of all state transitions in the funnel system
-- Usage: Track every movement between lifecycle states for analysis and debugging
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.prospect_movement (
    -- Primary key
    movement_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- State transition
    from_state              funnel.lifecycle_state NOT NULL,
    to_state                funnel.lifecycle_state NOT NULL,
    from_funnel             funnel.funnel_membership,
    to_funnel               funnel.funnel_membership,

    -- Triggering event
    event_type              funnel.event_type NOT NULL,
    triggering_event_id     UUID,  -- Reference to source event (engagement, talentflow, bit, etc.)
    triggering_event_table  VARCHAR(100),  -- Which table the event came from

    -- Transition timestamps
    event_ts                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    transition_processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Validation tracking
    validation_passed       BOOLEAN NOT NULL DEFAULT TRUE,
    validation_checks       JSONB NOT NULL DEFAULT '[]',  -- Array of checks performed

    -- Cooldown tracking
    was_in_cooldown         BOOLEAN NOT NULL DEFAULT FALSE,
    cooldown_bypassed       BOOLEAN NOT NULL DEFAULT FALSE,
    cooldown_bypass_reason  VARCHAR(255),

    -- Manual override tracking
    is_manual_override      BOOLEAN NOT NULL DEFAULT FALSE,
    override_user_id        VARCHAR(100),
    override_reason         TEXT,

    -- Sequence impact
    old_sequence_id         VARCHAR(100),
    new_sequence_id         VARCHAR(100),

    -- Metadata
    metadata                JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_state_change CHECK (from_state != to_state),
    CONSTRAINT chk_manual_override CHECK (
        (is_manual_override = FALSE) OR
        (is_manual_override = TRUE AND override_reason IS NOT NULL)
    )
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_movement_company_id ON funnel.prospect_movement(company_id);
CREATE INDEX idx_movement_person_id ON funnel.prospect_movement(person_id);
CREATE INDEX idx_movement_suspect_id ON funnel.prospect_movement(suspect_id);

-- State indexes
CREATE INDEX idx_movement_from_state ON funnel.prospect_movement(from_state);
CREATE INDEX idx_movement_to_state ON funnel.prospect_movement(to_state);
CREATE INDEX idx_movement_states ON funnel.prospect_movement(from_state, to_state);

-- Funnel indexes
CREATE INDEX idx_movement_from_funnel ON funnel.prospect_movement(from_funnel);
CREATE INDEX idx_movement_to_funnel ON funnel.prospect_movement(to_funnel);

-- Event type index
CREATE INDEX idx_movement_event_type ON funnel.prospect_movement(event_type);

-- Time-based indexes
CREATE INDEX idx_movement_event_ts ON funnel.prospect_movement(event_ts);
CREATE INDEX idx_movement_created_at ON funnel.prospect_movement(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_movement_person_ts ON funnel.prospect_movement(person_id, event_ts);
CREATE INDEX idx_movement_company_ts ON funnel.prospect_movement(company_id, event_ts);
CREATE INDEX idx_movement_type_ts ON funnel.prospect_movement(event_type, event_ts);
CREATE INDEX idx_movement_person_states ON funnel.prospect_movement(person_id, from_state, to_state);

-- Analysis indexes
CREATE INDEX idx_movement_validation ON funnel.prospect_movement(validation_passed)
    WHERE validation_passed = FALSE;
CREATE INDEX idx_movement_manual ON funnel.prospect_movement(is_manual_override)
    WHERE is_manual_override = TRUE;
CREATE INDEX idx_movement_cooldown_bypass ON funnel.prospect_movement(cooldown_bypassed)
    WHERE cooldown_bypassed = TRUE;

-- Triggering event tracking
CREATE INDEX idx_movement_trigger_event ON funnel.prospect_movement(triggering_event_id)
    WHERE triggering_event_id IS NOT NULL;
CREATE INDEX idx_movement_trigger_table ON funnel.prospect_movement(triggering_event_table);

-- JSONB indexes
CREATE INDEX idx_movement_metadata ON funnel.prospect_movement USING GIN (metadata);
CREATE INDEX idx_movement_validation_checks ON funnel.prospect_movement USING GIN (validation_checks);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Recent movements (last 7 days)
CREATE OR REPLACE VIEW funnel.v_recent_movements AS
SELECT
    movement_id,
    person_id,
    company_id,
    from_state,
    to_state,
    event_type,
    event_ts,
    is_manual_override,
    validation_passed
FROM funnel.prospect_movement
WHERE event_ts > NOW() - INTERVAL '7 days'
ORDER BY event_ts DESC;

-- Movement summary by state transition
CREATE OR REPLACE VIEW funnel.v_movement_summary AS
SELECT
    from_state,
    to_state,
    event_type,
    COUNT(*) as movement_count,
    COUNT(*) FILTER (WHERE is_manual_override = TRUE) as manual_count,
    COUNT(*) FILTER (WHERE validation_passed = FALSE) as failed_validation_count,
    MIN(event_ts) as first_occurrence,
    MAX(event_ts) as last_occurrence
FROM funnel.prospect_movement
GROUP BY from_state, to_state, event_type
ORDER BY movement_count DESC;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.prospect_movement IS 'Immutable audit log of all state transitions. Every movement between states is recorded here.';
COMMENT ON COLUMN funnel.prospect_movement.movement_id IS 'Primary key - unique identifier for each movement';
COMMENT ON COLUMN funnel.prospect_movement.from_state IS 'State before transition';
COMMENT ON COLUMN funnel.prospect_movement.to_state IS 'State after transition';
COMMENT ON COLUMN funnel.prospect_movement.event_type IS 'Event that triggered this transition';
COMMENT ON COLUMN funnel.prospect_movement.triggering_event_id IS 'FK to source event (in engagement_events, talentflow_signal_log, etc.)';
COMMENT ON COLUMN funnel.prospect_movement.validation_checks IS 'JSON array of validation checks performed before transition';
COMMENT ON COLUMN funnel.prospect_movement.is_manual_override IS 'TRUE if this was a manual admin override';
COMMENT ON COLUMN funnel.prospect_movement.override_reason IS 'Required explanation for manual overrides';
COMMENT ON VIEW funnel.v_recent_movements IS 'State transitions from the last 7 days';
COMMENT ON VIEW funnel.v_movement_summary IS 'Aggregate summary of movements by state transition type';
