-- ===========================================================================
-- DOL Hunter EIN Enrichment - Phase 1
-- ===========================================================================
-- Purpose: Link Hunter-discovered EINs to existing outreach records via domain matching
-- Date: 2026-02-03
-- Expected Impact: 53 outreach records enriched with EIN data
-- Database: Neon PostgreSQL (Marketing DB)
--
-- IMPORTANT: Review staging results before executing final INSERT/UPDATE
-- ===========================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- STEP 1: Create staging table for domain matches
-- ---------------------------------------------------------------------------
DROP TABLE IF EXISTS temp_hunter_domain_matches;

CREATE TEMP TABLE temp_hunter_domain_matches AS
SELECT
    eu.ein,
    eu.company_name as hunter_name,
    eu.domain as hunter_domain,
    eu.city,
    eu.state,
    o.outreach_id,
    o.sovereign_id,
    o.domain as outreach_domain
FROM dol.ein_urls eu
INNER JOIN outreach.outreach o
    ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND eu.domain IS NOT NULL
  AND o.domain IS NOT NULL;

-- Verify staging results
SELECT
    COUNT(*) as total_matches,
    COUNT(DISTINCT outreach_id) as unique_outreach_ids,
    COUNT(DISTINCT ein) as unique_eins
FROM temp_hunter_domain_matches;

-- Sample matches (for validation)
SELECT * FROM temp_hunter_domain_matches LIMIT 10;

-- ---------------------------------------------------------------------------
-- STEP 2: Analyze current state of matched outreach_ids in outreach.dol
-- ---------------------------------------------------------------------------
SELECT
    hdm.outreach_id,
    hdm.ein as hunter_ein,
    hdm.hunter_name,
    hdm.hunter_domain,
    od.dol_id,
    od.ein as existing_ein,
    od.filing_present as existing_filing_flag,
    CASE
        WHEN od.dol_id IS NULL THEN 'CREATE_NEW_DOL_RECORD'
        WHEN od.ein IS NULL THEN 'UPDATE_NULL_EIN'
        WHEN od.ein = hdm.ein THEN 'ALREADY_LINKED'
        ELSE 'EIN_CONFLICT'
    END as action_required
FROM temp_hunter_domain_matches hdm
LEFT JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
ORDER BY action_required, hdm.outreach_id;

-- Count by action type
SELECT
    CASE
        WHEN od.dol_id IS NULL THEN 'CREATE_NEW_DOL_RECORD'
        WHEN od.ein IS NULL THEN 'UPDATE_NULL_EIN'
        WHEN od.ein = hdm.ein THEN 'ALREADY_LINKED'
        ELSE 'EIN_CONFLICT'
    END as action_required,
    COUNT(*) as count
FROM temp_hunter_domain_matches hdm
LEFT JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
GROUP BY action_required
ORDER BY count DESC;

-- ---------------------------------------------------------------------------
-- STEP 3: Insert new outreach.dol records for outreach_ids without DOL data
-- ---------------------------------------------------------------------------
-- UNCOMMENT TO EXECUTE (review staging results first)
-- INSERT INTO outreach.dol (
--     dol_id,
--     outreach_id,
--     ein,
--     filing_present,
--     funding_type,
--     broker_or_advisor,
--     carrier,
--     created_at,
--     updated_at
-- )
-- SELECT
--     gen_random_uuid(),
--     hdm.outreach_id,
--     hdm.ein,
--     TRUE,  -- Hunter found domain from DOL filing = filing exists
--     NULL,  -- Unknown funding type
--     NULL,  -- Unknown broker/advisor
--     NULL,  -- Unknown carrier
--     NOW(),
--     NOW()
-- FROM temp_hunter_domain_matches hdm
-- LEFT JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
-- WHERE od.dol_id IS NULL;  -- Only insert if no DOL record exists

-- Preview what will be inserted
SELECT
    hdm.outreach_id,
    hdm.ein,
    hdm.hunter_name,
    hdm.hunter_domain,
    'NEW DOL RECORD' as action
FROM temp_hunter_domain_matches hdm
LEFT JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
WHERE od.dol_id IS NULL;

-- ---------------------------------------------------------------------------
-- STEP 4: Update existing outreach.dol records with NULL EINs
-- ---------------------------------------------------------------------------
-- UNCOMMENT TO EXECUTE (review staging results first)
-- UPDATE outreach.dol od
-- SET
--     ein = hdm.ein,
--     filing_present = TRUE,
--     updated_at = NOW()
-- FROM temp_hunter_domain_matches hdm
-- WHERE od.outreach_id = hdm.outreach_id
--   AND od.ein IS NULL;  -- Only update NULL EINs

-- Preview what will be updated
SELECT
    od.dol_id,
    od.outreach_id,
    od.ein as current_ein,
    hdm.ein as new_ein,
    hdm.hunter_name,
    'UPDATE NULL EIN' as action
FROM temp_hunter_domain_matches hdm
INNER JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
WHERE od.ein IS NULL;

-- ---------------------------------------------------------------------------
-- STEP 5: Flag EIN conflicts (different EIN already exists)
-- ---------------------------------------------------------------------------
-- These require manual review - domain match but EIN mismatch suggests:
-- - Company domain changed hands
-- - Hunter matched wrong domain
-- - Subsidiary/DBA relationship
-- - Data quality issue

SELECT
    od.dol_id,
    od.outreach_id,
    od.ein as existing_ein,
    hdm.ein as hunter_ein,
    hdm.hunter_name,
    hdm.hunter_domain,
    od.funding_type,
    od.filing_present,
    'MANUAL_REVIEW_REQUIRED' as action,
    'Domain match but EIN conflict' as reason
FROM temp_hunter_domain_matches hdm
INNER JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
WHERE od.ein IS NOT NULL
  AND od.ein != hdm.ein;

-- ---------------------------------------------------------------------------
-- STEP 6: Verify already-linked records (should match)
-- ---------------------------------------------------------------------------
SELECT
    od.dol_id,
    od.outreach_id,
    od.ein,
    hdm.hunter_name,
    hdm.hunter_domain,
    'ALREADY_LINKED' as status
FROM temp_hunter_domain_matches hdm
INNER JOIN outreach.dol od ON hdm.outreach_id = od.outreach_id
WHERE od.ein = hdm.ein;

-- ---------------------------------------------------------------------------
-- STEP 7: Post-execution validation (run after uncommenting inserts/updates)
-- ---------------------------------------------------------------------------
-- Verify enrichment success
-- UNCOMMENT AFTER EXECUTION:
-- SELECT
--     COUNT(*) as total_enriched,
--     COUNT(CASE WHEN od.created_at::date = CURRENT_DATE THEN 1 END) as created_today,
--     COUNT(CASE WHEN od.updated_at::date = CURRENT_DATE AND od.created_at::date != CURRENT_DATE THEN 1 END) as updated_today
-- FROM outreach.dol od
-- WHERE od.ein IN (
--     SELECT ein FROM dol.ein_urls
--     WHERE discovery_method = 'hunter_dol_enrichment'
-- );

-- ---------------------------------------------------------------------------
-- STEP 8: Cleanup
-- ---------------------------------------------------------------------------
-- Temp table will auto-drop at end of session
-- No cleanup needed

-- ROLLBACK;  -- Uncomment to rollback if reviewing only
-- COMMIT;    -- Uncomment to commit changes after validation

-- ===========================================================================
-- EXECUTION CHECKLIST
-- ===========================================================================
-- [ ] Review staging results (STEP 1)
-- [ ] Check action distribution (STEP 2)
-- [ ] Validate what will be inserted (STEP 3 preview)
-- [ ] Validate what will be updated (STEP 4 preview)
-- [ ] Review EIN conflicts (STEP 5) - expect none or few
-- [ ] Verify already-linked records (STEP 6)
-- [ ] Uncomment INSERT statement (STEP 3)
-- [ ] Uncomment UPDATE statement (STEP 4)
-- [ ] Replace ROLLBACK with COMMIT
-- [ ] Execute transaction
-- [ ] Run post-execution validation (STEP 7)
-- [ ] Document results in ops/master_error_log or audit log
-- ===========================================================================

-- Expected Results:
-- - 53 total matches found
-- - Majority should be "CREATE_NEW_DOL_RECORD" (no existing DOL data)
-- - Some may be "UPDATE_NULL_EIN" (DOL record exists but EIN is NULL)
-- - Few/none should be "EIN_CONFLICT" (requires manual review)
-- - None should be "ALREADY_LINKED" (would indicate prior enrichment)
--
-- Success Criteria:
-- - All 53 matches processed (insert or update)
-- - No data integrity violations
-- - Audit trail in outreach.dol.updated_at timestamps
-- ===========================================================================
