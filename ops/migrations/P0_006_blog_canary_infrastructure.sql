-- =============================================================================
-- P0 MIGRATION: BLOG CANARY INFRASTRUCTURE
-- =============================================================================
-- Migration ID: P0_006
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
-- Mode: CANARY ROLLOUT - Limited scope before global enablement
--
-- PURPOSE:
--   Add canary allowlist for phased Blog production rollout.
--   Global ingress stays OFF. Only canary outreach_ids are processed.
--
-- ROLLOUT STRATEGY:
--   1. Global enabled = FALSE (unchanged)
--   2. Canary allowlist with 10-25 outreach_ids
--   3. Worker checks: canary_enabled AND outreach_id IN canary
--   4. Run twice back-to-back — second run = zero fetches (history hits only)
--   5. Monitor 24 hours: history growth, error rate, no duplicates
--   6. If clean: remove canary filter, flip global ON
--
-- ROLLBACK: See P0_006_blog_canary_infrastructure_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- SECTION 1: CANARY ALLOWLIST TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.blog_canary_allowlist (
    canary_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The allowed outreach_id
    outreach_id UUID NOT NULL UNIQUE REFERENCES outreach.outreach(outreach_id),

    -- Why this company is in canary
    reason TEXT,

    -- Tracking
    added_at TIMESTAMPTZ DEFAULT NOW(),
    added_by TEXT DEFAULT 'system',

    -- Results
    first_run_at TIMESTAMPTZ,
    first_run_fetches INTEGER,
    second_run_at TIMESTAMPTZ,
    second_run_fetches INTEGER,  -- Should be 0 if idempotent

    -- Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'passed', 'failed', 'promoted'))
);

-- Index
CREATE INDEX IF NOT EXISTS idx_blog_canary_outreach
ON outreach.blog_canary_allowlist(outreach_id);

CREATE INDEX IF NOT EXISTS idx_blog_canary_status
ON outreach.blog_canary_allowlist(status);

-- Comment
COMMENT ON TABLE outreach.blog_canary_allowlist IS
'BLOG.CANARY.001 | Canary allowlist for phased Blog rollout.
Only outreach_ids in this table are processed when canary mode is active.
After 24h clean run, promote to global by removing canary filter.';

-- =============================================================================
-- SECTION 2: CANARY CONTROL FLAGS
-- =============================================================================

-- Add canary columns to ingress control
ALTER TABLE outreach.blog_ingress_control
ADD COLUMN IF NOT EXISTS canary_enabled BOOLEAN DEFAULT FALSE;

ALTER TABLE outreach.blog_ingress_control
ADD COLUMN IF NOT EXISTS canary_started_at TIMESTAMPTZ;

ALTER TABLE outreach.blog_ingress_control
ADD COLUMN IF NOT EXISTS canary_passed_at TIMESTAMPTZ;

ALTER TABLE outreach.blog_ingress_control
ADD COLUMN IF NOT EXISTS canary_notes TEXT;

-- Update default row
UPDATE outreach.blog_ingress_control
SET canary_enabled = FALSE,
    notes = 'Global ingress OFF. Canary mode available. Set canary_enabled=TRUE to start canary.'
WHERE singleton_key = 1;

-- Comments
COMMENT ON COLUMN outreach.blog_ingress_control.canary_enabled IS
'Canary mode flag. TRUE = only process outreach_ids in blog_canary_allowlist.
Global enabled stays FALSE during canary.';

COMMENT ON COLUMN outreach.blog_ingress_control.canary_started_at IS
'When canary mode was enabled.';

COMMENT ON COLUMN outreach.blog_ingress_control.canary_passed_at IS
'When canary passed validation (24h clean run).';

-- =============================================================================
-- SECTION 3: SEED CANARY WITH SAMPLE OUTREACH_IDS
-- =============================================================================
-- Select 25 outreach_ids that:
-- - Have company_target with domain
-- - Have not been processed for blog yet
-- - Are distributed across different companies

INSERT INTO outreach.blog_canary_allowlist (outreach_id, reason)
SELECT
    o.outreach_id,
    'Auto-selected canary: has domain, no existing blog records'
FROM outreach.outreach o
INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
WHERE ct.domain IS NOT NULL
  AND b.blog_id IS NULL
ORDER BY o.created_at DESC
LIMIT 25
ON CONFLICT (outreach_id) DO NOTHING;

-- =============================================================================
-- SECTION 4: UPDATED WORKER GUARD FUNCTION
-- =============================================================================

-- Replace the simple enabled check with canary-aware check
CREATE OR REPLACE FUNCTION outreach.blog_should_process(p_outreach_id UUID)
RETURNS TABLE (
    should_process BOOLEAN,
    mode VARCHAR,
    reason TEXT
) AS $$
DECLARE
    v_control RECORD;
    v_in_canary BOOLEAN;
BEGIN
    -- Get control settings
    SELECT * INTO v_control FROM outreach.blog_ingress_control LIMIT 1;

    -- Check if outreach_id is in canary
    SELECT EXISTS (
        SELECT 1 FROM outreach.blog_canary_allowlist
        WHERE outreach_id = p_outreach_id
          AND status IN ('pending', 'running')
    ) INTO v_in_canary;

    -- CASE 1: Global enabled = TRUE (post-canary, full production)
    IF v_control.enabled = TRUE THEN
        RETURN QUERY SELECT TRUE, 'GLOBAL'::VARCHAR, 'Global ingress enabled';
        RETURN;
    END IF;

    -- CASE 2: Canary enabled, outreach_id in allowlist
    IF v_control.canary_enabled = TRUE AND v_in_canary THEN
        RETURN QUERY SELECT TRUE, 'CANARY'::VARCHAR, 'Canary mode, outreach_id in allowlist';
        RETURN;
    END IF;

    -- CASE 3: Canary enabled, but outreach_id NOT in allowlist
    IF v_control.canary_enabled = TRUE AND NOT v_in_canary THEN
        RETURN QUERY SELECT FALSE, 'CANARY'::VARCHAR, 'Canary mode, outreach_id NOT in allowlist';
        RETURN;
    END IF;

    -- CASE 4: Everything disabled
    RETURN QUERY SELECT FALSE, 'DISABLED'::VARCHAR, 'Blog ingress disabled (global and canary)';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.blog_should_process IS
'Canary-aware ingress check. Returns TRUE only if:
1. Global enabled = TRUE, OR
2. Canary enabled = TRUE AND outreach_id in allowlist.
Call this INSTEAD of blog_ingress_enabled() during canary phase.';

-- =============================================================================
-- SECTION 5: UPDATED INGESTION QUEUE (Canary-Aware)
-- =============================================================================

CREATE OR REPLACE VIEW outreach.v_blog_ingestion_queue AS
WITH control AS (
    SELECT * FROM outreach.blog_ingress_control LIMIT 1
),
canary_ids AS (
    SELECT outreach_id FROM outreach.blog_canary_allowlist
    WHERE status IN ('pending', 'running')
),
candidates AS (
    SELECT
        o.outreach_id,
        o.sovereign_id,
        ct.domain,
        ct.company_name,
        bsh.source_url AS known_url,
        bsh.last_checked_at,
        bsh.status AS url_status,
        CASE
            WHEN bsh.source_url IS NULL THEN 1
            WHEN bsh.last_checked_at < NOW() - (SELECT url_ttl_days || ' days' FROM control)::INTERVAL THEN 2
            WHEN bsh.status = 'redirected' THEN 3
            ELSE 99
        END AS priority,
        -- Canary check
        CASE
            WHEN (SELECT enabled FROM control) = TRUE THEN TRUE
            WHEN (SELECT canary_enabled FROM control) = TRUE
                 AND o.outreach_id IN (SELECT outreach_id FROM canary_ids) THEN TRUE
            ELSE FALSE
        END AS is_allowed
    FROM outreach.outreach o
    INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.blog_source_history bsh ON o.outreach_id = bsh.outreach_id
    WHERE ct.domain IS NOT NULL
)
SELECT
    c.outreach_id,
    c.sovereign_id,
    c.domain,
    c.company_name,
    c.known_url,
    c.last_checked_at,
    c.url_status,
    c.priority,
    ctrl.enabled AS global_enabled,
    ctrl.canary_enabled,
    c.is_allowed,
    ctrl.max_urls_per_hour,
    ctrl.max_urls_per_company
FROM candidates c
CROSS JOIN control ctrl
WHERE c.priority < 99
  AND c.is_allowed = TRUE
ORDER BY c.priority ASC, c.last_checked_at ASC NULLS FIRST
LIMIT 100;

COMMENT ON VIEW outreach.v_blog_ingestion_queue IS
'BLOG.VIEW.002 | Canary-aware blog ingestion queue.
Only returns candidates that pass the canary/global gate.
During canary: only allowlist outreach_ids appear.
After global flip: all eligible outreach_ids appear.';

-- =============================================================================
-- SECTION 6: CANARY VALIDATION FUNCTIONS
-- =============================================================================

-- Function: Record canary run results
CREATE OR REPLACE FUNCTION outreach.record_canary_run(
    p_outreach_id UUID,
    p_fetches INTEGER
) RETURNS VOID AS $$
BEGIN
    UPDATE outreach.blog_canary_allowlist
    SET
        status = 'running',
        first_run_at = COALESCE(first_run_at, NOW()),
        first_run_fetches = COALESCE(first_run_fetches, p_fetches),
        second_run_at = CASE WHEN first_run_at IS NOT NULL THEN NOW() ELSE NULL END,
        second_run_fetches = CASE WHEN first_run_at IS NOT NULL THEN p_fetches ELSE NULL END
    WHERE outreach_id = p_outreach_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.record_canary_run IS
'Record canary run results. First call sets first_run_*, second call sets second_run_*.';

-- Function: Check canary idempotency
CREATE OR REPLACE FUNCTION outreach.check_canary_idempotency()
RETURNS TABLE (
    outreach_id UUID,
    first_run_fetches INTEGER,
    second_run_fetches INTEGER,
    is_idempotent BOOLEAN,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.outreach_id,
        c.first_run_fetches,
        c.second_run_fetches,
        (c.second_run_fetches = 0) AS is_idempotent,
        c.status
    FROM outreach.blog_canary_allowlist c
    WHERE c.first_run_at IS NOT NULL
      AND c.second_run_at IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.check_canary_idempotency IS
'Check if second canary run produced zero fetches (idempotent).
All rows should have second_run_fetches = 0.';

-- Function: Get canary health metrics
CREATE OR REPLACE FUNCTION outreach.get_canary_health()
RETURNS TABLE (
    metric VARCHAR,
    value BIGINT
) AS $$
BEGIN
    -- History growth
    RETURN QUERY
    SELECT 'history_records_24h'::VARCHAR,
           COUNT(*)::BIGINT
    FROM outreach.blog_source_history
    WHERE created_at >= NOW() - INTERVAL '24 hours';

    -- Error rate
    RETURN QUERY
    SELECT 'errors_24h'::VARCHAR,
           COUNT(*)::BIGINT
    FROM outreach.blog_errors
    WHERE created_at >= NOW() - INTERVAL '24 hours';

    -- Duplicate check (should be 0)
    RETURN QUERY
    SELECT 'duplicate_urls'::VARCHAR,
           (SELECT COUNT(*) - COUNT(DISTINCT (outreach_id, source_url))
            FROM outreach.blog_source_history)::BIGINT;

    -- Canary status counts
    RETURN QUERY
    SELECT 'canary_pending'::VARCHAR,
           COUNT(*)::BIGINT
    FROM outreach.blog_canary_allowlist WHERE status = 'pending';

    RETURN QUERY
    SELECT 'canary_running'::VARCHAR,
           COUNT(*)::BIGINT
    FROM outreach.blog_canary_allowlist WHERE status = 'running';

    RETURN QUERY
    SELECT 'canary_passed'::VARCHAR,
           COUNT(*)::BIGINT
    FROM outreach.blog_canary_allowlist WHERE status = 'passed';

    RETURN QUERY
    SELECT 'canary_failed'::VARCHAR,
           COUNT(*)::BIGINT
    FROM outreach.blog_canary_allowlist WHERE status = 'failed';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.get_canary_health IS
'Get canary health metrics. Watch: history growth, error rate, duplicate count (must be 0).';

-- =============================================================================
-- SECTION 7: CANARY PROMOTION FUNCTION
-- =============================================================================

-- Function: Mark canary as passed and promote to global
CREATE OR REPLACE FUNCTION outreach.promote_canary_to_global(p_operator TEXT)
RETURNS TEXT AS $$
DECLARE
    v_failed_count INTEGER;
    v_not_idempotent_count INTEGER;
    v_duplicate_count INTEGER;
BEGIN
    -- Check for failures
    SELECT COUNT(*) INTO v_failed_count
    FROM outreach.blog_canary_allowlist
    WHERE status = 'failed';

    IF v_failed_count > 0 THEN
        RETURN 'BLOCKED: ' || v_failed_count || ' canary entries have status=failed';
    END IF;

    -- Check idempotency
    SELECT COUNT(*) INTO v_not_idempotent_count
    FROM outreach.blog_canary_allowlist
    WHERE second_run_fetches IS NOT NULL
      AND second_run_fetches > 0;

    IF v_not_idempotent_count > 0 THEN
        RETURN 'BLOCKED: ' || v_not_idempotent_count || ' canary entries not idempotent (second_run_fetches > 0)';
    END IF;

    -- Check duplicates
    SELECT COUNT(*) - COUNT(DISTINCT (outreach_id, source_url))
    INTO v_duplicate_count
    FROM outreach.blog_source_history;

    IF v_duplicate_count > 0 THEN
        RETURN 'BLOCKED: ' || v_duplicate_count || ' duplicate rows in blog_source_history';
    END IF;

    -- All checks passed - promote
    UPDATE outreach.blog_canary_allowlist
    SET status = 'promoted'
    WHERE status IN ('pending', 'running', 'passed');

    UPDATE outreach.blog_ingress_control
    SET enabled = TRUE,
        enabled_at = NOW(),
        enabled_by = p_operator,
        canary_passed_at = NOW(),
        canary_notes = 'Canary passed. Promoted to global by ' || p_operator,
        notes = 'GLOBAL ENABLED after successful canary. Promoted by ' || p_operator || ' at ' || NOW()::TEXT
    WHERE singleton_key = 1;

    RETURN 'SUCCESS: Canary promoted to global. Blog ingress now enabled.';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.promote_canary_to_global IS
'Promote canary to global after validation.
Checks: no failures, idempotent (second_run=0), no duplicates.
On success: flips enabled=TRUE and marks canary as promoted.';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Check canary table created with seed data:
-- SELECT COUNT(*), status FROM outreach.blog_canary_allowlist GROUP BY status;
-- Expected: ~25 pending
--
-- 2. Check canary columns added to control:
-- SELECT canary_enabled, canary_started_at FROM outreach.blog_ingress_control;
-- Expected: canary_enabled = FALSE
--
-- 3. Check should_process function:
-- SELECT * FROM outreach.blog_should_process('some-outreach-id'::UUID);
-- Expected: should_process = FALSE, mode = 'DISABLED'
--
-- 4. Check queue is empty (nothing allowed yet):
-- SELECT COUNT(*) FROM outreach.v_blog_ingestion_queue;
-- Expected: 0 (canary not enabled)

-- =============================================================================
-- MIGRATION P0_006 COMPLETE
-- =============================================================================
-- CREATED:
--   - outreach.blog_canary_allowlist table (seeded with 25 outreach_ids)
--   - canary columns on blog_ingress_control
--   - outreach.blog_should_process() function (canary-aware)
--   - Updated v_blog_ingestion_queue view (canary-aware)
--   - outreach.record_canary_run() function
--   - outreach.check_canary_idempotency() function
--   - outreach.get_canary_health() function
--   - outreach.promote_canary_to_global() function
--
-- ROLLOUT COMMANDS:
--
-- STEP 1: Enable canary mode
--   UPDATE outreach.blog_ingress_control
--   SET canary_enabled = TRUE, canary_started_at = NOW();
--
-- STEP 2: Run worker twice, check idempotency
--   SELECT * FROM outreach.check_canary_idempotency();
--   -- All second_run_fetches should be 0
--
-- STEP 3: Monitor health for 24 hours
--   SELECT * FROM outreach.get_canary_health();
--   -- Watch: errors_24h, duplicate_urls (must be 0)
--
-- STEP 4: Promote to global
--   SELECT outreach.promote_canary_to_global('your_name');
-- =============================================================================
