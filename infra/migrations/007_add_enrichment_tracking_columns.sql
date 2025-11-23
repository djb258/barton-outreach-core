-- Migration: Add enrichment tracking columns
-- Purpose: Track enrichment attempts for invalid records
-- Date: 2025-11-19

-- Add enrichment tracking to company_invalid
ALTER TABLE marketing.company_invalid
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS enrichment_attempt_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS enrichment_notes TEXT;

-- Add enrichment tracking to people_invalid
ALTER TABLE marketing.people_invalid
ADD COLUMN IF NOT EXISTS last_enrichment_attempt TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS enrichment_attempt_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS enrichment_notes TEXT;

-- Create index for enrichment queries
CREATE INDEX IF NOT EXISTS idx_company_invalid_enrichment
    ON marketing.company_invalid(last_enrichment_attempt, reviewed);

CREATE INDEX IF NOT EXISTS idx_people_invalid_enrichment
    ON marketing.people_invalid(last_enrichment_attempt, reviewed);

-- Comments
COMMENT ON COLUMN marketing.company_invalid.last_enrichment_attempt IS 'Timestamp of last enrichment attempt';
COMMENT ON COLUMN marketing.company_invalid.enrichment_attempt_count IS 'Number of enrichment attempts made';
COMMENT ON COLUMN marketing.company_invalid.enrichment_notes IS 'Notes from enrichment process';

COMMENT ON COLUMN marketing.people_invalid.last_enrichment_attempt IS 'Timestamp of last enrichment attempt';
COMMENT ON COLUMN marketing.people_invalid.enrichment_attempt_count IS 'Number of enrichment attempts made';
COMMENT ON COLUMN marketing.people_invalid.enrichment_notes IS 'Notes from enrichment process';

-- Verification
SELECT 'Added enrichment tracking columns' as status;
