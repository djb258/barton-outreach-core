-- =============================================================================
-- Migration: Create outreach.signal_output
-- Date: 2026-03-02
-- Author: Manus AI
-- Purpose: Canonical signal table for Dumb Worker signal detection system.
--          Three independent workers (DOL, People, Blog) write here.
--          Replaces the unimplemented BIT v2.0 pressure_signals tables
--          as the operational signal interface.
-- CTB Registry: leaf_type = CANONICAL
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.signal_output (
    signal_id       UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    outreach_id     UUID        NOT NULL
                                REFERENCES outreach.outreach(outreach_id)
                                ON DELETE CASCADE,
    signal_code     VARCHAR(10) NOT NULL,           -- e.g. 'D-01', 'P-03', 'B-01'
    signal_name     TEXT        NOT NULL,            -- Human-readable label
    signal_source   VARCHAR(20) NOT NULL             -- Worker that emitted this
                                CHECK (signal_source IN ('dol', 'people', 'blog')),
    signal_value    JSONB       NOT NULL DEFAULT '{}', -- Evidence payload
    magnitude       INTEGER     NOT NULL DEFAULT 0
                                CHECK (magnitude BETWEEN 0 AND 100),
    detected_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    correlation_id  UUID        NOT NULL,
    run_month       DATE        NOT NULL,            -- First-of-month; dedup key
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Idempotency: one signal per company per code per monthly run
    CONSTRAINT uq_signal_dedup UNIQUE (outreach_id, signal_code, run_month)
);

-- Lookup by company (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_signal_output_outreach_id
    ON outreach.signal_output (outreach_id);

-- Lookup by signal code for analysis
CREATE INDEX IF NOT EXISTS idx_signal_output_signal_code
    ON outreach.signal_output (signal_code);

-- Lookup by source worker
CREATE INDEX IF NOT EXISTS idx_signal_output_signal_source
    ON outreach.signal_output (signal_source);

-- Monthly run queries
CREATE INDEX IF NOT EXISTS idx_signal_output_run_month
    ON outreach.signal_output (run_month);

-- Active (non-expired) signals — most dashboard queries filter here
CREATE INDEX IF NOT EXISTS idx_signal_output_expires_at_active
    ON outreach.signal_output (expires_at)
    WHERE expires_at > now();

-- Magnitude-ranked queries for prioritization
CREATE INDEX IF NOT EXISTS idx_signal_output_magnitude
    ON outreach.signal_output (magnitude DESC);

COMMENT ON TABLE outreach.signal_output IS
    'Canonical signal table. Written by DOL, People, and Blog dumb workers. '
    'One row per company per signal code per monthly run. '
    'Deduped on (outreach_id, signal_code, run_month).';

COMMENT ON COLUMN outreach.signal_output.signal_code IS
    'Structured signal identifier: D-01..D-07 (DOL), P-01..P-05 (People), B-01..B-06 (Blog)';
COMMENT ON COLUMN outreach.signal_output.signal_value IS
    'JSONB evidence payload. Contents vary by signal_code. '
    'Always include at minimum: {"source_table": "...", "detected_by": "..."}';
COMMENT ON COLUMN outreach.signal_output.magnitude IS
    'Signal strength 0-100. Used for prioritization. '
    'D-04 Renewal Proximity = 80 (current month) or 50 (next month). '
    'All others are fixed per signal_code.';
COMMENT ON COLUMN outreach.signal_output.run_month IS
    'First day of the month this worker run covers (e.g. 2026-03-01). '
    'Used as the dedup key — re-running the same month is safe.';
COMMENT ON COLUMN outreach.signal_output.expires_at IS
    'Signal expiry. DOL signals: 365d. People signals: 90d. Blog signals: 60d. '
    'Expired signals are retained for audit; filter WHERE expires_at > now() for active signals.';
