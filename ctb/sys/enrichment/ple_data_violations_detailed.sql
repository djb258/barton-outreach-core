-- ============================================================================
-- PLE DATA VIOLATION DETAILED REPORT
-- ============================================================================
-- Barton ID: 04.04.02.04.50000.003
-- Purpose: Identify specific records with constraint violations
-- Generated: 2025-11-26
-- ============================================================================

-- ============================================================================
-- VIOLATION 1: Employee Count Range (16 violations)
-- ============================================================================

SELECT
    company_unique_id,
    company_name,
    employee_count,
    CASE
        WHEN employee_count < 50 THEN 'Below minimum (50)'
        WHEN employee_count > 2000 THEN 'Above maximum (2000)'
    END as violation_type,
    'Set to NULL or correct value' as recommended_action
FROM marketing.company_master
WHERE employee_count IS NOT NULL
AND (employee_count < 50 OR employee_count > 2000)
ORDER BY employee_count DESC;

-- Suggested fix:
-- Option 1: Set violating employee_counts to NULL
-- UPDATE marketing.company_master
-- SET employee_count = NULL, updated_at = NOW()
-- WHERE employee_count IS NOT NULL
-- AND (employee_count < 50 OR employee_count > 2000);

-- Option 2: Manually correct if data is known to be accurate
-- (Review each record individually)

-- ============================================================================
-- VIOLATION 2: NULL created_at in company_master
-- ============================================================================

SELECT
    company_unique_id,
    company_name,
    source_system,
    promoted_from_intake_at,
    'created_at IS NULL' as violation,
    'Set to promoted_from_intake_at or NOW()' as recommended_action
FROM marketing.company_master
WHERE created_at IS NULL
LIMIT 20;

-- Count total NULL created_at
SELECT COUNT(*) as null_created_at_count
FROM marketing.company_master
WHERE created_at IS NULL;

-- Suggested fix:
-- Option 1: Use promoted_from_intake_at as created_at
-- UPDATE marketing.company_master
-- SET created_at = promoted_from_intake_at, updated_at = NOW()
-- WHERE created_at IS NULL AND promoted_from_intake_at IS NOT NULL;

-- Option 2: Use current timestamp for remaining NULLs
-- UPDATE marketing.company_master
-- SET created_at = NOW(), updated_at = NOW()
-- WHERE created_at IS NULL;

-- ============================================================================
-- VIOLATION 3: NULL created_at in people_master
-- ============================================================================

SELECT
    unique_id,
    first_name,
    last_name,
    company_unique_id,
    source_system,
    promoted_from_intake_at,
    'created_at IS NULL' as violation,
    'Set to promoted_from_intake_at or NOW()' as recommended_action
FROM marketing.people_master
WHERE created_at IS NULL
LIMIT 20;

-- Count total NULL created_at
SELECT COUNT(*) as null_created_at_count
FROM marketing.people_master
WHERE created_at IS NULL;

-- Suggested fix:
-- Option 1: Use promoted_from_intake_at as created_at
-- UPDATE marketing.people_master
-- SET created_at = promoted_from_intake_at, updated_at = NOW()
-- WHERE created_at IS NULL AND promoted_from_intake_at IS NOT NULL;

-- Option 2: Use current timestamp for remaining NULLs
-- UPDATE marketing.people_master
-- SET created_at = NOW(), updated_at = NOW()
-- WHERE created_at IS NULL;

-- ============================================================================
-- VALIDATION: Check for other potential issues
-- ============================================================================

-- Check for duplicate company_slot combinations
SELECT
    company_unique_id,
    slot_type,
    COUNT(*) as duplicate_count,
    string_agg(company_slot_unique_id, ', ') as slot_ids
FROM marketing.company_slot
GROUP BY company_unique_id, slot_type
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC;

-- Check slot_type values (should all be CEO, CFO, or HR)
SELECT
    slot_type,
    COUNT(*) as count
FROM marketing.company_slot
GROUP BY slot_type
ORDER BY count DESC;

-- Check for people without contact info
SELECT
    unique_id,
    first_name,
    last_name,
    company_unique_id,
    email,
    linkedin_url,
    'No contact info' as violation
FROM marketing.people_master
WHERE linkedin_url IS NULL AND email IS NULL
LIMIT 20;

-- Check for invalid state codes
SELECT
    address_state,
    COUNT(*) as count
FROM marketing.company_master
WHERE address_state IS NOT NULL
GROUP BY address_state
ORDER BY count DESC;

-- ============================================================================
-- SUMMARY STATS
-- ============================================================================

SELECT
    'employee_count violations' as issue,
    COUNT(*) as count
FROM marketing.company_master
WHERE employee_count IS NOT NULL
AND (employee_count < 50 OR employee_count > 2000)

UNION ALL

SELECT
    'company_master NULL created_at' as issue,
    COUNT(*) as count
FROM marketing.company_master
WHERE created_at IS NULL

UNION ALL

SELECT
    'people_master NULL created_at' as issue,
    COUNT(*) as count
FROM marketing.people_master
WHERE created_at IS NULL

UNION ALL

SELECT
    'duplicate company_slot' as issue,
    COUNT(*) as count
FROM (
    SELECT company_unique_id, slot_type
    FROM marketing.company_slot
    GROUP BY company_unique_id, slot_type
    HAVING COUNT(*) > 1
) sub

UNION ALL

SELECT
    'people without contact info' as issue,
    COUNT(*) as count
FROM marketing.people_master
WHERE linkedin_url IS NULL AND email IS NULL

UNION ALL

SELECT
    'invalid state codes' as issue,
    COUNT(*) as count
FROM marketing.company_master
WHERE address_state IS NOT NULL
AND address_state NOT IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky');

-- ============================================================================
-- END OF DETAILED VIOLATION REPORT
-- ============================================================================
