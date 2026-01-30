-- =============================================================================
-- CONSOLIDATE EXCLUSIONS: Clean outreach.outreach, move garbage to excluded
-- =============================================================================
-- Date: 2026-01-29
-- Purpose: Move all orphaned/invalid outreach records to outreach_excluded
-- Result: Clean outreach.outreach table with only valid CL PASS records
--
-- SAFETY: All operations archive data before deletion
-- =============================================================================

BEGIN;

-- =============================================================================
-- STEP 1: Add exclusion_reason categories if not present
-- =============================================================================

-- Ensure outreach_excluded has all needed columns
ALTER TABLE outreach.outreach_excluded
ADD COLUMN IF NOT EXISTS sovereign_id UUID,
ADD COLUMN IF NOT EXISTS cl_status TEXT,
ADD COLUMN IF NOT EXISTS excluded_by TEXT DEFAULT 'consolidation_migration';

-- =============================================================================
-- STEP 2: Move PENDING orphans (698 records)
-- These have CL sovereign_ids but identity_status = PENDING (not PASS)
-- =============================================================================

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
WHERE ci.identity_status = 'PENDING'
ON CONFLICT (outreach_id) DO NOTHING;

-- =============================================================================
-- STEP 3: Move FAIL orphans (2 records)
-- These have CL sovereign_ids but identity_status = FAIL
-- =============================================================================

INSERT INTO outreach.outreach_excluded (
    outreach_id, company_name, domain, exclusion_reason,
    sovereign_id, cl_status, excluded_at, created_at, updated_at
)
SELECT
    o.outreach_id,
    ci.canonical_name,
    o.domain,
    'CL_FAIL: identity_status=FAIL',
    o.sovereign_id,
    ci.identity_status::text,
    NOW(),
    o.created_at,
    o.updated_at
FROM outreach.outreach o
JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
WHERE ci.identity_status = 'FAIL'
ON CONFLICT (outreach_id) DO NOTHING;

-- =============================================================================
-- STEP 4: Move NOT_IN_CL orphans (60 records)
-- These have sovereign_ids that don't exist in cl.company_identity at all
-- =============================================================================

INSERT INTO outreach.outreach_excluded (
    outreach_id, company_name, domain, exclusion_reason,
    sovereign_id, cl_status, excluded_at, created_at, updated_at
)
SELECT
    o.outreach_id,
    NULL,  -- No CL record to get name from
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

-- =============================================================================
-- STEP 5: Cascade delete from sub-hub tables (before deleting from spine)
-- =============================================================================

-- Delete from company_target
DELETE FROM outreach.company_target ct
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = ct.outreach_id
    AND ci.identity_status = 'PASS'
);

-- Delete from dol
DELETE FROM outreach.dol d
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = d.outreach_id
    AND ci.identity_status = 'PASS'
);

-- Delete from blog
DELETE FROM outreach.blog b
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = b.outreach_id
    AND ci.identity_status = 'PASS'
);

-- Delete from bit_scores
DELETE FROM outreach.bit_scores bs
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = bs.outreach_id
    AND ci.identity_status = 'PASS'
);

-- Delete from people.company_slot
DELETE FROM people.company_slot cs
WHERE NOT EXISTS (
    SELECT 1 FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
    WHERE o.outreach_id = cs.outreach_id
    AND ci.identity_status = 'PASS'
);

-- =============================================================================
-- STEP 6: Delete orphans from outreach.outreach spine
-- =============================================================================

DELETE FROM outreach.outreach o
WHERE NOT EXISTS (
    SELECT 1 FROM cl.company_identity ci
    WHERE ci.company_unique_id = o.sovereign_id
    AND ci.identity_status = 'PASS'
);

-- =============================================================================
-- STEP 7: Verify alignment
-- =============================================================================

DO $$
DECLARE
    v_outreach_count INTEGER;
    v_cl_pass_with_outreach INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_outreach_count FROM outreach.outreach;

    SELECT COUNT(*) INTO v_cl_pass_with_outreach
    FROM cl.company_identity ci
    WHERE ci.identity_status = 'PASS'
    AND EXISTS (
        SELECT 1 FROM outreach.outreach o
        WHERE o.sovereign_id = ci.company_unique_id
    );

    RAISE NOTICE '=== POST-CLEANUP ALIGNMENT ===';
    RAISE NOTICE 'outreach.outreach count: %', v_outreach_count;
    RAISE NOTICE 'CL PASS with outreach: %', v_cl_pass_with_outreach;

    IF v_outreach_count = v_cl_pass_with_outreach THEN
        RAISE NOTICE 'STATUS: ALIGNED ✓';
    ELSE
        RAISE NOTICE 'STATUS: MISALIGNED - Delta: %', v_outreach_count - v_cl_pass_with_outreach;
    END IF;
END $$;

COMMIT;

-- =============================================================================
-- POST-MIGRATION VERIFICATION (Run manually)
-- =============================================================================
/*
-- Check exclusion counts by reason
SELECT exclusion_reason, COUNT(*)
FROM outreach.outreach_excluded
GROUP BY exclusion_reason
ORDER BY COUNT(*) DESC;

-- Verify alignment
SELECT
    (SELECT COUNT(*) FROM outreach.outreach) as outreach_count,
    (SELECT COUNT(*) FROM cl.company_identity WHERE identity_status = 'PASS'
     AND EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.sovereign_id = company_unique_id)) as cl_with_outreach;

-- Check for any remaining orphans
SELECT COUNT(*) FROM outreach.outreach o
WHERE NOT EXISTS (
    SELECT 1 FROM cl.company_identity ci
    WHERE ci.company_unique_id = o.sovereign_id
    AND ci.identity_status = 'PASS'
);
*/
