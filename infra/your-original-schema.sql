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