-- ============================================================================
-- HUNTER.IO DATA ANALYSIS QUERIES
-- ============================================================================
-- Purpose: Quick reference queries for Hunter.io data integration status
-- Generated: 2026-02-05
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. HUNTER COMPANY SUMMARY
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) as total_hunter_companies,
    COUNT(email_pattern) FILTER (WHERE email_pattern IS NOT NULL AND email_pattern != '') as has_pattern,
    COUNT(organization) FILTER (WHERE organization IS NOT NULL) as has_organization,
    COUNT(industry) FILTER (WHERE industry IS NOT NULL) as has_industry,
    COUNT(headcount) FILTER (WHERE headcount IS NOT NULL) as has_headcount,
    COUNT(outreach_id) FILTER (WHERE outreach_id IS NOT NULL) as linked_to_outreach
FROM enrichment.hunter_company;

-- Expected Results (2026-02-05):
-- total: 88,405 | has_pattern: 75,131 (85.0%) | linked: 32,901 (37.2%)

-- ----------------------------------------------------------------------------
-- 2. HUNTER CONTACT SUMMARY
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) as total_hunter_contacts,
    COUNT(email) FILTER (WHERE email IS NOT NULL) as has_email,
    COUNT(first_name) FILTER (WHERE first_name IS NOT NULL) as has_first_name,
    COUNT(last_name) FILTER (WHERE last_name IS NOT NULL) as has_last_name,
    COUNT(job_title) FILTER (WHERE job_title IS NOT NULL) as has_job_title,
    COUNT(department) FILTER (WHERE department IS NOT NULL) as has_department,
    COUNT(seniority_level) FILTER (WHERE seniority_level IS NOT NULL) as has_seniority,
    COUNT(outreach_id) FILTER (WHERE outreach_id IS NOT NULL) as linked_to_outreach
FROM enrichment.hunter_contact;

-- Expected Results (2026-02-05):
-- total: 583,433 | all have email (100%) | job_title: 385,070 (66.0%) | linked: 248,071 (42.5%)

-- ----------------------------------------------------------------------------
-- 3. OUTREACH TO HUNTER MATCH STATISTICS
-- ----------------------------------------------------------------------------
SELECT
    COUNT(DISTINCT o.outreach_id) as outreach_companies,
    COUNT(DISTINCT CASE WHEN hc.domain IS NOT NULL THEN o.outreach_id END) as matched_to_hunter_company,
    COUNT(DISTINCT CASE WHEN hcont.domain IS NOT NULL THEN o.outreach_id END) as matched_to_hunter_contact
FROM outreach.outreach o
LEFT JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
LEFT JOIN enrichment.hunter_contact hcont ON LOWER(o.domain) = LOWER(hcont.domain);

-- Expected Results (2026-02-05):
-- outreach: 95,004 | matched_company: 86,334 (90.9%) | matched_contact: 81,152 (85.4%)

-- ----------------------------------------------------------------------------
-- 4. GAP ANALYSIS: HUNTER PATTERNS NOT IN COMPANY_TARGET
-- ----------------------------------------------------------------------------
SELECT COUNT(DISTINCT o.outreach_id) as can_get_pattern_from_hunter
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NULL
AND hc.email_pattern IS NOT NULL
AND hc.email_pattern != '';

-- Expected Results (2026-02-05):
-- 0 records (RESOLVED - all patterns synced)

-- ----------------------------------------------------------------------------
-- 5. GAP ANALYSIS: HUNTER CONTACTS NOT IN OUTREACH.PEOPLE
-- ----------------------------------------------------------------------------
SELECT COUNT(*) as hunter_contacts_not_in_people
FROM enrichment.hunter_contact hc
WHERE hc.outreach_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM outreach.people p
    WHERE p.email = hc.email
    AND p.outreach_id = hc.outreach_id
);

-- Expected Results (2026-02-05):
-- 248,071 records (CRITICAL GAP - needs sync)

-- ----------------------------------------------------------------------------
-- 6. COMPANY_TARGET PATTERN AVAILABILITY
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) as total_company_target,
    COUNT(email_method) FILTER (WHERE email_method IS NOT NULL) as has_email_method,
    COUNT(verification_status) FILTER (WHERE verification_status = 'VERIFIED') as verified_patterns
FROM outreach.company_target;

-- Expected Results (2026-02-05):
-- total: 94,237 | has_email_method: 81,412 (86.4%)

-- ----------------------------------------------------------------------------
-- 7. SLOT ASSIGNMENT STATUS
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) as total_slots,
    COUNT(person_unique_id) FILTER (WHERE person_unique_id IS NOT NULL) as slots_filled,
    COUNT(DISTINCT outreach_id) as companies_with_slots,
    COUNT(DISTINCT CASE WHEN person_unique_id IS NOT NULL THEN outreach_id END) as companies_with_filled_slots
FROM people.company_slot;

-- Expected Results (2026-02-05):
-- total_slots: 285,012 | filled: 150,832 (52.9%) | companies_filled: 56,709 (59.7%)

-- ----------------------------------------------------------------------------
-- 8. OUTREACH.PEOPLE STATUS
-- ----------------------------------------------------------------------------
SELECT
    COUNT(*) as total_people,
    COUNT(email) FILTER (WHERE email IS NOT NULL) as has_email,
    COUNT(DISTINCT outreach_id) as unique_companies
FROM outreach.people;

-- Expected Results (2026-02-05):
-- total: 324 | has_email: 324 | unique_companies: 241

-- ----------------------------------------------------------------------------
-- 9. SAMPLE: HUNTER PATTERNS NOT IN COMPANY_TARGET (DEBUG QUERY)
-- ----------------------------------------------------------------------------
SELECT
    o.outreach_id,
    o.domain,
    hc.email_pattern as hunter_pattern,
    ct.email_method as ct_pattern
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
JOIN enrichment.hunter_company hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE ct.email_method IS NULL
AND hc.email_pattern IS NOT NULL
AND hc.email_pattern != ''
LIMIT 10;

-- Expected Results (2026-02-05):
-- 0 records (all patterns synced)

-- ----------------------------------------------------------------------------
-- 10. HUNTER CONTACTS BY JOB TITLE (FOR SLOT MAPPING)
-- ----------------------------------------------------------------------------
SELECT
    LOWER(job_title) as normalized_title,
    COUNT(*) as contact_count,
    COUNT(DISTINCT outreach_id) as unique_companies
FROM enrichment.hunter_contact
WHERE outreach_id IS NOT NULL
AND job_title IS NOT NULL
GROUP BY LOWER(job_title)
ORDER BY contact_count DESC
LIMIT 50;

-- Use this to build job_title -> slot_type mapping logic

-- ----------------------------------------------------------------------------
-- 11. HUNTER CONTACTS WITH C-SUITE TITLES (PRIORITIZATION QUERY)
-- ----------------------------------------------------------------------------
SELECT
    hc.outreach_id,
    hc.email,
    hc.first_name,
    hc.last_name,
    hc.job_title,
    hc.department,
    hc.confidence_score,
    CASE
        WHEN LOWER(hc.job_title) LIKE '%chief executive%' OR LOWER(hc.job_title) LIKE '%ceo%' THEN 'CEO'
        WHEN LOWER(hc.job_title) LIKE '%chief financial%' OR LOWER(hc.job_title) LIKE '%cfo%' THEN 'CFO'
        WHEN LOWER(hc.job_title) LIKE '%chief technology%' OR LOWER(hc.job_title) LIKE '%cto%' THEN 'CTO'
        WHEN LOWER(hc.job_title) LIKE '%chief marketing%' OR LOWER(hc.job_title) LIKE '%cmo%' THEN 'CMO'
        WHEN LOWER(hc.job_title) LIKE '%chief operating%' OR LOWER(hc.job_title) LIKE '%coo%' THEN 'COO'
        WHEN LOWER(hc.job_title) LIKE '%human resources%' OR LOWER(hc.job_title) LIKE '%hr director%' THEN 'HR'
        ELSE 'OTHER'
    END as inferred_slot_type
FROM enrichment.hunter_contact hc
WHERE hc.outreach_id IS NOT NULL
AND hc.job_title IS NOT NULL
AND (
    LOWER(hc.job_title) LIKE '%chief%'
    OR LOWER(hc.job_title) LIKE '%ceo%'
    OR LOWER(hc.job_title) LIKE '%cfo%'
    OR LOWER(hc.job_title) LIKE '%cto%'
    OR LOWER(hc.job_title) LIKE '%cmo%'
    OR LOWER(hc.job_title) LIKE '%coo%'
)
ORDER BY hc.confidence_score DESC NULLS LAST
LIMIT 100;

-- Use this to prioritize high-value contacts for slot assignment

-- ----------------------------------------------------------------------------
-- 12. HUNTER DATA QUALITY BY OUTREACH_ID
-- ----------------------------------------------------------------------------
SELECT
    o.outreach_id,
    o.domain,
    hcomp.email_pattern,
    hcomp.industry,
    hcomp.headcount,
    COUNT(hcont.id) as hunter_contact_count,
    COUNT(hcont.email) FILTER (WHERE hcont.job_title IS NOT NULL) as contacts_with_title,
    AVG(hcont.confidence_score) as avg_confidence_score,
    MAX(hcont.confidence_score) as max_confidence_score
FROM outreach.outreach o
LEFT JOIN enrichment.hunter_company hcomp ON LOWER(o.domain) = LOWER(hcomp.domain)
LEFT JOIN enrichment.hunter_contact hcont ON LOWER(o.domain) = LOWER(hcont.domain)
GROUP BY o.outreach_id, o.domain, hcomp.email_pattern, hcomp.industry, hcomp.headcount
HAVING COUNT(hcont.id) > 0
ORDER BY hunter_contact_count DESC
LIMIT 100;

-- Use this to identify companies with the richest Hunter data

-- ----------------------------------------------------------------------------
-- 13. COMPANIES WITH HUNTER CONTACTS BUT NO SLOTS FILLED
-- ----------------------------------------------------------------------------
SELECT
    o.outreach_id,
    o.domain,
    COUNT(hcont.id) as hunter_contact_count,
    COUNT(cs.slot_id) as total_slots,
    COUNT(cs.person_unique_id) FILTER (WHERE cs.person_unique_id IS NOT NULL) as filled_slots
FROM outreach.outreach o
JOIN enrichment.hunter_contact hcont ON LOWER(o.domain) = LOWER(hcont.domain)
LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
GROUP BY o.outreach_id, o.domain
HAVING COUNT(hcont.id) > 0
AND COUNT(cs.person_unique_id) FILTER (WHERE cs.person_unique_id IS NOT NULL) = 0
ORDER BY hunter_contact_count DESC
LIMIT 100;

-- Use this to identify companies with Hunter data but no slot assignments

-- ============================================================================
-- SYNC TEMPLATE: HUNTER CONTACTS TO OUTREACH.PEOPLE
-- ============================================================================

-- STEP 1: Preview what will be synced (DRY RUN)
SELECT
    hc.outreach_id,
    hc.email,
    hc.first_name,
    hc.last_name,
    hc.job_title,
    hc.department,
    hc.seniority_level,
    hc.linkedin_url,
    hc.confidence_score
FROM enrichment.hunter_contact hc
WHERE hc.outreach_id IS NOT NULL
AND hc.email IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM outreach.people p
    WHERE p.email = hc.email
    AND p.outreach_id = hc.outreach_id
)
LIMIT 10;

-- STEP 2: Actual sync (USE WITH CAUTION)
/*
INSERT INTO outreach.people (
    outreach_id,
    email,
    first_name,
    last_name,
    job_title,
    department,
    seniority_level,
    linkedin_url,
    confidence_score,
    source_system,
    created_at,
    updated_at
)
SELECT
    hc.outreach_id,
    hc.email,
    hc.first_name,
    hc.last_name,
    hc.job_title,
    hc.department,
    hc.seniority_level,
    hc.linkedin_url,
    hc.confidence_score,
    'hunter' as source_system,
    NOW(),
    NOW()
FROM enrichment.hunter_contact hc
WHERE hc.outreach_id IS NOT NULL
AND hc.email IS NOT NULL
ON CONFLICT (email, outreach_id) DO UPDATE SET
    job_title = EXCLUDED.job_title,
    department = EXCLUDED.department,
    seniority_level = EXCLUDED.seniority_level,
    linkedin_url = EXCLUDED.linkedin_url,
    confidence_score = EXCLUDED.confidence_score,
    updated_at = NOW();
*/

-- NOTE: Uncomment and run after testing

-- ============================================================================
-- END OF HUNTER.IO QUERIES
-- ============================================================================
