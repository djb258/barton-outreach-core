-- Cold Outreach Database Bootstrap (Neon/PostgreSQL)
-- Safe to run in a fresh database. Idempotent guards included where possible.

BEGIN;

------------------------------------------------------------
-- 0) SCHEMAS
------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS company;
CREATE SCHEMA IF NOT EXISTS people;
CREATE SCHEMA IF NOT EXISTS marketing;
CREATE SCHEMA IF NOT EXISTS bit;
CREATE SCHEMA IF NOT EXISTS ple; -- future

------------------------------------------------------------
-- 1) TYPES (ENUMS)
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
-- 2) TABLES
------------------------------------------------------------

-- company.company
CREATE TABLE IF NOT EXISTS company.company (
  company_id             BIGSERIAL PRIMARY KEY,
  company_name           TEXT NOT NULL,
  ein                    TEXT,
  website_url            TEXT,
  linkedin_url           TEXT,
  news_url               TEXT,

  -- Address (free-form; refine as needed)
  address_line1          TEXT,
  address_line2          TEXT,
  city                   TEXT,
  state_region           TEXT,
  postal_code            TEXT,
  country                TEXT,

  -- Renewal meta
  renewal_month                  INT CHECK (renewal_month BETWEEN 1 AND 12),
  renewal_notice_window_days     INT NOT NULL DEFAULT 120 CHECK (renewal_notice_window_days >= 0),

  -- Timestamps
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

-- people.contact_verification (1:1 with contact)
CREATE TABLE IF NOT EXISTS people.contact_verification (
  contact_id             BIGINT PRIMARY KEY REFERENCES people.contact(contact_id) ON DELETE CASCADE,
  email_status           people.email_status_t NOT NULL,
  email_checked_at       TIMESTAMPTZ,
  email_confidence       NUMERIC(5,2),
  email_source_url       TEXT
);

-- company.company_slot (exactly 3 per company: CEO, CFO, HR)
CREATE TABLE IF NOT EXISTS company.company_slot (
  company_slot_id        BIGSERIAL PRIMARY KEY,
  company_id             BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
  role_code              company.role_code_t NOT NULL,
  contact_id             BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_company_role UNIQUE (company_id, role_code)
);

-- marketing (optional, for campaigns)
CREATE TABLE IF NOT EXISTS marketing.campaign (
  campaign_id            BIGSERIAL PRIMARY KEY,
  name                   TEXT NOT NULL,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.campaign_contact (
  campaign_contact_id    BIGSERIAL PRIMARY KEY,
  campaign_id            BIGINT NOT NULL REFERENCES marketing.campaign(campaign_id) ON DELETE CASCADE,
  contact_id             BIGINT NOT NULL REFERENCES people.contact(contact_id) ON DELETE CASCADE,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.message_log (
  message_log_id         BIGSERIAL PRIMARY KEY,
  campaign_id            BIGINT REFERENCES marketing.campaign(campaign_id) ON DELETE SET NULL,
  contact_id             BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  direction              TEXT CHECK (direction IN ('outbound','inbound')),
  channel                TEXT CHECK (channel IN ('email','linkedin','phone','other')),
  subject                TEXT,
  body                   TEXT,
  sent_at                TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.booking_event (
  booking_event_id       BIGSERIAL PRIMARY KEY,
  contact_id             BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  company_id             BIGINT REFERENCES company.company(company_id) ON DELETE SET NULL,
  event_time             TIMESTAMPTZ NOT NULL,
  source                 TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS marketing.ac_handoff (
  handoff_id             BIGSERIAL PRIMARY KEY,
  company_id             BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
  contact_id             BIGINT REFERENCES people.contact(contact_id) ON DELETE SET NULL,
  notes                  TEXT,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- bit.signal (Buyer Intent Tool)
CREATE TABLE IF NOT EXISTS bit.signal (
  signal_id              BIGSERIAL PRIMARY KEY,
  company_id             BIGINT NOT NULL REFERENCES company.company(company_id) ON DELETE CASCADE,
  reason                 TEXT NOT NULL, -- e.g., 'renewal_window_open_120d', 'executive_movement'
  payload                JSONB,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at           TIMESTAMPTZ
);

------------------------------------------------------------
-- 3) COMMON INDEXES
------------------------------------------------------------

-- Company lookups & queue helpers
CREATE INDEX IF NOT EXISTS idx_company_name ON company.company (company_name);
CREATE INDEX IF NOT EXISTS idx_company_website ON company.company (website_url);
CREATE INDEX IF NOT EXISTS idx_company_last_site_checked ON company.company (last_site_checked_at);
CREATE INDEX IF NOT EXISTS idx_company_last_linkedin_checked ON company.company (last_linkedin_checked_at);
CREATE INDEX IF NOT EXISTS idx_company_last_news_checked ON company.company (last_news_checked_at);

-- Slot & people access
CREATE INDEX IF NOT EXISTS idx_company_slot_company ON company.company_slot (company_id);
CREATE INDEX IF NOT EXISTS idx_company_slot_role ON company.company_slot (role_code);
CREATE INDEX IF NOT EXISTS idx_contact_name ON people.contact (full_name);
CREATE INDEX IF NOT EXISTS idx_contact_email ON people.contact (email);
CREATE INDEX IF NOT EXISTS idx_contact_last_profile_checked ON people.contact (last_profile_checked_at);

-- Verification status scans
CREATE INDEX IF NOT EXISTS idx_contact_verif_status ON people.contact_verification (email_status);
CREATE INDEX IF NOT EXISTS idx_contact_verif_checked_at ON people.contact_verification (email_checked_at);

-- BIT signals pipeline
CREATE INDEX IF NOT EXISTS idx_signal_company ON bit.signal (company_id);
CREATE INDEX IF NOT EXISTS idx_signal_created_at ON bit.signal (created_at);

------------------------------------------------------------
-- 4) TRIGGERS: updated_at maintenance
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
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_company_updated_at'
  ) THEN
    CREATE TRIGGER trg_company_updated_at
    BEFORE UPDATE ON company.company
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_company_slot_updated_at'
  ) THEN
    CREATE TRIGGER trg_company_slot_updated_at
    BEFORE UPDATE ON company.company_slot
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_people_contact_updated_at'
  ) THEN
    CREATE TRIGGER trg_people_contact_updated_at
    BEFORE UPDATE ON people.contact
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
  END IF;
END$$;

------------------------------------------------------------
-- 5) VIEWS (for UI & BIT)
------------------------------------------------------------

-- 5.1 company.vw_company_slots → company + slot + contact + verification
CREATE OR REPLACE VIEW company.vw_company_slots AS
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
JOIN company.company_slot cs
  ON cs.company_id = c.company_id
LEFT JOIN people.contact p
  ON p.contact_id = cs.contact_id
LEFT JOIN people.contact_verification v
  ON v.contact_id = cs.contact_id;

-- 5.2 people.due_email_recheck_30d → contacts due for re-verify (30d TTL)
CREATE OR REPLACE VIEW people.due_email_recheck_30d AS
SELECT
  p.contact_id,
  p.full_name,
  p.title,
  p.email,
  v.email_status,
  v.email_checked_at,
  GREATEST(COALESCE(v.email_checked_at, 'epoch'::timestamptz), 'epoch'::timestamptz) AS last_checked_at
FROM people.contact p
LEFT JOIN people.contact_verification v
  ON v.contact_id = p.contact_id
WHERE p.email IS NOT NULL
  AND (
    v.email_checked_at IS NULL
    OR v.email_checked_at < (now() - INTERVAL '30 days')
  );

-- 5.3 company.next_company_urls_30d → URLs due for scrape (site/linkedin/news)
--     Emits one row per URL type that is due.
CREATE OR REPLACE VIEW company.next_company_urls_30d AS
SELECT company_id,
       'website'::text AS url_type,
       website_url     AS url,
       last_site_checked_at AS last_checked_at
FROM company.company
WHERE website_url IS NOT NULL
  AND (last_site_checked_at IS NULL OR last_site_checked_at < (now() - INTERVAL '30 days'))
UNION ALL
SELECT company_id,
       'linkedin'::text AS url_type,
       linkedin_url,
       last_linkedin_checked_at
FROM company.company
WHERE linkedin_url IS NOT NULL
  AND (last_linkedin_checked_at IS NULL OR last_linkedin_checked_at < (now() - INTERVAL '30 days'))
UNION ALL
SELECT company_id,
       'news'::text AS url_type,
       news_url,
       last_news_checked_at
FROM company.company
WHERE news_url IS NOT NULL
  AND (last_news_checked_at IS NULL OR last_news_checked_at < (now() - INTERVAL '30 days'));

-- 5.4 people.next_profile_urls_30d → person profiles due for scrape
CREATE OR REPLACE VIEW people.next_profile_urls_30d AS
SELECT
  contact_id,
  profile_source_url AS url,
  last_profile_checked_at AS last_checked_at
FROM people.contact
WHERE profile_source_url IS NOT NULL
  AND (last_profile_checked_at IS NULL OR last_profile_checked_at < (now() - INTERVAL '30 days'));

-- 5.5 company.vw_next_renewal → compute next renewal date + campaign window
--     next_renewal_date = first day of the next occurrence of renewal_month.
--     campaign_window_start = next_renewal_date - renewal_notice_window_days.
CREATE OR REPLACE VIEW company.vw_next_renewal AS
WITH base AS (
  SELECT
    company_id,
    company_name,
    renewal_month,
    COALESCE(renewal_notice_window_days, 120) AS notice_days
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
      -- first day of this year's renewal month
      DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int, b.renewal_month, 1))::date
      + CASE
          WHEN EXTRACT(MONTH FROM CURRENT_DATE)::int > b.renewal_month
               OR (EXTRACT(MONTH FROM CURRENT_DATE)::int = b.renewal_month AND CURRENT_DATE > DATE_TRUNC('month', CURRENT_DATE)::date)
          THEN INTERVAL '1 year'
          ELSE INTERVAL '0'
        END
  END::date AS next_renewal_date,
  CASE
    WHEN b.renewal_month IS NULL THEN NULL
    ELSE
      (
        CASE
          WHEN EXTRACT(MONTH FROM CURRENT_DATE)::int > b.renewal_month
               OR (EXTRACT(MONTH FROM CURRENT_DATE)::int = b.renewal_month AND CURRENT_DATE > DATE_TRUNC('month', CURRENT_DATE)::date)
          THEN (DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int + 1, b.renewal_month, 1))::date)
          ELSE (DATE_TRUNC('month', make_date(EXTRACT(YEAR FROM CURRENT_DATE)::int, b.renewal_month, 1))::date)
        END
      ) - (b.notice_days * INTERVAL '1 day')
  END::date AS campaign_window_start
FROM base b;

-- 5.6 company.vw_due_renewals_ready → in window AND has ≥1 green contact
CREATE OR REPLACE VIEW company.vw_due_renewals_ready AS
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

COMMIT;

-- Notes:
-- * Scraper "zero wandering" queues:
--     - company.next_company_urls_30d
--     - people.next_profile_urls_30d
--     - people.due_email_recheck_30d
--   Pattern: SELECT → scrape/verify → UPDATE timestamp → item disappears automatically.
--
-- * To stamp completion:
--   UPDATE company.company SET last_site_checked_at = now() WHERE company_id = $1;  -- site
--   UPDATE company.company SET last_linkedin_checked_at = now() WHERE company_id = $1;  -- linkedin
--   UPDATE company.company SET last_news_checked_at = now() WHERE company_id = $1;  -- news
--   UPDATE people.contact SET last_profile_checked_at = now() WHERE contact_id = $1;  -- profiles
--   UPDATE people.contact_verification SET email_checked_at = now(), email_status = $status WHERE contact_id = $1;  -- verify