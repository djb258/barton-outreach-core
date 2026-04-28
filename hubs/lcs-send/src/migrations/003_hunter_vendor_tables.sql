-- ═══════════════════════════════════════════════════════════
-- Migration 003: Hunter + Vendor tables for D1
-- Source: Neon seed_views (Marketing DB)
-- Scoped to 32,702 agent-coverage companies
-- ═══════════════════════════════════════════════════════════

-- ── Hunter Contacts (175,632 rows — verified emails from Hunter.io) ──
CREATE TABLE IF NOT EXISTS enrichment_hunter_contact (
  id INTEGER PRIMARY KEY,
  outreach_id TEXT NOT NULL,
  company_unique_id TEXT,
  domain TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  full_name TEXT,
  email TEXT,
  email_type TEXT,
  email_verified INTEGER DEFAULT 0,
  confidence_score INTEGER,
  job_title TEXT,
  title_normalized TEXT,
  seniority_level TEXT,
  department TEXT,
  department_normalized TEXT,
  linkedin_url TEXT,
  phone_number TEXT,
  num_sources INTEGER,
  is_decision_maker INTEGER DEFAULT 0,
  outreach_priority INTEGER,
  data_quality_score REAL,
  source TEXT,
  source_file TEXT,
  created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_hct_outreach ON enrichment_hunter_contact(outreach_id);
CREATE INDEX IF NOT EXISTS idx_hct_domain ON enrichment_hunter_contact(domain);
CREATE INDEX IF NOT EXISTS idx_hct_email ON enrichment_hunter_contact(email);

-- ── Hunter Company (15,537 rows — email patterns per domain) ──
CREATE TABLE IF NOT EXISTS enrichment_hunter_company (
  id INTEGER PRIMARY KEY,
  outreach_id TEXT,
  company_unique_id TEXT,
  domain TEXT NOT NULL,
  organization TEXT,
  email_pattern TEXT,
  industry TEXT,
  industry_normalized TEXT,
  company_type TEXT,
  headcount TEXT,
  headcount_min INTEGER,
  headcount_max INTEGER,
  country TEXT,
  state TEXT,
  city TEXT,
  postal_code TEXT,
  street TEXT,
  location_full TEXT,
  data_quality_score REAL,
  source TEXT,
  enriched_at TEXT,
  created_at TEXT,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_hco_outreach ON enrichment_hunter_company(outreach_id);
CREATE INDEX IF NOT EXISTS idx_hco_domain ON enrichment_hunter_company(domain);
CREATE INDEX IF NOT EXISTS idx_hco_pattern ON enrichment_hunter_company(email_pattern);

-- ── Vendor People (175,632 rows — enriched contacts from vendor pipeline) ──
CREATE TABLE IF NOT EXISTS vendor_people (
  vendor_row_id INTEGER PRIMARY KEY,
  outreach_id TEXT,
  company_unique_id TEXT,
  domain TEXT,
  first_name TEXT,
  last_name TEXT,
  full_name TEXT,
  email TEXT,
  email_type TEXT,
  email_verified INTEGER DEFAULT 0,
  confidence_score REAL,
  job_title TEXT,
  title_normalized TEXT,
  seniority_level TEXT,
  department TEXT,
  department_normalized TEXT,
  mapped_slot_type TEXT,
  linkedin_url TEXT,
  phone_number TEXT,
  work_phone TEXT,
  personal_phone TEXT,
  num_sources INTEGER,
  is_decision_maker INTEGER DEFAULT 0,
  company_name TEXT,
  city TEXT,
  state TEXT,
  country TEXT,
  source_system TEXT,
  backfill_source TEXT,
  enriched_by TEXT,
  data_quality_score REAL,
  source_table TEXT,
  created_at TEXT,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_vp_outreach ON vendor_people(outreach_id);
CREATE INDEX IF NOT EXISTS idx_vp_domain ON vendor_people(domain);
CREATE INDEX IF NOT EXISTS idx_vp_email ON vendor_people(email);

-- ── Vendor Company Target (18,683 rows — enriched company data) ──
CREATE TABLE IF NOT EXISTS vendor_ct (
  vendor_row_id INTEGER PRIMARY KEY,
  outreach_id TEXT,
  company_unique_id TEXT,
  domain TEXT,
  company_name TEXT,
  email_pattern TEXT,
  email_pattern_confidence INTEGER,
  email_pattern_source TEXT,
  email_pattern_verified_at TEXT,
  company_phone TEXT,
  company_type TEXT,
  employee_count INTEGER,
  industry TEXT,
  industry_normalized TEXT,
  description TEXT,
  city TEXT,
  state TEXT,
  country TEXT,
  postal_code TEXT,
  linkedin_url TEXT,
  facebook_url TEXT,
  twitter_url TEXT,
  ein TEXT,
  duns TEXT,
  source_system TEXT,
  enriched_by TEXT,
  data_quality_score REAL,
  enriched_at TEXT,
  source_table TEXT,
  created_at TEXT,
  updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_vct_outreach ON vendor_ct(outreach_id);
CREATE INDEX IF NOT EXISTS idx_vct_domain ON vendor_ct(domain);
CREATE INDEX IF NOT EXISTS idx_vct_pattern ON vendor_ct(email_pattern);
