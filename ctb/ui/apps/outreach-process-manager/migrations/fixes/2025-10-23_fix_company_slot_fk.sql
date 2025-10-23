-- ============================================================================
-- Migration: Fix Foreign Key Reference in marketing.company_slot
-- Date: 2025-10-23
-- Issue: FINAL_COLUMN_COMPLIANCE_REPORT flagged incorrect FK reference
-- Fix: Update FK to reference marketing.company_master instead of intake table
-- Doctrine Segment: 04.04.05 (company_slot)
-- ============================================================================

/**
 * ISSUE CONTEXT:
 *
 * The company_slot table has a foreign key that references intake.company_raw_intake,
 * but the correct reference should be to marketing.company_master (the promoted table).
 *
 * Per Barton Doctrine:
 * - intake.* = raw ingestion layer (temporary)
 * - marketing.* = promoted/master data (authoritative)
 *
 * company_slot should reference the authoritative master table, not the intake table.
 */

-- ==============================================================================
-- STEP 1: Drop existing incorrect foreign key
-- ==============================================================================

ALTER TABLE marketing.company_slot
    DROP CONSTRAINT IF EXISTS fk_company_slot_company;

ALTER TABLE marketing.company_slot
    DROP CONSTRAINT IF EXISTS company_slot_company_unique_id_fkey;

-- ==============================================================================
-- STEP 2: Add correct foreign key to marketing.company_master
-- ==============================================================================

ALTER TABLE marketing.company_slot
    ADD CONSTRAINT fk_company_slot_company_master
    FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

COMMENT ON CONSTRAINT fk_company_slot_company_master ON marketing.company_slot IS
    'FIXED 2025-10-23: References marketing.company_master (promoted table) instead of intake.company_raw_intake.
    Ensures referential integrity with authoritative company master data per Doctrine 04.04.01';

-- ==============================================================================
-- STEP 3: Verify the constraint exists
-- ==============================================================================

/**
 * Verification query (run after migration):
 *
 * SELECT constraint_name, table_name
 * FROM information_schema.table_constraints
 * WHERE constraint_schema = 'marketing'
 *   AND table_name = 'company_slot'
 *   AND constraint_type = 'FOREIGN KEY'
 *   AND constraint_name = 'fk_company_slot_company_master';
 *
 * Expected result: 1 row with constraint_name = 'fk_company_slot_company_master'
 */

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Status: ✅ Foreign key corrected to reference marketing.company_master
-- Result: Proper referential integrity with promoted master table
-- Compliance: Barton Doctrine schema hierarchy (intake → marketing)
-- ============================================================================
