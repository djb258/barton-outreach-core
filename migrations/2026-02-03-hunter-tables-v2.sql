-- Hunter.io Tables v2 - Full Data Capture
-- Captures ALL fields from Hunter.io CSV exports including all 30 source URLs
--
-- Run with: doppler run -- psql -f neon/migrations/2026-02-03-hunter-tables-v2.sql

BEGIN;

-- ============================================================================
-- HUNTER COMPANY TABLE (Company-level data)
-- ============================================================================

DROP TABLE IF EXISTS enrichment.hunter_company_v2 CASCADE;

CREATE TABLE enrichment.hunter_company_v2 (
    -- Primary Key
    id                      SERIAL PRIMARY KEY,

    -- Domain (unique identifier from Hunter)
    domain                  VARCHAR(255) NOT NULL UNIQUE,
    domain_name             VARCHAR(255),              -- Hunter's "Domain name" field

    -- Company Identity
    organization            VARCHAR(500),              -- Company name
    company_type            VARCHAR(100),              -- "privately held", "public company", "self owned"
    industry                VARCHAR(255),              -- Raw industry from Hunter

    -- Headcount
    headcount               VARCHAR(50),               -- "51-200", "201-500", etc.
    headcount_min           INTEGER,                   -- Parsed min
    headcount_max           INTEGER,                   -- Parsed max

    -- Location
    country                 VARCHAR(10),               -- ISO country code
    state                   VARCHAR(50),               -- State/province
    city                    VARCHAR(100),              -- City
    postal_code             VARCHAR(20),               -- ZIP/postal
    street                  VARCHAR(255),              -- Street address

    -- Email Pattern (critical for email generation)
    email_pattern           VARCHAR(100),              -- "{first}.{last}", "{f}{last}", etc.

    -- Linking to our spine
    company_unique_id       VARCHAR(50),               -- Link to company_target
    outreach_id             UUID,                      -- Link to outreach.outreach

    -- Audit
    source_file             VARCHAR(255),              -- Which CSV file this came from
    enriched_at             TIMESTAMPTZ,               -- When Hunter enriched this
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_hunter_company_v2_domain ON enrichment.hunter_company_v2(domain);
CREATE INDEX idx_hunter_company_v2_outreach_id ON enrichment.hunter_company_v2(outreach_id);
CREATE INDEX idx_hunter_company_v2_state ON enrichment.hunter_company_v2(state);
CREATE INDEX idx_hunter_company_v2_industry ON enrichment.hunter_company_v2(industry);

-- ============================================================================
-- HUNTER CONTACT TABLE (Contact-level data - ALL fields)
-- ============================================================================

DROP TABLE IF EXISTS enrichment.hunter_contact_v2 CASCADE;

CREATE TABLE enrichment.hunter_contact_v2 (
    -- Primary Key
    id                      SERIAL PRIMARY KEY,

    -- Domain (join key to company)
    domain                  VARCHAR(255) NOT NULL,

    -- Email (verified by Hunter)
    email                   VARCHAR(255),
    email_type              VARCHAR(20),               -- "personal" or "generic"
    confidence_score        INTEGER,                   -- 0-100
    num_sources             INTEGER,                   -- Number of sources Hunter found

    -- Person Identity (PII)
    first_name              VARCHAR(100),
    last_name               VARCHAR(100),
    full_name               VARCHAR(200) GENERATED ALWAYS AS (
                                TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
                            ) STORED,

    -- Job Information
    department              VARCHAR(100),              -- Raw department
    job_title               VARCHAR(255),              -- Raw job title
    position_raw            VARCHAR(500),              -- Full position description

    -- Social & Contact
    twitter_handle          VARCHAR(100),
    linkedin_url            VARCHAR(500),
    phone_number            VARCHAR(50),

    -- All 30 Source URLs (where Hunter found this contact)
    source_1                TEXT,
    source_2                TEXT,
    source_3                TEXT,
    source_4                TEXT,
    source_5                TEXT,
    source_6                TEXT,
    source_7                TEXT,
    source_8                TEXT,
    source_9                TEXT,
    source_10               TEXT,
    source_11               TEXT,
    source_12               TEXT,
    source_13               TEXT,
    source_14               TEXT,
    source_15               TEXT,
    source_16               TEXT,
    source_17               TEXT,
    source_18               TEXT,
    source_19               TEXT,
    source_20               TEXT,
    source_21               TEXT,
    source_22               TEXT,
    source_23               TEXT,
    source_24               TEXT,
    source_25               TEXT,
    source_26               TEXT,
    source_27               TEXT,
    source_28               TEXT,
    source_29               TEXT,
    source_30               TEXT,

    -- Linking to our spine
    company_unique_id       VARCHAR(50),               -- Link to company_target
    outreach_id             UUID,                      -- Link to outreach.outreach
    people_id               UUID,                      -- Link to people.people_master

    -- Audit
    source_file             VARCHAR(255),              -- Which CSV file this came from
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint on domain + email
    CONSTRAINT uq_hunter_contact_v2_domain_email UNIQUE (domain, email)
);

CREATE INDEX idx_hunter_contact_v2_domain ON enrichment.hunter_contact_v2(domain);
CREATE INDEX idx_hunter_contact_v2_email ON enrichment.hunter_contact_v2(email);
CREATE INDEX idx_hunter_contact_v2_outreach_id ON enrichment.hunter_contact_v2(outreach_id);
CREATE INDEX idx_hunter_contact_v2_confidence ON enrichment.hunter_contact_v2(confidence_score);
CREATE INDEX idx_hunter_contact_v2_email_type ON enrichment.hunter_contact_v2(email_type);
CREATE INDEX idx_hunter_contact_v2_linkedin ON enrichment.hunter_contact_v2(linkedin_url) WHERE linkedin_url IS NOT NULL;

-- ============================================================================
-- HUNTER SOURCES VIEW (Normalized view for blog sub-hub)
-- Unpivots all 30 source columns into rows for easy processing
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
FROM enrichment.hunter_contact_v2 c
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
-- HUNTER SOURCES BY TYPE VIEW (Categorized sources)
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
-- COMPANY SOURCES AGGREGATE VIEW
-- All unique source URLs per company (for company-level scraping)
-- ============================================================================

CREATE OR REPLACE VIEW enrichment.v_hunter_company_sources AS
SELECT DISTINCT
    c.domain,
    hc.organization,
    hc.outreach_id,
    s.source_url,
    s.source_type
FROM enrichment.v_hunter_sources_by_type s
JOIN enrichment.hunter_contact_v2 c ON s.contact_id = c.id
LEFT JOIN enrichment.hunter_company_v2 hc ON c.domain = hc.domain
WHERE s.source_type NOT IN ('google_search')  -- Exclude Google search URLs
ORDER BY c.domain, s.source_type;

COMMENT ON VIEW enrichment.v_hunter_company_sources IS
'Unique source URLs per company domain for blog sub-hub scraping queue.';

-- ============================================================================
-- UPDATED_AT TRIGGER
-- ============================================================================

CREATE OR REPLACE FUNCTION enrichment.update_hunter_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_hunter_company_v2_updated ON enrichment.hunter_company_v2;
CREATE TRIGGER trg_hunter_company_v2_updated
    BEFORE UPDATE ON enrichment.hunter_company_v2
    FOR EACH ROW EXECUTE FUNCTION enrichment.update_hunter_timestamp();

DROP TRIGGER IF EXISTS trg_hunter_contact_v2_updated ON enrichment.hunter_contact_v2;
CREATE TRIGGER trg_hunter_contact_v2_updated
    BEFORE UPDATE ON enrichment.hunter_contact_v2
    FOR EACH ROW EXECUTE FUNCTION enrichment.update_hunter_timestamp();

COMMIT;

-- ============================================================================
-- SUMMARY
-- ============================================================================
--
-- Tables created:
--   enrichment.hunter_company_v2  - Company-level data with email pattern
--   enrichment.hunter_contact_v2  - Contact-level data with all 30 source URLs
--
-- Views created:
--   enrichment.v_hunter_contact_sources   - Unpivoted sources (one row per source)
--   enrichment.v_hunter_sources_by_type   - Sources categorized by type
--   enrichment.v_hunter_company_sources   - Unique sources per company
--
-- Blog sub-hub can query:
--   SELECT * FROM enrichment.v_hunter_sources_by_type
--   WHERE source_type = 'press_release' AND outreach_id IS NOT NULL;
--
