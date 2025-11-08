-- ============================================================================
-- Neon-Only WV Validation Setup
-- ============================================================================
-- Creates validation_log and invalid tables for West Virginia data validation
-- All validation happens within Neon (no Supabase workspace)
-- ============================================================================

-- ──────────────────────────────────────────────────────────────
-- 1. Validation Log Table (shq schema)
-- ──────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS shq;

CREATE TABLE IF NOT EXISTS shq.validation_log (
  id BIGSERIAL PRIMARY KEY,
  batch_id TEXT NOT NULL,
  record_id TEXT NOT NULL,
  entity_type TEXT NOT NULL CHECK (entity_type IN ('company', 'person')),
  source_table TEXT NOT NULL,
  destination_table TEXT NOT NULL,

  -- Validation outcome
  validation_status TEXT NOT NULL CHECK (validation_status IN ('PASSED', 'FAILED')),
  reason_code TEXT,
  validation_errors JSONB,
  validation_warnings JSONB,

  -- Metadata
  timestamp TIMESTAMP DEFAULT now(),
  processing_time_ms INTEGER,
  validator_version TEXT DEFAULT '1.0',

  -- Indexes for performance
  CONSTRAINT unique_batch_record UNIQUE (batch_id, record_id)
);

CREATE INDEX IF NOT EXISTS idx_validation_log_batch_id ON shq.validation_log(batch_id);
CREATE INDEX IF NOT EXISTS idx_validation_log_entity_type ON shq.validation_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_validation_log_status ON shq.validation_log(validation_status);
CREATE INDEX IF NOT EXISTS idx_validation_log_timestamp ON shq.validation_log(timestamp DESC);

COMMENT ON TABLE shq.validation_log IS 'Audit trail for all validation operations (Neon-only WV validation)';

-- ──────────────────────────────────────────────────────────────
-- 2. Company Invalid Table
-- ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.company_invalid (
  id BIGSERIAL PRIMARY KEY,
  company_unique_id TEXT UNIQUE NOT NULL,

  -- Original data (preserved for review)
  company_name TEXT,
  domain TEXT,
  industry TEXT,
  employee_count INTEGER,
  website TEXT,
  phone TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip TEXT,

  -- Validation details
  validation_status TEXT DEFAULT 'FAILED' CHECK (validation_status = 'FAILED'),
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),

  -- Resolution tracking
  reviewed BOOLEAN DEFAULT false,
  reviewed_at TIMESTAMP,
  reviewed_by TEXT,
  resolution_action TEXT, -- 'fix_and_revalidate', 'discard', 'manual_promote'
  resolution_notes TEXT,

  -- Metadata
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.company_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_company_invalid_reason ON marketing.company_invalid(reason_code);
CREATE INDEX IF NOT EXISTS idx_company_invalid_reviewed ON marketing.company_invalid(reviewed);
CREATE INDEX IF NOT EXISTS idx_company_invalid_batch ON marketing.company_invalid(batch_id);
CREATE INDEX IF NOT EXISTS idx_company_invalid_state ON marketing.company_invalid(state);

COMMENT ON TABLE marketing.company_invalid IS 'Failed company validations requiring manual review';

-- ──────────────────────────────────────────────────────────────
-- 3. People Invalid Table
-- ──────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS marketing.people_invalid (
  id BIGSERIAL PRIMARY KEY,
  unique_id TEXT UNIQUE NOT NULL,

  -- Original data (preserved for review)
  full_name TEXT,
  first_name TEXT,
  last_name TEXT,
  email TEXT,
  phone TEXT,
  title TEXT,
  company_name TEXT,
  company_unique_id TEXT,
  linkedin_url TEXT,
  city TEXT,
  state TEXT,

  -- Validation details
  validation_status TEXT DEFAULT 'FAILED' CHECK (validation_status = 'FAILED'),
  reason_code TEXT NOT NULL,
  validation_errors JSONB NOT NULL,
  validation_warnings JSONB,
  failed_at TIMESTAMP DEFAULT now(),

  -- Resolution tracking
  reviewed BOOLEAN DEFAULT false,
  reviewed_at TIMESTAMP,
  reviewed_by TEXT,
  resolution_action TEXT, -- 'fix_and_revalidate', 'discard', 'manual_promote'
  resolution_notes TEXT,

  -- Metadata
  batch_id TEXT,
  source_table TEXT DEFAULT 'marketing.people_raw_wv',
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_people_invalid_reason ON marketing.people_invalid(reason_code);
CREATE INDEX IF NOT EXISTS idx_people_invalid_reviewed ON marketing.people_invalid(reviewed);
CREATE INDEX IF NOT EXISTS idx_people_invalid_batch ON marketing.people_invalid(batch_id);
CREATE INDEX IF NOT EXISTS idx_people_invalid_state ON marketing.people_invalid(state);

COMMENT ON TABLE marketing.people_invalid IS 'Failed people validations requiring manual review';

-- ──────────────────────────────────────────────────────────────
-- 4. Add validation_status columns to master tables if missing
-- ──────────────────────────────────────────────────────────────

-- Add to company_master (if not exists)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name = 'company_master'
    AND column_name = 'validation_status'
  ) THEN
    ALTER TABLE marketing.company_master
    ADD COLUMN validation_status TEXT DEFAULT 'PASSED'
    CHECK (validation_status = 'PASSED');

    ALTER TABLE marketing.company_master
    ADD COLUMN validated_at TIMESTAMP DEFAULT now();

    ALTER TABLE marketing.company_master
    ADD COLUMN batch_id TEXT;
  END IF;
END $$;

-- Add to people_master (if not exists)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name = 'people_master'
    AND column_name = 'validation_status'
  ) THEN
    ALTER TABLE marketing.people_master
    ADD COLUMN validation_status TEXT DEFAULT 'PASSED'
    CHECK (validation_status = 'PASSED');

    ALTER TABLE marketing.people_master
    ADD COLUMN validated_at TIMESTAMP DEFAULT now();

    ALTER TABLE marketing.people_master
    ADD COLUMN batch_id TEXT;
  END IF;
END $$;

-- ──────────────────────────────────────────────────────────────
-- 5. Helper Views
-- ──────────────────────────────────────────────────────────────

-- Validation summary by batch
CREATE OR REPLACE VIEW shq.vw_validation_summary AS
SELECT
  batch_id,
  entity_type,
  validation_status,
  COUNT(*) as record_count,
  MIN(timestamp) as batch_started_at,
  MAX(timestamp) as batch_completed_at,
  ROUND(AVG(processing_time_ms), 2) as avg_processing_time_ms
FROM shq.validation_log
GROUP BY batch_id, entity_type, validation_status
ORDER BY batch_started_at DESC;

-- Invalid records pending review
CREATE OR REPLACE VIEW marketing.vw_invalid_pending_review AS
SELECT
  'company' as entity_type,
  company_unique_id as unique_id,
  company_name as name,
  reason_code,
  failed_at,
  batch_id
FROM marketing.company_invalid
WHERE reviewed = false
UNION ALL
SELECT
  'person' as entity_type,
  unique_id,
  full_name as name,
  reason_code,
  failed_at,
  batch_id
FROM marketing.people_invalid
WHERE reviewed = false
ORDER BY failed_at DESC;

-- ──────────────────────────────────────────────────────────────
-- 6. Auto-update triggers
-- ──────────────────────────────────────────────────────────────

-- Create update function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for company_invalid
DROP TRIGGER IF EXISTS update_company_invalid_updated_at ON marketing.company_invalid;
CREATE TRIGGER update_company_invalid_updated_at
  BEFORE UPDATE ON marketing.company_invalid
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger for people_invalid
DROP TRIGGER IF EXISTS update_people_invalid_updated_at ON marketing.people_invalid;
CREATE TRIGGER update_people_invalid_updated_at
  BEFORE UPDATE ON marketing.people_invalid
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ──────────────────────────────────────────────────────────────
-- 7. Verification Queries
-- ──────────────────────────────────────────────────────────────

-- Check if all tables exist
SELECT
  'shq.validation_log' as table_name,
  EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='shq' AND table_name='validation_log') as exists
UNION ALL
SELECT
  'marketing.company_invalid',
  EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='marketing' AND table_name='company_invalid')
UNION ALL
SELECT
  'marketing.people_invalid',
  EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema='marketing' AND table_name='people_invalid');

-- ============================================================================
-- Setup Complete
-- ============================================================================
-- Tables created:
--   - shq.validation_log (audit trail)
--   - marketing.company_invalid (failed company records)
--   - marketing.people_invalid (failed people records)
--
-- Views created:
--   - shq.vw_validation_summary (batch statistics)
--   - marketing.vw_invalid_pending_review (records needing review)
--
-- Ready for WV validation execution!
-- ============================================================================
