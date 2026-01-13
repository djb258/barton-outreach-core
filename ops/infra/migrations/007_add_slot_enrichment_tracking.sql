-- ============================================================================
-- Migration 007: Add Enrichment Tracking to Company Slot Table
-- ============================================================================
-- Purpose: Add enrichment_attempts and status fields to company_slot table
--          to support slot evaluation and throttle control
-- Author: Claude Code
-- Created: 2025-11-18
-- Barton ID: 04.04.02.04.50000.007
-- ============================================================================

-- ============================================================================
-- ADD ENRICHMENT TRACKING FIELDS
-- ============================================================================

ALTER TABLE marketing.company_slot
ADD COLUMN IF NOT EXISTS enrichment_attempts INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'open';

-- Add index on status for filtering
CREATE INDEX IF NOT EXISTS idx_company_slot_status ON marketing.company_slot(status);
CREATE INDEX IF NOT EXISTS idx_company_slot_attempts ON marketing.company_slot(enrichment_attempts);

-- ============================================================================
-- UPDATE EXISTING RECORDS
-- ============================================================================

-- Set status based on current is_filled boolean
UPDATE marketing.company_slot
SET status = CASE
    WHEN is_filled = TRUE THEN 'filled'
    WHEN is_filled = FALSE THEN 'open'
    ELSE 'open'
END
WHERE status IS NULL OR status = 'open';

-- ============================================================================
-- ADD COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN marketing.company_slot.enrichment_attempts IS 'Number of enrichment attempts for this slot (0-2+)';
COMMENT ON COLUMN marketing.company_slot.status IS 'Slot status: filled (person found), open (enrichment < 2 attempts), closed_missing (enrichment ≥ 2 attempts)';

-- ============================================================================
-- ADD TRIGGER FOR AUTO-STATUS UPDATE
-- ============================================================================

-- Auto-update status when is_filled changes
CREATE OR REPLACE FUNCTION update_company_slot_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update status based on is_filled and enrichment_attempts
    IF NEW.is_filled = TRUE THEN
        NEW.status = 'filled';
    ELSIF NEW.enrichment_attempts >= 2 THEN
        NEW.status = 'closed_missing';
    ELSE
        NEW.status = 'open';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER company_slot_status_auto_update
    BEFORE INSERT OR UPDATE ON marketing.company_slot
    FOR EACH ROW
    EXECUTE FUNCTION update_company_slot_status();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 007 Complete:';
    RAISE NOTICE '  ✓ Added column: enrichment_attempts (INTEGER DEFAULT 0)';
    RAISE NOTICE '  ✓ Added column: status (VARCHAR(20) DEFAULT open)';
    RAISE NOTICE '  ✓ Created index: idx_company_slot_status';
    RAISE NOTICE '  ✓ Created index: idx_company_slot_attempts';
    RAISE NOTICE '  ✓ Updated existing records with status values';
    RAISE NOTICE '  ✓ Created auto-update trigger for status';
    RAISE NOTICE '  ✓ Added column comments';
    RAISE NOTICE '';
    RAISE NOTICE 'Status Values:';
    RAISE NOTICE '  - filled: Person found and assigned to slot';
    RAISE NOTICE '  - open: No person found, enrichment_attempts < 2';
    RAISE NOTICE '  - closed_missing: No person found, enrichment_attempts ≥ 2';
END $$;
