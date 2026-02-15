-- ============================================================================
-- Migration: 002_create_garage_2_0_schema.sql
-- Purpose: Add Garage 2.0 fields for enrichment routing and tracking
-- Date: 2025-11-18
-- ============================================================================

-- ============================================================================
-- 1. ADD FIELDS TO marketing.people_master
-- ============================================================================

-- VIN Tag (record hashing)
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS last_hash VARCHAR(64);

-- Enrichment TTL (next check timestamp)
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS enrichment_next_check TIMESTAMP;

-- Repair tracking
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS repair_attempts INTEGER DEFAULT 0;

ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS chronic_bad BOOLEAN DEFAULT FALSE;

-- Last enrichment timestamp
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMP;

-- Garage bay assignment
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS garage_bay VARCHAR(10);

-- Apollo ID for tracking
ALTER TABLE marketing.people_master
ADD COLUMN IF NOT EXISTS apollo_id VARCHAR(255);

COMMENT ON COLUMN marketing.people_master.last_hash IS 'VIN tag: SHA256 hash of title+company+domain+linkedin+apollo_id+timestamp';
COMMENT ON COLUMN marketing.people_master.enrichment_next_check IS 'TTL: Next enrichment check based on title seniority';
COMMENT ON COLUMN marketing.people_master.repair_attempts IS 'Number of repair attempts in last 30 days';
COMMENT ON COLUMN marketing.people_master.chronic_bad IS 'TRUE if repair_attempts > 3 in 30 days';
COMMENT ON COLUMN marketing.people_master.garage_bay IS 'Bay A (missing) or Bay B (contradictions)';

-- ============================================================================
-- 2. ADD FIELDS TO marketing.company_master
-- ============================================================================

-- VIN Tag (record hashing)
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS last_hash VARCHAR(64);

-- Repair tracking
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS repair_attempts INTEGER DEFAULT 0;

ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS chronic_bad BOOLEAN DEFAULT FALSE;

-- Last enrichment timestamp
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS last_enriched_at TIMESTAMP;

-- Garage bay assignment
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS garage_bay VARCHAR(10);

-- Apollo ID for tracking
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS apollo_id VARCHAR(255);

COMMENT ON COLUMN marketing.company_master.last_hash IS 'VIN tag: SHA256 hash of company+domain+linkedin+apollo_id+timestamp';
COMMENT ON COLUMN marketing.company_master.repair_attempts IS 'Number of repair attempts in last 30 days';
COMMENT ON COLUMN marketing.company_master.chronic_bad IS 'TRUE if repair_attempts > 3 in 30 days';
COMMENT ON COLUMN marketing.company_master.garage_bay IS 'Bay A (missing) or Bay B (contradictions)';

-- ============================================================================
-- 3. CREATE talent_flow SCHEMA FOR MOVEMENT TRACKING
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS talent_flow;

CREATE TABLE IF NOT EXISTS talent_flow.movements (
    movement_id SERIAL PRIMARY KEY,
    person_unique_id TEXT NOT NULL,
    company_unique_id TEXT NOT NULL,

    -- Movement details
    movement_type VARCHAR(50) NOT NULL,  -- 'promotion', 'lateral', 'demotion', 'new_company', 'left_company'
    movement_reason TEXT,

    -- Role change
    previous_role TEXT,
    new_role TEXT,
    previous_company TEXT,
    new_company TEXT,

    -- Turbulence window (0-90 days)
    turbulence_window_days INTEGER,  -- 0-30, 30-60, 60-90

    -- Timing
    detected_at TIMESTAMP DEFAULT NOW(),
    movement_date TIMESTAMP,

    -- BIT integration
    bit_score_updated BOOLEAN DEFAULT FALSE,
    bit_signal_id INTEGER,

    -- Metadata
    source TEXT,
    confidence_score NUMERIC(3,2),
    metadata JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_movements_person ON talent_flow.movements(person_unique_id);
CREATE INDEX IF NOT EXISTS idx_movements_company ON talent_flow.movements(company_unique_id);
CREATE INDEX IF NOT EXISTS idx_movements_detected_at ON talent_flow.movements(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_movements_turbulence ON talent_flow.movements(turbulence_window_days);

COMMENT ON TABLE talent_flow.movements IS 'Garage 2.0: Tracks talent movements with turbulence window (0-90 days)';
COMMENT ON COLUMN talent_flow.movements.turbulence_window_days IS 'Days since movement: 0-30 (heavy), 30-60 (moderate), 60-90 (light)';

-- ============================================================================
-- 4. ADD FIELDS TO bit.bit_signal FOR PAINT CODES
-- ============================================================================

-- Paint code (reason for BIT score)
ALTER TABLE bit.bit_signal
ADD COLUMN IF NOT EXISTS paint_code VARCHAR(50);

ALTER TABLE bit.bit_signal
ADD COLUMN IF NOT EXISTS paint_reason TEXT;

-- Movement integration
ALTER TABLE bit.bit_signal
ADD COLUMN IF NOT EXISTS movement_type VARCHAR(50);

ALTER TABLE bit.bit_signal
ADD COLUMN IF NOT EXISTS movement_strength INTEGER;

ALTER TABLE bit.bit_signal
ADD COLUMN IF NOT EXISTS movement_id INTEGER;

COMMENT ON COLUMN bit.bit_signal.paint_code IS 'Garage 2.0: Reason code for BIT score (e.g., "exec_promotion", "icp_hire")';
COMMENT ON COLUMN bit.bit_signal.paint_reason IS 'Human-readable reason for BIT score';
COMMENT ON COLUMN bit.bit_signal.movement_type IS 'Type of movement that triggered signal';
COMMENT ON COLUMN bit.bit_signal.movement_strength IS 'Strength of movement signal (1-100)';
COMMENT ON COLUMN bit.bit_signal.movement_id IS 'FK to talent_flow.movements';

-- ============================================================================
-- 5. CREATE GARAGE TRACKING TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.garage_runs (
    run_id SERIAL PRIMARY KEY,
    state VARCHAR(2) NOT NULL,
    snapshot_version VARCHAR(20) NOT NULL,

    -- Summary metrics
    records_skipped_hash INTEGER DEFAULT 0,
    records_skipped_ttl INTEGER DEFAULT 0,
    records_bay_a INTEGER DEFAULT 0,
    records_bay_b INTEGER DEFAULT 0,
    repair_success_count INTEGER DEFAULT 0,
    chronic_bad_count INTEGER DEFAULT 0,
    neon_reinserts INTEGER DEFAULT 0,
    bit_updates INTEGER DEFAULT 0,

    -- Cost tracking
    total_cost_estimate NUMERIC(10,2),

    -- B2 paths
    bay_a_b2_path TEXT,
    bay_b_b2_path TEXT,

    -- Timing
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_seconds INTEGER,

    -- Status
    status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'
    error_message TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_garage_runs_state ON public.garage_runs(state);
CREATE INDEX IF NOT EXISTS idx_garage_runs_snapshot ON public.garage_runs(snapshot_version);
CREATE INDEX IF NOT EXISTS idx_garage_runs_created_at ON public.garage_runs(created_at DESC);

COMMENT ON TABLE public.garage_runs IS 'Garage 2.0: Tracks enrichment garage runs by state and snapshot';

-- ============================================================================
-- 6. CREATE AGENT ROUTING LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.agent_routing_log (
    routing_id SERIAL PRIMARY KEY,
    garage_run_id INTEGER REFERENCES public.garage_runs(run_id),

    -- Record identification
    record_type VARCHAR(20) NOT NULL,  -- 'person' or 'company'
    record_id TEXT NOT NULL,

    -- Routing decision
    garage_bay VARCHAR(10) NOT NULL,  -- 'bay_a' or 'bay_b'
    agent_assigned VARCHAR(50),  -- 'firecrawl', 'apify', 'abacus', 'claude'

    -- Reason for routing
    routing_reason TEXT,
    missing_fields TEXT[],
    contradictions TEXT[],

    -- Hash/TTL checks
    hash_unchanged BOOLEAN DEFAULT FALSE,
    ttl_not_expired BOOLEAN DEFAULT FALSE,
    skipped BOOLEAN DEFAULT FALSE,

    -- Repair tracking
    repair_attempt_number INTEGER,
    is_chronic_bad BOOLEAN DEFAULT FALSE,

    -- Timing
    routed_at TIMESTAMP DEFAULT NOW(),
    agent_started_at TIMESTAMP,
    agent_completed_at TIMESTAMP,

    -- Results
    agent_status VARCHAR(20),  -- 'pending', 'running', 'success', 'failed'
    agent_cost NUMERIC(10,2),
    fields_repaired TEXT[],

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_routing_record ON public.agent_routing_log(record_type, record_id);
CREATE INDEX IF NOT EXISTS idx_agent_routing_garage_run ON public.agent_routing_log(garage_run_id);
CREATE INDEX IF NOT EXISTS idx_agent_routing_bay ON public.agent_routing_log(garage_bay);
CREATE INDEX IF NOT EXISTS idx_agent_routing_agent ON public.agent_routing_log(agent_assigned);

COMMENT ON TABLE public.agent_routing_log IS 'Garage 2.0: Logs agent routing decisions and results';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Log migration
INSERT INTO shq.audit_log (event_type, event_source, details, created_at)
VALUES (
    'schema_migration',
    'garage_2_0',
    '{"migration": "002_create_garage_2_0_schema", "tables_created": ["talent_flow.movements", "garage_runs", "agent_routing_log"], "fields_added": ["last_hash", "enrichment_next_check", "repair_attempts", "chronic_bad", "paint_code", "paint_reason"]}'::jsonb,
    NOW()
);
