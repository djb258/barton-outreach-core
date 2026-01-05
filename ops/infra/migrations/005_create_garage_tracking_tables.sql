-- ============================================================================
-- Migration 005: Create Garage 2.0 Tracking Tables
-- ============================================================================
-- Purpose: Create garage_runs and agent_routing_log tables for tracking
--          validation pipeline runs and agent assignments
-- Author: Claude Code
-- Created: 2025-11-18
-- Barton ID: 04.04.02.04.50000.005
-- ============================================================================

-- ============================================================================
-- TABLE: garage_runs
-- ============================================================================
-- Tracks each validation pipeline run with snapshot versioning

CREATE TABLE IF NOT EXISTS public.garage_runs (
    run_id SERIAL PRIMARY KEY,
    run_started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    run_completed_at TIMESTAMP,
    run_status VARCHAR(50) NOT NULL DEFAULT 'running',
    snapshot_version VARCHAR(50) NOT NULL,
    total_records_processed INTEGER DEFAULT 0,
    bay_a_count INTEGER DEFAULT 0,
    bay_b_count INTEGER DEFAULT 0,
    promoted_count INTEGER DEFAULT 0,
    chronic_bad_count INTEGER DEFAULT 0,
    run_mode VARCHAR(50),  -- 'validate_only' or 'validate_and_promote'
    record_type VARCHAR(50),  -- 'company' or 'people'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for garage_runs
CREATE INDEX IF NOT EXISTS idx_garage_runs_snapshot ON public.garage_runs(snapshot_version);
CREATE INDEX IF NOT EXISTS idx_garage_runs_status ON public.garage_runs(run_status);
CREATE INDEX IF NOT EXISTS idx_garage_runs_started ON public.garage_runs(run_started_at DESC);
CREATE INDEX IF NOT EXISTS idx_garage_runs_type ON public.garage_runs(record_type);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_garage_runs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER garage_runs_updated_at
    BEFORE UPDATE ON public.garage_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_garage_runs_updated_at();

COMMENT ON TABLE public.garage_runs IS 'Tracks validation pipeline runs for Garage 2.0 enrichment system';
COMMENT ON COLUMN public.garage_runs.snapshot_version IS 'Timestamp-based snapshot identifier (YYYYMMDDHHMMSS)';
COMMENT ON COLUMN public.garage_runs.bay_a_count IS 'Count of records with missing fields (sent to Bay A agents)';
COMMENT ON COLUMN public.garage_runs.bay_b_count IS 'Count of records with contradictions (sent to Bay B agents)';
COMMENT ON COLUMN public.garage_runs.chronic_bad_count IS 'Count of records with 2+ failed enrichment attempts';

-- ============================================================================
-- TABLE: agent_routing_log
-- ============================================================================
-- Tracks agent assignments for failed validation records

CREATE TABLE IF NOT EXISTS public.agent_routing_log (
    routing_id SERIAL PRIMARY KEY,
    garage_run_id INTEGER REFERENCES public.garage_runs(run_id) ON DELETE CASCADE,
    record_type VARCHAR(50) NOT NULL,  -- 'company' or 'people'
    record_id VARCHAR(255) NOT NULL,  -- ID from intake table
    garage_bay VARCHAR(10) NOT NULL,  -- 'bay_a' or 'bay_b'
    agent_name VARCHAR(100),  -- 'firecrawl', 'apify', 'abacus', 'claude'
    routing_reason TEXT,  -- Comma-separated validation failure reasons
    routed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'assigned', 'running', 'completed', 'failed'
    assigned_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    cost_credits DECIMAL(10, 4),  -- Cost in credits/dollars
    data_quality_score INTEGER,  -- 0-100 score after enrichment
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for agent_routing_log
CREATE INDEX IF NOT EXISTS idx_agent_routing_garage_run ON public.agent_routing_log(garage_run_id);
CREATE INDEX IF NOT EXISTS idx_agent_routing_record ON public.agent_routing_log(record_type, record_id);
CREATE INDEX IF NOT EXISTS idx_agent_routing_bay ON public.agent_routing_log(garage_bay);
CREATE INDEX IF NOT EXISTS idx_agent_routing_agent ON public.agent_routing_log(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_routing_status ON public.agent_routing_log(status);
CREATE INDEX IF NOT EXISTS idx_agent_routing_routed ON public.agent_routing_log(routed_at DESC);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_agent_routing_log_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER agent_routing_log_updated_at
    BEFORE UPDATE ON public.agent_routing_log
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_routing_log_updated_at();

COMMENT ON TABLE public.agent_routing_log IS 'Tracks agent assignments for Garage 2.0 enrichment jobs';
COMMENT ON COLUMN public.agent_routing_log.garage_bay IS 'Bay A = missing fields (web scraping), Bay B = contradictions (reasoning)';
COMMENT ON COLUMN public.agent_routing_log.agent_name IS 'Bay A: firecrawl/apify ($0.05-0.10), Bay B: abacus/claude ($0.50-1.00)';
COMMENT ON COLUMN public.agent_routing_log.data_quality_score IS 'Quality score (0-100) assigned after enrichment completion';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 005 Complete:';
    RAISE NOTICE '  ✓ Created table: public.garage_runs';
    RAISE NOTICE '  ✓ Created table: public.agent_routing_log';
    RAISE NOTICE '  ✓ Created 4 indexes on garage_runs';
    RAISE NOTICE '  ✓ Created 6 indexes on agent_routing_log';
    RAISE NOTICE '  ✓ Created auto-update triggers';
END $$;
