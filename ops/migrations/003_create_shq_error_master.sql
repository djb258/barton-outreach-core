-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: Create shq.error_master Table
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Purpose: Canonical error table for operational triage and enrichment routing
-- Doctrine: All FAIL HARD paths dual-write to:
--   1. Hub-specific AIR log (authoritative)
--   2. shq.error_master (operational / enrichment queue)
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Create SHQ schema if not exists
CREATE SCHEMA IF NOT EXISTS shq;

COMMENT ON SCHEMA shq IS 'Shared Hub Queue - Cross-hub operational infrastructure';

-- ═══════════════════════════════════════════════════════════════════════════
-- TABLE: shq.error_master
-- ═══════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS shq.error_master (
    -- Primary Key
    error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source Identification
    process_id VARCHAR(50) NOT NULL,        -- Barton ID prefix (e.g., '01.04.02.04.22000')
    agent_id VARCHAR(50) NOT NULL,          -- Source agent (e.g., 'DOL_EIN_SUBHUB')
    
    -- Severity (LOCKED ENUM)
    severity VARCHAR(20) NOT NULL DEFAULT 'HARD_FAIL',
    
    -- Error Classification
    error_type VARCHAR(50) NOT NULL,        -- Error code from hub's error enum
    message TEXT NOT NULL,                   -- Human-readable description
    
    -- Entity Context (may be NULL if identity gate failed)
    company_unique_id VARCHAR(50),          -- Sovereign company ID
    outreach_context_id VARCHAR(100),       -- Campaign context
    
    -- Cross-Reference to Authoritative Log
    air_event_id VARCHAR(50),               -- Reference to hub's AIR log entry
    
    -- Payload
    context JSONB DEFAULT '{}',             -- Additional error context
    
    -- Lifecycle
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ,                -- When error was resolved
    resolution_type VARCHAR(30),            -- How it was resolved
    
    -- Constraints
    CONSTRAINT chk_severity CHECK (
        severity IN ('HARD_FAIL', 'SOFT_FAIL', 'WARNING')
    ),
    CONSTRAINT chk_resolution_type CHECK (
        resolution_type IS NULL OR resolution_type IN (
            'ENRICHMENT_RESOLVED',
            'MANUAL_OVERRIDE',
            'AUTO_RETRY_SUCCESS',
            'MARKED_INVALID',
            'SUPERSEDED'
        )
    )
);

-- ═══════════════════════════════════════════════════════════════════════════
-- INDEXES
-- ═══════════════════════════════════════════════════════════════════════════

-- Find errors by process (hub)
CREATE INDEX IF NOT EXISTS idx_error_master_process 
    ON shq.error_master (process_id, created_at DESC);

-- Find errors by agent
CREATE INDEX IF NOT EXISTS idx_error_master_agent 
    ON shq.error_master (agent_id, created_at DESC);

-- Find errors by type (for enrichment queue routing)
CREATE INDEX IF NOT EXISTS idx_error_master_type 
    ON shq.error_master (error_type, created_at DESC);

-- Find unresolved errors
CREATE INDEX IF NOT EXISTS idx_error_master_unresolved 
    ON shq.error_master (created_at DESC)
    WHERE resolved_at IS NULL;

-- Find errors by company
CREATE INDEX IF NOT EXISTS idx_error_master_company 
    ON shq.error_master (company_unique_id, created_at DESC)
    WHERE company_unique_id IS NOT NULL;

-- Find errors by outreach context
CREATE INDEX IF NOT EXISTS idx_error_master_context 
    ON shq.error_master (outreach_context_id, created_at DESC)
    WHERE outreach_context_id IS NOT NULL;

-- Find errors by severity (prioritize HARD_FAIL)
CREATE INDEX IF NOT EXISTS idx_error_master_severity 
    ON shq.error_master (severity, created_at DESC);

-- JSONB context search
CREATE INDEX IF NOT EXISTS idx_error_master_context_gin 
    ON shq.error_master USING GIN (context);

-- ═══════════════════════════════════════════════════════════════════════════
-- COMMENTS
-- ═══════════════════════════════════════════════════════════════════════════

COMMENT ON TABLE shq.error_master IS 
    'Canonical error table for operational triage. All FAIL HARD paths dual-write here.';

COMMENT ON COLUMN shq.error_master.process_id IS 
    'Barton ID prefix of the source process (e.g., DOL = 01.04.02.04.22000)';

COMMENT ON COLUMN shq.error_master.agent_id IS 
    'Identifier of the agent that generated the error (e.g., DOL_EIN_SUBHUB)';

COMMENT ON COLUMN shq.error_master.severity IS 
    'HARD_FAIL = abort, SOFT_FAIL = recoverable, WARNING = informational';

COMMENT ON COLUMN shq.error_master.air_event_id IS 
    'Cross-reference to the authoritative AIR log entry in source hub';

COMMENT ON COLUMN shq.error_master.resolution_type IS 
    'How the error was resolved: enrichment, manual, retry, invalid, or superseded';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Unresolved DOL Errors (Enrichment Queue)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW shq.v_dol_enrichment_queue AS
SELECT
    error_id,
    error_type,
    message,
    company_unique_id,
    outreach_context_id,
    context,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at)) / 3600 AS hours_pending
FROM shq.error_master
WHERE process_id = '01.04.02.04.22000'  -- DOL Sub-Hub
  AND severity = 'HARD_FAIL'
  AND resolved_at IS NULL
ORDER BY created_at ASC;

COMMENT ON VIEW shq.v_dol_enrichment_queue IS 
    'DOL errors awaiting enrichment resolution. Ordered by age (oldest first).';

-- ═══════════════════════════════════════════════════════════════════════════
-- VIEW: Error Summary by Hub (Last 24h)
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW shq.v_error_summary_24h AS
SELECT
    process_id,
    agent_id,
    error_type,
    COUNT(*) AS error_count,
    COUNT(*) FILTER (WHERE resolved_at IS NULL) AS unresolved_count,
    MIN(created_at) AS earliest,
    MAX(created_at) AS latest
FROM shq.error_master
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY process_id, agent_id, error_type
ORDER BY error_count DESC;

COMMENT ON VIEW shq.v_error_summary_24h IS 
    'Error summary by hub and type for last 24 hours.';

-- ═══════════════════════════════════════════════════════════════════════════
-- FUNCTION: Mark Error Resolved
-- ═══════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION shq.resolve_error(
    p_error_id UUID,
    p_resolution_type VARCHAR(30)
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE shq.error_master
    SET resolved_at = NOW(),
        resolution_type = p_resolution_type
    WHERE error_id = p_error_id
      AND resolved_at IS NULL;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION shq.resolve_error IS 
    'Mark an error as resolved. Returns TRUE if error was found and updated.';

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- 1. Verify table created
-- SELECT * FROM information_schema.tables WHERE table_schema = 'shq' AND table_name = 'error_master';

-- 2. Verify indexes
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'shq' AND tablename = 'error_master';

-- 3. Test DOL enrichment queue view
-- SELECT * FROM shq.v_dol_enrichment_queue LIMIT 5;

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════
