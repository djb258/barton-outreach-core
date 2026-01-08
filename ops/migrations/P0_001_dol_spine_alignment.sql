-- =============================================================================
-- P0 MIGRATION: DOL SPINE ALIGNMENT
-- =============================================================================
-- Migration ID: P0_001
-- Date: 2026-01-08
-- Author: Claude Code (Schema Remediation Engineer)
-- Mode: SAFE MODE - No application code changes, reversible
--
-- PURPOSE:
--   Add outreach_id to dol.ein_linkage table to comply with Spine-First
--   Architecture v1.1. Currently FKs to marketing.company_master.company_unique_id.
--
-- DOCTRINE COMPLIANCE:
--   - All sub-hubs FK to outreach.outreach.outreach_id
--   - sovereign_id is hidden from sub-hubs
--   - Legacy company_unique_id column LEFT IN PLACE (do NOT drop yet)
--
-- ROLLBACK: See P0_001_dol_spine_alignment_ROLLBACK.sql
-- =============================================================================

-- =============================================================================
-- STEP 1: Add outreach_id column to dol.ein_linkage
-- =============================================================================

ALTER TABLE dol.ein_linkage
ADD COLUMN IF NOT EXISTS outreach_id UUID;

COMMENT ON COLUMN dol.ein_linkage.outreach_id IS
'DOL.SPINE.FK | Foreign key to outreach.outreach.outreach_id.
Added 2026-01-08 for Spine-First Architecture v1.1 compliance.
This is the primary identity for Outreach operations.
company_unique_id retained temporarily for backward compatibility.';

-- =============================================================================
-- STEP 2: Backfill outreach_id from spine
-- =============================================================================
-- Strategy: Join through outreach.outreach using sovereign_id mapping
-- The outreach.outreach table has sovereign_id which maps to company_unique_id

UPDATE dol.ein_linkage el
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE el.company_unique_id::UUID = o.sovereign_id
  AND el.outreach_id IS NULL;

-- Log backfill results
DO $$
DECLARE
    v_total INTEGER;
    v_backfilled INTEGER;
    v_missing INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total FROM dol.ein_linkage;
    SELECT COUNT(*) INTO v_backfilled FROM dol.ein_linkage WHERE outreach_id IS NOT NULL;
    v_missing := v_total - v_backfilled;

    RAISE NOTICE 'DOL EIN Linkage Backfill Results:';
    RAISE NOTICE '  Total records: %', v_total;
    RAISE NOTICE '  Backfilled: %', v_backfilled;
    RAISE NOTICE '  Missing outreach_id: % (these need manual resolution)', v_missing;

    -- Log to AIR if we have missing records
    IF v_missing > 0 THEN
        INSERT INTO dol.air_log (
            company_unique_id,
            outreach_context_id,
            event_type,
            event_status,
            event_message,
            event_payload,
            identity_gate_passed,
            identity_anchors_present
        )
        SELECT
            el.company_unique_id,
            el.outreach_context_id,
            'IDENTITY_GATE_FAILED',
            'FAILED',
            'P0 Migration: No matching outreach_id in spine for company_unique_id',
            jsonb_build_object(
                'migration_id', 'P0_001',
                'linkage_id', el.linkage_id,
                'ein', el.ein
            ),
            FALSE,
            jsonb_build_object('outreach_id', FALSE)
        FROM dol.ein_linkage el
        WHERE el.outreach_id IS NULL;
    END IF;
END $$;

-- =============================================================================
-- STEP 3: Add FK constraint (DEFERRED - records may not all have outreach_id)
-- =============================================================================
-- NOTE: FK constraint is NOT added yet because backfill may be incomplete.
-- Add this AFTER all records have outreach_id resolved:
--
-- ALTER TABLE dol.ein_linkage
-- ADD CONSTRAINT fk_ein_linkage_outreach
--     FOREIGN KEY (outreach_id)
--     REFERENCES outreach.outreach(outreach_id)
--     ON DELETE RESTRICT;

-- =============================================================================
-- STEP 4: Add index for outreach_id
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_ein_linkage_outreach_id
ON dol.ein_linkage(outreach_id)
WHERE outreach_id IS NOT NULL;

COMMENT ON INDEX dol.idx_ein_linkage_outreach_id IS
'P0_001 | Index for spine FK lookup. Partial index excludes NULL values.';

-- =============================================================================
-- STEP 5: Create view for records needing resolution
-- =============================================================================

CREATE OR REPLACE VIEW dol.v_ein_linkage_pending_spine AS
SELECT
    el.linkage_id,
    el.company_unique_id,
    el.ein,
    el.source,
    el.filing_year,
    el.outreach_context_id,
    el.created_at,
    el.outreach_id,
    CASE
        WHEN el.outreach_id IS NOT NULL THEN 'RESOLVED'
        WHEN o.outreach_id IS NOT NULL THEN 'RESOLVABLE'
        ELSE 'NO_SPINE_RECORD'
    END AS resolution_status
FROM dol.ein_linkage el
LEFT JOIN outreach.outreach o ON el.company_unique_id::UUID = o.sovereign_id
ORDER BY el.created_at DESC;

COMMENT ON VIEW dol.v_ein_linkage_pending_spine IS
'P0_001 | View showing EIN linkage records and their spine resolution status.
RESOLVED = outreach_id populated
RESOLVABLE = spine record exists, can backfill
NO_SPINE_RECORD = company not in spine, needs investigation';

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these after migration:
--
-- 1. Check backfill coverage:
-- SELECT resolution_status, COUNT(*) FROM dol.v_ein_linkage_pending_spine GROUP BY 1;
--
-- 2. Check column added:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_schema = 'dol' AND table_name = 'ein_linkage' AND column_name = 'outreach_id';
--
-- 3. Check index created:
-- SELECT indexname FROM pg_indexes WHERE schemaname = 'dol' AND indexname = 'idx_ein_linkage_outreach_id';

-- =============================================================================
-- MIGRATION P0_001 COMPLETE
-- =============================================================================
-- CREATED:
--   - dol.ein_linkage.outreach_id column
--   - dol.idx_ein_linkage_outreach_id index
--   - dol.v_ein_linkage_pending_spine view
--
-- BACKFILLED:
--   - outreach_id populated from outreach.outreach spine
--
-- DEFERRED:
--   - FK constraint (pending full backfill resolution)
--   - Dropping company_unique_id (Phase 2)
--
-- NEXT STEPS:
--   1. Review v_ein_linkage_pending_spine for NO_SPINE_RECORD entries
--   2. Resolve missing spine records
--   3. Add FK constraint once all records have outreach_id
-- =============================================================================
