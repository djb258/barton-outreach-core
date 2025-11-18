-- ============================================================================
-- Migration 008: Add Slot Backfill Tracking to People Raw Intake
-- ============================================================================
-- Purpose: Add slot_type and unique constraint to people_raw_intake table
--          to support slot backfill enrichment from company_slot evaluation
-- Author: Claude Code
-- Created: 2025-11-18
-- Barton ID: 04.04.02.04.50000.008
-- ============================================================================

-- ============================================================================
-- ADD SLOT BACKFILL FIELDS
-- ============================================================================

ALTER TABLE intake.people_raw_intake
ADD COLUMN IF NOT EXISTS slot_type VARCHAR(10),
ADD COLUMN IF NOT EXISTS backfill_source VARCHAR(50);

-- Add index on slot_type
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_slot_type ON intake.people_raw_intake(slot_type);
CREATE INDEX IF NOT EXISTS idx_people_raw_intake_backfill_source ON intake.people_raw_intake(backfill_source);

-- ============================================================================
-- ADD UNIQUE CONSTRAINT TO PREVENT DUPLICATE SLOT BACKFILLS
-- ============================================================================

-- Prevent duplicate backfill entries for same company/slot combination
-- Only applies when source_system = 'slot_backfill'
CREATE UNIQUE INDEX IF NOT EXISTS idx_people_raw_intake_unique_slot_backfill
ON intake.people_raw_intake(company_unique_id, slot_type)
WHERE source_system = 'slot_backfill' AND validated = FALSE;

-- ============================================================================
-- ADD COLUMN COMMENTS
-- ============================================================================

COMMENT ON COLUMN intake.people_raw_intake.slot_type IS 'Leadership slot type for backfill: CEO, CFO, or HR (NULL for non-backfill records)';
COMMENT ON COLUMN intake.people_raw_intake.backfill_source IS 'Backfill trigger source: slot_evaluation, manual, etc. (NULL for non-backfill records)';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Migration 008 Complete:';
    RAISE NOTICE '  ✓ Added column: slot_type (VARCHAR(10))';
    RAISE NOTICE '  ✓ Added column: backfill_source (VARCHAR(50))';
    RAISE NOTICE '  ✓ Created index: idx_people_raw_intake_slot_type';
    RAISE NOTICE '  ✓ Created index: idx_people_raw_intake_backfill_source';
    RAISE NOTICE '  ✓ Created unique constraint: idx_people_raw_intake_unique_slot_backfill';
    RAISE NOTICE '  ✓ Added column comments';
    RAISE NOTICE '';
    RAISE NOTICE 'Slot Backfill Support:';
    RAISE NOTICE '  - Prevents duplicate backfill requests for same company/slot';
    RAISE NOTICE '  - Tracks slot_type (CEO, CFO, HR) for enrichment targeting';
    RAISE NOTICE '  - Tracks backfill_source for audit trail';
END $$;
