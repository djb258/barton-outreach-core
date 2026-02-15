-- ═══════════════════════════════════════════════════════════════════════════════
-- MIGRATION: Sitemap Discovery Table
-- ═══════════════════════════════════════════════════════════════════════════════
-- Date:    2026-02-08
-- Author:  Claude Code
-- Purpose: Fast Phase 1 sitemap scanner results — tracks which outreach
--          companies have a discoverable sitemap.xml (via direct probe or
--          robots.txt Sitemap: directive).
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS outreach.sitemap_discovery (
    outreach_id       UUID PRIMARY KEY REFERENCES outreach.outreach(outreach_id),
    domain            VARCHAR NOT NULL,
    sitemap_url       TEXT,              -- NULL = no sitemap found
    sitemap_source    VARCHAR(10),       -- 'direct' | 'robots' | NULL
    has_sitemap       BOOLEAN NOT NULL DEFAULT FALSE,
    discovered_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Phase 1b: domain reachability check (HEAD request to homepage)
    domain_reachable       BOOLEAN,            -- NULL = not checked, TRUE = responded, FALSE = dead
    http_status            SMALLINT,           -- HTTP status code from homepage HEAD request
    reachable_checked_at   TIMESTAMPTZ         -- When the reachability check ran
);

CREATE INDEX IF NOT EXISTS idx_sitemap_discovery_has
    ON outreach.sitemap_discovery(has_sitemap);

COMMENT ON TABLE outreach.sitemap_discovery IS 'Phase 1 fast sitemap scan results for all 95K outreach companies';
COMMENT ON COLUMN outreach.sitemap_discovery.sitemap_url IS 'First valid sitemap URL found (NULL if none)';
COMMENT ON COLUMN outreach.sitemap_discovery.sitemap_source IS 'How sitemap was found: direct (/sitemap.xml) or robots (robots.txt Sitemap: directive)';
COMMENT ON COLUMN outreach.sitemap_discovery.has_sitemap IS 'TRUE if a valid sitemap.xml was discovered';
