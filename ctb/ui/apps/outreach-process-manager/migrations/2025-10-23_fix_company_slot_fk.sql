-- ============================================================================
-- Migration: Fix Foreign Key in marketing.company_slot
-- Date: 2025-10-23
-- Issue: FK referenced marketing.company_raw_intake instead of marketing.company_master
-- Fix: Drop old FK and create new one pointing to company_master
-- Doctrine Segment: 04.04.05
-- ============================================================================

-- ==============================================================================
-- FOREIGN KEY FIX: company_slot → company_master
-- ==============================================================================

/**
 * Original Issue:
 *   ALTER TABLE marketing.company_slot
 *     ADD CONSTRAINT fk_company_slot_company
 *     FOREIGN KEY (company_unique_id)
 *     REFERENCES marketing.company_raw_intake(company_unique_id)  -- WRONG TABLE
 *
 * Correct Reference:
 *   marketing.company_master is the promoted, validated source of truth
 *   company_raw_intake is the staging/intake table (Step 1)
 *
 * Doctrine Flow:
 *   intake.company_raw_intake → marketing.company_master → marketing.company_slot
 */

-- Drop existing incorrect FK if it exists
ALTER TABLE marketing.company_slot
    DROP CONSTRAINT IF EXISTS fk_company_slot_company;

-- Create correct FK to company_master
ALTER TABLE marketing.company_slot
    ADD CONSTRAINT fk_company_slot_company_master
    FOREIGN KEY (company_unique_id)
    REFERENCES marketing.company_master(company_unique_id)
    ON DELETE CASCADE
    ON UPDATE CASCADE;

-- ==============================================================================
-- VERIFICATION QUERY
-- ==============================================================================

/**
 * Verify FK is correct:
 *
 * SELECT
 *     tc.constraint_name,
 *     tc.table_name,
 *     kcu.column_name,
 *     ccu.table_name AS foreign_table_name,
 *     ccu.column_name AS foreign_column_name
 * FROM information_schema.table_constraints tc
 * JOIN information_schema.key_column_usage kcu
 *     ON tc.constraint_name = kcu.constraint_name
 * JOIN information_schema.constraint_column_usage ccu
 *     ON tc.constraint_name = ccu.constraint_name
 * WHERE tc.table_name = 'company_slot'
 *     AND tc.constraint_type = 'FOREIGN KEY';
 *
 * Expected Result:
 *   constraint_name: fk_company_slot_company_master
 *   table_name: company_slot
 *   column_name: company_unique_id
 *   foreign_table_name: company_master
 *   foreign_column_name: company_unique_id
 */

-- ==============================================================================
-- COMMENTS
-- ==============================================================================

COMMENT ON CONSTRAINT fk_company_slot_company_master ON marketing.company_slot IS
    'Foreign key to marketing.company_master (corrected from company_raw_intake 2025-10-23).
    Enforces Barton Doctrine: slots reference promoted company records, not raw intake.';

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Table: marketing.company_slot
-- Issue: FK pointed to company_raw_intake (intake table)
-- Resolution: FK now points to company_master (promoted table)
-- Constraint Name: fk_company_slot_company_master
-- Status: ✅ Foreign key corrected per Doctrine 04.04.05
-- ============================================================================
