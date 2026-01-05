-- ═══════════════════════════════════════════════════════════════════════════
-- Migration: DOL EIN Subhub Error Index
-- ═══════════════════════════════════════════════════════════════════════════
--
-- Version: 2.0.0
-- Date: 2025-01-01
-- Doctrine: /doctrine/ple/DOL_EIN_RESOLUTION.md
-- Barton ID: 01.04.02.04.22000
--
-- CANONICAL ERROR TABLE: shq.error_master
-- NOTE: shq_error_log is DEPRECATED and must not be referenced.
--
-- Purpose:
--   Add indexes to shq.error_master for efficient querying of DOL EIN Subhub errors.
--   Supports operational triage and failure analysis.
--
-- Failure Routing Doctrine:
--   All DOL Subhub failures are dual-written to:
--   1. dol.air_log (authoritative / audit)
--   2. shq.error_master (operational / triage)
--
-- Severity: HARD_FAIL (canonical value)
--
-- ═══════════════════════════════════════════════════════════════════════════

-- Index for DOL EIN errors by process_id
CREATE INDEX IF NOT EXISTS idx_error_master_dol_ein
ON shq.error_master (process_id, created_at DESC)
WHERE process_id = '01.04.02.04.22000';

COMMENT ON INDEX idx_error_master_dol_ein IS 'Index for DOL EIN Subhub errors (process_id=01.04.02.04.22000)';

-- Index for DOL EIN errors by agent_id
CREATE INDEX IF NOT EXISTS idx_error_master_dol_ein_agent
ON shq.error_master (agent_id, created_at DESC)
WHERE agent_id = 'DOL_EIN_SUBHUB';

COMMENT ON INDEX idx_error_master_dol_ein_agent IS 'Index for DOL EIN Subhub errors by agent_id';

-- ═══════════════════════════════════════════════════════════════════════════
-- VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════════════════════

-- Verify indexes created
-- SELECT indexname FROM pg_indexes WHERE tablename = 'error_master' AND schemaname = 'shq' AND indexname LIKE '%dol_ein%';
-- Expected: idx_error_master_dol_ein, idx_error_master_dol_ein_agent

-- Query DOL EIN failures (last 24 hours)
-- SELECT * FROM shq.error_master
-- WHERE process_id = '01.04.02.04.22000'
--   AND created_at >= NOW() - INTERVAL '24 hours'
-- ORDER BY created_at DESC;

-- ═══════════════════════════════════════════════════════════════════════════
-- DEPRECATION NOTICE
-- ═══════════════════════════════════════════════════════════════════════════
-- shq_error_log is DEPRECATED.
-- All new code MUST use shq.error_master.
-- Do not create indexes on shq_error_log.
-- ═══════════════════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════
