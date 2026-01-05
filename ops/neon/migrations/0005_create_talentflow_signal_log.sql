-- ============================================================================
-- Migration: 0005_create_talentflow_signal_log.sql
-- Description: Create talentflow_signal_log table (Funnel 2: TalentFlow Universe)
-- Version: 1.0.0
-- Created: 2025-12-05
-- ============================================================================

-- ============================================================================
-- TABLE: talentflow_signal_log
-- Purpose: Log of all TalentFlow movement signals (job changes, promotions, etc.)
-- Funnel: Funnel 2 - TalentFlow Universe qualification source
-- ============================================================================

CREATE TABLE IF NOT EXISTS funnel.talentflow_signal_log (
    -- Primary key
    signal_id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys
    company_id              UUID NOT NULL,
    person_id               UUID NOT NULL,
    suspect_id              UUID REFERENCES funnel.suspect_universe(suspect_id),

    -- Signal classification
    signal_type             funnel.talentflow_signal_type NOT NULL,

    -- Movement details
    old_company_id          UUID,
    old_company_name        VARCHAR(255),
    old_title               VARCHAR(255),
    new_company_id          UUID,
    new_company_name        VARCHAR(255),
    new_title               VARCHAR(255),

    -- Change tracking (generic old/new for flexible signal types)
    old_value               TEXT,
    new_value               TEXT,

    -- Signal timestamp
    signal_ts               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    movement_detected_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Signal freshness (days since movement)
    signal_age_days         INTEGER GENERATED ALWAYS AS (
        EXTRACT(DAY FROM (NOW() - signal_ts))::INTEGER
    ) STORED,

    -- Verification status
    is_verified             BOOLEAN NOT NULL DEFAULT FALSE,
    verified_at             TIMESTAMPTZ,
    verification_source     VARCHAR(100),  -- 'linkedin', 'manual', 'crm'
    verification_confidence DECIMAL(3,2),  -- 0.00 to 1.00

    -- Processing status
    is_processed            BOOLEAN NOT NULL DEFAULT FALSE,
    processed_at            TIMESTAMPTZ,
    triggered_state_change  BOOLEAN NOT NULL DEFAULT FALSE,

    -- Signal priority
    priority_score          INTEGER NOT NULL DEFAULT 50,  -- 0-100, higher = more priority

    -- Signal expiration (90 days per doctrine)
    is_expired              BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at              TIMESTAMPTZ,

    -- Source tracking
    source_system           VARCHAR(100),
    source_record_id        VARCHAR(255),

    -- Metadata
    metadata                JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT chk_signal_age CHECK (signal_age_days >= 0 OR signal_age_days IS NULL),
    CONSTRAINT chk_priority CHECK (priority_score >= 0 AND priority_score <= 100),
    CONSTRAINT chk_confidence CHECK (verification_confidence IS NULL OR (verification_confidence >= 0 AND verification_confidence <= 1))
);

-- ============================================================================
-- INDEXES (Aggressive indexing as specified)
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX idx_talentflow_company_id ON funnel.talentflow_signal_log(company_id);
CREATE INDEX idx_talentflow_person_id ON funnel.talentflow_signal_log(person_id);
CREATE INDEX idx_talentflow_suspect_id ON funnel.talentflow_signal_log(suspect_id);

-- Signal type index
CREATE INDEX idx_talentflow_signal_type ON funnel.talentflow_signal_log(signal_type);

-- Time-based indexes
CREATE INDEX idx_talentflow_signal_ts ON funnel.talentflow_signal_log(signal_ts);
CREATE INDEX idx_talentflow_detected_at ON funnel.talentflow_signal_log(movement_detected_at);
CREATE INDEX idx_talentflow_created_at ON funnel.talentflow_signal_log(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_talentflow_person_type ON funnel.talentflow_signal_log(person_id, signal_type);
CREATE INDEX idx_talentflow_company_type ON funnel.talentflow_signal_log(company_id, signal_type);
CREATE INDEX idx_talentflow_type_ts ON funnel.talentflow_signal_log(signal_type, signal_ts);

-- Processing status indexes
CREATE INDEX idx_talentflow_unprocessed ON funnel.talentflow_signal_log(is_processed, signal_ts)
    WHERE is_processed = FALSE;
CREATE INDEX idx_talentflow_unverified ON funnel.talentflow_signal_log(is_verified)
    WHERE is_verified = FALSE;
CREATE INDEX idx_talentflow_triggered ON funnel.talentflow_signal_log(triggered_state_change)
    WHERE triggered_state_change = TRUE;

-- Freshness indexes (for 90-day window queries)
CREATE INDEX idx_talentflow_age ON funnel.talentflow_signal_log(signal_age_days);
CREATE INDEX idx_talentflow_fresh ON funnel.talentflow_signal_log(signal_ts)
    WHERE signal_ts > NOW() - INTERVAL '90 days';
CREATE INDEX idx_talentflow_expired ON funnel.talentflow_signal_log(is_expired)
    WHERE is_expired = FALSE;

-- Priority index
CREATE INDEX idx_talentflow_priority ON funnel.talentflow_signal_log(priority_score DESC);

-- Company change tracking
CREATE INDEX idx_talentflow_old_company ON funnel.talentflow_signal_log(old_company_id)
    WHERE old_company_id IS NOT NULL;
CREATE INDEX idx_talentflow_new_company ON funnel.talentflow_signal_log(new_company_id)
    WHERE new_company_id IS NOT NULL;

-- JSONB metadata index
CREATE INDEX idx_talentflow_metadata ON funnel.talentflow_signal_log USING GIN (metadata);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE TRIGGER trg_talentflow_updated_at
    BEFORE UPDATE ON funnel.talentflow_signal_log
    FOR EACH ROW
    EXECUTE FUNCTION funnel.update_suspect_timestamp();

-- Auto-set expiration date
CREATE OR REPLACE FUNCTION funnel.set_talentflow_expiration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_at IS NULL THEN
        NEW.expires_at = NEW.signal_ts + INTERVAL '90 days';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_talentflow_expiration
    BEFORE INSERT ON funnel.talentflow_signal_log
    FOR EACH ROW
    EXECUTE FUNCTION funnel.set_talentflow_expiration();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE funnel.talentflow_signal_log IS 'TalentFlow movement signal log. Tracks job changes, promotions, and role movements.';
COMMENT ON COLUMN funnel.talentflow_signal_log.signal_id IS 'Primary key - unique identifier for each signal';
COMMENT ON COLUMN funnel.talentflow_signal_log.signal_type IS 'Type of movement (job_change, promotion, lateral, startup)';
COMMENT ON COLUMN funnel.talentflow_signal_log.signal_ts IS 'When the movement occurred (not when detected)';
COMMENT ON COLUMN funnel.talentflow_signal_log.signal_age_days IS 'Computed: days since movement (auto-updated)';
COMMENT ON COLUMN funnel.talentflow_signal_log.is_verified IS 'Whether signal has been verified against source';
COMMENT ON COLUMN funnel.talentflow_signal_log.priority_score IS 'Signal priority (0-100, higher = more priority)';
COMMENT ON COLUMN funnel.talentflow_signal_log.expires_at IS 'Signal expires 90 days after movement per doctrine';
