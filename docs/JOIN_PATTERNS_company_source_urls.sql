-- ============================================================================
-- JOIN PATTERNS: company.company_source_urls ↔ outreach.outreach
-- ============================================================================
-- Database: Neon PostgreSQL (Marketing DB)
-- Last Updated: 2026-02-02
-- Doctrine: CL Parent-Child v1.1
--
-- IMPORTANT: All joins MUST go through cl.company_identity (authority registry)
-- There is NO direct foreign key from company_source_urls to outreach.outreach
-- ============================================================================

-- ============================================================================
-- PATTERN 1: Company URLs → Outreach (Standard Forward Join)
-- ============================================================================
-- Use When: Finding outreach records for companies with specific URL types
-- Returns: All source URLs linked to their outreach records

SELECT
    csu.id as url_id,
    csu.company_unique_id,
    csu.source_type,
    csu.source_url,
    csu.page_title,
    csu.is_accessible,
    csu.discovered_at,
    --
    o.outreach_id,
    o.sovereign_id,
    o.domain,
    o.created_at as outreach_created_at,
    --
    ci.company_name,
    ci.company_domain
FROM company.company_source_urls csu
INNER JOIN company.company_master cm
    ON csu.company_unique_id = cm.company_unique_id
INNER JOIN cl.company_identity ci
    ON cm.company_unique_id = ci.company_unique_id
INNER JOIN outreach.outreach o
    ON ci.outreach_id = o.outreach_id
WHERE csu.source_type = 'press_page'
  AND csu.is_accessible = true
ORDER BY csu.discovered_at DESC
LIMIT 100;


-- ============================================================================
-- PATTERN 2: Outreach → Company URLs (Reverse Join)
-- ============================================================================
-- Use When: Finding all URLs discovered for companies in outreach
-- Returns: Outreach records with their discovered URLs (if any)

SELECT
    o.outreach_id,
    o.domain,
    o.created_at as outreach_created_at,
    --
    ci.company_unique_id,
    ci.company_name,
    ci.company_domain,
    --
    csu.source_type,
    csu.source_url,
    csu.page_title,
    csu.is_accessible,
    csu.discovered_at
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE o.outreach_id = '12345678-1234-1234-1234-123456789012'
ORDER BY csu.discovered_at DESC;


-- ============================================================================
-- PATTERN 3: Find Companies with NO Discovered URLs
-- ============================================================================
-- Use When: Identifying outreach companies that need URL discovery
-- Returns: Outreach records for companies with zero source URLs

SELECT
    o.outreach_id,
    ci.company_unique_id,
    ci.company_name,
    cm.website_url,
    o.created_at
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
WHERE NOT EXISTS (
    SELECT 1
    FROM company.company_source_urls csu
    WHERE csu.company_unique_id = cm.company_unique_id
)
ORDER BY o.created_at DESC;


-- ============================================================================
-- PATTERN 4: URL Type Coverage by Outreach Company
-- ============================================================================
-- Use When: Analyzing which URL types are discovered for outreach companies
-- Returns: Count of each URL type and accessibility rates

SELECT
    csu.source_type,
    COUNT(DISTINCT cm.company_unique_id) as companies_with_type,
    COUNT(DISTINCT csu.id) as total_urls_of_type,
    COUNT(DISTINCT CASE WHEN csu.is_accessible THEN csu.id END) as accessible_urls,
    ROUND(
        100.0 * COUNT(DISTINCT CASE WHEN csu.is_accessible THEN csu.id END)
        / NULLIF(COUNT(DISTINCT csu.id), 0),
        2
    ) as accessibility_pct
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
INNER JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
GROUP BY csu.source_type
ORDER BY companies_with_type DESC;


-- ============================================================================
-- PATTERN 5: URL Discovery Statistics per Company
-- ============================================================================
-- Use When: Showing overall URL discovery coverage metrics
-- Returns: Per-company counts of discovered URLs and accessibility

SELECT
    o.outreach_id,
    ci.company_name,
    COUNT(DISTINCT csu.source_type) as url_types_found,
    COUNT(DISTINCT csu.id) as total_urls,
    COUNT(DISTINCT CASE WHEN csu.is_accessible THEN csu.id END) as accessible_count,
    MAX(csu.discovered_at) as last_discovery,
    CASE
        WHEN COUNT(DISTINCT csu.id) = 0 THEN 'NO_URLS'
        WHEN COUNT(DISTINCT csu.id) > 0 AND COUNT(CASE WHEN csu.is_accessible THEN 1 END) = 0 THEN 'ALL_INACCESSIBLE'
        ELSE 'OK'
    END as discovery_status
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
GROUP BY o.outreach_id, ci.company_name
ORDER BY total_urls DESC;


-- ============================================================================
-- PATTERN 6: Join with company_target (Outreach Sub-Hub)
-- ============================================================================
-- Use When: Need to join URLs with outreach company targeting data
-- Returns: URLs linked to company targeting information

SELECT
    o.outreach_id,
    ci.company_name,
    ct.outreach_status,
    ct.bit_score_snapshot,
    --
    csu.source_type,
    csu.source_url,
    csu.is_accessible,
    csu.discovered_at
FROM outreach.company_target ct
INNER JOIN outreach.outreach o
    ON ct.outreach_id = o.outreach_id
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE ct.outreach_status = 'active'
ORDER BY ct.bit_score_snapshot DESC NULLS LAST;


-- ============================================================================
-- PATTERN 7: Filter by Source URL Accessibility Status
-- ============================================================================
-- Use When: Only want to analyze accessible/inaccessible URLs
-- Returns: Broken links that might indicate company website issues

SELECT
    o.outreach_id,
    ci.company_name,
    csu.source_type,
    csu.source_url,
    csu.http_status,
    csu.discovered_at
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
INNER JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE csu.is_accessible = false
  AND csu.http_status IS NOT NULL
ORDER BY o.created_at DESC;


-- ============================================================================
-- PATTERN 8: Recent URL Discoveries (Last N Days)
-- ============================================================================
-- Use When: Finding recently discovered URLs for outreach companies
-- Returns: URLs discovered in the last 7 days

SELECT
    o.outreach_id,
    ci.company_name,
    csu.source_type,
    csu.source_url,
    csu.discovered_at,
    AGE(NOW(), csu.discovered_at) as days_since_discovery
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
INNER JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE csu.discovered_at > NOW() - INTERVAL '7 days'
  AND csu.is_accessible = true
ORDER BY csu.discovered_at DESC;


-- ============================================================================
-- PATTERN 9: Multiple URL Types per Company
-- ============================================================================
-- Use When: Finding outreach companies with all key URL types
-- Returns: Companies with leadership, team, and press pages

WITH url_coverage AS (
    SELECT
        cm.company_unique_id,
        MAX(CASE WHEN csu.source_type = 'leadership_page' THEN 1 ELSE 0 END) as has_leadership,
        MAX(CASE WHEN csu.source_type = 'team_page' THEN 1 ELSE 0 END) as has_team,
        MAX(CASE WHEN csu.source_type = 'press_page' THEN 1 ELSE 0 END) as has_press,
        MAX(CASE WHEN csu.source_type = 'about_page' THEN 1 ELSE 0 END) as has_about
    FROM company.company_master cm
    LEFT JOIN company.company_source_urls csu
        ON cm.company_unique_id = csu.company_unique_id
    GROUP BY cm.company_unique_id
)
SELECT
    o.outreach_id,
    ci.company_name,
    uc.has_leadership,
    uc.has_team,
    uc.has_press,
    uc.has_about,
    (uc.has_leadership + uc.has_team + uc.has_press + uc.has_about) as url_type_count
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
INNER JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
INNER JOIN url_coverage uc
    ON cm.company_unique_id = uc.company_unique_id
WHERE (uc.has_leadership + uc.has_team + uc.has_press + uc.has_about) >= 3
ORDER BY url_type_count DESC;


-- ============================================================================
-- PATTERN 10: URL Discovery Audit (Missing Rows Detection)
-- ============================================================================
-- Use When: Checking for data integrity issues between tables
-- Returns: Companies in outreach but missing from company_master

SELECT
    o.outreach_id,
    ci.company_unique_id,
    ci.company_name,
    cm.company_unique_id as cm_present,
    csu.id as csu_present,
    CASE
        WHEN cm.company_unique_id IS NULL THEN 'COMPANY_MASTER_MISSING'
        WHEN csu.id IS NULL THEN 'URLS_NOT_DISCOVERED'
        ELSE 'OK'
    END as data_status
FROM outreach.outreach o
INNER JOIN cl.company_identity ci
    ON o.sovereign_id = ci.company_unique_id
LEFT JOIN company.company_master cm
    ON ci.company_unique_id = cm.company_unique_id
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE cm.company_unique_id IS NULL
   OR csu.id IS NULL;


-- ============================================================================
-- EDGE CASES & NULL HANDLING
-- ============================================================================

-- Case 1: What if outreach_id is NULL in CL?
-- Result: Company won't appear in any outreach.outreach join
SELECT COUNT(*)
FROM cl.company_identity
WHERE outreach_id IS NULL;  -- These companies are NOT in outreach


-- Case 2: What if a company has multiple URLs of same type?
-- Result: Multiple rows returned (one per URL)
SELECT
    cm.company_unique_id,
    COUNT(*) as url_count
FROM company.company_master cm
LEFT JOIN company.company_source_urls csu
    ON cm.company_unique_id = csu.company_unique_id
WHERE cm.company_unique_id = '12345678-1234-1234-1234-123456789012'
GROUP BY cm.company_unique_id;


-- Case 3: company_source_urls with NULL page_title
-- Result: Some URLs may not have extracted titles
SELECT
    csu.source_url,
    csu.page_title
FROM company.company_source_urls csu
WHERE csu.page_title IS NULL
LIMIT 10;


-- ============================================================================
-- PERFORMANCE OPTIMIZATION TIPS
-- ============================================================================

-- Tip 1: Pre-filter outreach companies first (faster than full join)
WITH outreach_companies AS (
    SELECT DISTINCT ci.company_unique_id
    FROM cl.company_identity ci
    WHERE ci.outreach_id IS NOT NULL
)
SELECT csu.*
FROM company.company_source_urls csu
WHERE csu.company_unique_id IN (SELECT company_unique_id FROM outreach_companies);


-- Tip 2: Use INNER JOIN to eliminate NULLs early
SELECT csu.source_type, COUNT(*) as count
FROM company.company_source_urls csu
INNER JOIN cl.company_identity ci
    ON (SELECT company_unique_id FROM company.company_master cm
        WHERE cm.company_unique_id = csu.company_unique_id) = ci.company_unique_id
WHERE ci.outreach_id IS NOT NULL
GROUP BY csu.source_type;


-- Tip 3: Avoid joining all the way to outreach if only company data needed
SELECT
    csu.*,
    cm.website_url,
    ci.company_name
FROM company.company_source_urls csu
INNER JOIN company.company_master cm
    ON csu.company_unique_id = cm.company_unique_id
INNER JOIN cl.company_identity ci
    ON cm.company_unique_id = ci.company_unique_id
WHERE ci.outreach_id IS NOT NULL;  -- Still filter by outreach presence


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify alignment between outreach and company tables
SELECT
    'outreach.outreach' as table_name,
    COUNT(*) as row_count
FROM outreach.outreach
UNION ALL
SELECT
    'cl.company_identity with outreach_id',
    COUNT(*)
FROM cl.company_identity
WHERE outreach_id IS NOT NULL
UNION ALL
SELECT
    'company.company_source_urls',
    COUNT(*)
FROM company.company_source_urls;

-- Show join coverage statistics
SELECT
    (SELECT COUNT(DISTINCT outreach_id) FROM cl.company_identity WHERE outreach_id IS NOT NULL) as companies_in_outreach,
    (SELECT COUNT(DISTINCT company_unique_id) FROM company.company_source_urls) as companies_with_urls,
    (SELECT COUNT(DISTINCT cm.company_unique_id)
     FROM company.company_master cm
     WHERE EXISTS (
        SELECT 1 FROM cl.company_identity ci
        WHERE ci.company_unique_id = cm.company_unique_id
        AND ci.outreach_id IS NOT NULL
     )) as outreach_companies_in_master;

-- ============================================================================
-- END OF PATTERNS
-- ============================================================================
