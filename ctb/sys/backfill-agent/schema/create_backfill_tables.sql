-- Backfill Agent Database Tables
-- Barton Doctrine ID: 04.04.02.04.80000.###
-- Purpose: Historical data import, matching, and baseline generation

-- ==============================================================
-- Table: backfill_log
-- Purpose: Track all backfill operations and match results
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.backfill_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_row_hash TEXT NOT NULL,
    source_data JSONB NOT NULL,
    match_type TEXT CHECK (match_type IN ('perfect_company', 'perfect_person', 'fuzzy_company', 'fuzzy_person', 'no_match')),
    match_confidence NUMERIC(5,3) CHECK (match_confidence >= 0 AND match_confidence <= 1),
    matched_company_id TEXT,
    matched_person_id TEXT,
    resolution_status TEXT NOT NULL CHECK (resolution_status IN ('initialized', 'unresolved', 'duplicate', 'error', 'skipped_locked')),
    actions_taken JSONB,
    error_message TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    worker_id TEXT,
    process_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_backfill_log_hash ON marketing.backfill_log(source_row_hash);
CREATE INDEX IF NOT EXISTS idx_backfill_log_status ON marketing.backfill_log(resolution_status);
CREATE INDEX IF NOT EXISTS idx_backfill_log_match_type ON marketing.backfill_log(match_type);
CREATE INDEX IF NOT EXISTS idx_backfill_log_created ON marketing.backfill_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_backfill_log_worker ON marketing.backfill_log(worker_id);

COMMENT ON TABLE marketing.backfill_log IS 'Audit trail for backfill operations and matching results';
COMMENT ON COLUMN marketing.backfill_log.source_row_hash IS 'MD5 hash of source CSV row for deduplication';
COMMENT ON COLUMN marketing.backfill_log.match_confidence IS 'Confidence score for fuzzy matches (0.0 - 1.0)';
COMMENT ON COLUMN marketing.backfill_log.resolution_status IS 'Final status: initialized/unresolved/duplicate/error/skipped_locked';

-- ==============================================================
-- Table: backfill_staging
-- Purpose: Temporary holding table for pre-normalization rows
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.backfill_staging (
    staging_id BIGSERIAL PRIMARY KEY,
    row_hash TEXT NOT NULL UNIQUE,
    raw_data JSONB NOT NULL,
    normalized_data JSONB,
    validation_errors JSONB,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_backfill_staging_processed ON marketing.backfill_staging(is_processed);
CREATE INDEX IF NOT EXISTS idx_backfill_staging_created ON marketing.backfill_staging(created_at DESC);

COMMENT ON TABLE marketing.backfill_staging IS 'Temporary staging area for backfill CSV rows before normalization';
COMMENT ON COLUMN marketing.backfill_staging.row_hash IS 'MD5 hash for deduplication check';

-- ==============================================================
-- Table: bit_baseline_snapshot
-- Purpose: Initial BIT state from historical engagement data
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.bit_baseline_snapshot (
    baseline_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,
    historical_open_count INTEGER DEFAULT 0,
    historical_reply_count INTEGER DEFAULT 0,
    historical_meeting_count INTEGER DEFAULT 0,
    last_engaged_at TIMESTAMPTZ,
    baseline_score INTEGER NOT NULL DEFAULT 0,
    baseline_tier TEXT CHECK (baseline_tier IN ('cold', 'warm', 'engaged', 'hot', 'burning')),
    signals_generated INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source TEXT NOT NULL DEFAULT 'backfill_agent',
    metadata JSONB,

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id),
    FOREIGN KEY (company_unique_id) REFERENCES marketing.company_master(company_unique_id),

    UNIQUE (person_unique_id, company_unique_id)
);

CREATE INDEX IF NOT EXISTS idx_bit_baseline_person ON marketing.bit_baseline_snapshot(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_bit_baseline_company ON marketing.bit_baseline_snapshot(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_bit_baseline_tier ON marketing.bit_baseline_snapshot(baseline_tier);
CREATE INDEX IF NOT EXISTS idx_bit_baseline_score ON marketing.bit_baseline_snapshot(baseline_score DESC);

COMMENT ON TABLE marketing.bit_baseline_snapshot IS 'Initial BIT state created from historical engagement data during backfill';
COMMENT ON COLUMN marketing.bit_baseline_snapshot.baseline_score IS 'Computed BIT score from historical signals (opens, replies, meetings)';
COMMENT ON COLUMN marketing.bit_baseline_snapshot.signals_generated IS 'Number of bit_signal rows created from this baseline';

-- ==============================================================
-- Table: talent_flow_baseline
-- Purpose: Initial Talent Flow snapshot before monthly sweeps
-- ==============================================================
CREATE TABLE IF NOT EXISTS marketing.talent_flow_baseline (
    baseline_id BIGSERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL UNIQUE,
    enrichment_hash TEXT NOT NULL,
    snapshot_data JSONB NOT NULL,
    baseline_date DATE NOT NULL DEFAULT CURRENT_DATE,
    source TEXT NOT NULL DEFAULT 'backfill_agent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,

    FOREIGN KEY (person_unique_id) REFERENCES marketing.people_master(unique_id)
);

CREATE INDEX IF NOT EXISTS idx_tf_baseline_person ON marketing.talent_flow_baseline(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_tf_baseline_hash ON marketing.talent_flow_baseline(enrichment_hash);
CREATE INDEX IF NOT EXISTS idx_tf_baseline_date ON marketing.talent_flow_baseline(baseline_date DESC);

COMMENT ON TABLE marketing.talent_flow_baseline IS 'Starting state snapshot for Talent Flow movement detection (created during backfill)';
COMMENT ON COLUMN marketing.talent_flow_baseline.enrichment_hash IS 'MD5 hash of key fields for future movement detection';
COMMENT ON COLUMN marketing.talent_flow_baseline.snapshot_data IS 'Complete person record at time of backfill';

-- ==============================================================
-- Table: garage.missing_parts (if not exists)
-- Purpose: Unresolved matches and low-confidence fallout
-- ==============================================================
CREATE SCHEMA IF NOT EXISTS garage;

CREATE TABLE IF NOT EXISTS garage.missing_parts (
    missing_id BIGSERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    issue_type TEXT NOT NULL,
    source_data JSONB NOT NULL,
    match_attempts JSONB,
    confidence_score NUMERIC(5,3),
    resolution_notes TEXT,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_missing_parts_source ON garage.missing_parts(source);
CREATE INDEX IF NOT EXISTS idx_missing_parts_issue ON garage.missing_parts(issue_type);
CREATE INDEX IF NOT EXISTS idx_missing_parts_resolved ON garage.missing_parts(resolved);
CREATE INDEX IF NOT EXISTS idx_missing_parts_created ON garage.missing_parts(created_at DESC);

COMMENT ON TABLE garage.missing_parts IS 'Unresolved matches and low-confidence fallout from backfill operations';
COMMENT ON COLUMN garage.missing_parts.confidence_score IS 'Highest confidence score achieved during matching attempts';

-- ==============================================================
-- View: backfill_summary (helpful for monitoring)
-- ==============================================================
CREATE OR REPLACE VIEW marketing.backfill_summary AS
SELECT
    resolution_status,
    match_type,
    COUNT(*) as count,
    AVG(match_confidence) as avg_confidence,
    MIN(created_at) as first_processed,
    MAX(created_at) as last_processed
FROM marketing.backfill_log
GROUP BY resolution_status, match_type
ORDER BY resolution_status, match_type;

COMMENT ON VIEW marketing.backfill_summary IS 'Summary statistics for backfill operations';

-- ==============================================================
-- Grant permissions (if needed)
-- ==============================================================
-- GRANT SELECT, INSERT, UPDATE ON marketing.backfill_log TO marketing_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON marketing.backfill_staging TO marketing_app_user;
-- GRANT SELECT, INSERT ON marketing.bit_baseline_snapshot TO marketing_app_user;
-- GRANT SELECT, INSERT ON marketing.talent_flow_baseline TO marketing_app_user;
-- GRANT SELECT, INSERT, UPDATE ON garage.missing_parts TO marketing_app_user;
