-- ============================================================================
-- BULK COMPANY VALIDATION & PROMOTION
-- Clay intake.company_raw_wv -> company.company_master
-- Processes 62,792+ records in ~10-20 seconds (vs 40+ minutes row-by-row)
-- ============================================================================

-- Step 0: Get current count before
SELECT 'BEFORE: ' || COUNT(*) || ' records in company.company_master' AS status
FROM company.company_master;

-- Step 1: Get next Barton ID sequence number
DO $$
DECLARE
    max_seq INTEGER;
BEGIN
    -- Find highest existing sequence number from Barton IDs
    SELECT COALESCE(MAX(CAST(SPLIT_PART(company_unique_id, '.', 5) AS INTEGER)), 499)
    INTO max_seq
    FROM company.company_master
    WHERE company_unique_id LIKE '04.04.01.%';

    -- Store it for use in later queries
    PERFORM set_config('app.next_barton_seq', (max_seq + 1)::TEXT, FALSE);
    RAISE NOTICE 'Next Barton sequence starting at: %', max_seq + 1;
END $$;

-- Step 2: Create validation results with new Barton IDs
DROP TABLE IF EXISTS _validation_results;
CREATE TEMP TABLE _validation_results AS
WITH numbered_records AS (
    SELECT
        *,
        ROW_NUMBER() OVER (ORDER BY company_unique_id) AS row_seq
    FROM intake.company_raw_wv
),
validation AS (
    SELECT
        r.company_unique_id AS intake_id,
        r.company_name,
        r.domain,
        r.website AS linkedin_url,
        r.industry,
        r.employee_count,
        r.city,
        r.state,
        r.row_seq,

        -- Generate new Barton ID: 04.04.01.XX.XXXXX.XXX
        '04.04.01.' ||
        LPAD(((current_setting('app.next_barton_seq')::INTEGER + r.row_seq - 1) % 99 + 1)::TEXT, 2, '0') || '.' ||
        LPAD((current_setting('app.next_barton_seq')::INTEGER + r.row_seq - 1)::TEXT, 5, '0') || '.' ||
        LPAD(((current_setting('app.next_barton_seq')::INTEGER + r.row_seq - 1) % 1000)::TEXT, 3, '0')
        AS new_barton_id,

        -- Validation checks
        (r.company_name IS NOT NULL AND LENGTH(TRIM(r.company_name)) >= 3) AS name_valid,
        (r.employee_count IS NOT NULL AND r.employee_count >= 50) AS employee_valid,
        (r.state IS NOT NULL AND r.state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')) AS state_valid,
        (r.domain IS NOT NULL AND LENGTH(TRIM(r.domain)) > 0) AS domain_valid,

        -- Overall validation
        (
            r.company_name IS NOT NULL AND LENGTH(TRIM(r.company_name)) >= 3 AND
            r.employee_count IS NOT NULL AND r.employee_count >= 50 AND
            r.state IS NOT NULL AND r.state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK') AND
            r.domain IS NOT NULL AND LENGTH(TRIM(r.domain)) > 0
        ) AS is_valid,

        -- Error messages array
        ARRAY_REMOVE(ARRAY[
            CASE WHEN r.company_name IS NULL OR LENGTH(TRIM(r.company_name)) < 3
                 THEN 'company_name: required and must be >= 3 chars' END,
            CASE WHEN r.employee_count IS NULL
                 THEN 'employee_count: required'
                 WHEN r.employee_count < 50
                 THEN 'employee_count: ' || r.employee_count || ' below minimum 50' END,
            CASE WHEN r.state IS NULL
                 THEN 'state: required'
                 WHEN r.state NOT IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
                 THEN 'state: ' || r.state || ' not in target states' END,
            CASE WHEN r.domain IS NULL OR LENGTH(TRIM(r.domain)) = 0
                 THEN 'domain: required for website_url' END
        ], NULL) AS validation_errors

    FROM numbered_records r
)
SELECT * FROM validation;

-- Create index for faster joins
CREATE INDEX ON _validation_results(intake_id);
CREATE INDEX ON _validation_results(is_valid);

-- Step 3: Show validation summary BEFORE promotion
SELECT
    '============ VALIDATION SUMMARY ============' AS header;

SELECT
    COUNT(*) AS total_records,
    SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) AS valid_count,
    SUM(CASE WHEN NOT is_valid THEN 1 ELSE 0 END) AS invalid_count,
    ROUND(100.0 * SUM(CASE WHEN is_valid THEN 1 ELSE 0 END) / COUNT(*), 2) AS pass_rate_pct
FROM _validation_results;

-- Step 4: Show error breakdown
SELECT
    '============ ERROR BREAKDOWN ============' AS header;

SELECT
    error_type,
    COUNT(*) AS failure_count
FROM (
    SELECT UNNEST(validation_errors) AS error_type
    FROM _validation_results
    WHERE NOT is_valid
) errors
GROUP BY error_type
ORDER BY failure_count DESC;

-- Step 5: Check for duplicates against existing company_master
SELECT
    '============ DUPLICATE CHECK ============' AS header;

SELECT
    COUNT(*) AS duplicate_count
FROM _validation_results v
JOIN company.company_master cm
    ON LOWER(TRIM(v.company_name)) = LOWER(TRIM(cm.company_name))
    AND v.state = cm.address_state
WHERE v.is_valid;

-- Step 6: Insert VALID records into company.company_master (excluding duplicates)
INSERT INTO company.company_master (
    company_unique_id,
    company_name,
    website_url,
    industry,
    employee_count,
    address_city,
    address_state,
    linkedin_url,
    source_system,
    source_record_id,
    import_batch_id,
    validated_at,
    validated_by,
    promoted_from_intake_at
)
SELECT
    v.new_barton_id,
    v.company_name,
    CASE
        WHEN v.domain LIKE 'http%' THEN v.domain
        ELSE 'http://' || v.domain
    END AS website_url,
    v.industry,
    v.employee_count,
    v.city,
    v.state,
    v.linkedin_url,
    'clay_import',
    v.intake_id,  -- Original Clay ID as reference
    'clay_bulk_' || TO_CHAR(NOW(), 'YYYYMMDD_HH24MISS'),
    NOW(),
    'bulk_validate_companies.sql',
    NOW()
FROM _validation_results v
WHERE v.is_valid = TRUE
  -- Exclude duplicates (same company name + state)
  AND NOT EXISTS (
      SELECT 1 FROM company.company_master cm
      WHERE LOWER(TRIM(cm.company_name)) = LOWER(TRIM(v.company_name))
        AND cm.address_state = v.state
  )
ON CONFLICT (company_unique_id) DO NOTHING;

-- Report how many were actually inserted
SELECT
    '============ PROMOTION RESULTS ============' AS header;

SELECT
    (SELECT COUNT(*) FROM _validation_results WHERE is_valid) AS valid_records,
    (SELECT COUNT(*) FROM company.company_master WHERE source_system = 'clay_import') AS promoted_to_master,
    (SELECT COUNT(*) FROM _validation_results v
     JOIN company.company_master cm
         ON LOWER(TRIM(v.company_name)) = LOWER(TRIM(cm.company_name))
         AND v.state = cm.address_state
     WHERE v.is_valid) AS skipped_duplicates;

-- Step 7: Show sample of promoted records
SELECT
    '============ SAMPLE PROMOTED RECORDS ============' AS header;

SELECT
    company_unique_id,
    company_name,
    address_state,
    employee_count,
    website_url
FROM company.company_master
WHERE source_system = 'clay_import'
ORDER BY promoted_from_intake_at DESC
LIMIT 5;

-- Step 8: Final count
SELECT 'AFTER: ' || COUNT(*) || ' records in company.company_master' AS status
FROM company.company_master;

-- Cleanup
DROP TABLE IF EXISTS _validation_results;
