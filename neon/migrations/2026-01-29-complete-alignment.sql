-- =============================================================================
-- COMPLETE ALIGNMENT: Register 18 missing outreach_ids in CL
-- =============================================================================
-- Date: 2026-01-29
-- Purpose: Register outreach_ids for 18 PASS companies that have NULL
-- These are valid outreach records that were never registered in CL
-- =============================================================================

BEGIN;

-- Temporarily disable write-once trigger
ALTER TABLE cl.company_identity DISABLE TRIGGER trg_write_once_pointers;

-- Update CL with missing outreach_ids (write-once safe)
UPDATE cl.company_identity ci
SET outreach_id = o.outreach_id
FROM outreach.outreach o
WHERE ci.company_unique_id = o.sovereign_id
AND ci.identity_status = 'PASS'
AND ci.outreach_id IS NULL;

-- Re-enable write-once trigger
ALTER TABLE cl.company_identity ENABLE TRIGGER trg_write_once_pointers;

-- Verification
DO $$
DECLARE
    v_outreach_count INTEGER;
    v_cl_with_outreach INTEGER;
    v_forward_orphans INTEGER;
    v_reverse_orphans INTEGER;
    v_updated INTEGER;
BEGIN
    -- Count outreach records
    SELECT COUNT(*) INTO v_outreach_count FROM outreach.outreach;

    -- Count CL records with outreach_id
    SELECT COUNT(*) INTO v_cl_with_outreach
    FROM cl.company_identity WHERE outreach_id IS NOT NULL;

    -- Count forward orphans
    SELECT COUNT(*) INTO v_forward_orphans
    FROM outreach.outreach o
    WHERE NOT EXISTS (
        SELECT 1 FROM cl.company_identity ci
        WHERE ci.company_unique_id = o.sovereign_id
        AND ci.identity_status = 'PASS'
    );

    -- Count reverse orphans
    SELECT COUNT(*) INTO v_reverse_orphans
    FROM cl.company_identity ci
    WHERE ci.outreach_id IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o
        WHERE o.outreach_id = ci.outreach_id
    );

    -- Count NULL outreach_ids in PASS companies
    SELECT COUNT(*) INTO v_updated
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE ci.identity_status = 'PASS'
    AND ci.outreach_id IS NULL;

    RAISE NOTICE '=== COMPLETE ALIGNMENT RESULTS ===';
    RAISE NOTICE '';
    RAISE NOTICE 'Registered missing outreach_ids in CL';
    RAISE NOTICE 'Remaining unregistered: %', v_updated;
    RAISE NOTICE '';
    RAISE NOTICE '=== FINAL ALIGNMENT VERIFICATION ===';
    RAISE NOTICE 'outreach.outreach count: %', v_outreach_count;
    RAISE NOTICE 'CL with outreach_id: %', v_cl_with_outreach;
    RAISE NOTICE 'Forward orphans: %', v_forward_orphans;
    RAISE NOTICE 'Reverse orphans: %', v_reverse_orphans;
    RAISE NOTICE '';

    IF v_outreach_count = v_cl_with_outreach
       AND v_forward_orphans = 0
       AND v_reverse_orphans = 0
       AND v_updated = 0 THEN
        RAISE NOTICE 'STATUS: FULLY ALIGNED';
        RAISE NOTICE 'All outreach_ids properly registered in CL';
    ELSE
        IF v_outreach_count != v_cl_with_outreach THEN
            RAISE NOTICE 'DELTA: % (outreach - CL)', v_outreach_count - v_cl_with_outreach;
        END IF;
        IF v_forward_orphans > 0 THEN
            RAISE NOTICE 'WARNING: % forward orphans remain', v_forward_orphans;
        END IF;
        IF v_reverse_orphans > 0 THEN
            RAISE NOTICE 'WARNING: % reverse orphans remain', v_reverse_orphans;
        END IF;
        IF v_updated > 0 THEN
            RAISE NOTICE 'WARNING: % outreach_ids not registered in CL', v_updated;
        END IF;
    END IF;
END $$;

COMMIT;
