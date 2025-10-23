-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-B55D532D
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────

-- Ensure schema
CREATE SCHEMA IF NOT EXISTS marketing;

-- =====================================================================
-- PEOPLE RAW INTAKE (minimal shell with doctrine & links)
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketing.people_raw_intake (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT NOT NULL,                 -- Barton 6-part ID
  company_unique_id TEXT NOT NULL,         -- link to company
  company_slot_unique_id TEXT NOT NULL,    -- link to company slot (CEO/CFO/HR/etc.)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Lookups
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_company_uid
  ON marketing.people_raw_intake (company_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_company_slot_uid
  ON marketing.people_raw_intake (company_slot_unique_id);

-- =====================================================================
-- PEOPLE AUDIT LOG (unified audit, scoped to people ops)
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketing.people_audit_log (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT NOT NULL,                 -- person record's unique_id (same as intake)
  company_unique_id TEXT NOT NULL,
  company_slot_unique_id TEXT NOT NULL,
  process_id TEXT NOT NULL,                -- Verb + Object canon
  altitude INT NOT NULL DEFAULT 10000,     -- Execution layer
  status TEXT NOT NULL,                    -- Success | Failed | Pending
  errors JSONB NOT NULL DEFAULT '[]'::jsonb,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  source TEXT NOT NULL                     -- e.g., 'scrape-log', 'validation', 'promotion'
);

-- Lookups
CREATE INDEX IF NOT EXISTS idx_people_audit_company_uid_slot_uid
  ON marketing.people_audit_log (company_unique_id, company_slot_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_audit_unique_id_ts
  ON marketing.people_audit_log (unique_id, timestamp DESC);

-- ---------------------------------------------------------------------
-- OPTIONAL: Add real foreign keys later once target tables are fixed.
-- Example (adjust schema/table/column names to your canon):
-- ALTER TABLE marketing.people_raw_intake
--   ADD CONSTRAINT fk_people_raw_company
--   FOREIGN KEY (company_unique_id)
--   REFERENCES marketing.company (unique_id) DEFERRABLE INITIALLY DEFERRED;
--
-- ALTER TABLE marketing.people_raw_intake
--   ADD CONSTRAINT fk_people_raw_company_slot
--   FOREIGN KEY (company_slot_unique_id)
--   REFERENCES marketing.company_slot (unique_id) DEFERRABLE INITIALLY DEFERRED;
--
-- ALTER TABLE marketing.people_audit_log
--   ADD CONSTRAINT fk_people_audit_company
--   FOREIGN KEY (company_unique_id)
--   REFERENCES marketing.company (unique_id) DEFERRABLE INITIALLY DEFERRED;
--
-- ALTER TABLE marketing.people_audit_log
--   ADD CONSTRAINT fk_people_audit_company_slot
--   FOREIGN KEY (company_slot_unique_id)
--   REFERENCES marketing.company_slot (unique_id) DEFERRABLE INITIALLY DEFERRED;