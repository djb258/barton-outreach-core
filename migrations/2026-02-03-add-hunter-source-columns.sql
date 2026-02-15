-- Add Source URL columns to existing Hunter tables
-- Captures all 30 source URLs from Hunter.io
--
-- Run with: doppler run -- python to execute

BEGIN;

-- ============================================================================
-- ADD SOURCE COLUMNS TO hunter_contact (all 30 sources)
-- ============================================================================

ALTER TABLE enrichment.hunter_contact
    ADD COLUMN IF NOT EXISTS source_1 TEXT,
    ADD COLUMN IF NOT EXISTS source_2 TEXT,
    ADD COLUMN IF NOT EXISTS source_3 TEXT,
    ADD COLUMN IF NOT EXISTS source_4 TEXT,
    ADD COLUMN IF NOT EXISTS source_5 TEXT,
    ADD COLUMN IF NOT EXISTS source_6 TEXT,
    ADD COLUMN IF NOT EXISTS source_7 TEXT,
    ADD COLUMN IF NOT EXISTS source_8 TEXT,
    ADD COLUMN IF NOT EXISTS source_9 TEXT,
    ADD COLUMN IF NOT EXISTS source_10 TEXT,
    ADD COLUMN IF NOT EXISTS source_11 TEXT,
    ADD COLUMN IF NOT EXISTS source_12 TEXT,
    ADD COLUMN IF NOT EXISTS source_13 TEXT,
    ADD COLUMN IF NOT EXISTS source_14 TEXT,
    ADD COLUMN IF NOT EXISTS source_15 TEXT,
    ADD COLUMN IF NOT EXISTS source_16 TEXT,
    ADD COLUMN IF NOT EXISTS source_17 TEXT,
    ADD COLUMN IF NOT EXISTS source_18 TEXT,
    ADD COLUMN IF NOT EXISTS source_19 TEXT,
    ADD COLUMN IF NOT EXISTS source_20 TEXT,
    ADD COLUMN IF NOT EXISTS source_21 TEXT,
    ADD COLUMN IF NOT EXISTS source_22 TEXT,
    ADD COLUMN IF NOT EXISTS source_23 TEXT,
    ADD COLUMN IF NOT EXISTS source_24 TEXT,
    ADD COLUMN IF NOT EXISTS source_25 TEXT,
    ADD COLUMN IF NOT EXISTS source_26 TEXT,
    ADD COLUMN IF NOT EXISTS source_27 TEXT,
    ADD COLUMN IF NOT EXISTS source_28 TEXT,
    ADD COLUMN IF NOT EXISTS source_29 TEXT,
    ADD COLUMN IF NOT EXISTS source_30 TEXT;

-- Add source_file to track which CSV the data came from
ALTER TABLE enrichment.hunter_contact
    ADD COLUMN IF NOT EXISTS source_file VARCHAR(255);

ALTER TABLE enrichment.hunter_company
    ADD COLUMN IF NOT EXISTS source_file VARCHAR(255);

-- ============================================================================
-- CREATE UNPIVOTED SOURCES VIEW (for blog sub-hub)
-- ============================================================================

CREATE OR REPLACE VIEW enrichment.v_hunter_contact_sources AS
SELECT
    c.id AS contact_id,
    c.domain,
    c.email,
    c.first_name,
    c.last_name,
    c.job_title,
    c.linkedin_url,
    c.outreach_id,
    s.source_order,
    s.source_url
FROM enrichment.hunter_contact c
CROSS JOIN LATERAL (
    VALUES
        (1, c.source_1), (2, c.source_2), (3, c.source_3), (4, c.source_4), (5, c.source_5),
        (6, c.source_6), (7, c.source_7), (8, c.source_8), (9, c.source_9), (10, c.source_10),
        (11, c.source_11), (12, c.source_12), (13, c.source_13), (14, c.source_14), (15, c.source_15),
        (16, c.source_16), (17, c.source_17), (18, c.source_18), (19, c.source_19), (20, c.source_20),
        (21, c.source_21), (22, c.source_22), (23, c.source_23), (24, c.source_24), (25, c.source_25),
        (26, c.source_26), (27, c.source_27), (28, c.source_28), (29, c.source_29), (30, c.source_30)
) AS s(source_order, source_url)
WHERE s.source_url IS NOT NULL AND s.source_url != '';

COMMENT ON VIEW enrichment.v_hunter_contact_sources IS
'Unpivoted view of all Hunter source URLs for blog sub-hub processing. Each row is one source URL for one contact.';

-- ============================================================================
-- CREATE SOURCES BY TYPE VIEW (categorized)
-- ============================================================================

CREATE OR REPLACE VIEW enrichment.v_hunter_sources_by_type AS
SELECT
    contact_id,
    domain,
    email,
    first_name,
    last_name,
    job_title,
    linkedin_url,
    outreach_id,
    source_order,
    source_url,
    CASE
        WHEN source_url LIKE '%linkedin.com%' THEN 'linkedin'
        WHEN source_url LIKE '%google.com/search%' THEN 'google_search'
        WHEN source_url LIKE '%prnewswire.com%' OR source_url LIKE '%businesswire.com%' THEN 'press_release'
        WHEN source_url LIKE '%sbir.gov%' THEN 'government'
        WHEN source_url LIKE '%.pdf%' THEN 'pdf'
        WHEN source_url LIKE '%/about%' OR source_url LIKE '%/team%' OR source_url LIKE '%/leadership%' THEN 'company_page'
        WHEN source_url LIKE '%twitter.com%' OR source_url LIKE '%x.com%' THEN 'twitter'
        WHEN source_url LIKE '%facebook.com%' THEN 'facebook'
        ELSE 'other'
    END AS source_type
FROM enrichment.v_hunter_contact_sources;

COMMENT ON VIEW enrichment.v_hunter_sources_by_type IS
'Hunter sources categorized by type for targeted blog sub-hub processing.';

-- ============================================================================
-- CREATE COMPANY SOURCES VIEW (unique sources per domain)
-- ============================================================================

CREATE OR REPLACE VIEW enrichment.v_hunter_company_sources AS
SELECT DISTINCT
    c.domain,
    hc.organization,
    hc.outreach_id,
    s.source_url,
    s.source_type
FROM enrichment.v_hunter_sources_by_type s
JOIN enrichment.hunter_contact c ON s.contact_id = c.id
LEFT JOIN enrichment.hunter_company hc ON c.domain = hc.domain
WHERE s.source_type NOT IN ('google_search')
ORDER BY c.domain, s.source_type;

COMMENT ON VIEW enrichment.v_hunter_company_sources IS
'Unique source URLs per company domain for blog sub-hub scraping queue.';

-- ============================================================================
-- DROP V2 TABLES (not needed - using enhanced existing tables)
-- ============================================================================

DROP TABLE IF EXISTS enrichment.hunter_contact_v2 CASCADE;
DROP TABLE IF EXISTS enrichment.hunter_company_v2 CASCADE;

COMMIT;
