-- Migration: Coverage Run Foundation
-- Date: 2026-02-10
-- Purpose: Geographic gating layer — binds a service agent to a ZIP-based radius
--          coverage list, producing a deterministic coverage_run_id.
--          No downstream action (CT join, enrichment, outreach) may occur
--          without a valid coverage_run_id.
-- Doctrine: CC-02 Hub level, IMO compliant, all tables CANONICAL

-- Ensure pgcrypto is available for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create coverage schema
CREATE SCHEMA IF NOT EXISTS coverage;

-- ============================================================================
-- Table 1: coverage.service_agent
-- CTB leaf type: CANONICAL
-- Purpose: Service agent entity that owns coverage runs
-- ============================================================================
CREATE TABLE IF NOT EXISTS coverage.service_agent (
    service_agent_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name        TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'inactive')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE coverage.service_agent IS 'Service agent entity for coverage runs. Each agent can own multiple coverage runs.';
COMMENT ON COLUMN coverage.service_agent.service_agent_id IS 'Primary key UUID, auto-generated';
COMMENT ON COLUMN coverage.service_agent.status IS 'Agent lifecycle: active or inactive';

-- ============================================================================
-- Table 2: coverage.coverage_run
-- CTB leaf type: CANONICAL
-- Purpose: Immutable coverage run snapshot: agent + anchor ZIP + radius
-- ============================================================================
CREATE TABLE IF NOT EXISTS coverage.coverage_run (
    coverage_run_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_agent_id  UUID NOT NULL
                      REFERENCES coverage.service_agent (service_agent_id),
    anchor_zip        TEXT NOT NULL
                      CHECK (anchor_zip ~ '^\d{5}$'),
    radius_miles      NUMERIC(6,1) NOT NULL
                      CHECK (radius_miles > 0),
    status            TEXT NOT NULL DEFAULT 'active'
                      CHECK (status IN ('active', 'retired')),
    created_by        TEXT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retired_at        TIMESTAMPTZ NULL,
    retired_by        TEXT NULL,
    notes             TEXT NULL
);

COMMENT ON TABLE coverage.coverage_run IS 'Immutable coverage run snapshot: agent + anchor ZIP + radius. Each run is a new snapshot — no upsert, no UNIQUE on (agent, zip, radius).';
COMMENT ON COLUMN coverage.coverage_run.anchor_zip IS '5-digit US ZIP code used as center point for radius query';
COMMENT ON COLUMN coverage.coverage_run.radius_miles IS 'Radius in miles from anchor ZIP';
COMMENT ON COLUMN coverage.coverage_run.status IS 'Lifecycle: active or retired';
COMMENT ON COLUMN coverage.coverage_run.retired_at IS 'Timestamp when run was retired (NULL if active)';
COMMENT ON COLUMN coverage.coverage_run.retired_by IS 'Who retired the run (NULL if active)';

-- ============================================================================
-- Table 3: coverage.coverage_run_zip
-- CTB leaf type: CANONICAL
-- Purpose: Derived ZIP list per coverage run (haversine radius result)
-- ============================================================================
CREATE TABLE IF NOT EXISTS coverage.coverage_run_zip (
    coverage_run_id   UUID NOT NULL
                      REFERENCES coverage.coverage_run (coverage_run_id)
                      ON DELETE CASCADE,
    zip               TEXT NOT NULL
                      CHECK (zip ~ '^\d{5}$'),
    distance_miles    NUMERIC(7,2) NOT NULL,
    PRIMARY KEY (coverage_run_id, zip)
);

COMMENT ON TABLE coverage.coverage_run_zip IS 'Derived ZIP list per coverage run. Each row is a ZIP within the radius of the anchor ZIP, with computed haversine distance.';
COMMENT ON COLUMN coverage.coverage_run_zip.zip IS '5-digit US ZIP code within radius';
COMMENT ON COLUMN coverage.coverage_run_zip.distance_miles IS 'Haversine distance from anchor ZIP in miles';

-- ============================================================================
-- Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_crun_agent
    ON coverage.coverage_run (service_agent_id);

CREATE INDEX IF NOT EXISTS idx_crun_anchor
    ON coverage.coverage_run (anchor_zip);

CREATE INDEX IF NOT EXISTS idx_crun_status
    ON coverage.coverage_run (status);

CREATE INDEX IF NOT EXISTS idx_crzip_zip
    ON coverage.coverage_run_zip (zip);

-- ============================================================================
-- CTB Registration (all CANONICAL)
-- ============================================================================
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, notes)
VALUES
    ('coverage', 'service_agent', 'CANONICAL', 'Service agent entity for coverage runs'),
    ('coverage', 'coverage_run', 'CANONICAL', 'Immutable coverage run snapshot: agent + anchor ZIP + radius'),
    ('coverage', 'coverage_run_zip', 'CANONICAL', 'Derived ZIP list per coverage run (haversine radius)')
ON CONFLICT (table_schema, table_name) DO NOTHING;
