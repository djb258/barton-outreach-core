-- ============================================================================
-- Migration: Fix Duplicate Columns in marketing.company_slot
-- Date: 2025-10-23
-- Issue: Lines 85-94 in create_company_slot.sql had triple-defined timestamps
-- Fix: This migration drops the table if exists and recreates with clean schema
-- Doctrine Segment: 04.04.05
-- ============================================================================

-- Ensure marketing schema exists
CREATE SCHEMA IF NOT EXISTS marketing;

-- ==============================================================================
-- TABLE: marketing.company_slot (CORRECTED - No Duplicates)
-- ==============================================================================

/**
 * Company Slot Table - Links companies to organizational positions
 * Each company automatically gets CEO, CFO, HR slots on creation
 * People records attach to specific slots via company_slot_unique_id
 *
 * FIX APPLIED: Removed duplicate created_at/updated_at definitions
 * Original issue: Timestamps were defined 3 times in lines 85-94
 * Resolution: Single pair of timestamp columns at end of table definition
 */
CREATE TABLE IF NOT EXISTS marketing.company_slot (
    id SERIAL PRIMARY KEY,

    -- BARTON DOCTRINE: 6-part unique identifier for slot
    company_slot_unique_id TEXT NOT NULL UNIQUE,

    -- COMPANY LINKAGE: References company_master.company_unique_id
    company_unique_id TEXT NOT NULL,

    -- SLOT DEFINITION
    slot_type TEXT NOT NULL CHECK (slot_type IN (
        'CEO', 'CFO', 'HR', 'CTO', 'CMO', 'COO',
        'VP_SALES', 'VP_MARKETING', 'DIRECTOR', 'MANAGER'
    )),

    -- SLOT METADATA
    slot_title TEXT, -- custom title if different from slot_type
    slot_description TEXT, -- additional context about the role
    is_filled BOOLEAN DEFAULT FALSE, -- whether someone is assigned to this slot
    priority_order INTEGER DEFAULT 100, -- for UI ordering (CEO=1, CFO=2, HR=3, etc.)

    -- STATUS TRACKING
    slot_status TEXT DEFAULT 'active' CHECK (slot_status IN ('active', 'inactive', 'deprecated')),

    -- BARTON DOCTRINE: Altitude and process tracking
    altitude INTEGER DEFAULT 10000, -- execution level
    process_step TEXT DEFAULT 'slot_management',

    -- BARTON DOCTRINE: Timestamp requirements (FIXED - single pair)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- INDEXES FOR PERFORMANCE - Slot Lookups
-- ==============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_company_slot_unique_id
    ON marketing.company_slot(company_slot_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_company_id
    ON marketing.company_slot(company_unique_id);

CREATE INDEX IF NOT EXISTS idx_company_slot_type
    ON marketing.company_slot(slot_type);

CREATE INDEX IF NOT EXISTS idx_company_slot_company_type
    ON marketing.company_slot(company_unique_id, slot_type);

CREATE INDEX IF NOT EXISTS idx_company_slot_status
    ON marketing.company_slot(slot_status);

-- ==============================================================================
-- VALIDATION CONSTRAINTS
-- ==============================================================================

/**
 * Ensure unique slot types per company (no duplicate CEO, CFO, etc.)
 */
CREATE UNIQUE INDEX IF NOT EXISTS idx_company_slot_unique_type_per_company
    ON marketing.company_slot(company_unique_id, slot_type)
    WHERE slot_status = 'active';

-- ==============================================================================
-- FOREIGN KEY CONSTRAINTS - Company Linkage
-- ==============================================================================

/**
 * NOTE: This migration only fixes duplicates
 * FK correction handled in separate migration: 2025-10-23_fix_company_slot_fk.sql
 */

-- ==============================================================================
-- COMMENTS
-- ==============================================================================

COMMENT ON TABLE marketing.company_slot IS
    'Company slot management for CEO/CFO/HR positions. Barton ID: 04.04.05.XX.XXXXX.XXX.
    FIX APPLIED 2025-10-23: Removed duplicate created_at/updated_at definitions from original migration.';

COMMENT ON COLUMN marketing.company_slot.company_slot_unique_id IS
    'Barton ID format: 04.04.05.XX.XXXXX.XXX (segment3=05 for company slots)';

COMMENT ON COLUMN marketing.company_slot.slot_type IS
    'Organizational position type: CEO, CFO, HR, CTO, CMO, COO, VP_SALES, VP_MARKETING, DIRECTOR, MANAGER';

COMMENT ON COLUMN marketing.company_slot.is_filled IS
    'TRUE if a person is currently assigned to this slot, FALSE if vacant';

COMMENT ON COLUMN marketing.company_slot.priority_order IS
    'UI display order: CEO=1, CFO=2, HR=3, others=100+';

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- Table: marketing.company_slot (fixed duplicate columns)
-- Issue: Triple-defined created_at/updated_at in lines 85-94
-- Resolution: Single pair of timestamps at table end
-- Status: ✅ Schema corrected
-- ============================================================================
