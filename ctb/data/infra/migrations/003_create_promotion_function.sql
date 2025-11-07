-- =============================================================
-- MIGRATION 3: Create Doctrinal Promotion Function
-- =============================================================
-- Created: 2025-10-24
-- Database: Marketing DB (white-union-26418370)
-- Purpose: Automate validated record promotion with logging

CREATE OR REPLACE FUNCTION shq.promote_company_records(batch TEXT, executor TEXT)
RETURNS INTEGER AS $$
DECLARE
    promoted_count INTEGER;
BEGIN
    -- 1️⃣ Insert validated records from intake → master
    INSERT INTO marketing.company_master (
        company_unique_id, company_name, website_url, industry, employee_count,
        company_phone, address_city, address_state, address_country,
        linkedin_url, facebook_url, twitter_url,
        sic_codes, founded_year,
        source_system, source_record_id, promoted_from_intake_at,
        state_abbrev, import_batch_id, validated_at, validated_by
    )
    SELECT
        '04.04.01.' ||
        LPAD((EXTRACT(EPOCH FROM NOW())::BIGINT % 100)::TEXT, 2, '0') || '.' ||
        LPAD((RANDOM() * 100000)::INT::TEXT, 5, '0') || '.' ||
        LPAD((id % 1000)::TEXT, 3, '0'),
        COALESCE(company, company_name_for_emails, 'Unknown Company'),
        COALESCE(website, 'https://example.com'),
        industry,
        num_employees,
        company_phone,
        company_city,
        company_state,
        company_country,
        company_linkedin_url,
        facebook_url,
        twitter_url,
        sic_codes,
        founded_year,
        'intake_promotion',
        id::TEXT,
        NOW(),
        state_abbrev,
        import_batch_id,
        NOW(),
        executor
    FROM intake.company_raw_intake
    WHERE validated IS TRUE
      AND import_batch_id = batch
      AND id::TEXT NOT IN (
          SELECT source_record_id FROM marketing.company_master
      );

    GET DIAGNOSTICS promoted_count = ROW_COUNT;

    -- 2️⃣ Log validation run
    INSERT INTO shq_validation_log (
        validation_run_id, source_table, target_table,
        total_records, passed_records, failed_records,
        executed_by, notes
    )
    VALUES (
        batch,
        'intake.company_raw_intake',
        'marketing.company_master',
        (SELECT COUNT(*) FROM intake.company_raw_intake WHERE import_batch_id = batch),
        promoted_count,
        (SELECT COUNT(*) FROM intake.company_raw_intake WHERE import_batch_id = batch AND validated IS FALSE),
        executor,
        'Promotion completed successfully'
    );

    RETURN promoted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION shq.promote_company_records(TEXT, TEXT) IS
'Promotes validated companies from intake to master table with automatic logging. Parameters: (batch_id, executor_name).';
