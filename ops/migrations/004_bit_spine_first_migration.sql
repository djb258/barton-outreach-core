-- ============================================================================
-- Migration: 004_bit_spine_first_migration.sql
-- Purpose: Migrate BIT Engine to Spine-First Architecture
-- Date: 2026-01-08
-- Doctrine: Spine-First Architecture v1.1
-- ============================================================================
--
-- This migration:
-- 1. Creates outreach.bit_signals (signals FK to outreach_id)
-- 2. Creates outreach.bit_scores (company scores FK to outreach_id)
-- 3. Deprecates legacy bit.* tables (left in place for reference)
--
-- DOCTRINE: All sub-hub tables FK to outreach_id. sovereign_id is HIDDEN.
--
-- ============================================================================

-- ============================================================================
-- 1. CREATE outreach.bit_signals TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach.bit_signals (
    -- Primary Key
    signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine Anchor (DOCTRINE: FK to outreach_id, NOT sovereign_id)
    outreach_id UUID NOT NULL REFERENCES outreach.outreach(outreach_id),

    -- Signal Classification
    signal_type VARCHAR(50) NOT NULL,
    signal_impact NUMERIC(5,2) NOT NULL,
    source_spoke VARCHAR(50) NOT NULL,

    -- Traceability (DOCTRINE: correlation_id REQUIRED)
    correlation_id UUID NOT NULL,
    process_id UUID,

    -- Signal Metadata
    signal_metadata JSONB,

    -- Decay Model
    decay_period_days INTEGER NOT NULL DEFAULT 90,
    decayed_impact NUMERIC(5,2),

    -- Timestamps
    signal_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for bit_signals
CREATE INDEX IF NOT EXISTS idx_bit_signals_outreach_id ON outreach.bit_signals(outreach_id);
CREATE INDEX IF NOT EXISTS idx_bit_signals_type ON outreach.bit_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_bit_signals_source ON outreach.bit_signals(source_spoke);
CREATE INDEX IF NOT EXISTS idx_bit_signals_correlation ON outreach.bit_signals(correlation_id);
CREATE INDEX IF NOT EXISTS idx_bit_signals_timestamp ON outreach.bit_signals(signal_timestamp DESC);

-- Comments
COMMENT ON TABLE outreach.bit_signals IS 'BIT Engine signals - Spine-First Architecture v1.1';
COMMENT ON COLUMN outreach.bit_signals.outreach_id IS 'FK to spine - DOCTRINE: sub-hubs FK to outreach_id only';
COMMENT ON COLUMN outreach.bit_signals.correlation_id IS 'DOCTRINE: Required for traceability';
COMMENT ON COLUMN outreach.bit_signals.decay_period_days IS 'Days until signal fully decays (90/180/365)';


-- ============================================================================
-- 2. CREATE outreach.bit_scores TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach.bit_scores (
    -- Primary Key (outreach_id is unique per company)
    outreach_id UUID PRIMARY KEY REFERENCES outreach.outreach(outreach_id),

    -- Score Fields
    score NUMERIC(5,2) NOT NULL DEFAULT 0,
    score_tier VARCHAR(10) NOT NULL DEFAULT 'COLD',
    signal_count INTEGER NOT NULL DEFAULT 0,

    -- Score Breakdown by Source
    people_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    dol_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    blog_score NUMERIC(5,2) NOT NULL DEFAULT 0,
    talent_flow_score NUMERIC(5,2) NOT NULL DEFAULT 0,

    -- Timestamps
    last_signal_at TIMESTAMPTZ,
    last_scored_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: Valid tier values
    CONSTRAINT chk_score_tier CHECK (score_tier IN ('COLD', 'WARM', 'HOT', 'BURNING'))
);

-- Indexes for bit_scores
CREATE INDEX IF NOT EXISTS idx_bit_scores_tier ON outreach.bit_scores(score_tier);
CREATE INDEX IF NOT EXISTS idx_bit_scores_score ON outreach.bit_scores(score DESC);
CREATE INDEX IF NOT EXISTS idx_bit_scores_last_signal ON outreach.bit_scores(last_signal_at DESC);

-- Comments
COMMENT ON TABLE outreach.bit_scores IS 'BIT Engine company scores - Spine-First Architecture v1.1';
COMMENT ON COLUMN outreach.bit_scores.outreach_id IS 'PK and FK to spine - one score per company';
COMMENT ON COLUMN outreach.bit_scores.score_tier IS 'COLD (0-24), WARM (25-49), HOT (50-74), BURNING (75+)';


-- ============================================================================
-- 3. CREATE outreach.bit_errors TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS outreach.bit_errors (
    -- Primary Key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Spine Anchor
    outreach_id UUID REFERENCES outreach.outreach(outreach_id),

    -- Error Classification
    pipeline_stage VARCHAR(20) NOT NULL,
    failure_code VARCHAR(30) NOT NULL,
    blocking_reason TEXT NOT NULL,
    severity VARCHAR(10) NOT NULL DEFAULT 'ERROR',

    -- Terminal Failure Doctrine
    retry_allowed BOOLEAN NOT NULL DEFAULT FALSE,

    -- Traceability
    correlation_id UUID,
    process_id UUID,

    -- Debug Info
    raw_input JSONB,
    stack_trace TEXT,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: Valid severity
    CONSTRAINT chk_bit_error_severity CHECK (severity IN ('INFO', 'WARN', 'ERROR', 'FATAL'))
);

-- Indexes for bit_errors
CREATE INDEX IF NOT EXISTS idx_bit_errors_outreach_id ON outreach.bit_errors(outreach_id);
CREATE INDEX IF NOT EXISTS idx_bit_errors_code ON outreach.bit_errors(failure_code);
CREATE INDEX IF NOT EXISTS idx_bit_errors_stage ON outreach.bit_errors(pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_bit_errors_created ON outreach.bit_errors(created_at DESC);

-- Comments
COMMENT ON TABLE outreach.bit_errors IS 'BIT Engine errors - Terminal Failure Doctrine';
COMMENT ON COLUMN outreach.bit_errors.retry_allowed IS 'DOCTRINE: Always FALSE - errors are terminal';


-- ============================================================================
-- 4. CREATE VIEWS
-- ============================================================================

-- View: Hot companies ready for outreach
CREATE OR REPLACE VIEW outreach.v_bit_hot_companies AS
SELECT
    bs.outreach_id,
    o.domain,
    bs.score,
    bs.score_tier,
    bs.signal_count,
    bs.people_score,
    bs.dol_score,
    bs.blog_score,
    bs.talent_flow_score,
    bs.last_signal_at,
    bs.last_scored_at
FROM outreach.bit_scores bs
JOIN outreach.outreach o ON bs.outreach_id = o.outreach_id
WHERE bs.score >= 50
ORDER BY bs.score DESC;

COMMENT ON VIEW outreach.v_bit_hot_companies IS 'Companies with BIT score >= 50 (HOT or BURNING)';


-- View: Recent signals
CREATE OR REPLACE VIEW outreach.v_bit_recent_signals AS
SELECT
    s.signal_id,
    s.outreach_id,
    o.domain,
    s.signal_type,
    s.signal_impact,
    s.source_spoke,
    s.signal_timestamp,
    s.decay_period_days,
    -- Calculate current decayed impact
    GREATEST(0, s.signal_impact * (1 - EXTRACT(EPOCH FROM (NOW() - s.signal_timestamp)) / (s.decay_period_days * 86400))) AS current_impact
FROM outreach.bit_signals s
JOIN outreach.outreach o ON s.outreach_id = o.outreach_id
WHERE s.signal_timestamp > NOW() - INTERVAL '90 days'
ORDER BY s.signal_timestamp DESC;

COMMENT ON VIEW outreach.v_bit_recent_signals IS 'Signals from last 90 days with current decayed impact';


-- View: Score distribution by tier
CREATE OR REPLACE VIEW outreach.v_bit_tier_distribution AS
SELECT
    score_tier,
    COUNT(*) as company_count,
    AVG(score) as avg_score,
    MAX(score) as max_score,
    AVG(signal_count) as avg_signals
FROM outreach.bit_scores
GROUP BY score_tier
ORDER BY
    CASE score_tier
        WHEN 'BURNING' THEN 1
        WHEN 'HOT' THEN 2
        WHEN 'WARM' THEN 3
        WHEN 'COLD' THEN 4
    END;

COMMENT ON VIEW outreach.v_bit_tier_distribution IS 'Company distribution by BIT tier';


-- ============================================================================
-- 5. DEPRECATION NOTICE FOR LEGACY TABLES
-- ============================================================================

-- Add deprecation comments to legacy tables (do not drop)
DO $$
BEGIN
    -- Check if bit schema exists before commenting
    IF EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'bit') THEN
        COMMENT ON SCHEMA bit IS 'DEPRECATED: Use outreach.bit_* tables instead (Spine-First Migration 2026-01-08)';

        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'bit' AND table_name = 'bit_company_score') THEN
            COMMENT ON TABLE bit.bit_company_score IS 'DEPRECATED: Use outreach.bit_scores instead';
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'bit' AND table_name = 'bit_signal') THEN
            COMMENT ON TABLE bit.bit_signal IS 'DEPRECATED: Use outreach.bit_signals instead';
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'bit' AND table_name = 'bit_contact_score') THEN
            COMMENT ON TABLE bit.bit_contact_score IS 'DEPRECATED: Use outreach.bit_scores instead (contact scores moved to people sub-hub)';
        END IF;
    END IF;
END $$;


-- ============================================================================
-- 6. AUDIT LOG ENTRY
-- ============================================================================

INSERT INTO shq.audit_log (event_type, event_source, details, created_at)
VALUES (
    'schema_migration',
    'bit_spine_first',
    '{
        "migration": "004_bit_spine_first_migration",
        "doctrine": "Spine-First Architecture v1.1",
        "tables_created": ["outreach.bit_signals", "outreach.bit_scores", "outreach.bit_errors"],
        "views_created": ["outreach.v_bit_hot_companies", "outreach.v_bit_recent_signals", "outreach.v_bit_tier_distribution"],
        "deprecated": ["bit.bit_company_score", "bit.bit_signal", "bit.bit_contact_score"],
        "key_change": "BIT now FKs to outreach_id instead of company_unique_id"
    }'::jsonb,
    NOW()
);


-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
