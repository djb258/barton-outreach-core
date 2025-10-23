-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-39ECE9EB
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Last-Mile Patch: ple schema, auto-seed slots, missing triggers, perf indexes
-- Run on your Neon DB. Safe to re-run.

BEGIN;

-- 1) Ensure ple schema exists
CREATE SCHEMA IF NOT EXISTS ple;

-- 2) Helper + trigger to auto-create CEO/CFO/HR for every new company
--    (and backfill for existing companies)

-- 2a) Helper function: ensure three slots exist for a company_id
CREATE OR REPLACE FUNCTION company.ensure_company_slots(p_company_id BIGINT)
RETURNS void AS $$
BEGIN
  -- CEO
  INSERT INTO company.company_slot (company_id, role_code)
  SELECT p_company_id, 'CEO'
  WHERE NOT EXISTS (
    SELECT 1 FROM company.company_slot
    WHERE company_id = p_company_id AND role_code = 'CEO'
  );

  -- CFO
  INSERT INTO company.company_slot (company_id, role_code)
  SELECT p_company_id, 'CFO'
  WHERE NOT EXISTS (
    SELECT 1 FROM company.company_slot
    WHERE company_id = p_company_id AND role_code = 'CFO'
  );

  -- HR
  INSERT INTO company.company_slot (company_id, role_code)
  SELECT p_company_id, 'HR'
  WHERE NOT EXISTS (
    SELECT 1 FROM company.company_slot
    WHERE company_id = p_company_id AND role_code = 'HR'
  );
END;
$$ LANGUAGE plpgsql;

-- 2b) Proper trigger function (uses NEW.company_id)
CREATE OR REPLACE FUNCTION company.trgfn_ensure_slots()
RETURNS trigger AS $$
BEGIN
  PERFORM company.ensure_company_slots(NEW.company_id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2c) AFTER INSERT trigger on company.company
DROP TRIGGER IF EXISTS trg_company_after_insert_slots ON company.company;
CREATE TRIGGER trg_company_after_insert_slots
AFTER INSERT ON company.company
FOR EACH ROW
EXECUTE FUNCTION company.trgfn_ensure_slots();

-- 2d) Backfill existing companies (no-ops where already present)
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT company_id FROM company.company LOOP
    PERFORM company.ensure_company_slots(r.company_id);
  END LOOP;
END$$;

-- 3) Ensure updated_at triggers exist (company, company_slot, people.contact)
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

-- 4) Lean performance indexes (composites + BRIN)
-- 4a) Verification scans: status + recency
CREATE INDEX IF NOT EXISTS idx_verif_status_checked
  ON people.contact_verification (email_status, email_checked_at);

-- 4b) Renewal scans: month optimization
CREATE INDEX IF NOT EXISTS idx_company_renewal_month
  ON company.company (renewal_month);

-- 4c) Large time-range queries over message_log: BRIN on created_at
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

COMMIT;

-- Quick sanity checks (optional)
-- SELECT 'ple schema' AS check, EXISTS(SELECT 1 FROM pg_namespace WHERE nspname='ple') AS ok;
-- SELECT 'trigger slots', EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_company_after_insert_slots') AS ok;
-- SELECT 'trg company', EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_company_updated_at') AS ok;
-- SELECT 'trg slot', EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_company_slot_updated_at') AS ok;
-- SELECT 'trg contact', EXISTS(SELECT 1 FROM pg_trigger WHERE tgname='trg_people_contact_updated_at') AS ok;
-- SELECT 'idx verif', EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_verif_status_checked') AS ok;
-- SELECT 'idx renewal', EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='idx_company_renewal_month') AS ok;
-- SELECT 'idx brin', EXISTS(SELECT 1 FROM pg_indexes WHERE indexname='brin_message_log_created_at') AS ok;