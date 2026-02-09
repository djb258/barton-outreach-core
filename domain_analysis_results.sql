-- ============================================================================
-- DOMAIN-BASED SLOT FILLING ANALYSIS
-- ============================================================================
-- READ-ONLY investigation of Hunter contact matching via domain linkage
-- Date: 2026-02-06
-- ============================================================================

-- Query 1: Hunter contacts matchable via domain
-- ----------------------------------------------------------------------------
SELECT COUNT(DISTINCT hc.domain) as matchable_hunter_domains
FROM enrichment.hunter_contact hc
JOIN outreach.outreach o ON LOWER(hc.domain) = LOWER(o.domain);

-- Expected: ~81,000 domains (based on 85.4% match rate from HUNTER_QUERIES.sql)


-- Query 2: CEO slot fill potential via domain matching
-- ----------------------------------------------------------------------------
SELECT COUNT(*) as fillable_ceo_slots_via_hunter
FROM people.company_slot cs
JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE cs.slot_type = 'CEO'
  AND cs.is_filled = FALSE
  AND cs.person_unique_id IS NULL
  AND (hc.job_title ILIKE '%chief executive%'
       OR hc.job_title ILIKE '%ceo%'
       OR (hc.job_title ILIKE '%president%' AND hc.job_title NOT ILIKE '%vice%'));

-- Context query: Total unfilled CEO slots
SELECT COUNT(*) as total_unfilled_ceo_slots
FROM people.company_slot
WHERE slot_type = 'CEO'
  AND is_filled = FALSE
  AND person_unique_id IS NULL;


-- Query 3: CFO slot fill potential via domain matching
-- ----------------------------------------------------------------------------
SELECT COUNT(*) as fillable_cfo_slots_via_hunter
FROM people.company_slot cs
JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE cs.slot_type = 'CFO'
  AND cs.is_filled = FALSE
  AND cs.person_unique_id IS NULL
  AND (hc.job_title ILIKE '%chief financial%'
       OR hc.job_title ILIKE '%cfo%'
       OR hc.job_title ILIKE '%finance director%');

-- Context query: Total unfilled CFO slots
SELECT COUNT(*) as total_unfilled_cfo_slots
FROM people.company_slot
WHERE slot_type = 'CFO'
  AND is_filled = FALSE
  AND person_unique_id IS NULL;


-- Query 4: HR slot fill potential via domain matching
-- ----------------------------------------------------------------------------
SELECT COUNT(*) as fillable_hr_slots_via_hunter
FROM people.company_slot cs
JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE cs.slot_type = 'HR'
  AND cs.is_filled = FALSE
  AND cs.person_unique_id IS NULL
  AND (hc.job_title ILIKE '%human resources%'
       OR hc.job_title ILIKE '%hr director%'
       OR hc.job_title ILIKE '%hr manager%'
       OR hc.job_title ILIKE '%people operations%');

-- Context query: Total unfilled HR slots
SELECT COUNT(*) as total_unfilled_hr_slots
FROM people.company_slot
WHERE slot_type = 'HR'
  AND is_filled = FALSE
  AND person_unique_id IS NULL;


-- Query 5: Sample CEO slot fills with contact details
-- ----------------------------------------------------------------------------
SELECT
    cs.slot_id,
    cs.outreach_id,
    o.domain,
    hc.email,
    hc.first_name,
    hc.last_name,
    hc.job_title,
    hc.department,
    hc.seniority_level,
    hc.confidence_score,
    hc.linkedin_url
FROM people.company_slot cs
JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
WHERE cs.slot_type = 'CEO'
  AND cs.is_filled = FALSE
  AND cs.person_unique_id IS NULL
  AND (hc.job_title ILIKE '%chief executive%'
       OR hc.job_title ILIKE '%ceo%'
       OR (hc.job_title ILIKE '%president%' AND hc.job_title NOT ILIKE '%vice%'))
ORDER BY hc.confidence_score DESC NULLS LAST
LIMIT 5;


-- Query 6: Check outreach.company_target schema for domain column
-- ----------------------------------------------------------------------------
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'outreach'
  AND table_name = 'company_target'
ORDER BY ordinal_position;

-- Specific check for domain column
SELECT EXISTS (
    SELECT 1
    FROM information_schema.columns
    WHERE table_schema = 'outreach'
      AND table_name = 'company_target'
      AND column_name = 'domain'
) as domain_column_exists_in_company_target;

-- Note: Based on architecture, domain is stored in outreach.outreach table
-- company_target links via outreach_id FK


-- BONUS: Summary statistics
-- ----------------------------------------------------------------------------
SELECT
    'Total Unfilled Slots' as metric,
    COUNT(*) as value
FROM people.company_slot
WHERE is_filled = FALSE AND person_unique_id IS NULL

UNION ALL

SELECT
    'CEO Unfilled' as metric,
    COUNT(*) as value
FROM people.company_slot
WHERE slot_type = 'CEO' AND is_filled = FALSE AND person_unique_id IS NULL

UNION ALL

SELECT
    'CFO Unfilled' as metric,
    COUNT(*) as value
FROM people.company_slot
WHERE slot_type = 'CFO' AND is_filled = FALSE AND person_unique_id IS NULL

UNION ALL

SELECT
    'HR Unfilled' as metric,
    COUNT(*) as value
FROM people.company_slot
WHERE slot_type = 'HR' AND is_filled = FALSE AND person_unique_id IS NULL

UNION ALL

SELECT
    'Hunter Domains' as metric,
    COUNT(DISTINCT domain) as value
FROM enrichment.hunter_contact

UNION ALL

SELECT
    'Hunter Contacts' as metric,
    COUNT(*) as value
FROM enrichment.hunter_contact;

-- ============================================================================
-- END OF ANALYSIS
-- ============================================================================
