-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-0533CA43
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: ORBT
-- ─────────────────────────────────────────────


-- Updated At Trigger Function
CREATE OR REPLACE FUNCTION trigger_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Barton ID Generator Function
-- Generates format: NN.NN.NN.NN.NNNNN.NNN
CREATE OR REPLACE FUNCTION generate_barton_id()
RETURNS VARCHAR(23) AS $$
DECLARE
    segment1 VARCHAR(2);
    segment2 VARCHAR(2);
    segment3 VARCHAR(2);
    segment4 VARCHAR(2);
    segment5 VARCHAR(5);
    segment6 VARCHAR(3);
BEGIN
    -- Use timestamp and random for uniqueness
    segment1 := LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0');
    segment2 := LPAD((EXTRACT(MICROSECONDS FROM NOW()) % 100)::TEXT, 2, '0');
    segment3 := LPAD((RANDOM() * 100)::INT::TEXT, 2, '0');
    segment4 := '07'; -- Fixed segment for database records
    segment5 := LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0');
    segment6 := LPAD((RANDOM() * 1000)::INT::TEXT, 3, '0');

    RETURN segment1 || '.' || segment2 || '.' || segment3 || '.' || segment4 || '.' || segment5 || '.' || segment6;
END;
$$ LANGUAGE plpgsql;

-- Barton Doctrine Migration
-- File: create_people_tables
-- Purpose: Database schema migration with Barton ID compliance
-- Requirements: All tables must have unique_id (Barton ID) and audit columns
-- MCP: All access via Composio bridge, no direct connections

-- Ensure schema
CREATE SCHEMA IF NOT EXISTS marketing;

-- =====================================================================
-- PEOPLE RAW INTAKE (minimal shell with doctrine & links)
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketing.people_raw_intake (id BIGSERIAL PRIMARY KEY,
  unique_id TEXT NOT NULL,                 -- Barton 6-part ID
  company_unique_id TEXT NOT NULL,         -- link to company
  company_slot_unique_id TEXT NOT NULL,    -- link to company slot (CEO/CFO/HR/etc.)
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

-- Lookups
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_company_uid
  ON marketing.people_raw_intake (company_unique_id);
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_company_slot_uid
  ON marketing.people_raw_intake (company_slot_unique_id);

-- =====================================================================
-- PEOPLE AUDIT LOG (unified audit, scoped to people ops)
-- =====================================================================
CREATE TABLE IF NOT EXISTS marketing.people_audit_log (id BIGSERIAL PRIMARY KEY,
  unique_id TEXT NOT NULL,                 -- person record's unique_id (same as intake)
  company_unique_id TEXT NOT NULL,
  company_slot_unique_id TEXT NOT NULL,
  process_id TEXT NOT NULL,                -- Verb + Object canon
  altitude INT NOT NULL DEFAULT 10000,     -- Execution layer
  status TEXT NOT NULL,                    -- Success | Failed | Pending
  errors JSONB NOT NULL DEFAULT '[]'::jsonb,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
  source TEXT NOT NULL                     -- e.g., 'scrape-log', 'validation', 'promotion',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW());

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
-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();

-- Trigger for IF
CREATE TRIGGER trigger_IF_updated_at
    BEFORE UPDATE ON IF
    FOR EACH ROW
    EXECUTE FUNCTION trigger_updated_at();
