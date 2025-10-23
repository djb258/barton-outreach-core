-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-2BAD79A1
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

-- ============================================================================
-- Migration: Fix Duplicate Timestamp Columns in marketing.company_slot
-- Date: 2025-10-23
-- Issue: FINAL_COLUMN_COMPLIANCE_REPORT flagged 3 pairs of created_at/updated_at
-- Fix: Remove 2 duplicate pairs, keep single pair at bottom
-- Doctrine Segment: 04.04.05 (company_slot)
-- ============================================================================

/**
 * ISSUE CONTEXT:
 *
 * The create_company_slot.sql migration file (lines 85-94) contains THREE
 * pairs of created_at/updated_at column definitions:
 *
 *   Line 85-86: First pair
 *   Line 89-90: Second pair
 *   Line 93-94: Third pair
 *
 * PostgreSQL only allows one column with each name, causing migration failures.
 *
 * This migration drops the table and recreates it with a single pair of
 * timestamp columns at the bottom (standard practice).
 */

-- ==============================================================================
-- STEP 1: Drop existing table if it exists (preserves data via temp table)
-- ==============================================================================

-- Create backup of existing data
CREATE TEMP TABLE company_slot_backup AS
SELECT * FROM marketing.company_slot;

-- Drop the problematic table
DROP TABLE IF EXISTS marketing.company_slot CASCADE;

-- ==============================================================================
-- STEP 2: Recreate table with correct column definitions (no duplicates)
-- ==============================================================================

CREATE TABLE marketing.company_slot (
    id SERIAL PRIMARY KEY,
    company_slot_unique_id TEXT NOT NULL UNIQUE,
    company_unique_id TEXT NOT NULL,
    slot_type TEXT NOT NULL CHECK (slot_type IN (
        'CEO', 'CFO', 'HR', 'CTO', 'CMO', 'COO',
        'VP_SALES', 'VP_MARKETING', 'DIRECTOR', 'MANAGER'
    )),
    person_unique_id TEXT,
    person_name TEXT,
    person_email TEXT,
    person_phone TEXT,
    person_linkedin_url TEXT,
    person_title TEXT,
    assignment_status TEXT CHECK (assignment_status IN ('filled', 'vacant', 'pending')),
    assigned_at TIMESTAMPTZ,
    last_verified_at TIMESTAMPTZ,
    notes TEXT,

    -- FIXED: Single pair of audit timestamps (was 3 pairs)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Foreign key will be added in next migration
    CONSTRAINT fk_company_slot_company_master
        FOREIGN KEY (company_unique_id)
        REFERENCES marketing.company_master(company_unique_id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

COMMENT ON TABLE marketing.company_slot IS
    'Doctrine Segment 04.04.05: Company role slots (CEO, CFO, HR, etc.).
    FIXED 2025-10-23: Removed duplicate created_at/updated_at column definitions.
    Original issue: 3 pairs defined in lines 85-94 of create_company_slot.sql';

-- ==============================================================================
-- STEP 3: Restore data from backup
-- ==============================================================================

INSERT INTO marketing.company_slot
SELECT * FROM company_slot_backup;

-- ==============================================================================
-- STEP 4: Create indexes
-- ==============================================================================

CREATE INDEX idx_company_slot_company_id ON marketing.company_slot(company_unique_id);
CREATE INDEX idx_company_slot_person_id ON marketing.company_slot(person_unique_id);
CREATE INDEX idx_company_slot_type ON marketing.company_slot(slot_type);
CREATE INDEX idx_company_slot_status ON marketing.company_slot(assignment_status);

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Status: ✅ Duplicate timestamp columns removed
-- Result: Single created_at/updated_at pair at bottom of table definition
-- Compliance: Barton Doctrine 04.04.05 schema naming standards
-- ============================================================================
