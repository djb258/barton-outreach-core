/**
 * Apify Data Preparation Functions - Barton Doctrine Pipeline
 * Transforms raw Apify JSON data into structured format for batch processing
 * Handles data validation, enrichment, and preparation for import
 *
 * Barton Doctrine Rules:
 * - All data transformations must preserve audit trail
 * - Validation errors must be logged with structured details
 * - Data enrichment must use standardized normalization functions
 */

-- ==============================================================================
-- APIFY COMPANY DATA PREPARATION
-- ==============================================================================

/**
 * Prepare Apify company data for batch processing
 * Transforms raw JSON into staging table format with validation
 */
CREATE OR REPLACE FUNCTION prepare_apify_company_data(
    batch_id TEXT,
    raw_companies JSONB[],
    actor_id TEXT DEFAULT 'apify/unknown'
)
RETURNS JSONB AS $$
DECLARE
    company_data JSONB;
    prepared_count INTEGER := 0;
    validation_errors INTEGER := 0;
    normalized_name TEXT;
    normalized_website TEXT;
    normalized_phone TEXT;
    staging_id INTEGER;
    result JSONB;
BEGIN
    -- Validate batch exists
    IF NOT EXISTS (
        SELECT 1 FROM marketing.apify_batch_log
        WHERE batch_unique_id = batch_id
    ) THEN
        RAISE EXCEPTION 'Batch % does not exist', batch_id;
    END IF;

    -- Process each company record
    FOREACH company_data IN ARRAY raw_companies
    LOOP
        BEGIN
            -- Extract and normalize core fields
            normalized_name := standardize_company_name(
                COALESCE(
                    company_data->>'name',
                    company_data->>'companyName',
                    company_data->>'company'
                )
            );

            normalized_website := extract_domain(
                COALESCE(
                    company_data->>'website',
                    company_data->>'url',
                    company_data->>'websiteUrl'
                )
            );

            normalized_phone := normalize_phone_enhanced(
                COALESCE(
                    company_data->>'phone',
                    company_data->>'phoneNumber',
                    company_data->>'telephone'
                )
            );

            -- Validate minimum required fields
            IF normalized_name IS NULL OR TRIM(normalized_name) = '' THEN
                validation_errors := validation_errors + 1;

                -- Log validation failure
                INSERT INTO marketing.apify_company_staging (
                    batch_unique_id,
                    raw_data,
                    company_name,
                    website_url,
                    processing_status,
                    processing_errors,
                    created_at
                ) VALUES (
                    batch_id,
                    company_data,
                    NULL,
                    NULL,
                    'validation_failed',
                    jsonb_build_object(
                        'error_type', 'missing_company_name',
                        'raw_name_fields', jsonb_build_object(
                            'name', company_data->>'name',
                            'companyName', company_data->>'companyName',
                            'company', company_data->>'company'
                        )
                    ),
                    NOW()
                );

                CONTINUE;
            END IF;

            -- Insert prepared data into staging
            INSERT INTO marketing.apify_company_staging (
                batch_unique_id,
                raw_data,
                company_name,
                website_url,
                industry,
                employee_count,
                address_street,
                address_city,
                address_state,
                address_zip,
                address_country,
                linkedin_url,
                facebook_url,
                twitter_url,
                keywords,
                description,
                apify_record_id,
                processing_status,
                created_at
            ) VALUES (
                batch_id,
                company_data,
                normalized_name,
                normalized_website,
                company_data->>'industry',
                CASE
                    WHEN company_data->>'employeeCount' ~ '^\d+$' THEN
                        (company_data->>'employeeCount')::INTEGER
                    WHEN company_data->>'employees' ~ '^\d+$' THEN
                        (company_data->>'employees')::INTEGER
                    ELSE NULL
                END,
                company_data->>'street',
                company_data->>'city',
                company_data->>'state',
                COALESCE(company_data->>'postalCode', company_data->>'zipCode'),
                COALESCE(company_data->>'country', 'USA'),
                normalize_linkedin_url(company_data->>'linkedinUrl'),
                company_data->>'facebookUrl',
                company_data->>'twitterUrl',
                company_data->>'keywords',
                company_data->>'description',
                COALESCE(
                    company_data->>'id',
                    company_data->>'apifyRecordId',
                    company_data->>'_id'
                ),
                'pending',
                NOW()
            );

            prepared_count := prepared_count + 1;

        EXCEPTION WHEN OTHERS THEN
            validation_errors := validation_errors + 1;

            -- Log processing error
            INSERT INTO marketing.apify_company_staging (
                batch_unique_id,
                raw_data,
                company_name,
                website_url,
                processing_status,
                processing_errors,
                created_at
            ) VALUES (
                batch_id,
                company_data,
                NULL,
                NULL,
                'processing_error',
                jsonb_build_object(
                    'error_type', 'data_preparation_exception',
                    'message', SQLERRM,
                    'sqlstate', SQLSTATE
                ),
                NOW()
            );
        END;
    END LOOP;

    -- Update batch log with preparation results
    UPDATE marketing.apify_batch_log
    SET total_records = total_records + prepared_count + validation_errors,
        prepared_records = prepared_count,
        validation_errors = validation_errors,
        processing_stats = COALESCE(processing_stats, '{}'::jsonb) || jsonb_build_object(
            'preparation_completed_at', NOW(),
            'preparation_errors', validation_errors,
            'actor_id', actor_id
        )
    WHERE batch_unique_id = batch_id;

    result := jsonb_build_object(
        'batch_id', batch_id,
        'prepared_companies', prepared_count,
        'validation_errors', validation_errors,
        'total_processed', prepared_count + validation_errors
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- APIFY PEOPLE DATA PREPARATION
-- ==============================================================================

/**
 * Prepare Apify people data for batch processing
 * Handles company linkage and slot type detection
 */
CREATE OR REPLACE FUNCTION prepare_apify_people_data(
    batch_id TEXT,
    raw_people JSONB[],
    actor_id TEXT DEFAULT 'apify/unknown'
)
RETURNS JSONB AS $$
DECLARE
    person_data JSONB;
    prepared_count INTEGER := 0;
    validation_errors INTEGER := 0;
    company_linkage_errors INTEGER := 0;
    normalized_first_name TEXT;
    normalized_last_name TEXT;
    normalized_linkedin TEXT;
    normalized_phone TEXT;
    company_identifier TEXT;
    detected_slot_type TEXT;
    result JSONB;
BEGIN
    -- Validate batch exists
    IF NOT EXISTS (
        SELECT 1 FROM marketing.apify_batch_log
        WHERE batch_unique_id = batch_id
    ) THEN
        RAISE EXCEPTION 'Batch % does not exist', batch_id;
    END IF;

    -- Process each person record
    FOREACH person_data IN ARRAY raw_people
    LOOP
        BEGIN
            -- Extract and normalize core fields
            normalized_first_name := TRIM(
                COALESCE(
                    person_data->>'firstName',
                    person_data->>'first_name',
                    SPLIT_PART(person_data->>'fullName', ' ', 1)
                )
            );

            normalized_last_name := TRIM(
                COALESCE(
                    person_data->>'lastName',
                    person_data->>'last_name',
                    SPLIT_PART(person_data->>'fullName', ' ', -1)
                )
            );

            normalized_linkedin := normalize_linkedin_url(
                COALESCE(
                    person_data->>'linkedinUrl',
                    person_data->>'linkedin',
                    person_data->>'profileUrl'
                )
            );

            normalized_phone := normalize_phone_enhanced(
                COALESCE(
                    person_data->>'phone',
                    person_data->>'phoneNumber',
                    person_data->>'workPhone'
                )
            );

            -- Detect slot type from job title
            detected_slot_type := detect_slot_type_from_title(
                COALESCE(
                    person_data->>'title',
                    person_data->>'jobTitle',
                    person_data->>'position'
                )
            );

            -- Extract company identifier for linkage
            company_identifier := COALESCE(
                person_data->>'companyName',
                person_data->>'company',
                person_data->>'employer'
            );

            -- Validate minimum required fields
            IF normalized_first_name IS NULL OR normalized_last_name IS NULL THEN
                validation_errors := validation_errors + 1;

                INSERT INTO marketing.apify_people_staging (
                    batch_unique_id,
                    raw_data,
                    first_name,
                    last_name,
                    processing_status,
                    processing_errors,
                    created_at
                ) VALUES (
                    batch_id,
                    person_data,
                    normalized_first_name,
                    normalized_last_name,
                    'validation_failed',
                    jsonb_build_object(
                        'error_type', 'missing_required_name',
                        'first_name_extracted', normalized_first_name,
                        'last_name_extracted', normalized_last_name
                    ),
                    NOW()
                );

                CONTINUE;
            END IF;

            -- Check for company linkage (optional - people can exist without companies)
            IF company_identifier IS NULL THEN
                company_linkage_errors := company_linkage_errors + 1;
            END IF;

            -- Insert prepared data into staging
            INSERT INTO marketing.apify_people_staging (
                batch_unique_id,
                raw_data,
                first_name,
                last_name,
                title,
                company_name_for_linkage,
                linkedin_url,
                detected_slot_type,
                seniority,
                department,
                email,
                work_phone,
                bio,
                skills,
                apify_record_id,
                processing_status,
                processing_notes,
                created_at
            ) VALUES (
                batch_id,
                person_data,
                normalized_first_name,
                normalized_last_name,
                COALESCE(
                    person_data->>'title',
                    person_data->>'jobTitle',
                    person_data->>'position'
                ),
                company_identifier,
                normalized_linkedin,
                detected_slot_type,
                person_data->>'seniority',
                person_data->>'department',
                person_data->>'email',
                normalized_phone,
                person_data->>'bio',
                person_data->>'skills',
                COALESCE(
                    person_data->>'id',
                    person_data->>'apifyRecordId',
                    person_data->>'_id'
                ),
                CASE
                    WHEN company_identifier IS NULL THEN 'needs_company_linkage'
                    ELSE 'pending'
                END,
                CASE
                    WHEN company_identifier IS NULL THEN
                        jsonb_build_object('warning', 'No company identifier found for linkage')
                    ELSE NULL
                END,
                NOW()
            );

            prepared_count := prepared_count + 1;

        EXCEPTION WHEN OTHERS THEN
            validation_errors := validation_errors + 1;

            INSERT INTO marketing.apify_people_staging (
                batch_unique_id,
                raw_data,
                first_name,
                last_name,
                processing_status,
                processing_errors,
                created_at
            ) VALUES (
                batch_id,
                person_data,
                NULL,
                NULL,
                'processing_error',
                jsonb_build_object(
                    'error_type', 'data_preparation_exception',
                    'message', SQLERRM,
                    'sqlstate', SQLSTATE
                ),
                NOW()
            );
        END;
    END LOOP;

    -- Update batch log
    UPDATE marketing.apify_batch_log
    SET total_records = total_records + prepared_count + validation_errors,
        prepared_records = COALESCE(prepared_records, 0) + prepared_count,
        validation_errors = COALESCE(validation_errors, 0) + validation_errors,
        processing_stats = COALESCE(processing_stats, '{}'::jsonb) || jsonb_build_object(
            'people_preparation_completed_at', NOW(),
            'people_preparation_errors', validation_errors,
            'people_company_linkage_issues', company_linkage_errors,
            'actor_id', actor_id
        )
    WHERE batch_unique_id = batch_id;

    result := jsonb_build_object(
        'batch_id', batch_id,
        'prepared_people', prepared_count,
        'validation_errors', validation_errors,
        'company_linkage_issues', company_linkage_errors,
        'total_processed', prepared_count + validation_errors
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- COMBINED BATCH PREPARATION
-- ==============================================================================

/**
 * Prepare mixed Apify data batch (companies + people)
 * Handles both data types in a single operation
 */
CREATE OR REPLACE FUNCTION prepare_apify_mixed_batch(
    batch_id TEXT,
    raw_data JSONB,
    actor_id TEXT DEFAULT 'apify/unknown'
)
RETURNS JSONB AS $$
DECLARE
    companies_array JSONB[];
    people_array JSONB[];
    company_result JSONB;
    people_result JSONB;
    combined_result JSONB;
BEGIN
    -- Extract companies and people arrays from raw data
    IF raw_data ? 'companies' AND jsonb_typeof(raw_data->'companies') = 'array' THEN
        companies_array := ARRAY(SELECT jsonb_array_elements(raw_data->'companies'));
    END IF;

    IF raw_data ? 'people' AND jsonb_typeof(raw_data->'people') = 'array' THEN
        people_array := ARRAY(SELECT jsonb_array_elements(raw_data->'people'));
    END IF;

    -- Process companies first
    IF companies_array IS NOT NULL AND array_length(companies_array, 1) > 0 THEN
        company_result := prepare_apify_company_data(batch_id, companies_array, actor_id);
    ELSE
        company_result := jsonb_build_object(
            'prepared_companies', 0,
            'validation_errors', 0
        );
    END IF;

    -- Process people second
    IF people_array IS NOT NULL AND array_length(people_array, 1) > 0 THEN
        people_result := prepare_apify_people_data(batch_id, people_array, actor_id);
    ELSE
        people_result := jsonb_build_object(
            'prepared_people', 0,
            'validation_errors', 0,
            'company_linkage_issues', 0
        );
    END IF;

    -- Combine results
    combined_result := jsonb_build_object(
        'batch_id', batch_id,
        'company_results', company_result,
        'people_results', people_result,
        'summary', jsonb_build_object(
            'total_companies_prepared', company_result->>'prepared_companies',
            'total_people_prepared', people_result->>'prepared_people',
            'total_validation_errors',
                (COALESCE((company_result->>'validation_errors')::INTEGER, 0) +
                 COALESCE((people_result->>'validation_errors')::INTEGER, 0)),
            'people_company_linkage_issues', people_result->>'company_linkage_issues'
        )
    );

    RETURN combined_result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- DATA ENRICHMENT FUNCTIONS
-- ==============================================================================

/**
 * Enrich company data with additional standardization
 * Applies advanced normalization and industry classification
 */
CREATE OR REPLACE FUNCTION enrich_staged_companies(batch_id TEXT)
RETURNS JSONB AS $$
DECLARE
    enriched_count INTEGER := 0;
    company_record RECORD;
    industry_classification TEXT;
    employee_range TEXT;
BEGIN
    FOR company_record IN
        SELECT * FROM marketing.apify_company_staging
        WHERE batch_unique_id = batch_id
        AND processing_status = 'pending'
    LOOP
        -- Industry classification enrichment
        industry_classification := CASE
            WHEN company_record.industry ILIKE '%tech%' OR company_record.industry ILIKE '%software%' THEN 'Technology'
            WHEN company_record.industry ILIKE '%health%' OR company_record.industry ILIKE '%medical%' THEN 'Healthcare'
            WHEN company_record.industry ILIKE '%finance%' OR company_record.industry ILIKE '%bank%' THEN 'Financial Services'
            WHEN company_record.industry ILIKE '%retail%' OR company_record.industry ILIKE '%commerce%' THEN 'Retail'
            WHEN company_record.industry ILIKE '%education%' OR company_record.industry ILIKE '%university%' THEN 'Education'
            ELSE company_record.industry
        END;

        -- Employee count classification
        employee_range := CASE
            WHEN company_record.employee_count IS NULL THEN 'Unknown'
            WHEN company_record.employee_count <= 10 THEN '1-10'
            WHEN company_record.employee_count <= 50 THEN '11-50'
            WHEN company_record.employee_count <= 200 THEN '51-200'
            WHEN company_record.employee_count <= 1000 THEN '201-1000'
            ELSE '1000+'
        END;

        -- Update with enriched data
        UPDATE marketing.apify_company_staging
        SET raw_data = raw_data || jsonb_build_object(
                'enriched_industry', industry_classification,
                'employee_range', employee_range,
                'enrichment_timestamp', NOW()
            ),
            industry = industry_classification,
            processing_status = 'enriched'
        WHERE id = company_record.id;

        enriched_count := enriched_count + 1;
    END LOOP;

    RETURN jsonb_build_object(
        'batch_id', batch_id,
        'enriched_companies', enriched_count
    );
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- MIGRATION COMPLETE - APIFY DATA PREPARATION
-- ==============================================================================

/**
 * Apify Data Preparation Functions Complete
 *
 * Created:
 * - prepare_apify_company_data() - Transform raw company JSON into staging format
 * - prepare_apify_people_data() - Transform raw people JSON with company linkage
 * - prepare_apify_mixed_batch() - Handle combined company/people data
 * - enrich_staged_companies() - Apply advanced data enrichment
 *
 * Features:
 * - Comprehensive data validation and normalization
 * - Structured error logging for failed records
 * - Automatic slot type detection for people
 * - Company linkage preparation for people records
 * - Industry classification and employee range enrichment
 * - Full audit trail maintenance
 *
 * Usage:
 * 1. Create batch: generate_apify_batch_id()
 * 2. Prepare data: prepare_apify_mixed_batch(batch_id, raw_json)
 * 3. Enrich: enrich_staged_companies(batch_id)
 * 4. Process: process_apify_company_batch() / process_apify_people_batch()
 */