-- ============================================================================
-- Migration: 0002_create_suspect_universe.sql
-- Description: Create suspect_universe table (Funnel 1: Cold Universe)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- TABLE: suspect_universe
-- Purpose: Primary table tracking all contacts and their current lifecycle state
-- Funnel: Entry point for all contacts (Funnel 1: Cold Universe by default)
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.suspect_universe (
    -- Primary key
    suspect_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys to existing tables
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,

    -- Contact identifiers
    email                   VARCHAR(255) NOT NULL,

    -- Lifecycle state management
    funnel_state            funnel.lifecycle_state NOT NULL DEFAULT 'SUSPECT',
    funnel_membership       funnel.funnel_membership NOT NULL DEFAULT 'COLD_UNIVERSE',

    -- State tracking timestamps
    last_event_ts           TIMESTAMPTZ,
    last_state_change_ts    TIMESTAMPTZ,
    entered_suspect_ts      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Engagement counters (for threshold tracking)
    email_open_count        INTEGER NOT NULL DEFAULT 0,
    email_click_count       INTEGER NOT NULL DEFAULT 0,
    email_reply_count       INTEGER NOT NULL DEFAULT 0,

    -- BIT score tracking
    current_bit_score       INTEGER NOT NULL DEFAULT 0,

    -- Re-engagement tracking
    reengagement_cycle      INTEGER NOT NULL DEFAULT 0,
    last_reengagement_ts    TIMESTAMPTZ,

    -- State lock (prevents transitions during processing)
    is_locked               BOOLEAN NOT NULL DEFAULT FALSE,
    lock_reason             VARCHAR(255),
    locked_at               TIMESTAMPTZ,

    -- Cooldown tracking (anti-thrashing)
    cooldown_until          TIMESTAMPTZ,

    -- Suppression flags
    is_bounced              BOOLEAN NOT NULL DEFAULT FALSE,
    is_unsubscribed         BOOLEAN NOT NULL DEFAULT FALSE,
    is_disqualified         BOOLEAN NOT NULL DEFAULT FALSE,

    -- Metadata
    source                  VARCHAR(100),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT uq_suspect_person UNIQUE (person_id),
    CONSTRAINT uq_suspect_email UNIQUE (email),
    CONSTRAINT chk_reengagement_cycle CHECK (reengagement_cycle >= 0 AND reengagement_cycle <= 5),
    CONSTRAINT chk_bit_score CHECK (current_bit_score >= 0)
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_suspect_company_id ON funnel.suspect_universe(company_id);
CREATE INDEX idx_suspect_person_id ON funnel.suspect_universe(person_id);
CREATE INDEX idx_suspect_email ON funnel.suspect_universe(email);

-- State-based indexes
CREATE INDEX idx_suspect_funnel_state ON funnel.suspect_universe(funnel_state);
CREATE INDEX idx_suspect_funnel_membership ON funnel.suspect_universe(funnel_membership);

-- Composite indexes for common queries
CREATE INDEX idx_suspect_state_company ON funnel.suspect_universe(funnel_state, company_id);
CREATE INDEX idx_suspect_state_last_event ON funnel.suspect_universe(funnel_state, last_event_ts);
CREATE INDEX idx_suspect_membership_state ON funnel.suspect_universe(funnel_membership, funnel_state);

-- Time-based indexes
CREATE INDEX idx_suspect_last_event_ts ON funnel.suspect_universe(last_event_ts);
CREATE INDEX idx_suspect_last_state_change ON funnel.suspect_universe(last_state_change_ts);
CREATE INDEX idx_suspect_created_at ON funnel.suspect_universe(created_at);

-- Processing indexes
CREATE INDEX idx_suspect_is_locked ON funnel.suspect_universe(is_locked) WHERE is_locked = TRUE;
CREATE INDEX idx_suspect_cooldown ON funnel.suspect_universe(cooldown_until) WHERE cooldown_until IS NOT NULL;
CREATE INDEX idx_suspect_reengagement ON funnel.suspect_universe(reengagement_cycle, last_reengagement_ts)
    WHERE funnel_state = 'REENGAGEMENT';

-- Suppression indexes
CREATE INDEX idx_suspect_active ON funnel.suspect_universe(funnel_state)
    WHERE is_bounced = FALSE AND is_unsubscribed = FALSE AND is_disqualified = FALSE;

-- BIT score index for threshold queries
CREATE INDEX idx_suspect_bit_score ON funnel.suspect_universe(current_bit_score);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION funnel.update_suspect_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_suspect_updated_at
    BEFORE UPDATE ON funnel.suspect_universe
    FOR EACH ROW
    EXECUTE FUNCTION funnel.update_suspect_timestamp();

-- Track state changes
CREATE OR REPLACE FUNCTION funnel.track_state_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.funnel_state IS DISTINCT FROM NEW.funnel_state THEN
        NEW.last_state_change_ts = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_suspect_state_change
    BEFORE UPDATE ON funnel.suspect_universe
    FOR EACH ROW
    EXECUTE FUNCTION funnel.track_state_change();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.suspect_universe IS 'Primary contact lifecycle table for 4-Funnel GTM System. All contacts start here as SUSPECT.';
COMMENT ON COLUMN funnel.suspect_universe.suspect_id IS 'Primary key - unique identifier for each contact entry';
COMMENT ON COLUMN funnel.suspect_universe.company_id IS 'FK to company.company_master';
COMMENT ON COLUMN funnel.suspect_universe.person_id IS 'FK to people.people_master';
COMMENT ON COLUMN funnel.suspect_universe.funnel_state IS 'Current lifecycle state (SUSPECT, WARM, TALENTFLOW_WARM, etc.)';
COMMENT ON COLUMN funnel.suspect_universe.funnel_membership IS 'Current funnel universe membership';
COMMENT ON COLUMN funnel.suspect_universe.last_event_ts IS 'Timestamp of most recent engagement event';
COMMENT ON COLUMN funnel.suspect_universe.reengagement_cycle IS 'Number of re-engagement attempts (max 3)';
COMMENT ON COLUMN funnel.suspect_universe.is_locked IS 'Prevents state transitions during processing';
COMMENT ON COLUMN funnel.suspect_universe.cooldown_until IS 'Prevents state changes until this timestamp (anti-thrashing)';
