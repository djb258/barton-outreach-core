-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/infra
-- Barton ID: 05.01.01
-- Unique ID: CTB-10CC8A84
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Barton Doctrine Infrastructure
-- All tables must have unique_id (Barton ID) and audit columns
-- MCP: Access only via Composio bridge

-- ===================================================
-- YOUR ORIGINAL SCHEMA - Exact specification
-- ===================================================

CREATE TABLE company (
  company_id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  website_url TEXT,
  last_url_refresh_at TIMESTAMPTZ
);

CREATE TABLE contact (
  contact_id BIGSERIAL PRIMARY KEY,
  company_id BIGINT REFERENCES company(company_id) ON DELETE CASCADE,
  full_name TEXT,
  title TEXT,
  email TEXT,
  last_profile_fetch_at TIMESTAMPTZ
);

CREATE TABLE contact_verification (
  contact_id BIGINT PRIMARY KEY REFERENCES contact(contact_id) ON DELETE CASCADE,
  status TEXT CHECK (status IN ('green','yellow','red','gray')) DEFAULT 'gray',
  last_checked_at TIMESTAMPTZ
);