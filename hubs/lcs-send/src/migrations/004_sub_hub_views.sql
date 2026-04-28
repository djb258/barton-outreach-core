-- Sub-Hub Views — new naming convention over existing tables
-- Old tables stay. New views provide SP/People/CT/DOL naming.
-- Zero breaking changes. Process 100 reads from these views.

-- ═══════════════════════════════════════════════════════════
-- SP (Social Platform) — was "Blog"
-- Everything about a company's public online presence
-- ═══════════════════════════════════════════════════════════

CREATE VIEW IF NOT EXISTS sp_blog AS SELECT * FROM outreach_blog;

-- page_raw_html contains leadership/about pages — those are People sources
-- Moved to People sub-hub. SP is social platforms only.

-- SP summary per company (from CEO slot on workbench)
-- Social PLATFORMS only: Glassdoor, Indeed, Facebook, LinkedIn co, X, BBB, etc.
-- Leadership/about pages are People, not SP.
CREATE VIEW IF NOT EXISTS sp_company AS
SELECT
    outreach_id,
    company_name,
    domain,
    blog_source_url,
    recon_linkedin_company,
    recon_platform_urls,
    recon_result_urls,
    recon_snippets,
    recon_result_count,
    last_recon_at
FROM slot_workbench
WHERE slot_type = 'CEO';

-- ═══════════════════════════════════════════════════════════
-- PEOPLE — was split across 200/201/202
-- Everything about the people at a company
-- ═══════════════════════════════════════════════════════════

-- People slots (the workbench IS the people table)
CREATE VIEW IF NOT EXISTS people_slots AS
SELECT
    slot_id,
    outreach_id,
    slot_type,
    is_filled,
    person_first_name,
    person_last_name,
    person_full_name,
    person_email,
    person_email_verified,
    person_linkedin,
    person_source,
    has_name,
    has_email,
    has_verified_email,
    has_linkedin,
    readiness_tier,
    person_found_at,
    email_found_at,
    linkedin_found_at,
    email_verified_at
FROM slot_workbench;

-- Leadership/about pages are a PEOPLE source — the page exists to show who works there
CREATE VIEW IF NOT EXISTS people_leadership_pages AS
SELECT
    outreach_id,
    about_url,
    recon_organized_people,
    recon_organized_linkedin,
    last_recon_at AS page_last_checked
FROM slot_workbench
WHERE slot_type = 'CEO'
AND about_url IS NOT NULL AND about_url != '';

-- Raw HTML of leadership pages — People source material for key extraction
CREATE VIEW IF NOT EXISTS people_page_html AS SELECT * FROM page_raw_html;

CREATE VIEW IF NOT EXISTS people_hunter AS SELECT * FROM enrichment_hunter_contact;

CREATE VIEW IF NOT EXISTS people_hunter_company AS SELECT * FROM enrichment_hunter_company;

CREATE VIEW IF NOT EXISTS people_vendor AS SELECT * FROM vendor_people;

CREATE VIEW IF NOT EXISTS people_title_map AS SELECT * FROM people_title_slot_mapping;

-- ═══════════════════════════════════════════════════════════
-- CT (Company Target)
-- The company identity and targeting data
-- ═══════════════════════════════════════════════════════════

CREATE VIEW IF NOT EXISTS ct_company AS SELECT * FROM outreach_company_target;

CREATE VIEW IF NOT EXISTS ct_outreach AS SELECT * FROM outreach_outreach;

-- ═══════════════════════════════════════════════════════════
-- DOL (Department of Labor)
-- Filing data, brokers, signers
-- ═══════════════════════════════════════════════════════════

CREATE VIEW IF NOT EXISTS dol_filings AS SELECT * FROM dol_form_5500;

CREATE VIEW IF NOT EXISTS dol_brokers AS SELECT * FROM dol_schedule_a;

CREATE VIEW IF NOT EXISTS dol_providers AS SELECT * FROM dol_schedule_c;

CREATE VIEW IF NOT EXISTS dol_summary AS SELECT * FROM outreach_dol;

-- ═══════════════════════════════════════════════════════════
-- SUB-HUB REGISTRY — maps old table names to new sub-hub names
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sub_hub_registry (
    old_table TEXT NOT NULL,
    new_view TEXT NOT NULL,
    sub_hub TEXT NOT NULL CHECK(sub_hub IN ('SP', 'People', 'CT', 'DOL')),
    description TEXT,
    PRIMARY KEY (old_table)
);

INSERT OR IGNORE INTO sub_hub_registry VALUES
    ('outreach_blog', 'sp_blog', 'SP', 'Blog content'),
    ('page_raw_html', 'people_page_html', 'People', 'Leadership page raw HTML — people source material'),
    ('enrichment_hunter_contact', 'people_hunter', 'People', 'Hunter contacts'),
    ('enrichment_hunter_company', 'people_hunter_company', 'People', 'Hunter email patterns'),
    ('vendor_people', 'people_vendor', 'People', 'Vendor enriched contacts'),
    ('people_title_slot_mapping', 'people_title_map', 'People', 'Title classifier mapping'),
    ('outreach_company_target', 'ct_company', 'CT', 'Company targeting data'),
    ('outreach_outreach', 'ct_outreach', 'CT', 'Outreach status'),
    ('dol_form_5500', 'dol_filings', 'DOL', 'Form 5500 filings'),
    ('dol_schedule_a', 'dol_brokers', 'DOL', 'Schedule A broker detail'),
    ('dol_schedule_c', 'dol_providers', 'DOL', 'Schedule C service providers'),
    ('outreach_dol', 'dol_summary', 'DOL', 'DOL summary view');
