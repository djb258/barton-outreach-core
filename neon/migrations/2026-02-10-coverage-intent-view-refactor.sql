-- Migration: Coverage Intent + View Refactor
-- Date: 2026-02-10
-- ADR: docs/adr/ADR-COVERAGE-INTENT-VIEW-REFACTOR.md
-- Purpose: Replace materialized coverage_run_zip with intent table + derived view.
--          Persist intent (agent + anchor_zip + radius), derive membership via haversine view.
--          Only real entities stay in CTB; view is outside truth surface.

-- ============================================================================
-- Step 1: Create service_agent_coverage (replaces coverage_run)
-- CTB leaf type: CANONICAL
-- ============================================================================
CREATE TABLE IF NOT EXISTS coverage.service_agent_coverage (
    coverage_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

COMMENT ON TABLE coverage.service_agent_coverage IS 'Coverage intent: binds a service agent to an anchor ZIP + radius. ZIP membership is derived via view, not stored.';
COMMENT ON COLUMN coverage.service_agent_coverage.coverage_id IS 'Stable FK for all downstream joins. Replaces coverage_run_id.';
COMMENT ON COLUMN coverage.service_agent_coverage.anchor_zip IS '5-digit US ZIP code used as center point for radius derivation';
COMMENT ON COLUMN coverage.service_agent_coverage.radius_miles IS 'Radius in miles from anchor ZIP';
COMMENT ON COLUMN coverage.service_agent_coverage.status IS 'Lifecycle: active or retired';

CREATE INDEX IF NOT EXISTS idx_sac_agent
    ON coverage.service_agent_coverage (service_agent_id);

CREATE INDEX IF NOT EXISTS idx_sac_anchor
    ON coverage.service_agent_coverage (anchor_zip);

CREATE INDEX IF NOT EXISTS idx_sac_status
    ON coverage.service_agent_coverage (status);

-- ============================================================================
-- Step 2: Migrate existing coverage_run rows (if any)
-- ============================================================================
INSERT INTO coverage.service_agent_coverage (
    coverage_id, service_agent_id, anchor_zip, radius_miles,
    status, created_by, created_at, retired_at, retired_by, notes
)
SELECT
    coverage_run_id, service_agent_id, anchor_zip, radius_miles,
    status, created_by, created_at, retired_at, retired_by, notes
FROM coverage.coverage_run
ON CONFLICT (coverage_id) DO NOTHING;

-- ============================================================================
-- Step 3: Create derived view (haversine ZIP membership)
-- This view is NOT registered in CTB — it is a read projection, not a truth surface.
-- ============================================================================
CREATE OR REPLACE VIEW coverage.v_service_agent_coverage_zips AS
WITH coverage_anchors AS (
    SELECT
        sac.coverage_id,
        sac.service_agent_id,
        sac.anchor_zip,
        sac.radius_miles,
        ref_anchor.lat AS anchor_lat,
        ref_anchor.lng AS anchor_lng
    FROM coverage.service_agent_coverage sac
    JOIN reference.us_zip_codes ref_anchor
        ON ref_anchor.zip = sac.anchor_zip
    WHERE sac.status = 'active'
),
distances AS (
    SELECT
        ca.coverage_id,
        ca.service_agent_id,
        z.zip,
        z.city,
        z.state_id,
        z.population,
        ca.radius_miles,
        ROUND((3959 * acos(
            LEAST(1.0, GREATEST(-1.0,
                cos(radians(ca.anchor_lat)) * cos(radians(z.lat)) *
                cos(radians(z.lng) - radians(ca.anchor_lng)) +
                sin(radians(ca.anchor_lat)) * sin(radians(z.lat))
            ))
        ))::numeric, 2) AS distance_miles
    FROM coverage_anchors ca
    CROSS JOIN LATERAL (
        SELECT zip, city, state_id, population, lat, lng
        FROM reference.us_zip_codes
        WHERE lat BETWEEN ca.anchor_lat - (ca.radius_miles / 69.0)
                      AND ca.anchor_lat + (ca.radius_miles / 69.0)
          AND lng BETWEEN ca.anchor_lng - (ca.radius_miles / (69.0 * cos(radians(ca.anchor_lat))))
                      AND ca.anchor_lng + (ca.radius_miles / (69.0 * cos(radians(ca.anchor_lat))))
    ) z
)
SELECT
    coverage_id,
    service_agent_id,
    zip,
    distance_miles,
    city,
    state_id,
    population
FROM distances
WHERE distance_miles <= radius_miles;

COMMENT ON VIEW coverage.v_service_agent_coverage_zips IS 'Derived ZIP membership per active coverage intent. Haversine distance from anchor ZIP with bounding box pre-filter. NOT a CTB truth surface.';

-- ============================================================================
-- Step 4: Drop materialized tables (replaced by intent + view)
-- ============================================================================
DROP TABLE IF EXISTS coverage.coverage_run_zip CASCADE;
DROP TABLE IF EXISTS coverage.coverage_run CASCADE;

-- ============================================================================
-- Step 5: Update CTB registry
-- Remove old registrations, add new
-- ============================================================================
DELETE FROM ctb.table_registry
WHERE table_schema = 'coverage'
  AND table_name IN ('coverage_run', 'coverage_run_zip');

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, notes)
VALUES (
    'coverage',
    'service_agent_coverage',
    'CANONICAL',
    'Coverage intent: agent + anchor ZIP + radius. ZIP membership derived via view, not stored.'
)
ON CONFLICT (table_schema, table_name) DO NOTHING;
