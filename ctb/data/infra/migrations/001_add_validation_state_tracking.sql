-- =============================================================
-- MIGRATION 1: Add Validation + State Tracking Columns
-- =============================================================
-- Created: 2025-10-24
-- Database: Marketing DB (white-union-26418370)
-- Status: Ready to Execute

-- 1️⃣ intake.company_raw_intake — add provenance + batch tracking
ALTER TABLE intake.company_raw_intake
ADD COLUMN IF NOT EXISTS state_abbrev TEXT,
ADD COLUMN IF NOT EXISTS import_batch_id TEXT,
ADD COLUMN IF NOT EXISTS validated BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS validation_notes TEXT,
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS validated_by TEXT;

COMMENT ON COLUMN intake.company_raw_intake.import_batch_id IS
'Unique ID for each CSV/state import (e.g. 20251024-WV-BATCH1)';
COMMENT ON COLUMN intake.company_raw_intake.validated IS
'True when record passes doctrinal validation checks';

-- 2️⃣ marketing.company_master — mirror provenance
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS state_abbrev TEXT,
ADD COLUMN IF NOT EXISTS import_batch_id TEXT,
ADD COLUMN IF NOT EXISTS validated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS validated_by TEXT;

-- 3️⃣ Add data quality score (optional future use)
ALTER TABLE marketing.company_master
ADD COLUMN IF NOT EXISTS data_quality_score NUMERIC(5,2);

COMMENT ON COLUMN marketing.company_master.data_quality_score IS
'System-computed field representing confidence / enrichment quality (0-100)';
