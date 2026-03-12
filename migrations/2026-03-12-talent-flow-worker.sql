-- =============================================================================
-- Migration: Talent Flow Dumb Worker support
-- Date: 2026-03-12
-- Author: Claude Code (CC-01)
-- Purpose: (1) Add 'talent_flow' to signal_output.signal_source CHECK constraint
--          (2) Create error table for talent flow worker
--          (3) Register error table in CTB
-- BAR: BAR-50
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 1: Update signal_source CHECK constraint to include 'talent_flow'
-- ─────────────────────────────────────────────────────────────────────────────

-- Drop old constraint
ALTER TABLE outreach.signal_output
    DROP CONSTRAINT IF EXISTS signal_output_signal_source_check;

-- Re-add with talent_flow included
ALTER TABLE outreach.signal_output
    ADD CONSTRAINT signal_output_signal_source_check
    CHECK (signal_source IN ('dol', 'people', 'blog', 'talent_flow'));

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 2: Register error table in CTB
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO ctb.table_registry (
    table_schema,
    table_name,
    leaf_type,
    registered_by,
    is_frozen,
    notes
)
VALUES (
    'outreach',
    'talent_flow_errors',
    'ERROR',
    'talent_flow_migration',
    FALSE,
    'Error table for Talent Flow dumb worker. Captures ICP failures, write errors, cascade failures.'
)
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 3: Create error table
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS outreach.talent_flow_errors (
    error_id        UUID        PRIMARY KEY,
    source_spoke    TEXT        NOT NULL DEFAULT 'talent_flow',
    error_type      TEXT        NOT NULL,
    raw_payload     JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tf_errors_created
    ON outreach.talent_flow_errors (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_tf_errors_type
    ON outreach.talent_flow_errors (error_type);

COMMENT ON TABLE outreach.talent_flow_errors IS
    'Error table for Talent Flow dumb worker. Append-only. '
    'Captures ICP validation failures, signal write errors, cascade trace failures.';

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 4: Update signal_output comment to include talent_flow
-- ─────────────────────────────────────────────────────────────────────────────

COMMENT ON TABLE outreach.signal_output IS
    'Canonical signal table. Written by DOL, People, Blog, and Talent Flow dumb workers. '
    'One row per company per signal code per monthly run. '
    'Deduped on (outreach_id, signal_code, run_month).';

COMMENT ON COLUMN outreach.signal_output.signal_code IS
    'Structured signal identifier: D-01..D-07 (DOL), P-01..P-05 (People), '
    'B-01..B-06 (Blog), TF-01..TF-04 (Talent Flow)';

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFICATION
-- ─────────────────────────────────────────────────────────────────────────────

SELECT table_schema, table_name, leaf_type, is_frozen, notes
FROM ctb.table_registry
WHERE table_schema = 'outreach' AND table_name = 'talent_flow_errors';
