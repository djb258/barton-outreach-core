-- =============================================================================
-- P0 ROLLBACK: BLOG CANARY INFRASTRUCTURE
-- =============================================================================
-- Migration ID: P0_006
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
--
-- PURPOSE:
--   Rollback P0_006_blog_canary_infrastructure.sql
--   Removes canary infrastructure, reverts to simple enabled check
--
-- WARNING: If blog is in production, this will break canary-aware workers.
-- =============================================================================

-- Drop functions
DROP FUNCTION IF EXISTS outreach.promote_canary_to_global(TEXT);
DROP FUNCTION IF EXISTS outreach.get_canary_health();
DROP FUNCTION IF EXISTS outreach.check_canary_idempotency();
DROP FUNCTION IF EXISTS outreach.record_canary_run(UUID, INTEGER);
DROP FUNCTION IF EXISTS outreach.blog_should_process(UUID);

-- Drop updated view (restore original in P0_005)
DROP VIEW IF EXISTS outreach.v_blog_ingestion_queue;

-- Recreate original view from P0_005
CREATE OR REPLACE VIEW outreach.v_blog_ingestion_queue AS
WITH control AS (
    SELECT * FROM outreach.blog_ingress_control LIMIT 1
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
        END AS priority
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
    ctrl.enabled AS ingress_enabled,
    ctrl.max_urls_per_hour,
    ctrl.max_urls_per_company
FROM candidates c
CROSS JOIN control ctrl
WHERE c.priority < 99
  AND ctrl.enabled = TRUE
ORDER BY c.priority ASC, c.last_checked_at ASC NULLS FIRST
LIMIT 100;

-- Remove canary columns from control table
ALTER TABLE outreach.blog_ingress_control
DROP COLUMN IF EXISTS canary_enabled;

ALTER TABLE outreach.blog_ingress_control
DROP COLUMN IF EXISTS canary_started_at;

ALTER TABLE outreach.blog_ingress_control
DROP COLUMN IF EXISTS canary_passed_at;

ALTER TABLE outreach.blog_ingress_control
DROP COLUMN IF EXISTS canary_notes;

-- Drop canary allowlist table
DROP INDEX IF EXISTS outreach.idx_blog_canary_outreach;
DROP INDEX IF EXISTS outreach.idx_blog_canary_status;
DROP TABLE IF EXISTS outreach.blog_canary_allowlist;

-- =============================================================================
-- ROLLBACK P0_006 COMPLETE
-- =============================================================================
