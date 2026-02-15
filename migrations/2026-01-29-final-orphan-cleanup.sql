-- =============================================================================
-- FINAL ORPHAN CLEANUP: Complete CL-Outreach Alignment
-- =============================================================================
-- Date: 2026-01-29
-- Purpose: Clean remaining forward and reverse orphans after consolidation
-- Target: Zero orphans in both directions
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Move remaining forward orphans to excluded
-- (outreach records without valid CL PASS)
-- =============================================================================

-- Forward orphans: NOT_IN_CL (sovereign_id doesn't exist in CL at all)
INSERT INTO outreach.outreach_excluded (
    outreach_id, company_name, domain, exclusion_reason,
    sovereign_id, cl_status, excluded_at, created_at, updated_at
)
SELECT
    o.outreach_id,
    NULL,
    o.domain,
    'NOT_IN_CL: sovereign_id does not exist in cl.company_identity',
    o.sovereign_id,
    'NOT_IN_CL',
    NOW(),
    o.created_at,
    o.updated_at
FROM outreach.outreach o
WHERE NOT EXISTS (
    SELECT 1 FROM cl.company_identity ci
    WHERE ci.company_unique_id = o.sovereign_id
)
ON CONFLICT (outreach_id) DO NOTHING;

-- Forward orphans: CL exists but not PASS
INSERT INTO outreach.outreach_excluded (
    outreach_id, company_name, domain, exclusion_reason,
    sovereign_id, cl_status, excluded_at, created_at, updated_at
)
SELECT
    o.outreach_id,
    ci.canonical_name,
    o.domain,
    'CL_NOT_PASS: identity_status=' || ci.identity_status,
    o.sovereign_id,
    ci.identity_status::text,
    NOW(),
    o.created_at,
    o.updated_at
FROM outreach.outreach o
JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
WHERE ci.identity_status != 'PASS'
ON CONFLICT (outreach_id) DO NOTHING;

-- =============================================================================
-- STEP 2: Cascade delete forward orphans from sub-hubs
-- =============================================================================

DELETE FROM outreach.company_target ct
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = ct.outreach_id
    AND ci.identity_status = 'PASS'
);

DELETE FROM outreach.dol d
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = d.outreach_id
    AND ci.identity_status = 'PASS'
);

DELETE FROM outreach.blog b
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = b.outreach_id
    AND ci.identity_status = 'PASS'
);

DELETE FROM outreach.bit_scores bs
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = bs.outreach_id
    AND ci.identity_status = 'PASS'
);

DELETE FROM people.company_slot cs
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = cs.outreach_id
    AND ci.identity_status = 'PASS'
);

-- =============================================================================
-- STEP 3: Delete forward orphans from outreach spine
-- =============================================================================

DELETE FROM outreach.outreach o
WHERE NOT EXISTS (
    SELECT 1 FROM cl.company_identity ci
    WHERE ci.company_unique_id = o.sovereign_id
    AND ci.identity_status = 'PASS'
);

-- =============================================================================
-- STEP 4: Clean reverse orphans (CL outreach_ids that don't exist in outreach)
-- Null out orphaned outreach_ids in CL
-- =============================================================================

UPDATE cl.company_identity ci
SET outreach_id = NULL
WHERE ci.outreach_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    WHERE o.outreach_id = ci.outreach_id
);

-- =============================================================================
-- STEP 5: Verify complete alignment
-- =============================================================================

DO $$
DECLARE
    v_outreach_count INTEGER;
    v_cl_with_outreach INTEGER;
    v_forward_orphans INTEGER;
    v_reverse_orphans INTEGER;
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

    RAISE NOTICE '=== FINAL ALIGNMENT VERIFICATION ===';
    RAISE NOTICE 'outreach.outreach count: %', v_outreach_count;
    RAISE NOTICE 'CL with outreach_id: %', v_cl_with_outreach;
    RAISE NOTICE 'Forward orphans: %', v_forward_orphans;
    RAISE NOTICE 'Reverse orphans: %', v_reverse_orphans;

    IF v_outreach_count = v_cl_with_outreach
       AND v_forward_orphans = 0
       AND v_reverse_orphans = 0 THEN
        RAISE NOTICE 'STATUS: FULLY ALIGNED ✓';
    ELSE
        RAISE NOTICE 'STATUS: ALIGNMENT DELTA = %', v_cl_with_outreach - v_outreach_count;
    END IF;
END $$;

COMMIT;
