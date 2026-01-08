-- =============================================================================
-- P0 MIGRATION: BLOG PRODUCTION ENABLEMENT
-- =============================================================================
-- Migration ID: P0_005
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
-- Mode: PRODUCTION ENABLEMENT - Gates only, no data ingestion
--
-- PURPOSE:
--   Create production control infrastructure for Blog sub-hub.
--   Blog is COMPANY-LEVEL ONLY. No people data. No scoring. No execution.
--
-- SCOPE:
--   - Blog ingress control (kill switch)
--   - Source type enforcement
--   - Ready view for downstream
--   - Worker guard contract
--
-- HARD STOP:
--   This migration does NOT ingest data. It creates the gates.
--   Ingestion happens ONLY when operator flips enabled = TRUE.
--
-- ROLLBACK: See P0_005_blog_production_enablement_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- SECTION 1: BLOG INGRESS CONTROL (Kill Switch)
-- =============================================================================
-- Purpose: Gate all blog ingestion. Default OFF.
-- Operator flips to TRUE when ready for production.
-- =============================================================================

CREATE TABLE IF NOT EXISTS outreach.blog_ingress_control (
    control_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- The switch
    enabled BOOLEAN NOT NULL DEFAULT FALSE,

    -- Audit trail
    enabled_at TIMESTAMPTZ,
    enabled_by TEXT,
    disabled_at TIMESTAMPTZ,
    disabled_by TEXT,

    -- Rate limiting
    max_urls_per_hour INTEGER DEFAULT 100,
    max_urls_per_company INTEGER DEFAULT 10,

    -- TTL for re-checks
    url_ttl_days INTEGER DEFAULT 30,          -- Re-check URLs older than this
    content_ttl_days INTEGER DEFAULT 7,       -- Re-check content older than this

    -- Notes
    notes TEXT,

    -- Singleton enforcement
    singleton_key INTEGER DEFAULT 1 UNIQUE CHECK (singleton_key = 1),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert default OFF state
INSERT INTO outreach.blog_ingress_control (enabled, notes)
VALUES (FALSE, 'Initial state: Blog ingress DISABLED. Flip enabled=TRUE to start.')
ON CONFLICT (singleton_key) DO NOTHING;

-- Comment
COMMENT ON TABLE outreach.blog_ingress_control IS
'BLOG.CONTROL.001 | Blog ingress kill switch. SINGLETON table.
Default: enabled = FALSE (no ingestion until operator flips).
Check this BEFORE any blog URL fetch.
Rule: If enabled = FALSE, worker MUST halt immediately.';

COMMENT ON COLUMN outreach.blog_ingress_control.enabled IS
'The kill switch. FALSE = all blog ingestion halted. TRUE = proceed with guards.';

COMMENT ON COLUMN outreach.blog_ingress_control.max_urls_per_hour IS
'Rate limit: Maximum URLs to fetch per hour across all companies.';

COMMENT ON COLUMN outreach.blog_ingress_control.max_urls_per_company IS
'Rate limit: Maximum URLs to fetch per company per run.';

COMMENT ON COLUMN outreach.blog_ingress_control.url_ttl_days IS
'TTL: Re-check URLs not seen in this many days.';

COMMENT ON COLUMN outreach.blog_ingress_control.content_ttl_days IS
'TTL: Re-check content not updated in this many days.';

-- =============================================================================
-- SECTION 2: BLOG SOURCE TYPE ENUM
-- =============================================================================
-- Purpose: Enforce valid source types on outreach.blog table.
-- =============================================================================

DO $$ BEGIN
    CREATE TYPE outreach.blog_source_type AS ENUM (
        'website',          -- Company main website
        'blog',             -- Company blog
        'press',            -- Press releases
        'news',             -- News articles mentioning company
        'social',           -- DISALLOWED by doctrine (scope guard)
        'filing',           -- SEC/regulatory filings
        'careers'           -- Careers page
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

COMMENT ON TYPE outreach.blog_source_type IS
'BLOG.ENUM.001 | Valid blog source types.
Note: social is in enum but DISALLOWED by doctrine (DISALLOW_SOCIAL_METRICS = TRUE).
Attempting to insert social type will be blocked by trigger.';

-- =============================================================================
-- SECTION 3: ADD source_type_enum COLUMN TO outreach.blog
-- =============================================================================
-- Migrate from TEXT to ENUM for type safety.
-- =============================================================================

-- Add new enum column
ALTER TABLE outreach.blog
ADD COLUMN IF NOT EXISTS source_type_enum outreach.blog_source_type;

-- Backfill from existing source_type TEXT column
UPDATE outreach.blog
SET source_type_enum = source_type::outreach.blog_source_type
WHERE source_type_enum IS NULL
  AND source_type IS NOT NULL
  AND source_type IN ('website', 'blog', 'press', 'news', 'filing', 'careers');

-- Add comment
COMMENT ON COLUMN outreach.blog.source_type_enum IS
'BLOG.ENUM.FK | Typed source classification. Replaces source_type TEXT.
Valid: website, blog, press, news, filing, careers.
FORBIDDEN: social (blocked by doctrine guard).';

-- =============================================================================
-- SECTION 4: SCOPE GUARD (No Social Metrics)
-- =============================================================================
-- Purpose: Enforce DISALLOW_SOCIAL_METRICS doctrine.
-- Block any attempt to insert social source type.
-- =============================================================================

CREATE OR REPLACE FUNCTION outreach.guard_blog_no_social()
RETURNS TRIGGER AS $$
BEGIN
    -- Check source_type_enum
    IF NEW.source_type_enum = 'social' THEN
        RAISE EXCEPTION 'DOCTRINE VIOLATION: Blog sub-hub DISALLOWS social metrics. source_type_enum cannot be ''social''.';
    END IF;

    -- Check legacy source_type TEXT field
    IF NEW.source_type = 'social' THEN
        RAISE EXCEPTION 'DOCTRINE VIOLATION: Blog sub-hub DISALLOWS social metrics. source_type cannot be ''social''.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_blog_no_social
    BEFORE INSERT OR UPDATE ON outreach.blog
    FOR EACH ROW
    EXECUTE FUNCTION outreach.guard_blog_no_social();

COMMENT ON FUNCTION outreach.guard_blog_no_social IS
'DOCTRINE GUARD: Enforces DISALLOW_SOCIAL_METRICS = TRUE.
Blocks any attempt to insert social source type into blog table.';

-- =============================================================================
-- SECTION 5: v_blog_ready VIEW (Downstream Consumption)
-- =============================================================================
-- Purpose: Clean view for downstream systems.
-- Only returns blog records ready for consumption.
-- =============================================================================

CREATE OR REPLACE VIEW outreach.v_blog_ready AS
SELECT
    b.blog_id,
    b.outreach_id,
    o.sovereign_id,
    b.context_summary,
    COALESCE(b.source_type_enum::TEXT, b.source_type) AS source_type,
    b.source_url,
    b.context_timestamp,
    b.created_at,

    -- Source health (from history)
    bsh.status AS url_status,
    bsh.last_checked_at,
    bsh.http_status,
    bsh.checksum AS content_hash,

    -- Freshness
    CASE
        WHEN b.context_timestamp >= NOW() - INTERVAL '7 days' THEN 'FRESH'
        WHEN b.context_timestamp >= NOW() - INTERVAL '30 days' THEN 'RECENT'
        WHEN b.context_timestamp >= NOW() - INTERVAL '90 days' THEN 'AGING'
        ELSE 'STALE'
    END AS freshness_tier,

    -- Usability
    CASE
        WHEN b.context_summary IS NOT NULL
         AND LENGTH(b.context_summary) > 50
         AND bsh.status = 'active'
        THEN TRUE
        ELSE FALSE
    END AS is_usable

FROM outreach.blog b
INNER JOIN outreach.outreach o ON b.outreach_id = o.outreach_id
LEFT JOIN outreach.blog_source_history bsh
    ON b.outreach_id = bsh.outreach_id
    AND b.source_url = bsh.source_url
WHERE b.source_type_enum != 'social' OR b.source_type_enum IS NULL
ORDER BY b.context_timestamp DESC NULLS LAST;

COMMENT ON VIEW outreach.v_blog_ready IS
'BLOG.VIEW.001 | Blog records ready for downstream consumption.
Joins with source history for health status.
Excludes social (doctrine guard).
Use is_usable = TRUE for production queries.';

-- =============================================================================
-- SECTION 6: v_blog_ingestion_queue VIEW (Worker Queue)
-- =============================================================================
-- Purpose: What the worker should process next.
-- Respects history, TTL, and rate limits.
-- =============================================================================

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
        -- Check if we've seen this company's blog before
        bsh.source_url AS known_url,
        bsh.last_checked_at,
        bsh.status AS url_status,
        -- Calculate priority
        CASE
            WHEN bsh.source_url IS NULL THEN 1                    -- Never seen
            WHEN bsh.last_checked_at < NOW() - (SELECT url_ttl_days || ' days' FROM control)::INTERVAL THEN 2  -- TTL expired
            WHEN bsh.status = 'redirected' THEN 3                 -- Needs re-check
            ELSE 99                                               -- Skip
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

COMMENT ON VIEW outreach.v_blog_ingestion_queue IS
'BLOG.VIEW.002 | Blog ingestion work queue for worker.
Only returns candidates when ingress_control.enabled = TRUE.
Respects TTL and rate limits.
Worker pulls from this view, processes, and writes to blog + blog_source_history.';

-- =============================================================================
-- SECTION 7: HELPER FUNCTIONS
-- =============================================================================

-- Function: Check if blog ingress is enabled
CREATE OR REPLACE FUNCTION outreach.blog_ingress_enabled()
RETURNS BOOLEAN AS $$
DECLARE
    v_enabled BOOLEAN;
BEGIN
    SELECT enabled INTO v_enabled
    FROM outreach.blog_ingress_control
    LIMIT 1;

    RETURN COALESCE(v_enabled, FALSE);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.blog_ingress_enabled IS
'Check if blog ingress is enabled. Call at START of every worker run.
Returns FALSE if control row missing (fail safe).';

-- Function: Get blog ingress config
CREATE OR REPLACE FUNCTION outreach.get_blog_ingress_config()
RETURNS TABLE (
    enabled BOOLEAN,
    max_urls_per_hour INTEGER,
    max_urls_per_company INTEGER,
    url_ttl_days INTEGER,
    content_ttl_days INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        bic.enabled,
        bic.max_urls_per_hour,
        bic.max_urls_per_company,
        bic.url_ttl_days,
        bic.content_ttl_days
    FROM outreach.blog_ingress_control bic
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.get_blog_ingress_config IS
'Get full blog ingress configuration for worker initialization.';

-- Function: Should we fetch this URL?
CREATE OR REPLACE FUNCTION outreach.should_fetch_blog_url(
    p_outreach_id UUID,
    p_source_url TEXT
) RETURNS TABLE (
    should_fetch BOOLEAN,
    reason TEXT,
    last_checked TIMESTAMPTZ,
    current_status VARCHAR
) AS $$
DECLARE
    v_history RECORD;
    v_ttl INTEGER;
BEGIN
    -- Get TTL from control
    SELECT url_ttl_days INTO v_ttl FROM outreach.blog_ingress_control LIMIT 1;
    v_ttl := COALESCE(v_ttl, 30);

    -- Check history
    SELECT * INTO v_history
    FROM outreach.blog_source_history bsh
    WHERE bsh.outreach_id = p_outreach_id
      AND bsh.source_url = p_source_url;

    IF NOT FOUND THEN
        -- Never seen
        RETURN QUERY SELECT TRUE, 'NEW_URL', NULL::TIMESTAMPTZ, NULL::VARCHAR;
        RETURN;
    END IF;

    IF v_history.status = 'dead' THEN
        -- Don't fetch dead URLs
        RETURN QUERY SELECT FALSE, 'URL_DEAD', v_history.last_checked_at, v_history.status;
        RETURN;
    END IF;

    IF v_history.last_checked_at < NOW() - (v_ttl || ' days')::INTERVAL THEN
        -- TTL expired
        RETURN QUERY SELECT TRUE, 'TTL_EXPIRED', v_history.last_checked_at, v_history.status;
        RETURN;
    END IF;

    -- Recently checked
    RETURN QUERY SELECT FALSE, 'RECENTLY_CHECKED', v_history.last_checked_at, v_history.status;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION outreach.should_fetch_blog_url IS
'Determine if a blog URL should be fetched based on history and TTL.
Call BEFORE making any HTTP request.';

-- =============================================================================
-- SECTION 8: UPDATE TRIGGER FOR CONTROL TABLE
-- =============================================================================

DROP TRIGGER IF EXISTS set_updated_at ON outreach.blog_ingress_control;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON outreach.blog_ingress_control
    FOR EACH ROW EXECUTE FUNCTION outreach.trigger_set_updated_at();

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Check control table exists with default OFF:
-- SELECT enabled, notes FROM outreach.blog_ingress_control;
-- Expected: enabled = FALSE
--
-- 2. Check enum created:
-- SELECT enumlabel FROM pg_enum WHERE enumtypid = 'outreach.blog_source_type'::regtype;
-- Expected: website, blog, press, news, social, filing, careers
--
-- 3. Check views created:
-- SELECT viewname FROM pg_views WHERE schemaname = 'outreach' AND viewname LIKE '%blog%';
-- Expected: v_blog_ready, v_blog_ingestion_queue
--
-- 4. Check helper functions:
-- SELECT outreach.blog_ingress_enabled();
-- Expected: FALSE
--
-- 5. Test social guard:
-- INSERT INTO outreach.blog (outreach_id, source_type_enum, source_url)
-- VALUES ('some-uuid', 'social', 'https://twitter.com/test');
-- Expected: ERROR - DOCTRINE VIOLATION

-- =============================================================================
-- MIGRATION P0_005 COMPLETE
-- =============================================================================
-- CREATED:
--   - outreach.blog_ingress_control (kill switch, default OFF)
--   - outreach.blog_source_type ENUM
--   - outreach.blog.source_type_enum column
--   - outreach.guard_blog_no_social() function + trigger
--   - outreach.v_blog_ready view
--   - outreach.v_blog_ingestion_queue view
--   - outreach.blog_ingress_enabled() function
--   - outreach.get_blog_ingress_config() function
--   - outreach.should_fetch_blog_url() function
--
-- DEFAULT STATE:
--   Blog ingress is DISABLED. No data will be ingested until operator
--   explicitly enables it.
--
-- TO ENABLE (When Ready):
--   UPDATE outreach.blog_ingress_control
--   SET enabled = TRUE,
--       enabled_at = NOW(),
--       enabled_by = 'operator',
--       notes = 'Initial production enablement';
-- =============================================================================
