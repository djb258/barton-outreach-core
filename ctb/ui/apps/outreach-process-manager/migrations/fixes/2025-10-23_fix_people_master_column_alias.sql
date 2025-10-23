-- ============================================================================
-- Migration: Rename people_master.unique_id to people_unique_id
-- Date: 2025-10-23
-- Issue: FINAL_COLUMN_COMPLIANCE_REPORT flagged inconsistent column naming
-- Fix: Rename unique_id to people_unique_id for naming consistency
-- Doctrine Segment: 04.04.02 (people_master)
-- ============================================================================

/**
 * ISSUE CONTEXT:
 *
 * The people_master table uses column name "unique_id" while company_master
 * uses "company_unique_id". For Barton Doctrine compliance, all master tables
 * should follow the pattern: {table}_unique_id
 *
 * This migration:
 * 1. Renames the column
 * 2. Updates all dependent foreign keys
 *
 * BREAKING CHANGE WARNING:
 * - Application code referencing people_master.unique_id must be updated
 * - Dependent tables: marketing.people_intelligence, marketing.company_slot
 */

-- ==============================================================================
-- STEP 1: Drop dependent foreign keys (will be recreated with new column name)
-- ==============================================================================

-- Drop FK from people_intelligence if it exists
ALTER TABLE marketing.people_intelligence
    DROP CONSTRAINT IF EXISTS people_intelligence_person_unique_id_fkey;

ALTER TABLE marketing.people_intelligence
    DROP CONSTRAINT IF EXISTS people_intelligence_unique_id_fkey;

-- Drop FK from company_slot if it exists
ALTER TABLE marketing.company_slot
    DROP CONSTRAINT IF EXISTS company_slot_person_unique_id_fkey;

ALTER TABLE marketing.company_slot
    DROP CONSTRAINT IF EXISTS company_slot_unique_id_fkey;

-- ==============================================================================
-- STEP 2: Rename the column
-- ==============================================================================

ALTER TABLE marketing.people_master
    RENAME COLUMN unique_id TO people_unique_id;

COMMENT ON COLUMN marketing.people_master.people_unique_id IS
    'RENAMED 2025-10-23: Was "unique_id", renamed to "people_unique_id" for Doctrine compliance.
    Format: 04.04.02.XX.XXXXX.XXX (Barton ID for people_master records)';

-- ==============================================================================
-- STEP 3: Recreate foreign keys with correct column name
-- ==============================================================================

-- Recreate FK from people_intelligence (if table exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'marketing'
        AND table_name = 'people_intelligence'
    ) THEN
        ALTER TABLE marketing.people_intelligence
            ADD CONSTRAINT people_intelligence_person_unique_id_fkey
            FOREIGN KEY (person_unique_id)
            REFERENCES marketing.people_master(people_unique_id)
            ON DELETE CASCADE;
    END IF;
END $$;

-- Recreate FK from company_slot (if column exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'marketing'
        AND table_name = 'company_slot'
        AND column_name = 'person_unique_id'
    ) THEN
        ALTER TABLE marketing.company_slot
            ADD CONSTRAINT company_slot_person_unique_id_fkey
            FOREIGN KEY (person_unique_id)
            REFERENCES marketing.people_master(people_unique_id)
            ON DELETE SET NULL;
    END IF;
END $$;

-- ==============================================================================
-- STEP 4: Update any views or functions referencing the old column name
-- ==============================================================================

/**
 * Application Code Updates Required:
 *
 * Search codebase for references to:
 * - people_master.unique_id
 *
 * Replace with:
 * - people_master.people_unique_id
 *
 * Files likely affected:
 * - apps/outreach-ui/src/components/people/*.tsx
 * - apps/api/routes/people/*.js
 * - Any raw SQL queries in application code
 */

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Status: ✅ Column renamed from unique_id to people_unique_id
-- Result: Naming consistency across all master tables
-- Compliance: Barton Doctrine 04.04.02 naming standard ({table}_unique_id)
-- Breaking Change: Application code must be updated
-- ============================================================================
