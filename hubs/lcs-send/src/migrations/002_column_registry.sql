-- ═══════════════════════════════════════════════════════════════════════════════
-- COLUMN REGISTRY — Self-Describing D1 Tables
-- ═══════════════════════════════════════════════════════════════════════════════
-- Every column in every table has: name, unique_id, description, format.
-- Any AI or human reading this knows exactly what goes in each field.
-- Authority: Foundational Bedrock — brain-template v1.0.0
-- Locked constant: 32,702 companies
-- ═══════════════════════════════════════════════════════════════════════════════

-- Clear old registry and rebuild
DELETE FROM outreach_column_registry;

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ outreach_company_target — The 32,702 agent-assigned companies              │
-- │ PK: target_id. One row per company. The gate for everything downstream.    │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('outreach', 'outreach_company_target', 'target_id', 'outreach.outreach_company_target.target_id', 'Primary key — UUID from Neon outreach.company_target', 'TEXT (UUID)', 0, NULL, NULL),
('outreach', 'outreach_company_target', 'company_unique_id', 'outreach.outreach_company_target.company_unique_id', 'FK to cl_company_identity — sovereign identity of this company', 'TEXT (UUID)', 0, NULL, 'cl.company_identity.company_unique_id'),
('outreach', 'outreach_company_target', 'outreach_status', 'outreach.outreach_company_target.outreach_status', 'Current outreach status: queued, active, paused, completed', 'TEXT', 0, 'queued', NULL),
('outreach', 'outreach_company_target', 'outreach_id', 'outreach.outreach_company_target.outreach_id', 'Universal join key — links this company across all sub-hub tables', 'TEXT (UUID)', 0, NULL, 'outreach.outreach.outreach_id'),
('outreach', 'outreach_company_target', 'email_method', 'outreach.outreach_company_target.email_method', 'Email delivery method: COLD, WARM, CATCHALL, NONE', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'industry', 'outreach.outreach_company_target.industry', 'Company industry classification', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'employees', 'outreach.outreach_company_target.employees', 'Employee count (approximate)', 'INTEGER', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'state', 'outreach.outreach_company_target.state', 'US state code (2 letter)', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'city', 'outreach.outreach_company_target.city', 'City name', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'postal_code', 'outreach.outreach_company_target.postal_code', 'ZIP code — the key that ties to coverage zones via Haversine radius', 'TEXT', 1, NULL, 'coverage.v_service_agent_coverage_zips.zip'),
('outreach', 'outreach_company_target', 'service_agent_id', 'outreach.outreach_company_target.service_agent_id', 'Assigned service agent UUID — variable, can be reassigned', 'TEXT (UUID)', 1, NULL, 'coverage.service_agent.service_agent_id'),
('outreach', 'outreach_company_target', 'service_agent_name', 'outreach.outreach_company_target.service_agent_name', 'Agent display name (denormalized for query convenience)', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'service_agent_number', 'outreach.outreach_company_target.service_agent_number', 'Agent number: SA-001, SA-002, SA-003', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_company_target', 'created_at', 'outreach.outreach_company_target.created_at', 'Record creation timestamp', 'TEXT (ISO-8601)', 0, 'datetime(now)', NULL),
('outreach', 'outreach_company_target', 'updated_at', 'outreach.outreach_company_target.updated_at', 'Last update timestamp', 'TEXT (ISO-8601)', 0, 'datetime(now)', NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ outreach_outreach — Outreach status + domain per company                   │
-- │ PK: outreach_id. The universal join key across all sub-hub tables.         │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('outreach', 'outreach_outreach', 'outreach_id', 'outreach.outreach_outreach.outreach_id', 'Primary key + universal join key — links every sub-hub table', 'TEXT (UUID)', 0, NULL, NULL),
('outreach', 'outreach_outreach', 'sovereign_id', 'outreach.outreach_outreach.sovereign_id', 'Sovereign company ID from CL spine', 'TEXT', 1, NULL, 'cl.company_identity.sovereign_company_id'),
('outreach', 'outreach_outreach', 'domain', 'outreach.outreach_outreach.domain', 'Company website domain (e.g., acme.com) — used for blog fetch and email derivation', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_outreach', 'ein', 'outreach.outreach_outreach.ein', 'Employer Identification Number — links to DOL filings', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_outreach', 'has_appointment', 'outreach.outreach_outreach.has_appointment', 'Whether an appointment/meeting exists for this company', 'INTEGER (0/1)', 1, NULL, NULL),
('outreach', 'outreach_outreach', 'created_at', 'outreach.outreach_outreach.created_at', 'Record creation timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL),
('outreach', 'outreach_outreach', 'updated_at', 'outreach.outreach_outreach.updated_at', 'Last update timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ outreach_blog — Blog/web presence data per company                         │
-- │ PK: blog_id. One row per company. Combines vendor.blog crawl data +        │
-- │ outreach.blog extraction data. Source: seed_views.v_agent_blog             │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('outreach', 'outreach_blog', 'blog_id', 'outreach.outreach_blog.blog_id', 'Primary key — UUID or outreach_id fallback', 'TEXT', 0, NULL, NULL),
('outreach', 'outreach_blog', 'outreach_id', 'outreach.outreach_blog.outreach_id', 'FK to outreach_outreach — universal join key', 'TEXT (UUID)', 0, NULL, 'outreach.outreach.outreach_id'),
('outreach', 'outreach_blog', 'about_url', 'outreach.outreach_blog.about_url', 'Discovered about/team page URL — target for Process 300 people extraction', 'TEXT (URL)', 1, NULL, NULL),
('outreach', 'outreach_blog', 'source_url', 'outreach.outreach_blog.source_url', 'Primary source URL from vendor.blog crawl', 'TEXT (URL)', 1, NULL, NULL),
('outreach', 'outreach_blog', 'context_summary', 'outreach.outreach_blog.context_summary', 'Extracted people data as JSON: {people: [{name, title}], people_count, extracted_at}', 'TEXT (JSON)', 1, NULL, NULL),
('outreach', 'outreach_blog', 'source_type', 'outreach.outreach_blog.source_type', 'How this record was sourced: sitemap, crawl, manual', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_blog', 'extraction_method', 'outreach.outreach_blog.extraction_method', 'How content was extracted: direct_fetch, startpage_search, parse_existing', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_blog', 'last_extracted_at', 'outreach.outreach_blog.last_extracted_at', 'When content was last extracted from the about_url', 'TEXT (ISO-8601)', 1, NULL, NULL),
('outreach', 'outreach_blog', 'created_at', 'outreach.outreach_blog.created_at', 'Record creation timestamp', 'TEXT (ISO-8601)', 0, 'datetime(now)', NULL),
('outreach', 'outreach_blog', 'updated_at', 'outreach.outreach_blog.updated_at', 'Last update timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ outreach_dol — DOL Form 5500 summary per company                          │
-- │ PK: dol_id. One row per company. 32,702 rows (empty if no filing).        │
-- │ Detailed filing data in dol_form_5500, dol_schedule_a/c/other.            │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('outreach', 'outreach_dol', 'dol_id', 'outreach.outreach_dol.dol_id', 'Primary key — UUID from Neon', 'TEXT (UUID)', 1, NULL, NULL),
('outreach', 'outreach_dol', 'outreach_id', 'outreach.outreach_dol.outreach_id', 'FK to outreach_outreach — universal join key', 'TEXT (UUID)', 0, NULL, 'outreach.outreach.outreach_id'),
('outreach', 'outreach_dol', 'ein', 'outreach.outreach_dol.ein', 'Employer Identification Number — links to dol_form_5500.sponsor_dfe_ein', 'TEXT', 1, NULL, 'dol.form_5500.sponsor_dfe_ein'),
('outreach', 'outreach_dol', 'filing_present', 'outreach.outreach_dol.filing_present', 'Whether DOL Form 5500 filing exists for this company (1=yes, 0=no)', 'INTEGER (0/1)', 0, '0', NULL),
('outreach', 'outreach_dol', 'funding_type', 'outreach.outreach_dol.funding_type', 'Benefits funding: fully_insured, self_funded, level_funded, unknown', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_dol', 'broker_or_advisor', 'outreach.outreach_dol.broker_or_advisor', 'Current broker/advisor name from Schedule A', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_dol', 'carrier', 'outreach.outreach_dol.carrier', 'Current insurance carrier name from Schedule A', 'TEXT', 1, NULL, NULL),
('outreach', 'outreach_dol', 'renewal_month', 'outreach.outreach_dol.renewal_month', 'Expected renewal month (1-12) derived from plan_eff_date', 'INTEGER', 1, NULL, NULL),
('outreach', 'outreach_dol', 'outreach_start_month', 'outreach.outreach_dol.outreach_start_month', 'When to begin outreach (3 months before renewal)', 'INTEGER', 1, NULL, NULL),
('outreach', 'outreach_dol', 'created_at', 'outreach.outreach_dol.created_at', 'Record creation timestamp', 'TEXT (ISO-8601)', 0, 'datetime(now)', NULL),
('outreach', 'outreach_dol', 'updated_at', 'outreach.outreach_dol.updated_at', 'Last update timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ people_company_slot — 3 slots per company (CEO, CFO, HR)                   │
-- │ PK: slot_id. 98,106 rows (32,702 × 3). The structure is the constant.     │
-- │ Whether a slot is filled is the variable.                                  │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('people', 'people_company_slot', 'slot_id', 'people.people_company_slot.slot_id', 'Primary key — UUID. One slot per company per role.', 'TEXT (UUID)', 0, NULL, NULL),
('people', 'people_company_slot', 'outreach_id', 'people.people_company_slot.outreach_id', 'FK to outreach_outreach — universal join key', 'TEXT (UUID)', 0, NULL, 'outreach.outreach.outreach_id'),
('people', 'people_company_slot', 'company_unique_id', 'people.people_company_slot.company_unique_id', 'FK to cl_company_identity — sovereign identity', 'TEXT (UUID)', 0, NULL, 'cl.company_identity.company_unique_id'),
('people', 'people_company_slot', 'slot_type', 'people.people_company_slot.slot_type', 'Role this slot represents: CEO, CFO, or HR', 'TEXT (enum: CEO, CFO, HR)', 0, NULL, NULL),
('people', 'people_company_slot', 'person_unique_id', 'people.people_company_slot.person_unique_id', 'FK to people_people_master — NULL if slot is empty, UUID if filled', 'TEXT (UUID)', 1, NULL, 'people.people_master.unique_id'),
('people', 'people_company_slot', 'is_filled', 'people.people_company_slot.is_filled', 'Whether this slot has a person assigned (1=filled, 0=empty)', 'INTEGER (0/1)', 0, '0', NULL),
('people', 'people_company_slot', 'filled_at', 'people.people_company_slot.filled_at', 'When the slot was filled with a person', 'TEXT (ISO-8601)', 1, NULL, NULL),
('people', 'people_company_slot', 'confidence_score', 'people.people_company_slot.confidence_score', 'How confident we are in this assignment (0.0-1.0)', 'REAL', 1, NULL, NULL),
('people', 'people_company_slot', 'source_system', 'people.people_company_slot.source_system', 'Which system filled this slot: neon_seed, intake_staging, blog_recon, startpage_proxy, brave_search', 'TEXT', 1, NULL, NULL),
('people', 'people_company_slot', 'created_at', 'people.people_company_slot.created_at', 'Record creation timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL),
('people', 'people_company_slot', 'updated_at', 'people.people_company_slot.updated_at', 'Last update timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ people_people_master — Actual person records                               │
-- │ PK: unique_id. One row per person. Referenced by people_company_slot.      │
-- │ A person without email AND LinkedIn is a dead record — can't reach them.   │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('people', 'people_people_master', 'unique_id', 'people.people_people_master.unique_id', 'Primary key — UUID. Referenced by people_company_slot.person_unique_id', 'TEXT (UUID)', 0, NULL, NULL),
('people', 'people_people_master', 'company_unique_id', 'people.people_people_master.company_unique_id', 'FK to cl_company_identity — which company this person belongs to', 'TEXT (UUID)', 0, NULL, 'cl.company_identity.company_unique_id'),
('people', 'people_people_master', 'first_name', 'people.people_people_master.first_name', 'Person first name', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'last_name', 'people.people_people_master.last_name', 'Person last name', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'full_name', 'people.people_people_master.full_name', 'Full display name (first + last)', 'TEXT', 0, NULL, NULL),
('people', 'people_people_master', 'title', 'people.people_people_master.title', 'Job title — determines which slot they fill (CEO, CFO, HR)', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'email', 'people.people_people_master.email', 'Verified email address — primary outreach channel for Mailgun delivery', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'linkedin_url', 'people.people_people_master.linkedin_url', 'LinkedIn profile URL — secondary outreach channel for HeyReach delivery', 'TEXT (URL)', 1, NULL, NULL),
('people', 'people_people_master', 'email_verified', 'people.people_people_master.email_verified', 'Whether email has been verified (1=verified, 0=unverified)', 'INTEGER (0/1)', 0, '0', NULL),
('people', 'people_people_master', 'outreach_ready', 'people.people_people_master.outreach_ready', 'Whether this person can receive outreach (1=ready, 0=not ready)', 'INTEGER (0/1)', 0, '0', NULL),
('people', 'people_people_master', 'source_system', 'people.people_people_master.source_system', 'Which system created this record: neon_seed, intake_staging, blog_recon, startpage_proxy', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'seniority', 'people.people_people_master.seniority', 'Seniority level: C-Suite, VP, Director, Manager', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'department', 'people.people_people_master.department', 'Department: Executive, Finance, Human Resources, Benefits', 'TEXT', 1, NULL, NULL),
('people', 'people_people_master', 'created_at', 'people.people_people_master.created_at', 'Record creation timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL),
('people', 'people_people_master', 'updated_at', 'people.people_people_master.updated_at', 'Last update timestamp', 'TEXT (ISO-8601)', 1, NULL, NULL),
('people', 'people_people_master', 'last_verified_at', 'people.people_people_master.last_verified_at', 'When this person record was last verified against source', 'TEXT (ISO-8601)', 1, NULL, NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ coverage_service_agent — The 3 agents                                      │
-- │ PK: service_agent_id. Agent defines geography, not ownership.              │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('coverage', 'coverage_service_agent', 'service_agent_id', 'coverage.coverage_service_agent.service_agent_id', 'Primary key — UUID. The agent who defines this coverage zone.', 'TEXT (UUID)', 0, NULL, NULL),
('coverage', 'coverage_service_agent', 'agent_name', 'coverage.coverage_service_agent.agent_name', 'Agent display name (e.g., Jeff Mussolino)', 'TEXT', 0, NULL, NULL),
('coverage', 'coverage_service_agent', 'agent_number', 'coverage.coverage_service_agent.agent_number', 'Agent number: SA-001, SA-002, SA-003', 'TEXT', 0, NULL, NULL),
('coverage', 'coverage_service_agent', 'status', 'coverage.coverage_service_agent.status', 'Agent status: active, retired', 'TEXT', 0, NULL, NULL);

-- ┌─────────────────────────────────────────────────────────────────────────────┐
-- │ coverage_service_agent_coverage — The 3 coverage zones                     │
-- │ PK: coverage_id. Agent anchor ZIP + radius = qualifying ZIPs.              │
-- └─────────────────────────────────────────────────────────────────────────────┘

INSERT INTO outreach_column_registry (schema_name, table_name, column_name, column_unique_id, column_description, column_format, is_nullable, default_value, fk_reference) VALUES
('coverage', 'coverage_service_agent_coverage', 'coverage_id', 'coverage.coverage_service_agent_coverage.coverage_id', 'Primary key — UUID. One coverage zone per agent.', 'TEXT (UUID)', 0, NULL, NULL),
('coverage', 'coverage_service_agent_coverage', 'service_agent_id', 'coverage.coverage_service_agent_coverage.service_agent_id', 'FK to coverage_service_agent — which agent anchors this zone', 'TEXT (UUID)', 0, NULL, 'coverage.service_agent.service_agent_id'),
('coverage', 'coverage_service_agent_coverage', 'anchor_zip', 'coverage.coverage_service_agent_coverage.anchor_zip', 'Center ZIP code for the coverage radius', 'TEXT', 0, NULL, NULL),
('coverage', 'coverage_service_agent_coverage', 'radius_miles', 'coverage.coverage_service_agent_coverage.radius_miles', 'Coverage radius in miles from anchor ZIP (Haversine calculation)', 'REAL', 0, NULL, NULL),
('coverage', 'coverage_service_agent_coverage', 'status', 'coverage.coverage_service_agent_coverage.status', 'Zone status: active only (retired zones not in D1)', 'TEXT', 0, NULL, NULL);
