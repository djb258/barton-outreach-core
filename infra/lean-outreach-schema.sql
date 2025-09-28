-- Barton Doctrine Infrastructure
-- All tables must have unique_id (Barton ID) and audit columns
-- MCP: Access only via Composio bridge

-- Lean Outreach DB: Marketing Cleanup & Canonical Bootstrap (Neon/Postgres)
-- Safe to run once; adapts if objects already exist.

BEGIN;

------------------------------------------------------------
-- 0) SCHEMAS
------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS company;
CREATE SCHEMA IF NOT EXISTS people;
CREATE SCHEMA IF NOT EXISTS marketing;

------------------------------------------------------------
-- 1) ENUM TYPES
------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'role_code_t' AND n.nspname = 'company'
  ) THEN
    CREATE TYPE company.role_code_t AS ENUM ('CEO','CFO','HR');
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE t.typname = 'email_status_t' AND n.nspname = 'people'
  ) THEN
    CREATE TYPE people.email_status_t AS ENUM ('green','yellow','red','gray');
  END IF;
END$$;

------------------------------------------------------------
-- 2) CANONICAL TABLES
------------------------------------------------------------
-- company.company
CREATE TABLE IF NOT EXISTS company.company (
  company_id             BIGSERIAL PRIMARY KEY,
  company_name           TEXT NOT NULL,
  ein                    TEXT,
  website_url            TEXT,
  linkedin_url           TEXT,
  news_url               TEXT,
  address_line1          TEXT,
  address_line2          TEXT,
  city                   TEXT,
  state_region           TEXT,
  postal_code            TEXT,
  country                TEXT,
  renewal_month          INT CHECK (renewal_month BETWEEN 1 AND 12),
  renewal_notice_window_days INT NOT NULL DEFAULT 120 CHECK (renewal_notice_window_days >= 0),
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_site_checked_at   TIMESTAMPTZ,
  last_linkedin_checked_at TIMESTAMPTZ,
  last_news_checked_at   TIMESTAMPTZ
);

-- people.contact
CREATE TABLE IF NOT EXISTS people.contact (
  contact_id             BIGSERIAL PRIMARY KEY,
  full_name              TEXT NOT NULL,
  title                  TEXT,
  email                  TEXT,
  phone                  TEXT,
  profile_source_url     TEXT,
  last_profile_checked_at TIMESTAMPTZ,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- people.contact_verification (1:1)
CREATE TABLE IF NOT EXISTS people.contact_verification (
  contact_id       BIGINT PRIMARY KEY REFERENCES people.contact(contact_id) ON DELETE CASCADE,
  email_status     people.email_status_t NOT NULL DEFAULT 'gray',
  email_checked_at TIMESTAMPTZ,
  email_confidence NUMERIC(5,2),
  email_source_url TEXT
);

-- company.company_slot (exactly 3 per company; one per role)
CREATE TABLE IF NOT EXISTS company.company_slot (
  company_slot_id  BIGSERIAL PRIMARY KEY,
  company_id       BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
  role_code        company.role_code_t NOT NULL,
  contact_id       BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_company_role UNIQUE (company_id, role_code)
);

------------------------------------------------------------
-- 3) MARKETING CORE (keep)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS marketing.campaign (
  campaign_id BIGSERIAL PRIMARY KEY,
  name        TEXT NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.campaign_contact (
  campaign_contact_id BIGSERIAL PRIMARY KEY,
  campaign_id BIGINT NOT NULL REFERENCES marketing.campaign(campaign_id) ON DELETE CASCADE,
  contact_id  BIGINT NOT NULL REFERENCES people.contact(contact_id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.message_log (
  message_log_id BIGSERIAL PRIMARY KEY,
  campaign_id    BIGINT REFERENCES marketing.campaign(campaign_id) ON DELETE SET NULL,
  contact_id     BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  direction      TEXT CHECK (direction IN ('outbound','inbound')),
  channel        TEXT CHECK (channel IN ('email','linkedin','phone','other')),
  subject        TEXT,
  body           TEXT,
  sent_at        TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.booking_event (
  booking_event_id BIGSERIAL PRIMARY KEY,
  contact_id BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  company_id BIGINT REFERENCES company.company(company_id) ON DELETE SET NULL,
  event_time TIMESTAMPTZ NOT NULL,
  source     TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.ac_handoff (
  handoff_id  BIGSERIAL PRIMARY KEY,
  company_id  BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
  contact_id  BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  notes       TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Keep these two staging/metadata tables as-is:
-- marketing.marketing_apollo_raw (kept)
-- marketing.marketing_company_column_metadata (kept)

------------------------------------------------------------
-- 4) TRIGGERS (updated_at maintainers)
------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_company_updated_at') THEN
    CREATE TRIGGER trg_company_updated_at
    BEFORE UPDATE ON company.company
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_company_slot_updated_at') THEN
    CREATE TRIGGER trg_company_slot_updated_at
    BEFORE UPDATE ON company.company_slot
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_people_contact_updated_at') THEN
    CREATE TRIGGER trg_people_contact_updated_at
    BEFORE UPDATE ON people.contact
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END$$;

------------------------------------------------------------
-- 5) INDEXES (help queues & lookups)
------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_company_name ON company.company (company_name);
CREATE INDEX IF NOT EXISTS idx_company_last_site_checked ON company.company (last_site_checked_at);
CREATE INDEX IF NOT EXISTS idx_company_last_linkedin_checked ON company.company (last_linkedin_checked_at);
CREATE INDEX IF NOT EXISTS idx_company_last_news_checked ON company.company (last_news_checked_at);

CREATE INDEX IF NOT EXISTS idx_company_slot_company ON company.company_slot (company_id);
CREATE INDEX IF NOT EXISTS idx_company_slot_role ON company.company_slot (role_code);

CREATE INDEX IF NOT EXISTS idx_contact_name ON people.contact (full_name);
CREATE INDEX IF NOT EXISTS idx_contact_email ON people.contact (email);
CREATE INDEX IF NOT EXISTS idx_contact_last_profile_checked ON people.contact (last_profile_checked_at);

CREATE INDEX IF NOT EXISTS idx_contact_verif_status ON people.contact_verification (email_status);
CREATE INDEX IF NOT EXISTS idx_contact_verif_checked_at ON people.contact_verification (email_checked_at);

------------------------------------------------------------
-- 6) DROP EXISTING VIEWS FIRST (to avoid conflicts)
------------------------------------------------------------
DROP VIEW IF EXISTS company.vw_due_renewals_ready CASCADE;
DROP VIEW IF EXISTS company.vw_next_renewal CASCADE;
DROP VIEW IF EXISTS company.vw_company_slots CASCADE;
DROP VIEW IF EXISTS company.next_company_urls_30d CASCADE;
DROP VIEW IF EXISTS people.due_email_recheck_30d CASCADE;
DROP VIEW IF EXISTS people.next_profile_urls_30d CASCADE;

------------------------------------------------------------
-- 7) RECREATE VIEWS (for UI & queues)
------------------------------------------------------------
-- company.vw_company_slots
CREATE VIEW company.vw_company_slots AS
SELECT
  c.company_id,
  c.company_name,
  cs.company_slot_id,
  cs.role_code,
  cs.contact_id,
  p.full_name,
  p.title,
  p.email,
  p.phone,
  p.profile_source_url,
  v.email_status,
  v.email_checked_at,
  c.website_url,
  c.linkedin_url,
  c.news_url
FROM company.company c
JOIN company.company_slot cs ON cs.company_id = c.company_id
LEFT JOIN people.contact p ON p.contact_id = cs.contact_id
LEFT JOIN people.contact_verification v ON v.contact_id = cs.contact_id;

-- people.due_email_recheck_30d
CREATE VIEW people.due_email_recheck_30d AS
SELECT
  p.contact_id,
  p.full_name,
  p.title,
  p.email,
  v.email_status,
  v.email_checked_at,
  GREATEST(COALESCE(v.email_checked_at, 'epoch'::timestamptz), 'epoch'::timestamptz) AS last_checked_at
FROM people.contact p
LEFT JOIN people.contact_verification v ON v.contact_id = p.contact_id
WHERE p.email IS NOT NULL
  AND (v.email_checked_at IS NULL OR v.email_checked_at < (now() - INTERVAL '30 days'));

-- company.next_company_urls_30d
CREATE VIEW company.next_company_urls_30d AS
SELECT company_id, 'website'::text AS url_type, website_url AS url, last_site_checked_at AS last_checked_at
FROM company.company
WHERE website_url IS NOT NULL
  AND (last_site_checked_at IS NULL OR last_site_checked_at < (now() - INTERVAL '30 days'))
UNION ALL
SELECT company_id, 'linkedin'::text, linkedin_url, last_linkedin_checked_at
FROM company.company
WHERE linkedin_url IS NOT NULL
  AND (last_linkedin_checked_at IS NULL OR last_linkedin_checked_at < (now() - INTERVAL '30 days'))
UNION ALL
SELECT company_id, 'news'::text, news_url, last_news_checked_at
FROM company.company
WHERE news_url IS NOT NULL
  AND (last_news_checked_at IS NULL OR last_news_checked_at < (now() - INTERVAL '30 days'));

-- people.next_profile_urls_30d
CREATE VIEW people.next_profile_urls_30d AS
SELECT
  contact_id,
  profile_source_url AS url,
  last_profile_checked_at AS last_checked_at
FROM people.contact
WHERE profile_source_url IS NOT NULL
  AND (last_profile_checked_at IS NULL OR last_profile_checked_at < (now() - INTERVAL '30 days'));

-- company.vw_next_renewal
CREATE VIEW company.vw_next_renewal AS
WITH base AS (
  SELECT company_id, company_name, renewal_month, COALESCE(renewal_notice_window_days,120) AS notice_days
  FROM company.company
)
SELECT
  b.company_id,
  b.company_name,
  b.renewal_month,
  b.notice_days,
  CASE
    WHEN b.renewal_month IS NULL THEN NULL
    ELSE
      DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int, b.renewal_month, 1))::date
      + CASE
          WHEN EXTRACT(MONTH FROM CURRENT_DATE)::int > b.renewal_month
               OR (EXTRACT(MONTH FROM CURRENT_DATE)::int = b.renewal_month AND CURRENT_DATE > DATE_TRUNC('month', CURRENT_DATE)::date)
          THEN INTERVAL '1 year' ELSE INTERVAL '0'
        END
  END::date AS next_renewal_date,
  CASE
    WHEN b.renewal_month IS NULL THEN NULL
    ELSE
      (
        CASE
          WHEN EXTRACT(MONTH FROM CURRENT_DATE)::int > b.renewal_month
               OR (EXTRACT(MONTH FROM CURRENT_DATE)::int = b.renewal_month AND CURRENT_DATE > DATE_TRUNC('month', CURRENT_DATE)::date)
          THEN DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int + 1, b.renewal_month, 1))::date
          ELSE DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int, b.renewal_month, 1))::date
        END
      ) - (b.notice_days * INTERVAL '1 day')
  END::date AS campaign_window_start
FROM base b;

-- company.vw_due_renewals_ready
CREATE VIEW company.vw_due_renewals_ready AS
WITH next_r AS (
  SELECT company_id, next_renewal_date, campaign_window_start
  FROM company.vw_next_renewal
)
SELECT
  c.company_id,
  c.company_name,
  nr.next_renewal_date,
  nr.campaign_window_start,
  EXISTS (
    SELECT 1
    FROM company.vw_company_slots s
    WHERE s.company_id = c.company_id
      AND s.contact_id IS NOT NULL
      AND s.email IS NOT NULL
      AND s.email_status = 'green'
  ) AS has_green_contact
FROM company.company c
JOIN next_r nr ON nr.company_id = c.company_id
WHERE nr.campaign_window_start IS NOT NULL
  AND CURRENT_DATE >= nr.campaign_window_start
  AND EXISTS (
    SELECT 1
    FROM company.vw_company_slots s2
    WHERE s2.company_id = c.company_id
      AND s2.contact_id IS NOT NULL
      AND s2.email IS NOT NULL
      AND s2.email_status = 'green'
  );

------------------------------------------------------------
-- 8) COMPATIBILITY VIEWS (replace legacy per-role tables)
------------------------------------------------------------
-- Drop tables first if they exist (they're tables, not views)
DROP TABLE IF EXISTS marketing.marketing_ceo CASCADE;
DROP TABLE IF EXISTS marketing.marketing_cfo CASCADE;
DROP TABLE IF EXISTS marketing.marketing_hr CASCADE;

-- Drop views if they exist
DROP VIEW IF EXISTS marketing.marketing_ceo CASCADE;
DROP VIEW IF EXISTS marketing.marketing_cfo CASCADE;
DROP VIEW IF EXISTS marketing.marketing_hr CASCADE;

CREATE VIEW marketing.marketing_ceo AS
SELECT 
  gen_random_uuid() as id,
  NULL::text as external_id,
  gen_random_uuid() as company_id,
  cs.full_name,
  cs.email,
  cs.title,
  'CEO'::text as persona_type,
  COALESCE(p.created_at, now())::timestamp as created_at
FROM company.vw_company_slots cs
LEFT JOIN people.contact p ON p.contact_id = cs.contact_id
WHERE cs.role_code = 'CEO';

CREATE VIEW marketing.marketing_cfo AS
SELECT 
  gen_random_uuid() as id,
  NULL::text as external_id,
  gen_random_uuid() as company_id,
  cs.full_name,
  cs.email,
  cs.title,
  'CFO'::text as persona_type,
  COALESCE(p.created_at, now())::timestamp as created_at
FROM company.vw_company_slots cs
LEFT JOIN people.contact p ON p.contact_id = cs.contact_id
WHERE cs.role_code = 'CFO';

CREATE VIEW marketing.marketing_hr AS
SELECT 
  gen_random_uuid() as id,
  NULL::text as external_id,
  gen_random_uuid() as company_id,
  cs.full_name,
  cs.email,
  cs.title,
  'HR'::text as persona_type,
  COALESCE(p.created_at, now())::timestamp as created_at
FROM company.vw_company_slots cs
LEFT JOIN people.contact p ON p.contact_id = cs.contact_id
WHERE cs.role_code = 'HR';

COMMENT ON VIEW marketing.marketing_ceo IS 'Compatibility view; prefer company.vw_company_slots filtered by role_code.';
COMMENT ON VIEW marketing.marketing_cfo IS 'Compatibility view; prefer company.vw_company_slots filtered by role_code.';
COMMENT ON VIEW marketing.marketing_hr IS 'Compatibility view; prefer company.vw_company_slots filtered by role_code.';

------------------------------------------------------------
-- 9) DATA MIGRATION (if tables have data)
------------------------------------------------------------
DO $$
DECLARE
  v_count INTEGER;
BEGIN
  -- Check if we need to migrate any data from old tables
  
  -- Migrate marketing_ceo data if exists
  SELECT COUNT(*) INTO v_count FROM information_schema.tables 
  WHERE table_schema = 'marketing' AND table_name = 'marketing_ceo';
  
  IF v_count > 0 THEN
    PERFORM COUNT(*) FROM marketing.marketing_ceo;
    IF FOUND THEN
      RAISE NOTICE 'Found data in marketing.marketing_ceo - migration may be needed';
    END IF;
  END IF;

  -- Similar checks for cfo and hr tables
  SELECT COUNT(*) INTO v_count FROM information_schema.tables 
  WHERE table_schema = 'marketing' AND table_name = 'marketing_cfo';
  
  IF v_count > 0 THEN
    PERFORM COUNT(*) FROM marketing.marketing_cfo;
    IF FOUND THEN
      RAISE NOTICE 'Found data in marketing.marketing_cfo - migration may be needed';
    END IF;
  END IF;

  SELECT COUNT(*) INTO v_count FROM information_schema.tables 
  WHERE table_schema = 'marketing' AND table_name = 'marketing_hr';
  
  IF v_count > 0 THEN
    PERFORM COUNT(*) FROM marketing.marketing_hr;
    IF FOUND THEN
      RAISE NOTICE 'Found data in marketing.marketing_hr - migration may be needed';
    END IF;
  END IF;
END$$;

------------------------------------------------------------
-- 10) DROP UNNEEDED/LEGACY MARKETING TABLES
-- (All were empty in your snapshot; we keep apollo_raw & metadata; we keep core campaign tables.)
------------------------------------------------------------
-- NOTE: Commenting out the drops for safety - uncomment when ready to clean up

-- Raw intake (empty): remove
-- DROP TABLE IF EXISTS marketing.company_raw_intake CASCADE;

-- Per-role physical tables (replace with views above)
-- DROP TABLE IF EXISTS marketing.marketing_ceo CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_cfo CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_hr CASCADE;

-- David Barton project tables (all empty)
-- DROP TABLE IF EXISTS marketing.marketing_david_barton_company CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_david_barton_people CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_david_barton_prep_table CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_david_barton_command_log CASCADE;

-- SHQ project tables (all empty)
-- DROP TABLE IF EXISTS marketing.marketing_shq_command_log CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_shq_error_log CASCADE;
-- DROP TABLE IF EXISTS marketing.marketing_shq_prep_table CASCADE;

-- NOTE: Intentionally NOT dropping:
--   marketing.marketing_apollo_raw
--   marketing.marketing_company_column_metadata
--   marketing.campaign*
--   marketing.message_log
--   marketing.booking_event
--   marketing.ac_handoff

------------------------------------------------------------
-- 11) SUMMARY
------------------------------------------------------------
DO $$
BEGIN
  RAISE NOTICE '';
  RAISE NOTICE '==============================================';
  RAISE NOTICE 'Lean Outreach Schema Setup Complete!';
  RAISE NOTICE '==============================================';
  RAISE NOTICE 'Created/Updated:';
  RAISE NOTICE '  - 3 schemas (company, people, marketing)';
  RAISE NOTICE '  - 2 enum types (role_code_t, email_status_t)';
  RAISE NOTICE '  - 4 core tables + marketing tables';
  RAISE NOTICE '  - 6 views for queues and UI';
  RAISE NOTICE '  - 3 compatibility views for legacy code';
  RAISE NOTICE '';
  RAISE NOTICE 'To clean up legacy tables, uncomment the DROP statements in section 10';
  RAISE NOTICE '';
  RAISE NOTICE 'Post-run stamps for scrapers (examples):';
  RAISE NOTICE '  UPDATE company.company SET last_site_checked_at = now() WHERE company_id = $1;';
  RAISE NOTICE '  UPDATE people.contact SET last_profile_checked_at = now() WHERE contact_id = $1;';
  RAISE NOTICE '  UPDATE people.contact_verification SET email_checked_at = now() WHERE contact_id = $1;';
  RAISE NOTICE '==============================================';
END$$;

COMMIT;