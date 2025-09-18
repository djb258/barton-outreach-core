-- Lean + Useful Improvements (Indexes, Validation, Health, Retention)
-- Safe to run multiple times.

BEGIN;

------------------------------------------------------------
-- 1) INDEXES
------------------------------------------------------------

-- Email verification scans (status, recency)
CREATE INDEX IF NOT EXISTS idx_verif_status_checked
  ON people.contact_verification (email_status, email_checked_at);

-- Renewal scans (month optimization)
CREATE INDEX IF NOT EXISTS idx_company_renewal_month
  ON company.company (renewal_month);

-- Time-range queries over large message logs -> BRIN is tiny & fast to maintain
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname='marketing' AND indexname='brin_message_log_created_at'
  ) THEN
    CREATE INDEX brin_message_log_created_at
      ON marketing.message_log
      USING BRIN (created_at);
  END IF;
END$$;

------------------------------------------------------------
-- 2) DUPLICATE PROTECTION (emails)
------------------------------------------------------------

-- Allow many NULLs but enforce uniqueness for real emails (case-insensitive)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname='people' AND indexname='uq_contact_email_ci'
  ) THEN
    CREATE UNIQUE INDEX uq_contact_email_ci
      ON people.contact (LOWER(email))
      WHERE email IS NOT NULL;
  END IF;
END$$;

------------------------------------------------------------
-- 3) LIGHT VALIDATION (email + URL)
------------------------------------------------------------

-- SIMPLE email shape (keep regex minimal; app can be stricter)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.constraint_column_usage 
    WHERE constraint_name = 'contact_email_format_ck'
  ) THEN
    ALTER TABLE people.contact
      ADD CONSTRAINT contact_email_format_ck
      CHECK (
        email IS NULL
        OR email ~* '^[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}$'
      )
      NOT VALID;
  END IF;
END$$;

-- Website/LinkedIn/News URLs should start with http(s)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.constraint_column_usage 
    WHERE constraint_name = 'company_urls_format_ck'
  ) THEN
    ALTER TABLE company.company
      ADD CONSTRAINT company_urls_format_ck
      CHECK (
        (website_url  IS NULL OR website_url  ~* '^https?://')
        AND (linkedin_url IS NULL OR linkedin_url ~* '^https?://')
        AND (news_url     IS NULL OR news_url     ~* '^https?://')
      )
      NOT VALID;
  END IF;
END$$;

-- (Optional) Validate on existing rows later:
--   ALTER TABLE people.contact VALIDATE CONSTRAINT contact_email_format_ck;
--   ALTER TABLE company.company VALIDATE CONSTRAINT company_urls_format_ck;

------------------------------------------------------------
-- 4) HEALTH / MONITORING VIEWS
------------------------------------------------------------

-- Age thresholds you care about (edit if needed)
--  - Company URLs should be checked every 30d
--  - Profiles every 30d
CREATE OR REPLACE VIEW marketing.vw_health_crawl_staleness AS
WITH c AS (
  SELECT
    company_id,
    company_name,
    GREATEST(
      COALESCE(last_site_checked_at,      'epoch'::timestamptz),
      COALESCE(last_linkedin_checked_at,  'epoch'::timestamptz),
      COALESCE(last_news_checked_at,      'epoch'::timestamptz)
    ) AS last_any_checked_at
  FROM company.company
)
SELECT
  COUNT(*)                           AS companies_total,
  COUNT(*) FILTER (WHERE last_any_checked_at IS NULL) AS companies_never_checked,
  COUNT(*) FILTER (WHERE last_any_checked_at < (now() - INTERVAL '30 days')) AS companies_stale_30d
FROM c;

CREATE OR REPLACE VIEW marketing.vw_health_profile_staleness AS
SELECT
  COUNT(*) AS contacts_total,
  COUNT(*) FILTER (WHERE last_profile_checked_at IS NULL) AS contacts_never_checked,
  COUNT(*) FILTER (WHERE last_profile_checked_at < (now() - INTERVAL '30 days')) AS contacts_stale_30d
FROM people.contact;

-- Queue sizes at a glance (should trend to zero when scrapers keep up)
CREATE OR REPLACE VIEW marketing.vw_queue_sizes AS
SELECT
  (SELECT COUNT(*) FROM company.next_company_urls_30d) AS due_company_urls,
  (SELECT COUNT(*) FROM people.next_profile_urls_30d)  AS due_profile_urls,
  (SELECT COUNT(*) FROM people.due_email_recheck_30d)  AS due_email_rechecks;

------------------------------------------------------------
-- 5) SIMPLE RETENTION HOOK (manual/cron)
------------------------------------------------------------

-- Delete old message_log rows (default: 365 days). Call this from a cron or ops job.
CREATE OR REPLACE FUNCTION marketing.prune_message_log(p_older_than INTERVAL DEFAULT INTERVAL '365 days')
RETURNS INTEGER AS $$
DECLARE v_deleted INTEGER;
BEGIN
  WITH gone AS (
    DELETE FROM marketing.message_log
    WHERE created_at IS NOT NULL AND created_at < (now() - p_older_than)
    RETURNING 1
  )
  SELECT COUNT(*) INTO v_deleted FROM gone;
  RETURN v_deleted;
END;
$$ LANGUAGE plpgsql;

-- Example cron call (outside DB):
--   SELECT marketing.prune_message_log('365 days'::interval);

COMMIT;