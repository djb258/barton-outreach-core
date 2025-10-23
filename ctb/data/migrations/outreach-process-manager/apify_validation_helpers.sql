-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-1FAE3CEC
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

/**
 * Apify Validation Helpers - Barton Doctrine Pipeline
 * Specialized validation functions for Apify-sourced data
 * Extends core validation system with Apify-specific rules and quality checks
 *
 * Barton Doctrine Rules:
 * - Validation must preserve full audit trail
 * - Quality scoring must be transparent and configurable
 * - All validation failures must include actionable recommendations
 */

-- ==============================================================================
-- APIFY COMPANY VALIDATION HELPERS
-- ==============================================================================

/**
 * Validate Apify company record with enhanced quality checks
 * Returns detailed validation results with scoring and recommendations
 */
CREATE OR REPLACE FUNCTION validate_apify_company(
    company_id TEXT,
    validation_level TEXT DEFAULT 'standard'
)
RETURNS JSONB AS $$
DECLARE
    company_record RECORD;
    validation_score INTEGER := 0;
    validation_issues TEXT[] := ARRAY[]::TEXT[];
    validation_warnings TEXT[] := ARRAY[]::TEXT[];
    quality_metrics JSONB := '{}'::jsonb;
    result JSONB;
BEGIN
    -- Get company record
    SELECT * INTO company_record
    FROM marketing.company_raw_intake
    WHERE company_unique_id = company_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'valid', false,
            'error', 'Company record not found',
            'company_id', company_id
        );
    END IF;

    -- Core field validation (required fields)
    IF company_record.company_name IS NULL OR TRIM(company_record.company_name) = '' THEN
        validation_issues := array_append(validation_issues, 'Company name is required');
    ELSE
        validation_score := validation_score + 25;
        quality_metrics := quality_metrics || jsonb_build_object('has_company_name', true);
    END IF;

    -- Website validation
    IF company_record.website_url IS NULL OR TRIM(company_record.website_url) = '' THEN
        IF validation_level = 'strict' THEN
            validation_issues := array_append(validation_issues, 'Website URL is required in strict mode');
        ELSE
            validation_warnings := array_append(validation_warnings, 'Website URL is missing');
        END IF;
    ELSE
        -- Validate URL format
        IF company_record.website_url ~ '^https?://[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}.*$' THEN
            validation_score := validation_score + 20;
            quality_metrics := quality_metrics || jsonb_build_object('has_valid_website', true);
        ELSE
            validation_warnings := array_append(validation_warnings, 'Website URL format appears invalid');
            quality_metrics := quality_metrics || jsonb_build_object('has_valid_website', false);
        END IF;
    END IF;

    -- Phone validation
    IF company_record.company_phone IS NULL THEN
        validation_warnings := array_append(validation_warnings, 'Phone number is missing');
    ELSE
        -- E.164 format validation
        IF company_record.company_phone ~ '^\+[1-9][0-9]{1,15}$' THEN
            validation_score := validation_score + 15;
            quality_metrics := quality_metrics || jsonb_build_object('has_valid_phone', true);
        ELSE
            validation_warnings := array_append(validation_warnings, 'Phone number format may be invalid');
            quality_metrics := quality_metrics || jsonb_build_object('has_valid_phone', false);
        END IF;
    END IF;

    -- Industry validation
    IF company_record.industry IS NULL OR TRIM(company_record.industry) = '' THEN
        validation_warnings := array_append(validation_warnings, 'Industry classification is missing');
    ELSE
        validation_score := validation_score + 10;
        quality_metrics := quality_metrics || jsonb_build_object('has_industry', true);
    END IF;

    -- Employee count validation
    IF company_record.employee_count IS NOT NULL THEN
        IF company_record.employee_count > 0 AND company_record.employee_count < 1000000 THEN
            validation_score := validation_score + 10;
            quality_metrics := quality_metrics || jsonb_build_object('has_valid_employee_count', true);
        ELSE
            validation_warnings := array_append(validation_warnings, 'Employee count seems unrealistic');
        END IF;
    END IF;

    -- Address completeness check
    IF company_record.address_city IS NOT NULL AND company_record.address_state IS NOT NULL THEN
        validation_score := validation_score + 10;
        quality_metrics := quality_metrics || jsonb_build_object('has_location_data', true);
    ELSE
        validation_warnings := array_append(validation_warnings, 'Location data is incomplete');
    END IF;

    -- Apify-specific validations
    IF company_record.source_system = 'apify' THEN
        -- Check for Apify scraping artifacts
        IF company_record.company_name ILIKE '%error%' OR company_record.company_name ILIKE '%failed%' THEN
            validation_issues := array_append(validation_issues, 'Company name contains scraping error indicators');
        END IF;

        -- Check for placeholder data
        IF company_record.website_url IN ('http://example.com', 'https://example.com', 'N/A', 'n/a') THEN
            validation_warnings := array_append(validation_warnings, 'Website appears to be placeholder data');
        END IF;

        -- Validate source record ID exists
        IF company_record.source_record_id IS NULL OR TRIM(company_record.source_record_id) = '' THEN
            validation_warnings := array_append(validation_warnings, 'Apify source record ID is missing');
        ELSE
            validation_score := validation_score + 10;
            quality_metrics := quality_metrics || jsonb_build_object('has_source_tracking', true);
        END IF;
    END IF;

    -- Calculate final validation status
    DECLARE
        is_valid BOOLEAN := (array_length(validation_issues, 1) IS NULL OR array_length(validation_issues, 1) = 0);
        validation_status TEXT := CASE
            WHEN is_valid AND validation_score >= 80 THEN 'excellent'
            WHEN is_valid AND validation_score >= 60 THEN 'good'
            WHEN is_valid AND validation_score >= 40 THEN 'acceptable'
            WHEN is_valid THEN 'poor'
            ELSE 'failed'
        END;
    BEGIN
        result := jsonb_build_object(
            'company_id', company_id,
            'valid', is_valid,
            'validation_status', validation_status,
            'quality_score', validation_score,
            'max_possible_score', 100,
            'validation_issues', validation_issues,
            'validation_warnings', validation_warnings,
            'quality_metrics', quality_metrics,
            'validation_level', validation_level,
            'validated_at', NOW()
        );
    END;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- APIFY PEOPLE VALIDATION HELPERS
-- ==============================================================================

/**
 * Validate Apify people record with company linkage verification
 * Includes slot assignment validation and professional profile quality checks
 */
CREATE OR REPLACE FUNCTION validate_apify_person(
    person_id TEXT,
    validation_level TEXT DEFAULT 'standard'
)
RETURNS JSONB AS $$
DECLARE
    person_record RECORD;
    company_exists BOOLEAN := false;
    slot_exists BOOLEAN := false;
    validation_score INTEGER := 0;
    validation_issues TEXT[] := ARRAY[]::TEXT[];
    validation_warnings TEXT[] := ARRAY[]::TEXT[];
    quality_metrics JSONB := '{}'::jsonb;
    result JSONB;
BEGIN
    -- Get person record with company and slot details
    SELECT
        p.*,
        c.company_name,
        cs.slot_type,
        cs.is_filled
    INTO person_record
    FROM marketing.people_raw_intake p
    LEFT JOIN marketing.company_raw_intake c ON p.company_unique_id = c.company_unique_id
    LEFT JOIN marketing.company_slot cs ON p.company_slot_unique_id = cs.company_slot_unique_id
    WHERE p.unique_id = person_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'valid', false,
            'error', 'Person record not found',
            'person_id', person_id
        );
    END IF;

    -- Basic name validation
    IF person_record.first_name IS NULL OR TRIM(person_record.first_name) = '' THEN
        validation_issues := array_append(validation_issues, 'First name is required');
    ELSE
        validation_score := validation_score + 20;
        quality_metrics := quality_metrics || jsonb_build_object('has_first_name', true);
    END IF;

    IF person_record.last_name IS NULL OR TRIM(person_record.last_name) = '' THEN
        validation_issues := array_append(validation_issues, 'Last name is required');
    ELSE
        validation_score := validation_score + 20;
        quality_metrics := quality_metrics || jsonb_build_object('has_last_name', true);
    END IF;

    -- Company linkage validation
    company_exists := (person_record.company_name IS NOT NULL);
    IF NOT company_exists THEN
        IF validation_level = 'strict' THEN
            validation_issues := array_append(validation_issues, 'Company linkage is required in strict mode');
        ELSE
            validation_warnings := array_append(validation_warnings, 'Person is not linked to a company');
        END IF;
    ELSE
        validation_score := validation_score + 20;
        quality_metrics := quality_metrics || jsonb_build_object('has_company_linkage', true);
    END IF;

    -- Slot assignment validation
    slot_exists := (person_record.slot_type IS NOT NULL);
    IF NOT slot_exists THEN
        validation_warnings := array_append(validation_warnings, 'Person is not assigned to a company slot');
    ELSE
        validation_score := validation_score + 15;
        quality_metrics := quality_metrics || jsonb_build_object('has_slot_assignment', true);

        -- Check if slot is already filled
        IF person_record.is_filled = TRUE THEN
            validation_warnings := array_append(validation_warnings, 'Assigned slot is already marked as filled');
        END IF;
    END IF;

    -- Job title validation
    IF person_record.title IS NULL OR TRIM(person_record.title) = '' THEN
        validation_warnings := array_append(validation_warnings, 'Job title is missing');
    ELSE
        validation_score := validation_score + 10;
        quality_metrics := quality_metrics || jsonb_build_object('has_job_title', true);
    END IF;

    -- Professional contact information
    IF person_record.email IS NOT NULL AND person_record.email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        validation_score := validation_score + 10;
        quality_metrics := quality_metrics || jsonb_build_object('has_valid_email', true);
    ELSE
        validation_warnings := array_append(validation_warnings, 'Professional email is missing or invalid');
    END IF;

    IF person_record.work_phone_e164 IS NOT NULL AND person_record.work_phone_e164 ~ '^\+[1-9][0-9]{1,15}$' THEN
        validation_score := validation_score + 5;
        quality_metrics := quality_metrics || jsonb_build_object('has_valid_phone', true);
    END IF;

    -- LinkedIn profile validation
    IF person_record.linkedin_url IS NOT NULL THEN
        IF person_record.linkedin_url ~ '^https://www\.linkedin\.com/in/[^/?]+/?(\?.*)?$' THEN
            validation_score := validation_score + 10;
            quality_metrics := quality_metrics || jsonb_build_object('has_valid_linkedin', true);
        ELSE
            validation_warnings := array_append(validation_warnings, 'LinkedIn URL format appears invalid');
        END IF;
    END IF;

    -- Apify-specific validations for people
    IF person_record.source_system = 'apify' THEN
        -- Check for scraping artifacts in names
        IF person_record.first_name ILIKE '%error%' OR person_record.last_name ILIKE '%error%' THEN
            validation_issues := array_append(validation_issues, 'Name contains scraping error indicators');
        END IF;

        -- Validate source record tracking
        IF person_record.source_record_id IS NOT NULL THEN
            validation_score := validation_score + 5;
            quality_metrics := quality_metrics || jsonb_build_object('has_source_tracking', true);
        END IF;
    END IF;

    -- Calculate final validation result
    DECLARE
        is_valid BOOLEAN := (array_length(validation_issues, 1) IS NULL OR array_length(validation_issues, 1) = 0);
        validation_status TEXT := CASE
            WHEN is_valid AND validation_score >= 90 THEN 'excellent'
            WHEN is_valid AND validation_score >= 70 THEN 'good'
            WHEN is_valid AND validation_score >= 50 THEN 'acceptable'
            WHEN is_valid THEN 'poor'
            ELSE 'failed'
        END;
    BEGIN
        result := jsonb_build_object(
            'person_id', person_id,
            'valid', is_valid,
            'validation_status', validation_status,
            'quality_score', validation_score,
            'max_possible_score', 115,
            'validation_issues', validation_issues,
            'validation_warnings', validation_warnings,
            'quality_metrics', quality_metrics,
            'company_linkage', jsonb_build_object(
                'has_company', company_exists,
                'company_name', person_record.company_name,
                'has_slot', slot_exists,
                'slot_type', person_record.slot_type,
                'slot_filled', person_record.is_filled
            ),
            'validation_level', validation_level,
            'validated_at', NOW()
        );
    END;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- BATCH VALIDATION FUNCTIONS
-- ==============================================================================

/**
 * Run comprehensive validation on entire Apify batch
 * Provides batch-level quality metrics and recommendations
 */
CREATE OR REPLACE FUNCTION validate_apify_batch_comprehensive(
    batch_id TEXT,
    validation_level TEXT DEFAULT 'standard'
)
RETURNS JSONB AS $$
DECLARE
    batch_record RECORD;
    company_results JSONB[] := ARRAY[]::JSONB[];
    people_results JSONB[] := ARRAY[]::JSONB[];
    company_summary JSONB;
    people_summary JSONB;
    overall_recommendations TEXT[] := ARRAY[]::TEXT[];
    result JSONB;
    company_id TEXT;
    person_id TEXT;
    temp_result JSONB;
BEGIN
    -- Get batch info
    SELECT * INTO batch_record
    FROM marketing.apify_batch_log
    WHERE batch_unique_id = batch_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'error', 'Batch not found',
            'batch_id', batch_id
        );
    END IF;

    -- Validate companies if batch includes them
    IF batch_record.batch_type IN ('companies', 'mixed') THEN
        FOR company_id IN
            SELECT company_unique_id
            FROM marketing.company_raw_intake
            WHERE source_system = 'apify'
            AND created_at >= batch_record.created_at
            AND created_at < COALESCE(batch_record.completed_at, NOW() + INTERVAL '1 hour')
        LOOP
            temp_result := validate_apify_company(company_id, validation_level);
            company_results := array_append(company_results, temp_result);
        END LOOP;

        -- Summarize company results
        SELECT jsonb_build_object(
            'total_companies', array_length(company_results, 1),
            'valid_companies', (
                SELECT COUNT(*)
                FROM unnest(company_results) AS r
                WHERE (r->>'valid')::boolean = true
            ),
            'average_quality_score', (
                SELECT COALESCE(AVG((r->>'quality_score')::integer), 0)
                FROM unnest(company_results) AS r
                WHERE (r->>'valid')::boolean = true
            ),
            'validation_distribution', jsonb_build_object(
                'excellent', (
                    SELECT COUNT(*)
                    FROM unnest(company_results) AS r
                    WHERE r->>'validation_status' = 'excellent'
                ),
                'good', (
                    SELECT COUNT(*)
                    FROM unnest(company_results) AS r
                    WHERE r->>'validation_status' = 'good'
                ),
                'acceptable', (
                    SELECT COUNT(*)
                    FROM unnest(company_results) AS r
                    WHERE r->>'validation_status' = 'acceptable'
                ),
                'poor', (
                    SELECT COUNT(*)
                    FROM unnest(company_results) AS r
                    WHERE r->>'validation_status' = 'poor'
                ),
                'failed', (
                    SELECT COUNT(*)
                    FROM unnest(company_results) AS r
                    WHERE r->>'validation_status' = 'failed'
                )
            )
        ) INTO company_summary;
    END IF;

    -- Validate people if batch includes them
    IF batch_record.batch_type IN ('people', 'mixed') THEN
        FOR person_id IN
            SELECT unique_id
            FROM marketing.people_raw_intake
            WHERE source_system = 'apify'
            AND created_at >= batch_record.created_at
            AND created_at < COALESCE(batch_record.completed_at, NOW() + INTERVAL '1 hour')
        LOOP
            temp_result := validate_apify_person(person_id, validation_level);
            people_results := array_append(people_results, temp_result);
        END LOOP;

        -- Summarize people results
        SELECT jsonb_build_object(
            'total_people', array_length(people_results, 1),
            'valid_people', (
                SELECT COUNT(*)
                FROM unnest(people_results) AS r
                WHERE (r->>'valid')::boolean = true
            ),
            'average_quality_score', (
                SELECT COALESCE(AVG((r->>'quality_score')::integer), 0)
                FROM unnest(people_results) AS r
                WHERE (r->>'valid')::boolean = true
            ),
            'company_linkage_rate', (
                SELECT COALESCE(
                    AVG(CASE WHEN (r->'quality_metrics'->>'has_company_linkage')::boolean THEN 1 ELSE 0 END),
                    0
                )
                FROM unnest(people_results) AS r
            )
        ) INTO people_summary;
    END IF;

    -- Generate overall recommendations
    IF company_summary->>'average_quality_score' IS NOT NULL AND
       (company_summary->>'average_quality_score')::numeric < 60 THEN
        overall_recommendations := array_append(
            overall_recommendations,
            'Company data quality is below acceptable threshold - review scraping configuration'
        );
    END IF;

    IF people_summary->>'company_linkage_rate' IS NOT NULL AND
       (people_summary->>'company_linkage_rate')::numeric < 0.8 THEN
        overall_recommendations := array_append(
            overall_recommendations,
            'Many people records lack company linkage - consider improving data source correlation'
        );
    END IF;

    -- Compile final result
    result := jsonb_build_object(
        'batch_id', batch_id,
        'batch_type', batch_record.batch_type,
        'validation_level', validation_level,
        'validated_at', NOW(),
        'company_summary', COALESCE(company_summary, '{}'::jsonb),
        'people_summary', COALESCE(people_summary, '{}'::jsonb),
        'overall_recommendations', overall_recommendations,
        'detailed_results', jsonb_build_object(
            'companies', company_results,
            'people', people_results
        )
    );

    -- Update batch log with validation results
    UPDATE marketing.apify_batch_log
    SET processing_stats = COALESCE(processing_stats, '{}'::jsonb) || jsonb_build_object(
        'validation_completed_at', NOW(),
        'validation_summary', jsonb_build_object(
            'company_summary', company_summary,
            'people_summary', people_summary,
            'overall_recommendations', overall_recommendations
        )
    )
    WHERE batch_unique_id = batch_id;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- VALIDATION MONITORING AND REPORTING
-- ==============================================================================

/**
 * Create view for Apify validation monitoring
 * Provides real-time quality metrics across all batches
 */
CREATE OR REPLACE VIEW marketing.apify_validation_monitor AS
SELECT
    bl.batch_unique_id,
    bl.batch_type,
    bl.status,
    bl.source_actor_id,
    bl.created_at,
    bl.completed_at,

    -- Company metrics
    CASE WHEN bl.batch_type IN ('companies', 'mixed') THEN
        (bl.processing_stats->'company_summary'->>'total_companies')::integer
    ELSE NULL END as total_companies,

    CASE WHEN bl.batch_type IN ('companies', 'mixed') THEN
        (bl.processing_stats->'company_summary'->>'valid_companies')::integer
    ELSE NULL END as valid_companies,

    CASE WHEN bl.batch_type IN ('companies', 'mixed') THEN
        (bl.processing_stats->'company_summary'->>'average_quality_score')::numeric
    ELSE NULL END as company_avg_quality,

    -- People metrics
    CASE WHEN bl.batch_type IN ('people', 'mixed') THEN
        (bl.processing_stats->'people_summary'->>'total_people')::integer
    ELSE NULL END as total_people,

    CASE WHEN bl.batch_type IN ('people', 'mixed') THEN
        (bl.processing_stats->'people_summary'->>'valid_people')::integer
    ELSE NULL END as valid_people,

    CASE WHEN bl.batch_type IN ('people', 'mixed') THEN
        (bl.processing_stats->'people_summary'->>'company_linkage_rate')::numeric
    ELSE NULL END as people_linkage_rate,

    -- Overall health score
    CASE
        WHEN bl.batch_type = 'companies' THEN
            (bl.processing_stats->'company_summary'->>'average_quality_score')::numeric
        WHEN bl.batch_type = 'people' THEN
            (bl.processing_stats->'people_summary'->>'average_quality_score')::numeric *
            (bl.processing_stats->'people_summary'->>'company_linkage_rate')::numeric * 100
        WHEN bl.batch_type = 'mixed' THEN
            ((bl.processing_stats->'company_summary'->>'average_quality_score')::numeric +
             (bl.processing_stats->'people_summary'->>'average_quality_score')::numeric) / 2
        ELSE NULL
    END as overall_health_score

FROM marketing.apify_batch_log bl
WHERE bl.processing_stats ? 'validation_completed_at'
ORDER BY bl.created_at DESC;

-- ==============================================================================
-- MIGRATION COMPLETE - APIFY VALIDATION HELPERS
-- ==============================================================================

/**
 * Apify Validation Helpers Complete
 *
 * Created:
 * - validate_apify_company() - Comprehensive company validation with quality scoring
 * - validate_apify_person() - People validation with company linkage verification
 * - validate_apify_batch_comprehensive() - Full batch validation with recommendations
 * - apify_validation_monitor view - Real-time quality metrics dashboard
 *
 * Features:
 * - Graduated validation levels (standard/strict)
 * - Quality scoring with transparent metrics
 * - Apify-specific scraping artifact detection
 * - Company-person linkage validation
 * - Batch-level quality assessment and recommendations
 * - Real-time monitoring capabilities
 *
 * Integration:
 * - Works with existing company and people validators
 * - Extends validation system with Apify-specific rules
 * - Provides actionable quality improvement recommendations
 * - Maintains full Barton Doctrine audit compliance
 */