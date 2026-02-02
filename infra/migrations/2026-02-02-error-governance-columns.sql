-- =============================================================================
-- ERROR GOVERNANCE COLUMNS MIGRATION
-- =============================================================================
--
-- PURPOSE:
--   Add error governance columns to all hub-owned error tables as specified
--   in ERROR_TTL_PARKING_POLICY.md
--
-- COLUMNS ADDED:
--   - disposition: ENUM (RETRY, PARKED, ARCHIVED, IGNORE, RESOLVED)
--   - retry_count: INTEGER (current retry attempts)
--   - max_retries: INTEGER (maximum allowed retries)
--   - archived_at: TIMESTAMPTZ (when error was archived)
--   - parked_at: TIMESTAMPTZ (when error was parked)
--   - escalation_level: INTEGER (0-3 escalation tier)
--   - ttl_tier: ENUM (SHORT, MEDIUM, LONG, INFINITE)
--
-- TABLES MODIFIED:
--   - outreach.dol_errors
--   - outreach.company_target_errors
--   - people.people_errors
--   - company.url_discovery_failures
--   - public.shq_error_log
--
-- AUTHORITY: ERROR_TTL_PARKING_POLICY.md v1.0.0
-- =============================================================================

-- =============================================================================
-- STEP 1: Create ENUM types for disposition and TTL tier
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'error_disposition') THEN
        CREATE TYPE error_disposition AS ENUM (
            'RETRY',      -- Error is retryable, queued for reprocessing
            'PARKED',     -- Error requires manual review
            'ARCHIVED',   -- Error is terminal, moved to archive
            'IGNORE',     -- Error is informational only
            'RESOLVED'    -- Error was successfully resolved
        );
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ttl_tier') THEN
        CREATE TYPE ttl_tier AS ENUM (
            'SHORT',      -- 7 days
            'MEDIUM',     -- 30 days
            'LONG',       -- 90 days
            'INFINITE'    -- Never expires
        );
    END IF;
END $$;

-- =============================================================================
-- STEP 2: Add columns to outreach.dol_errors
-- =============================================================================

ALTER TABLE outreach.dol_errors
    ADD COLUMN IF NOT EXISTS disposition error_disposition DEFAULT 'RETRY',
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 5,  -- DOL override: 5 (vs default 3)
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_by TEXT,
    ADD COLUMN IF NOT EXISTS park_reason TEXT,
    ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ttl_tier ttl_tier DEFAULT 'MEDIUM',
    ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS retry_exhausted BOOLEAN DEFAULT FALSE;

-- =============================================================================
-- STEP 3: Add columns to outreach.company_target_errors
-- =============================================================================

ALTER TABLE outreach.company_target_errors
    ADD COLUMN IF NOT EXISTS disposition error_disposition DEFAULT 'RETRY',
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_by TEXT,
    ADD COLUMN IF NOT EXISTS park_reason TEXT,
    ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ttl_tier ttl_tier DEFAULT 'MEDIUM',
    ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS retry_exhausted BOOLEAN DEFAULT FALSE;

-- =============================================================================
-- STEP 4: Add columns to people.people_errors
-- =============================================================================

ALTER TABLE people.people_errors
    ADD COLUMN IF NOT EXISTS disposition error_disposition DEFAULT 'RETRY',
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_by TEXT,
    ADD COLUMN IF NOT EXISTS park_reason TEXT,
    ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ttl_tier ttl_tier DEFAULT 'MEDIUM',
    ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS retry_exhausted BOOLEAN DEFAULT FALSE;

-- =============================================================================
-- STEP 5: Add columns to company.url_discovery_failures
-- =============================================================================

ALTER TABLE company.url_discovery_failures
    ADD COLUMN IF NOT EXISTS disposition error_disposition DEFAULT 'ARCHIVED',  -- STRUCTURAL errors default to ARCHIVED
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 1,  -- STRUCTURAL: only 1 retry
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS parked_by TEXT,
    ADD COLUMN IF NOT EXISTS park_reason TEXT,
    ADD COLUMN IF NOT EXISTS escalation_level INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS escalated_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ttl_tier ttl_tier DEFAULT 'LONG',  -- 90 days for STRUCTURAL
    ADD COLUMN IF NOT EXISTS last_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS retry_exhausted BOOLEAN DEFAULT FALSE;

-- =============================================================================
-- STEP 6: Add columns to shq.error_master (global error table)
-- =============================================================================

ALTER TABLE shq.error_master
    ADD COLUMN IF NOT EXISTS disposition error_disposition DEFAULT 'IGNORE',
    ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS ttl_tier ttl_tier DEFAULT 'LONG';  -- 90 days for global log

-- =============================================================================
-- STEP 7: Create indexes for governance queries
-- =============================================================================

-- Index for finding errors by disposition (for retry processing, parking review)
CREATE INDEX IF NOT EXISTS idx_dol_errors_disposition ON outreach.dol_errors (disposition) WHERE disposition IN ('RETRY', 'PARKED');
CREATE INDEX IF NOT EXISTS idx_company_target_errors_disposition ON outreach.company_target_errors (disposition) WHERE disposition IN ('RETRY', 'PARKED');
CREATE INDEX IF NOT EXISTS idx_people_errors_disposition ON people.people_errors (disposition) WHERE disposition IN ('RETRY', 'PARKED');
CREATE INDEX IF NOT EXISTS idx_url_discovery_failures_disposition ON company.url_discovery_failures (disposition) WHERE disposition IN ('RETRY', 'PARKED');

-- Index for finding errors to archive (TTL expiration check)
CREATE INDEX IF NOT EXISTS idx_dol_errors_ttl ON outreach.dol_errors (created_at, ttl_tier) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_company_target_errors_ttl ON outreach.company_target_errors (created_at, ttl_tier) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_people_errors_ttl ON people.people_errors (created_at, ttl_tier) WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_url_discovery_failures_ttl ON company.url_discovery_failures (created_at, ttl_tier) WHERE archived_at IS NULL;

-- Index for finding errors by escalation level (for escalation queue)
CREATE INDEX IF NOT EXISTS idx_dol_errors_escalation ON outreach.dol_errors (escalation_level) WHERE disposition = 'PARKED' AND escalation_level > 0;
CREATE INDEX IF NOT EXISTS idx_company_target_errors_escalation ON outreach.company_target_errors (escalation_level) WHERE disposition = 'PARKED' AND escalation_level > 0;
CREATE INDEX IF NOT EXISTS idx_people_errors_escalation ON people.people_errors (escalation_level) WHERE disposition = 'PARKED' AND escalation_level > 0;

-- =============================================================================
-- STEP 8: Add check constraints
-- =============================================================================

-- Escalation level must be 0-3
ALTER TABLE outreach.dol_errors ADD CONSTRAINT chk_dol_errors_escalation CHECK (escalation_level >= 0 AND escalation_level <= 3);
ALTER TABLE outreach.company_target_errors ADD CONSTRAINT chk_company_target_errors_escalation CHECK (escalation_level >= 0 AND escalation_level <= 3);
ALTER TABLE people.people_errors ADD CONSTRAINT chk_people_errors_escalation CHECK (escalation_level >= 0 AND escalation_level <= 3);

-- Max retries must be positive
ALTER TABLE outreach.dol_errors ADD CONSTRAINT chk_dol_errors_max_retries CHECK (max_retries > 0);
ALTER TABLE outreach.company_target_errors ADD CONSTRAINT chk_company_target_errors_max_retries CHECK (max_retries > 0);
ALTER TABLE people.people_errors ADD CONSTRAINT chk_people_errors_max_retries CHECK (max_retries > 0);
ALTER TABLE company.url_discovery_failures ADD CONSTRAINT chk_url_discovery_failures_max_retries CHECK (max_retries > 0);

-- =============================================================================
-- STEP 9: Comments for documentation
-- =============================================================================

COMMENT ON COLUMN outreach.dol_errors.disposition IS 'Error disposition: RETRY (retryable), PARKED (manual review), ARCHIVED (terminal), IGNORE (informational), RESOLVED (fixed)';
COMMENT ON COLUMN outreach.dol_errors.retry_count IS 'Current number of retry attempts';
COMMENT ON COLUMN outreach.dol_errors.max_retries IS 'Maximum allowed retry attempts. DOL uses 5 (override from default 3)';
COMMENT ON COLUMN outreach.dol_errors.archived_at IS 'Timestamp when error was moved to archive';
COMMENT ON COLUMN outreach.dol_errors.parked_at IS 'Timestamp when error was parked for manual review';
COMMENT ON COLUMN outreach.dol_errors.parked_by IS 'System or user that parked the error';
COMMENT ON COLUMN outreach.dol_errors.park_reason IS 'Reason for parking: MAX_RETRIES_EXCEEDED, NON_RETRYABLE_ERROR, etc.';
COMMENT ON COLUMN outreach.dol_errors.escalation_level IS 'Escalation tier: 0=System, 1=Hub Team, 2=Hub Lead, 3=Platform Team';
COMMENT ON COLUMN outreach.dol_errors.escalated_at IS 'Timestamp of last escalation';
COMMENT ON COLUMN outreach.dol_errors.ttl_tier IS 'Time-to-live tier: SHORT (7d), MEDIUM (30d), LONG (90d), INFINITE';
COMMENT ON COLUMN outreach.dol_errors.last_retry_at IS 'Timestamp of last retry attempt';
COMMENT ON COLUMN outreach.dol_errors.next_retry_at IS 'Scheduled time for next retry';
COMMENT ON COLUMN outreach.dol_errors.retry_exhausted IS 'True if retry_count >= max_retries';

-- Apply same comments to other tables
COMMENT ON COLUMN outreach.company_target_errors.disposition IS 'Error disposition: RETRY (retryable), PARKED (manual review), ARCHIVED (terminal), IGNORE (informational), RESOLVED (fixed)';
COMMENT ON COLUMN outreach.company_target_errors.ttl_tier IS 'Time-to-live tier: SHORT (7d), MEDIUM (30d), LONG (90d), INFINITE';

COMMENT ON COLUMN people.people_errors.disposition IS 'Error disposition: RETRY (retryable), PARKED (manual review), ARCHIVED (terminal), IGNORE (informational), RESOLVED (fixed)';
COMMENT ON COLUMN people.people_errors.ttl_tier IS 'Time-to-live tier: SHORT (7d), MEDIUM (30d), LONG (90d), INFINITE';

COMMENT ON COLUMN company.url_discovery_failures.disposition IS 'Error disposition: defaults to ARCHIVE for STRUCTURAL errors';
COMMENT ON COLUMN company.url_discovery_failures.ttl_tier IS 'Time-to-live tier: LONG (90d) for STRUCTURAL errors';

-- =============================================================================
-- USAGE NOTES
-- =============================================================================
--
-- After running this migration:
--
-- 1. BACKFILL DISPOSITION:
--    UPDATE outreach.dol_errors SET disposition = 'RETRY' WHERE resolved_at IS NULL;
--    UPDATE outreach.dol_errors SET disposition = 'RESOLVED' WHERE resolved_at IS NOT NULL;
--
-- 2. SET TTL TIER BASED ON ERROR TYPE:
--    -- Transient errors (rate limit, timeout) -> SHORT
--    UPDATE outreach.dol_errors SET ttl_tier = 'SHORT' WHERE failure_code IN ('RATE_LIMIT', 'TIMEOUT', 'API_ERROR');
--    -- Operational errors (validation, missing data) -> MEDIUM
--    UPDATE outreach.dol_errors SET ttl_tier = 'MEDIUM' WHERE failure_code IN ('VALIDATION_ERROR', 'MISSING_DATA');
--    -- Structural errors (bad data, schema) -> LONG
--    UPDATE outreach.dol_errors SET ttl_tier = 'LONG' WHERE failure_code IN ('BAD_DATA', 'SCHEMA_MISMATCH');
--
-- 3. MARK EXHAUSTED RETRIES:
--    UPDATE outreach.dol_errors SET retry_exhausted = TRUE, disposition = 'PARKED', park_reason = 'MAX_RETRIES_EXCEEDED'
--    WHERE retry_count >= max_retries AND disposition = 'RETRY';
--
-- =============================================================================
