-- =============================================================================
-- MIGRATION: Vendor Schema Creation
-- Date: 2026-02-20
-- Phase: Legacy Collapse Playbook — Phase 3 (Migrate)
-- Purpose: Create vendor schema + 8 vendor tables for 4-Tier Funnel
-- =============================================================================

-- Create vendor schema
CREATE SCHEMA IF NOT EXISTS vendor;

-- =============================================================================
-- 1. vendor.ct — Company-level external vendor data
--    Sources: enrichment.hunter_company, company.company_master,
--             intake.company_raw_intake, intake.company_raw_wv
-- =============================================================================

CREATE TABLE vendor.ct (
    vendor_row_id       BIGSERIAL PRIMARY KEY,
    source_table        TEXT NOT NULL,          -- e.g. 'enrichment.hunter_company'
    source_row_id       TEXT,                   -- original PK cast to text
    migrated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    domain              TEXT,
    company_name        TEXT,
    company_unique_id   TEXT,
    outreach_id         UUID,

    -- Geography
    street              TEXT,
    city                TEXT,
    state               TEXT,
    state_abbrev        TEXT,
    postal_code         TEXT,
    country             TEXT,
    address_full        TEXT,                   -- location_full / company_address

    -- Company profile
    industry            TEXT,
    industry_normalized TEXT,
    employee_count      INTEGER,
    headcount_raw       TEXT,                   -- raw string from Hunter
    headcount_min       INTEGER,
    headcount_max       INTEGER,
    company_type        TEXT,
    company_phone       TEXT,
    founded_year        INTEGER,
    sic_codes           TEXT,
    description         TEXT,
    keywords            TEXT[],
    tags                TEXT[],

    -- Web/Social
    website_url         TEXT,
    linkedin_url        TEXT,
    facebook_url        TEXT,
    twitter_url         TEXT,

    -- Email pattern
    email_pattern       TEXT,
    email_pattern_confidence INTEGER,
    email_pattern_source TEXT,
    email_pattern_verified_at TIMESTAMP,

    -- Enrichment metadata
    data_quality_score  NUMERIC,
    source_system       TEXT,
    source_record_id    TEXT,
    source_file         TEXT,
    import_batch_id     TEXT,
    enriched_at         TIMESTAMP,
    ein                 TEXT,
    duns                TEXT,
    cage_code           TEXT,

    -- Validation
    validated           BOOLEAN,
    validation_notes    TEXT,
    validation_reasons  TEXT,
    validated_at        TIMESTAMPTZ,
    validated_by        TEXT,
    enrichment_attempt  INTEGER,
    chronic_bad         BOOLEAN,
    last_enriched_at    TIMESTAMP,
    enriched_by         TEXT,

    -- Intake-specific
    company_name_for_emails TEXT,
    b2_file_path        TEXT,
    b2_uploaded_at      TIMESTAMP,
    apollo_id           TEXT,
    last_hash           TEXT,
    garage_bay          TEXT,
    promoted_from_intake_at TIMESTAMPTZ,
    promotion_audit_log_id INTEGER,

    -- Timestamps
    original_created_at TIMESTAMPTZ,
    original_updated_at TIMESTAMPTZ
);

CREATE INDEX idx_vendor_ct_source ON vendor.ct (source_table);
CREATE INDEX idx_vendor_ct_domain ON vendor.ct (domain);
CREATE INDEX idx_vendor_ct_outreach_id ON vendor.ct (outreach_id) WHERE outreach_id IS NOT NULL;

COMMENT ON TABLE vendor.ct IS 'Tier-1 vendor staging: company data from Hunter, Clay, CSV imports. Append-only.';

-- =============================================================================
-- 2. vendor.people — People-level external vendor data
--    Sources: enrichment.hunter_contact, intake.people_raw_intake,
--             intake.people_staging, intake.people_raw_wv
-- =============================================================================

CREATE TABLE vendor.people (
    vendor_row_id       BIGSERIAL PRIMARY KEY,
    source_table        TEXT NOT NULL,
    source_row_id       TEXT,
    migrated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    domain              TEXT,
    email               TEXT,
    first_name          TEXT,
    last_name           TEXT,
    full_name           TEXT,
    company_name        TEXT,
    company_unique_id   TEXT,
    outreach_id         UUID,

    -- Title / Role
    job_title           TEXT,
    title_normalized    TEXT,
    position_raw        TEXT,
    seniority_level     TEXT,
    department          TEXT,
    department_normalized TEXT,
    slot_type           TEXT,
    mapped_slot_type    TEXT,
    is_decision_maker   BOOLEAN,

    -- Contact
    phone_number        TEXT,
    work_phone          TEXT,
    personal_phone      TEXT,
    linkedin_url        TEXT,
    twitter_url         TEXT,
    twitter_handle      TEXT,
    facebook_url        TEXT,

    -- Email metadata
    email_type          TEXT,
    email_verified      BOOLEAN,
    confidence_score    NUMERIC,
    num_sources         INTEGER,

    -- Enrichment metadata
    data_quality_score  NUMERIC,
    outreach_priority   INTEGER,
    source_system       TEXT,
    source_record_id    TEXT,
    source_file         TEXT,
    import_batch_id     TEXT,
    backfill_source     TEXT,
    tags                TEXT[],
    hunter_sources      TEXT[],                 -- collapsed source_1..source_30

    -- Bio/Professional
    bio                 TEXT,
    skills              TEXT[],
    education           TEXT,
    certifications      TEXT,

    -- Geography
    city                TEXT,
    state               TEXT,
    state_abbrev        TEXT,
    country             TEXT,

    -- Validation
    validated           BOOLEAN,
    validation_notes    TEXT,
    validated_at        TIMESTAMP,
    validated_by        TEXT,
    enrichment_attempt  INTEGER,
    chronic_bad         BOOLEAN,
    last_enriched_at    TIMESTAMP,
    enriched_by         TEXT,

    -- Intake-specific
    b2_file_path        TEXT,
    b2_uploaded_at      TIMESTAMP,
    raw_name            TEXT,
    status              TEXT,
    source_url_id       UUID,
    processed_at        TIMESTAMP,

    -- Timestamps
    original_created_at TIMESTAMPTZ,
    original_updated_at TIMESTAMPTZ
);

CREATE INDEX idx_vendor_people_source ON vendor.people (source_table);
CREATE INDEX idx_vendor_people_domain ON vendor.people (domain);
CREATE INDEX idx_vendor_people_email ON vendor.people (email) WHERE email IS NOT NULL;
CREATE INDEX idx_vendor_people_outreach_id ON vendor.people (outreach_id) WHERE outreach_id IS NOT NULL;

COMMENT ON TABLE vendor.people IS 'Tier-1 vendor staging: people/contacts from Hunter, Clay, scrapers. Append-only.';

-- =============================================================================
-- 3. vendor.blog — Blog/URL external vendor data
--    Sources: outreach.sitemap_discovery, outreach.source_urls,
--             company.company_source_urls
-- =============================================================================

CREATE TABLE vendor.blog (
    vendor_row_id       BIGSERIAL PRIMARY KEY,
    source_table        TEXT NOT NULL,
    source_row_id       TEXT,
    migrated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    domain              TEXT,
    outreach_id         UUID,
    company_unique_id   TEXT,

    -- URL data
    source_type         TEXT,
    source_url          TEXT,
    sitemap_url         TEXT,
    page_title          TEXT,

    -- Discovery metadata
    discovered_from     TEXT,
    discovered_at       TIMESTAMPTZ,
    sitemap_source      TEXT,
    has_sitemap         BOOLEAN,

    -- Health/Status
    domain_reachable    BOOLEAN,
    http_status         SMALLINT,
    is_accessible       BOOLEAN,
    reachable_checked_at TIMESTAMPTZ,
    last_checked_at     TIMESTAMPTZ,

    -- Content tracking
    content_checksum    TEXT,
    last_content_change_at TIMESTAMPTZ,
    extraction_status   TEXT,
    extracted_at        TIMESTAMPTZ,
    extraction_error    TEXT,
    people_extracted    INTEGER,
    requires_paid_enrichment BOOLEAN,

    -- Timestamps
    original_created_at TIMESTAMPTZ,
    original_updated_at TIMESTAMPTZ
);

CREATE INDEX idx_vendor_blog_source ON vendor.blog (source_table);
CREATE INDEX idx_vendor_blog_outreach_id ON vendor.blog (outreach_id) WHERE outreach_id IS NOT NULL;
CREATE INDEX idx_vendor_blog_source_type ON vendor.blog (source_type);

COMMENT ON TABLE vendor.blog IS 'Tier-1 vendor staging: sitemaps, discovered URLs, source pages. Append-only.';

-- =============================================================================
-- 4. vendor.ct_claude — CL enrichment outputs (JSONB sandbox allowed)
--    Sources: cl.company_domains, cl.company_names, cl.company_candidate,
--             cl.identity_confidence, cl.domain_hierarchy,
--             cl.company_domains_excluded, cl.company_names_excluded,
--             cl.identity_confidence_excluded
-- =============================================================================

CREATE TABLE vendor.ct_claude (
    vendor_row_id       BIGSERIAL PRIMARY KEY,
    source_table        TEXT NOT NULL,
    source_row_id       TEXT,
    migrated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Common identity
    company_unique_id   UUID,
    domain              TEXT,

    -- CL enrichment data (structured for most common columns)
    name_value          TEXT,
    name_type           TEXT,
    domain_health       TEXT,
    mx_present          BOOLEAN,
    domain_name_confidence INTEGER,
    confidence_score    INTEGER,
    confidence_bucket   TEXT,
    relationship_type   TEXT,
    resolution_method   TEXT,
    parent_company_id   UUID,
    child_company_id    UUID,
    verification_status TEXT,
    verification_error  TEXT,

    -- Candidate-specific
    source_system       TEXT,
    source_record_id    TEXT,
    state_code          CHAR(2),
    raw_payload         JSONB,                  -- CL candidate raw data (JSONB sandbox)
    ingestion_run_id    TEXT,

    -- Timestamps
    verified_at         TIMESTAMPTZ,
    checked_at          TIMESTAMPTZ,
    computed_at         TIMESTAMPTZ,
    original_created_at TIMESTAMPTZ
);

CREATE INDEX idx_vendor_ct_claude_source ON vendor.ct_claude (source_table);
CREATE INDEX idx_vendor_ct_claude_company ON vendor.ct_claude (company_unique_id);

COMMENT ON TABLE vendor.ct_claude IS 'Tier-1 vendor staging: CL enrichment outputs (domains, names, candidates, confidence). JSONB sandbox.';

-- =============================================================================
-- 5. vendor.people_claude — People enrichment queue outputs (JSONB sandbox)
--    Sources: people.paid_enrichment_queue, people.people_resolution_queue
-- =============================================================================

CREATE TABLE vendor.people_claude (
    vendor_row_id           BIGSERIAL PRIMARY KEY,
    source_table            TEXT NOT NULL,
    source_row_id           TEXT,
    migrated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    company_unique_id       TEXT,
    company_slot_unique_id  TEXT,
    company_name            TEXT,
    source_url_id           UUID,

    -- Queue data
    slot_type               TEXT,
    source_url              TEXT,
    url_type                TEXT,
    existing_email          TEXT,
    issue_type              TEXT,
    failure_reason          TEXT,
    empty_slots             TEXT[],
    priority                INTEGER,
    status                  TEXT,

    -- Resolution
    resolved_contact_id     TEXT,
    assigned_to             TEXT,
    touched_by              TEXT,
    notes                   TEXT,
    error_details           JSONB,              -- JSONB sandbox
    attempt_count           INTEGER,
    processed_via           TEXT,

    -- Timestamps
    queued_at               TIMESTAMP,
    processed_at            TIMESTAMP,
    resolved_at             TIMESTAMP,
    last_touched_at         TIMESTAMP,
    original_created_at     TIMESTAMP
);

CREATE INDEX idx_vendor_people_claude_source ON vendor.people_claude (source_table);

COMMENT ON TABLE vendor.people_claude IS 'Tier-1 vendor staging: people enrichment queue data. JSONB sandbox.';

-- =============================================================================
-- 6. vendor.blog_claude — Blog enrichment outputs (empty, future use)
-- =============================================================================

CREATE TABLE vendor.blog_claude (
    vendor_row_id       BIGSERIAL PRIMARY KEY,
    source_table        TEXT NOT NULL,
    source_row_id       TEXT,
    migrated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    outreach_id         UUID,
    domain              TEXT,

    -- Payload
    enrichment_type     TEXT,
    payload             JSONB,                  -- JSONB sandbox

    -- Timestamps
    original_created_at TIMESTAMPTZ
);

COMMENT ON TABLE vendor.blog_claude IS 'Tier-1 vendor staging: blog enrichment outputs. JSONB sandbox. Currently empty.';

-- =============================================================================
-- 7. vendor.dol_claude — DOL enrichment outputs (JSONB sandbox)
--    Sources: outreach.dol_url_enrichment (16 rows)
-- =============================================================================

CREATE TABLE vendor.dol_claude (
    vendor_row_id           BIGSERIAL PRIMARY KEY,
    source_table            TEXT NOT NULL,
    source_row_id           TEXT,
    migrated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    ein                     TEXT,
    legal_name              TEXT,
    dba_name                TEXT,
    matched_company_unique_id TEXT,

    -- Enrichment
    enriched_url            TEXT,
    search_query            TEXT,
    confidence              TEXT,
    match_status            TEXT,
    participants            INTEGER,

    -- Geography
    city                    TEXT,
    state                   TEXT,
    zip                     TEXT,

    -- Payload for future enrichment
    payload                 JSONB,              -- JSONB sandbox

    -- Timestamps
    original_created_at     TIMESTAMPTZ
);

CREATE INDEX idx_vendor_dol_claude_ein ON vendor.dol_claude (ein);

COMMENT ON TABLE vendor.dol_claude IS 'Tier-1 vendor staging: DOL URL enrichment + future DOL enrichment outputs. JSONB sandbox.';

-- =============================================================================
-- 8. vendor.lane_claude — Lane enrichment outputs (empty, future use)
-- =============================================================================

CREATE TABLE vendor.lane_claude (
    vendor_row_id       BIGSERIAL PRIMARY KEY,
    source_table        TEXT NOT NULL,
    source_row_id       TEXT,
    migrated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Identity
    outreach_id         UUID,
    domain              TEXT,

    -- Payload
    enrichment_type     TEXT,
    lane                TEXT,                   -- 'appointments' | 'fractional_cfo'
    payload             JSONB,                  -- JSONB sandbox

    -- Timestamps
    original_created_at TIMESTAMPTZ
);

COMMENT ON TABLE vendor.lane_claude IS 'Tier-1 vendor staging: lane-specific enrichment outputs. JSONB sandbox. Currently empty.';

-- =============================================================================
-- Register all 8 vendor tables in CTB
-- =============================================================================

INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, registered_by, is_frozen, notes)
VALUES
    ('vendor', 'ct',            'STAGING', 'legacy_collapse_phase3', FALSE, 'Company vendor data — Hunter, Clay, CSV'),
    ('vendor', 'people',        'STAGING', 'legacy_collapse_phase3', FALSE, 'People vendor data — Hunter contacts, Clay, scrapers'),
    ('vendor', 'blog',          'STAGING', 'legacy_collapse_phase3', FALSE, 'Blog/URL vendor data — sitemaps, source URLs'),
    ('vendor', 'ct_claude',     'STAGING', 'legacy_collapse_phase3', FALSE, 'CL enrichment outputs — domains, names, candidates'),
    ('vendor', 'people_claude', 'STAGING', 'legacy_collapse_phase3', FALSE, 'People enrichment queue data'),
    ('vendor', 'blog_claude',   'STAGING', 'legacy_collapse_phase3', FALSE, 'Blog enrichment outputs (empty, future)'),
    ('vendor', 'dol_claude',    'STAGING', 'legacy_collapse_phase3', FALSE, 'DOL URL enrichment outputs'),
    ('vendor', 'lane_claude',   'STAGING', 'legacy_collapse_phase3', FALSE, 'Lane enrichment outputs (empty, future)')
ON CONFLICT (table_schema, table_name) DO NOTHING;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Should show 8 new vendor tables
SELECT table_schema, table_name, leaf_type, notes
FROM ctb.table_registry
WHERE table_schema = 'vendor'
ORDER BY table_name;
