-- ─────────────────────────────────────────────
-- 📁 CTB Classification Metadata
-- ─────────────────────────────────────────────
-- CTB Branch: data/migrations
-- Barton ID: 05.01.02
-- Unique ID: CTB-140143CF
-- Blueprint Hash:
-- Last Updated: 2025-10-23
-- Enforcement: HEIR
-- ─────────────────────────────────────────────

/**
 * Apify Integration Helper Functions - Barton Doctrine Compliant
 * Prerequisites for Companies + People data ingestion via Apify
 *
 * Barton Doctrine Rules:
 * - All operations must use Barton 6-part unique_id
 * - Audit log every operation
 * - Company → Slot → Person linkage enforcement
 * - Composio MCP integration ready
 */

-- ==============================================================================
-- APIFY BATCH PROCESSING SUPPORT
-- ==============================================================================

/**
 * Create batch tracking table for Apify imports
 * Tracks batches of company/people data from Apify scraping runs
 */
CREATE TABLE IF NOT EXISTS marketing.apify_batch_log (
    id SERIAL PRIMARY KEY,
    batch_unique_id TEXT NOT NULL UNIQUE, -- Barton ID for batch
    batch_type TEXT NOT NULL CHECK (batch_type IN ('companies', 'people', 'mixed')),
    source_actor_id TEXT, -- Apify actor that generated the data
    source_run_id TEXT, -- Apify run ID for traceability

    -- Statistics
    total_records INTEGER DEFAULT 0,
    processed_records INTEGER DEFAULT 0,
    validated_records INTEGER DEFAULT 0,
    failed_records INTEGER DEFAULT 0,

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial')),
    error_details JSONB,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Barton Doctrine
    altitude INTEGER DEFAULT 10000,
    process_step TEXT DEFAULT 'apify_batch_import'
);

-- ==============================================================================
-- APIFY DATA STAGING TABLES
-- ==============================================================================

/**
 * Staging table for raw Apify company data before validation
 * Allows bulk import then gradual validation/processing
 */
CREATE TABLE IF NOT EXISTS marketing.apify_company_staging (
    id SERIAL PRIMARY KEY,
    batch_unique_id TEXT NOT NULL, -- Link to apify_batch_log

    -- Raw data from Apify (flexible schema)
    raw_data JSONB NOT NULL,

    -- Extracted core fields for quick filtering
    company_name TEXT,
    website_url TEXT,
    linkedin_url TEXT,

    -- Processing status
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'validated', 'failed', 'imported')),
    processing_errors JSONB,
    company_unique_id TEXT, -- Generated after validation

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    -- Index for batch processing
    INDEX idx_apify_company_staging_batch (batch_unique_id),
    INDEX idx_apify_company_staging_status (processing_status)
);

/**
 * Staging table for raw Apify people data before validation
 */
CREATE TABLE IF NOT EXISTS marketing.apify_people_staging (
    id SERIAL PRIMARY KEY,
    batch_unique_id TEXT NOT NULL, -- Link to apify_batch_log

    -- Raw data from Apify
    raw_data JSONB NOT NULL,

    -- Extracted core fields
    first_name TEXT,
    last_name TEXT,
    company_name TEXT, -- For matching to company
    linkedin_url TEXT,
    title TEXT,

    -- Company linkage (resolved during processing)
    company_unique_id TEXT,
    company_slot_unique_id TEXT,
    slot_type TEXT,

    -- Processing status
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'validated', 'failed', 'imported')),
    processing_errors JSONB,
    people_unique_id TEXT, -- Generated after validation

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,

    -- Indexes
    INDEX idx_apify_people_staging_batch (batch_unique_id),
    INDEX idx_apify_people_staging_status (processing_status),
    INDEX idx_apify_people_staging_company (company_name)
);

-- ==============================================================================
-- APIFY BATCH ID GENERATION
-- ==============================================================================

/**
 * Generate Barton ID for Apify batch
 * Format: 04.04.05.07.10000.XXX (microprocess 05 = batch management)
 */
CREATE OR REPLACE FUNCTION generate_apify_batch_id()
RETURNS TEXT AS $$
DECLARE
    database_code TEXT := '04';
    subhive_code TEXT := '04';
    microprocess_code TEXT := '05'; -- batch management
    tool_code TEXT := '07'; -- Apify
    altitude_code TEXT := '10000';
    step_number INTEGER;
    step_padded TEXT;
    barton_id TEXT;
BEGIN
    -- Get next step number
    SELECT COALESCE(MAX(
        CAST(SPLIT_PART(batch_unique_id, '.', 6) AS INTEGER)
    ), 0) + 1
    INTO step_number
    FROM marketing.apify_batch_log
    WHERE batch_unique_id LIKE database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.%';

    step_padded := LPAD(step_number::TEXT, 3, '0');
    barton_id := database_code || '.' || subhive_code || '.' || microprocess_code || '.' || tool_code || '.' || altitude_code || '.' || step_padded;

    RETURN barton_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- COMPANY MATCHING AND DEDUPLICATION
-- ==============================================================================

/**
 * Find existing company by various identifiers
 * Used to prevent duplicate company imports from Apify
 */
CREATE OR REPLACE FUNCTION find_existing_company(
    p_company_name TEXT,
    p_website_url TEXT DEFAULT NULL,
    p_linkedin_url TEXT DEFAULT NULL
)
RETURNS TABLE(
    company_unique_id TEXT,
    company_name TEXT,
    match_type TEXT,
    match_confidence NUMERIC
) AS $$
BEGIN
    -- Exact website match (highest confidence)
    IF p_website_url IS NOT NULL THEN
        RETURN QUERY
        SELECT
            c.company_unique_id,
            c.company_name,
            'website_exact'::TEXT as match_type,
            1.0::NUMERIC as match_confidence
        FROM marketing.company_raw_intake c
        WHERE LOWER(c.website_url) = LOWER(p_website_url)
        LIMIT 1;

        IF FOUND THEN RETURN; END IF;
    END IF;

    -- LinkedIn URL match (high confidence)
    IF p_linkedin_url IS NOT NULL THEN
        RETURN QUERY
        SELECT
            c.company_unique_id,
            c.company_name,
            'linkedin_exact'::TEXT as match_type,
            0.95::NUMERIC as match_confidence
        FROM marketing.company_raw_intake c
        WHERE LOWER(c.linkedin_url) = LOWER(p_linkedin_url)
        LIMIT 1;

        IF FOUND THEN RETURN; END IF;
    END IF;

    -- Exact name match (medium confidence)
    RETURN QUERY
    SELECT
        c.company_unique_id,
        c.company_name,
        'name_exact'::TEXT as match_type,
        0.8::NUMERIC as match_confidence
    FROM marketing.company_raw_intake c
    WHERE LOWER(TRIM(c.company_name)) = LOWER(TRIM(p_company_name))
    LIMIT 1;

    -- If no exact matches, try fuzzy name match (low confidence)
    IF NOT FOUND AND length(p_company_name) > 5 THEN
        RETURN QUERY
        SELECT
            c.company_unique_id,
            c.company_name,
            'name_fuzzy'::TEXT as match_type,
            0.6::NUMERIC as match_confidence
        FROM marketing.company_raw_intake c
        WHERE levenshtein_less_equal(LOWER(c.company_name), LOWER(p_company_name), 3) <= 3
        ORDER BY levenshtein(LOWER(c.company_name), LOWER(p_company_name))
        LIMIT 1;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- PEOPLE TO SLOT ASSIGNMENT
-- ==============================================================================

/**
 * Smart slot type detection from job title
 * Maps various title variations to standard slot types
 */
CREATE OR REPLACE FUNCTION detect_slot_type_from_title(p_title TEXT)
RETURNS TEXT AS $$
DECLARE
    title_lower TEXT;
BEGIN
    IF p_title IS NULL THEN
        RETURN NULL;
    END IF;

    title_lower := LOWER(p_title);

    -- CEO variations
    IF title_lower ~ '(chief executive|ceo|president|managing director|executive director)' THEN
        RETURN 'CEO';

    -- CFO variations
    ELSIF title_lower ~ '(chief financial|cfo|finance director|treasurer|controller)' THEN
        RETURN 'CFO';

    -- HR variations
    ELSIF title_lower ~ '(human resource|hr director|chief people|people director|talent director|chro)' THEN
        RETURN 'HR';

    -- CTO variations
    ELSIF title_lower ~ '(chief technology|cto|technology director|engineering director)' THEN
        RETURN 'CTO';

    -- CMO variations
    ELSIF title_lower ~ '(chief marketing|cmo|marketing director|brand director)' THEN
        RETURN 'CMO';

    -- COO variations
    ELSIF title_lower ~ '(chief operating|coo|operations director)' THEN
        RETURN 'COO';

    -- VP Sales
    ELSIF title_lower ~ '(vp sales|vice president sales|sales director|head of sales)' THEN
        RETURN 'VP_SALES';

    -- VP Marketing
    ELSIF title_lower ~ '(vp marketing|vice president marketing|marketing manager)' THEN
        RETURN 'VP_MARKETING';

    -- Director level
    ELSIF title_lower ~ '(director|head of|vp|vice president)' THEN
        RETURN 'DIRECTOR';

    -- Manager level
    ELSIF title_lower ~ '(manager|supervisor|lead|coordinator)' THEN
        RETURN 'MANAGER';

    ELSE
        -- Default to manager for unknown titles
        RETURN 'MANAGER';
    END IF;
END;
$$ LANGUAGE plpgsql;

/**
 * Find or create appropriate slot for a person
 * Ensures slot exists before person assignment
 */
CREATE OR REPLACE FUNCTION ensure_company_slot_exists(
    p_company_unique_id TEXT,
    p_slot_type TEXT
)
RETURNS TEXT AS $$
DECLARE
    v_slot_id TEXT;
BEGIN
    -- Check if slot already exists
    SELECT company_slot_unique_id
    INTO v_slot_id
    FROM marketing.company_slot
    WHERE company_unique_id = p_company_unique_id
      AND slot_type = p_slot_type
      AND slot_status = 'active';

    -- If exists, return it
    IF v_slot_id IS NOT NULL THEN
        RETURN v_slot_id;
    END IF;

    -- Create new slot if it doesn't exist
    v_slot_id := generate_slot_barton_id('07'); -- Apify tool code

    INSERT INTO marketing.company_slot (
        company_slot_unique_id,
        company_unique_id,
        slot_type,
        slot_title,
        slot_description,
        priority_order,
        slot_status,
        altitude,
        process_step
    ) VALUES (
        v_slot_id,
        p_company_unique_id,
        p_slot_type,
        p_slot_type,
        'Auto-created slot for Apify import',
        CASE
            WHEN p_slot_type = 'CEO' THEN 1
            WHEN p_slot_type = 'CFO' THEN 2
            WHEN p_slot_type = 'HR' THEN 3
            WHEN p_slot_type = 'CTO' THEN 4
            WHEN p_slot_type = 'CMO' THEN 5
            WHEN p_slot_type = 'COO' THEN 6
            ELSE 100
        END,
        'active',
        10000,
        'apify_slot_creation'
    );

    RETURN v_slot_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- BATCH PROCESSING FUNCTIONS
-- ==============================================================================

/**
 * Process a batch of staged Apify companies
 * Validates and moves from staging to company_raw_intake
 */
CREATE OR REPLACE FUNCTION process_apify_company_batch(
    p_batch_unique_id TEXT,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE(
    processed INTEGER,
    validated INTEGER,
    failed INTEGER
) AS $$
DECLARE
    v_processed INTEGER := 0;
    v_validated INTEGER := 0;
    v_failed INTEGER := 0;
    v_record RECORD;
    v_company_id TEXT;
    v_existing_company RECORD;
BEGIN
    -- Process pending records from staging
    FOR v_record IN
        SELECT * FROM marketing.apify_company_staging
        WHERE batch_unique_id = p_batch_unique_id
          AND processing_status = 'pending'
        LIMIT p_limit
    LOOP
        v_processed := v_processed + 1;

        BEGIN
            -- Update status to processing
            UPDATE marketing.apify_company_staging
            SET processing_status = 'processing'
            WHERE id = v_record.id;

            -- Check for existing company
            SELECT * INTO v_existing_company
            FROM find_existing_company(
                v_record.company_name,
                (v_record.raw_data->>'website')::TEXT,
                (v_record.raw_data->>'linkedinUrl')::TEXT
            );

            IF v_existing_company.company_unique_id IS NOT NULL THEN
                -- Company exists, mark as duplicate
                UPDATE marketing.apify_company_staging
                SET processing_status = 'failed',
                    processing_errors = jsonb_build_object(
                        'error', 'duplicate_company',
                        'existing_id', v_existing_company.company_unique_id,
                        'match_type', v_existing_company.match_type
                    ),
                    processed_at = NOW()
                WHERE id = v_record.id;

                v_failed := v_failed + 1;
            ELSE
                -- Generate new company ID
                v_company_id := generate_company_barton_id('07'); -- Apify tool

                -- Insert into company_raw_intake
                INSERT INTO marketing.company_raw_intake (
                    company_unique_id,
                    company_name,
                    website_url,
                    industry,
                    employee_count,
                    company_phone,
                    address_street,
                    address_city,
                    address_state,
                    address_zip,
                    address_country,
                    linkedin_url,
                    facebook_url,
                    x_url,
                    keywords,
                    seo_description,
                    source_system,
                    source_record_id,
                    validation_status,
                    altitude,
                    process_step
                ) VALUES (
                    v_company_id,
                    COALESCE(v_record.raw_data->>'name', v_record.company_name),
                    COALESCE(v_record.raw_data->>'website', v_record.website_url),
                    v_record.raw_data->>'industry',
                    CASE
                        WHEN v_record.raw_data->>'employeeCount' ~ '^\d+$'
                        THEN (v_record.raw_data->>'employeeCount')::INTEGER
                        ELSE NULL
                    END,
                    COALESCE(v_record.raw_data->>'phone', '+10000000000'), -- Default if missing
                    COALESCE(v_record.raw_data->>'street', ''),
                    COALESCE(v_record.raw_data->>'city', ''),
                    COALESCE(v_record.raw_data->>'state', ''),
                    COALESCE(v_record.raw_data->>'postalCode', ''),
                    COALESCE(v_record.raw_data->>'country', 'USA'),
                    v_record.raw_data->>'linkedinUrl',
                    v_record.raw_data->>'facebookUrl',
                    v_record.raw_data->>'twitterUrl',
                    v_record.raw_data->>'keywords',
                    v_record.raw_data->>'description',
                    'apify',
                    v_record.raw_data->>'apifyRunId',
                    'validated',
                    10000,
                    'apify_batch_import'
                );

                -- Update staging record
                UPDATE marketing.apify_company_staging
                SET processing_status = 'imported',
                    company_unique_id = v_company_id,
                    processed_at = NOW()
                WHERE id = v_record.id;

                -- Log to audit
                INSERT INTO marketing.company_audit_log (
                    company_unique_id,
                    action,
                    status,
                    source,
                    new_values,
                    altitude,
                    process_id,
                    session_id
                ) VALUES (
                    v_company_id,
                    'insert',
                    'success',
                    'apify_batch_processor',
                    v_record.raw_data,
                    10000,
                    'apify_company_import',
                    p_batch_unique_id
                );

                v_validated := v_validated + 1;
            END IF;

        EXCEPTION WHEN OTHERS THEN
            -- Mark as failed
            UPDATE marketing.apify_company_staging
            SET processing_status = 'failed',
                processing_errors = jsonb_build_object(
                    'error', 'processing_exception',
                    'message', SQLERRM
                ),
                processed_at = NOW()
            WHERE id = v_record.id;

            v_failed := v_failed + 1;
        END;
    END LOOP;

    -- Update batch statistics
    UPDATE marketing.apify_batch_log
    SET processed_records = processed_records + v_processed,
        validated_records = validated_records + v_validated,
        failed_records = failed_records + v_failed
    WHERE batch_unique_id = p_batch_unique_id;

    RETURN QUERY SELECT v_processed, v_validated, v_failed;
END;
$$ LANGUAGE plpgsql;

/**
 * Process a batch of staged Apify people
 * Validates, links to companies/slots, and imports
 */
CREATE OR REPLACE FUNCTION process_apify_people_batch(
    p_batch_unique_id TEXT,
    p_limit INTEGER DEFAULT 100
)
RETURNS TABLE(
    processed INTEGER,
    validated INTEGER,
    failed INTEGER
) AS $$
DECLARE
    v_processed INTEGER := 0;
    v_validated INTEGER := 0;
    v_failed INTEGER := 0;
    v_record RECORD;
    v_people_id TEXT;
    v_company RECORD;
    v_slot_type TEXT;
    v_slot_id TEXT;
BEGIN
    FOR v_record IN
        SELECT * FROM marketing.apify_people_staging
        WHERE batch_unique_id = p_batch_unique_id
          AND processing_status = 'pending'
        LIMIT p_limit
    LOOP
        v_processed := v_processed + 1;

        BEGIN
            -- Update status
            UPDATE marketing.apify_people_staging
            SET processing_status = 'processing'
            WHERE id = v_record.id;

            -- Find company
            SELECT * INTO v_company
            FROM find_existing_company(
                v_record.company_name,
                v_record.raw_data->>'companyWebsite',
                v_record.raw_data->>'companyLinkedIn'
            );

            IF v_company.company_unique_id IS NULL THEN
                -- No company found
                UPDATE marketing.apify_people_staging
                SET processing_status = 'failed',
                    processing_errors = jsonb_build_object(
                        'error', 'company_not_found',
                        'company_name', v_record.company_name
                    ),
                    processed_at = NOW()
                WHERE id = v_record.id;

                v_failed := v_failed + 1;
                CONTINUE;
            END IF;

            -- Detect slot type from title
            v_slot_type := detect_slot_type_from_title(
                COALESCE(v_record.title, v_record.raw_data->>'title')
            );

            -- Ensure slot exists
            v_slot_id := ensure_company_slot_exists(
                v_company.company_unique_id,
                v_slot_type
            );

            -- Generate people ID
            v_people_id := generate_people_barton_id('07'); -- Apify

            -- Insert into people_raw_intake
            INSERT INTO marketing.people_raw_intake (
                unique_id,
                company_unique_id,
                company_slot_unique_id,
                first_name,
                last_name,
                title,
                seniority,
                department,
                email,
                work_phone_e164,
                linkedin_url,
                twitter_url,
                bio,
                skills,
                source_system,
                source_record_id,
                validation_status,
                altitude,
                process_step
            ) VALUES (
                v_people_id,
                v_company.company_unique_id,
                v_slot_id,
                COALESCE(v_record.raw_data->>'firstName', v_record.first_name, ''),
                COALESCE(v_record.raw_data->>'lastName', v_record.last_name, ''),
                COALESCE(v_record.raw_data->>'title', v_record.title),
                v_record.raw_data->>'seniority',
                v_record.raw_data->>'department',
                v_record.raw_data->>'email',
                v_record.raw_data->>'phone',
                COALESCE(v_record.raw_data->>'linkedinUrl', v_record.linkedin_url),
                v_record.raw_data->>'twitterUrl',
                v_record.raw_data->>'bio',
                v_record.raw_data->>'skills',
                'apify',
                v_record.raw_data->>'apifyRunId',
                'validated',
                10000,
                'apify_batch_import'
            );

            -- Mark slot as filled
            UPDATE marketing.company_slot
            SET is_filled = TRUE, updated_at = NOW()
            WHERE company_slot_unique_id = v_slot_id;

            -- Update staging record
            UPDATE marketing.apify_people_staging
            SET processing_status = 'imported',
                people_unique_id = v_people_id,
                company_unique_id = v_company.company_unique_id,
                company_slot_unique_id = v_slot_id,
                slot_type = v_slot_type,
                processed_at = NOW()
            WHERE id = v_record.id;

            -- Audit log
            INSERT INTO marketing.people_audit_log (
                unique_id,
                company_unique_id,
                company_slot_unique_id,
                action,
                status,
                source,
                new_values,
                altitude,
                process_id,
                session_id
            ) VALUES (
                v_people_id,
                v_company.company_unique_id,
                v_slot_id,
                'insert',
                'success',
                'apify_batch_processor',
                v_record.raw_data,
                10000,
                'apify_people_import',
                p_batch_unique_id
            );

            v_validated := v_validated + 1;

        EXCEPTION WHEN OTHERS THEN
            UPDATE marketing.apify_people_staging
            SET processing_status = 'failed',
                processing_errors = jsonb_build_object(
                    'error', 'processing_exception',
                    'message', SQLERRM
                ),
                processed_at = NOW()
            WHERE id = v_record.id;

            v_failed := v_failed + 1;
        END;
    END LOOP;

    -- Update batch statistics
    UPDATE marketing.apify_batch_log
    SET processed_records = processed_records + v_processed,
        validated_records = validated_records + v_validated,
        failed_records = failed_records + v_failed
    WHERE batch_unique_id = p_batch_unique_id;

    RETURN QUERY SELECT v_processed, v_validated, v_failed;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- VIEWS FOR MONITORING
-- ==============================================================================

/**
 * View of pending Apify imports
 */
CREATE OR REPLACE VIEW marketing.apify_import_status AS
SELECT
    'companies' as type,
    batch_unique_id,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending,
    COUNT(*) FILTER (WHERE processing_status = 'processing') as processing,
    COUNT(*) FILTER (WHERE processing_status = 'imported') as imported,
    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed
FROM marketing.apify_company_staging
GROUP BY batch_unique_id

UNION ALL

SELECT
    'people' as type,
    batch_unique_id,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE processing_status = 'pending') as pending,
    COUNT(*) FILTER (WHERE processing_status = 'processing') as processing,
    COUNT(*) FILTER (WHERE processing_status = 'imported') as imported,
    COUNT(*) FILTER (WHERE processing_status = 'failed') as failed
FROM marketing.apify_people_staging
GROUP BY batch_unique_id;

-- ==============================================================================
-- EXTENSION REQUIREMENTS
-- ==============================================================================

/**
 * Ensure required extensions are installed
 * fuzzystrmatch provides levenshtein for company name matching
 */
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

-- ==============================================================================
-- SAMPLE USAGE
-- ==============================================================================

/**
 * Example: Import companies from Apify
 *
 * 1. Create batch:
 * INSERT INTO marketing.apify_batch_log (batch_unique_id, batch_type, source_actor_id)
 * VALUES (generate_apify_batch_id(), 'companies', 'apify/google-search-scraper');
 *
 * 2. Stage data:
 * INSERT INTO marketing.apify_company_staging (batch_unique_id, raw_data, company_name, website_url)
 * VALUES ('04.04.05.07.10000.001', '{"name":"Test Co","website":"test.com"}'::jsonb, 'Test Co', 'test.com');
 *
 * 3. Process batch:
 * SELECT * FROM process_apify_company_batch('04.04.05.07.10000.001', 100);
 */

-- ==============================================================================
-- ENHANCED HELPER FUNCTIONS FOR APIFY INTEGRATION
-- ==============================================================================

/**
 * Enhanced phone normalization with country detection
 * Handles international formats from Apify data sources
 */
CREATE OR REPLACE FUNCTION normalize_phone_enhanced(
    raw_phone TEXT,
    default_country_code TEXT DEFAULT '+1'
)
RETURNS TEXT AS $$
DECLARE
    clean_phone TEXT;
    result_phone TEXT;
BEGIN
    -- Return NULL for empty input
    IF raw_phone IS NULL OR TRIM(raw_phone) = '' THEN
        RETURN NULL;
    END IF;

    -- Remove all non-digit characters except +
    clean_phone := REGEXP_REPLACE(raw_phone, '[^+0-9]', '', 'g');

    -- Handle different formats
    CASE
        -- Already has country code
        WHEN clean_phone ~ '^\+[1-9][0-9]{1,15}$' THEN
            result_phone := clean_phone;

        -- US/CA format without country code (10 digits)
        WHEN clean_phone ~ '^[0-9]{10}$' THEN
            result_phone := default_country_code || clean_phone;

        -- US/CA format with leading 1 (11 digits)
        WHEN clean_phone ~ '^1[0-9]{10}$' THEN
            result_phone := '+' || clean_phone;

        -- International without + (assume valid if 7-15 digits)
        WHEN clean_phone ~ '^[1-9][0-9]{6,14}$' THEN
            result_phone := '+' || clean_phone;

        -- Invalid format
        ELSE
            RETURN NULL;
    END CASE;

    -- Final E.164 validation
    IF result_phone ~ '^\+[1-9][0-9]{1,15}$' THEN
        RETURN result_phone;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

/**
 * Extract domain from URL for website normalization
 * Handles various URL formats from Apify scraping
 */
CREATE OR REPLACE FUNCTION extract_domain(raw_url TEXT)
RETURNS TEXT AS $$
DECLARE
    clean_url TEXT;
    domain_part TEXT;
BEGIN
    -- Return NULL for empty input
    IF raw_url IS NULL OR TRIM(raw_url) = '' THEN
        RETURN NULL;
    END IF;

    -- Convert to lowercase and trim
    clean_url := LOWER(TRIM(raw_url));

    -- Add protocol if missing
    IF NOT clean_url ~ '^https?://' THEN
        clean_url := 'https://' || clean_url;
    END IF;

    -- Extract domain using regex
    domain_part := SUBSTRING(clean_url FROM 'https?://(?:www\.)?([^/]+)');

    -- Remove trailing slash and query params
    domain_part := SPLIT_PART(domain_part, '/', 1);
    domain_part := SPLIT_PART(domain_part, '?', 1);

    -- Validate domain format
    IF domain_part ~ '^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.[a-zA-Z]{2,}$' THEN
        RETURN 'https://' || domain_part;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

/**
 * Clean and standardize company names for deduplication
 * Removes common suffixes and normalizes format
 */
CREATE OR REPLACE FUNCTION standardize_company_name(company_name TEXT)
RETURNS TEXT AS $$
DECLARE
    clean_name TEXT;
    suffixes TEXT[] := ARRAY[
        'inc', 'inc.', 'incorporated',
        'llc', 'l.l.c.', 'l.l.c',
        'ltd', 'ltd.', 'limited',
        'corp', 'corp.', 'corporation',
        'co', 'co.', 'company',
        'plc', 'p.l.c.'
    ];
    suffix TEXT;
BEGIN
    -- Return NULL for empty input
    IF company_name IS NULL OR TRIM(company_name) = '' THEN
        RETURN NULL;
    END IF;

    -- Initial cleanup
    clean_name := LOWER(TRIM(company_name));

    -- Remove common punctuation
    clean_name := REGEXP_REPLACE(clean_name, '[.,&]+$', '', 'g');

    -- Remove common suffixes
    FOREACH suffix IN ARRAY suffixes LOOP
        clean_name := REGEXP_REPLACE(clean_name, '\s+' || suffix || '$', '', 'i');
    END LOOP;

    -- Final cleanup
    clean_name := TRIM(clean_name);

    -- Return proper case
    RETURN INITCAP(clean_name);
END;
$$ LANGUAGE plpgsql;

/**
 * Validate and normalize LinkedIn URLs
 * Ensures consistent LinkedIn profile format
 */
CREATE OR REPLACE FUNCTION normalize_linkedin_url(raw_url TEXT)
RETURNS TEXT AS $$
DECLARE
    clean_url TEXT;
    profile_id TEXT;
BEGIN
    -- Return NULL for empty input
    IF raw_url IS NULL OR TRIM(raw_url) = '' THEN
        RETURN NULL;
    END IF;

    -- Convert to lowercase and trim
    clean_url := LOWER(TRIM(raw_url));

    -- Extract LinkedIn profile ID
    profile_id := SUBSTRING(clean_url FROM 'linkedin\.com/in/([^/?]+)');

    IF profile_id IS NOT NULL AND profile_id != '' THEN
        RETURN 'https://www.linkedin.com/in/' || profile_id;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql;

/**
 * Clean up old staging data and batch logs
 * Maintains staging table performance by removing old records
 */
CREATE OR REPLACE FUNCTION cleanup_apify_staging(retention_days INTEGER DEFAULT 30)
RETURNS JSONB AS $$
DECLARE
    deleted_companies INTEGER;
    deleted_people INTEGER;
    deleted_batches INTEGER;
    cutoff_date TIMESTAMPTZ;
BEGIN
    cutoff_date := NOW() - (retention_days || ' days')::INTERVAL;

    -- Clean up processed staging records
    DELETE FROM marketing.apify_company_staging
    WHERE processed_at < cutoff_date
    AND processing_status IN ('imported', 'failed');

    GET DIAGNOSTICS deleted_companies = ROW_COUNT;

    DELETE FROM marketing.apify_people_staging
    WHERE processed_at < cutoff_date
    AND processing_status IN ('imported', 'failed');

    GET DIAGNOSTICS deleted_people = ROW_COUNT;

    -- Clean up old batch logs
    DELETE FROM marketing.apify_batch_log
    WHERE completed_at < cutoff_date
    AND status IN ('completed', 'failed');

    GET DIAGNOSTICS deleted_batches = ROW_COUNT;

    RETURN jsonb_build_object(
        'retention_days', retention_days,
        'deleted_companies', deleted_companies,
        'deleted_people', deleted_people,
        'deleted_batches', deleted_batches,
        'cutoff_date', cutoff_date
    );
END;
$$ LANGUAGE plpgsql;

/**
 * Validate Apify data quality before processing
 * Returns quality score and recommendations
 */
CREATE OR REPLACE FUNCTION validate_apify_batch_quality(batch_id TEXT)
RETURNS JSONB AS $$
DECLARE
    company_stats RECORD;
    people_stats RECORD;
    quality_score INTEGER := 0;
    recommendations TEXT[] := ARRAY[]::TEXT[];
    result JSONB;
BEGIN
    -- Analyze company data quality
    SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE company_name IS NOT NULL AND company_name != '') as has_name,
        COUNT(*) FILTER (WHERE website_url IS NOT NULL AND website_url != '') as has_website,
        COUNT(*) FILTER (WHERE raw_data->>'phone' IS NOT NULL) as has_phone,
        COUNT(*) FILTER (WHERE raw_data->>'industry' IS NOT NULL) as has_industry
    INTO company_stats
    FROM marketing.apify_company_staging
    WHERE batch_unique_id = batch_id;

    -- Analyze people data quality
    SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE first_name IS NOT NULL AND first_name != '') as has_first_name,
        COUNT(*) FILTER (WHERE last_name IS NOT NULL AND last_name != '') as has_last_name,
        COUNT(*) FILTER (WHERE title IS NOT NULL AND title != '') as has_title,
        COUNT(*) FILTER (WHERE raw_data->>'email' IS NOT NULL) as has_email,
        COUNT(*) FILTER (WHERE linkedin_url IS NOT NULL) as has_linkedin
    INTO people_stats
    FROM marketing.apify_people_staging
    WHERE batch_unique_id = batch_id;

    -- Calculate quality score (0-100)
    IF company_stats.total > 0 THEN
        quality_score := quality_score +
            (company_stats.has_name * 100 / company_stats.total) * 0.3 +
            (company_stats.has_website * 100 / company_stats.total) * 0.3 +
            (company_stats.has_phone * 100 / company_stats.total) * 0.2 +
            (company_stats.has_industry * 100 / company_stats.total) * 0.2;
    END IF;

    IF people_stats.total > 0 THEN
        quality_score := (quality_score +
            (people_stats.has_first_name * 100 / people_stats.total) * 0.3 +
            (people_stats.has_last_name * 100 / people_stats.total) * 0.3 +
            (people_stats.has_title * 100 / people_stats.total) * 0.2 +
            (people_stats.has_email * 100 / people_stats.total) * 0.2) / 2;
    END IF;

    -- Generate recommendations
    IF company_stats.has_name < company_stats.total * 0.9 THEN
        recommendations := array_append(recommendations, 'Missing company names detected - check scraping configuration');
    END IF;

    IF company_stats.has_website < company_stats.total * 0.8 THEN
        recommendations := array_append(recommendations, 'Many companies missing websites - consider additional data sources');
    END IF;

    IF people_stats.has_title < people_stats.total * 0.7 THEN
        recommendations := array_append(recommendations, 'Many people missing job titles - may affect slot assignment');
    END IF;

    IF quality_score < 70 THEN
        recommendations := array_append(recommendations, 'Overall data quality is low - consider improving scraping targets');
    END IF;

    result := jsonb_build_object(
        'batch_id', batch_id,
        'quality_score', quality_score,
        'recommendations', recommendations,
        'company_stats', jsonb_build_object(
            'total', company_stats.total,
            'name_coverage', CASE WHEN company_stats.total > 0 THEN company_stats.has_name::FLOAT / company_stats.total ELSE 0 END,
            'website_coverage', CASE WHEN company_stats.total > 0 THEN company_stats.has_website::FLOAT / company_stats.total ELSE 0 END,
            'phone_coverage', CASE WHEN company_stats.total > 0 THEN company_stats.has_phone::FLOAT / company_stats.total ELSE 0 END
        ),
        'people_stats', jsonb_build_object(
            'total', people_stats.total,
            'name_coverage', CASE WHEN people_stats.total > 0 THEN (people_stats.has_first_name + people_stats.has_last_name)::FLOAT / (people_stats.total * 2) ELSE 0 END,
            'title_coverage', CASE WHEN people_stats.total > 0 THEN people_stats.has_title::FLOAT / people_stats.total ELSE 0 END,
            'email_coverage', CASE WHEN people_stats.total > 0 THEN people_stats.has_email::FLOAT / people_stats.total ELSE 0 END
        )
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================

/**
 * Apify Integration Prerequisites Complete
 *
 * Created:
 * - Batch tracking system with Barton IDs
 * - Staging tables for incremental processing
 * - Company deduplication functions
 * - Smart slot type detection from titles
 * - Batch processing functions for companies and people
 * - Monitoring views for import status
 *
 * Ready for:
 * - High-volume Apify data imports
 * - Automatic company/people linkage
 * - Slot assignment based on job titles
 * - Full audit trail compliance
 */