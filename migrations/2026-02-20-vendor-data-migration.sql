-- =============================================================================
-- MIGRATION: Vendor Data Migration
-- Date: 2026-02-20
-- Phase: Legacy Collapse Playbook — Phase 3 (Migrate), Step 2
-- Purpose: INSERT data from source tables INTO vendor.* tables
-- Approach: INSERT...SELECT per source table, preserving ALL data
-- =============================================================================

-- =============================================================================
-- VENDOR.CT — Company vendor data
-- =============================================================================

-- Source 1: enrichment.hunter_company → vendor.ct
INSERT INTO vendor.ct (
    source_table, source_row_id,
    domain, company_name, company_unique_id, outreach_id,
    street, city, state, postal_code, country, address_full,
    industry, industry_normalized, headcount_raw, headcount_min, headcount_max,
    company_type, email_pattern,
    data_quality_score, source_system, source_file, tags, enriched_at,
    original_created_at, original_updated_at
)
SELECT
    'enrichment.hunter_company', id::text,
    domain, organization, company_unique_id, outreach_id,
    street, city, state, postal_code, country, location_full,
    industry, industry_normalized, headcount, headcount_min, headcount_max,
    company_type, email_pattern,
    data_quality_score, source, source_file, tags, enriched_at,
    created_at, updated_at
FROM enrichment.hunter_company;

-- Source 2: company.company_master → vendor.ct
INSERT INTO vendor.ct (
    source_table, source_row_id,
    domain, company_name, company_unique_id,
    street, city, state, state_abbrev, postal_code, country,
    industry, employee_count, company_phone, founded_year, sic_codes,
    description, keywords,
    website_url, linkedin_url, facebook_url, twitter_url,
    email_pattern, email_pattern_confidence, email_pattern_source, email_pattern_verified_at,
    data_quality_score, source_system, source_record_id, import_batch_id,
    ein, duns, cage_code,
    validated_at, validated_by,
    promoted_from_intake_at, promotion_audit_log_id,
    original_created_at, original_updated_at
)
SELECT
    'company.company_master', company_unique_id,
    website_url, company_name, company_unique_id,
    address_street, address_city, address_state, state_abbrev, address_zip, address_country,
    industry, employee_count, company_phone, founded_year, sic_codes,
    description, keywords,
    website_url, linkedin_url, facebook_url, twitter_url,
    email_pattern, email_pattern_confidence, email_pattern_source, email_pattern_verified_at,
    data_quality_score, source_system, source_record_id, import_batch_id,
    ein, duns, cage_code,
    validated_at, validated_by,
    promoted_from_intake_at, promotion_audit_log_id,
    created_at, updated_at
FROM company.company_master;

-- Source 3: intake.company_raw_intake → vendor.ct
INSERT INTO vendor.ct (
    source_table, source_row_id,
    domain, company_name, company_name_for_emails,
    city, state, postal_code, country, address_full,
    industry, employee_count, company_phone, founded_year, sic_codes,
    website_url, linkedin_url, facebook_url, twitter_url,
    import_batch_id,
    validated, validation_notes, validation_reasons, validated_at, validated_by,
    enrichment_attempt, chronic_bad, last_enriched_at, enriched_by,
    state_abbrev, b2_file_path, b2_uploaded_at, apollo_id, last_hash, garage_bay,
    original_created_at
)
SELECT
    'intake.company_raw_intake', id::text,
    website, company, company_name_for_emails,
    company_city, company_state, company_postal_code, company_country, company_address,
    industry, num_employees, company_phone, founded_year, sic_codes,
    website, company_linkedin_url, facebook_url, twitter_url,
    import_batch_id,
    validated, validation_notes, validation_reasons, validated_at, validated_by,
    enrichment_attempt, chronic_bad, last_enriched_at, enriched_by,
    state_abbrev, b2_file_path, b2_uploaded_at, apollo_id, last_hash, garage_bay,
    created_at
FROM intake.company_raw_intake;

-- Source 4: intake.company_raw_wv → vendor.ct
INSERT INTO vendor.ct (
    source_table, source_row_id,
    domain, company_name, company_unique_id,
    website_url, industry, employee_count, company_phone,
    address_full, city, state, postal_code,
    original_created_at
)
SELECT
    'intake.company_raw_wv', company_unique_id,
    domain, company_name, company_unique_id,
    website, industry, employee_count, phone,
    address, city, state, zip,
    created_at
FROM intake.company_raw_wv;


-- =============================================================================
-- VENDOR.PEOPLE — People vendor data
-- =============================================================================

-- Source 1: enrichment.hunter_contact → vendor.people
-- Note: source_1..source_30 collapsed into hunter_sources array
INSERT INTO vendor.people (
    source_table, source_row_id,
    domain, email, first_name, last_name, full_name,
    company_unique_id, outreach_id,
    job_title, title_normalized, position_raw, seniority_level,
    department, department_normalized, is_decision_maker,
    phone_number, linkedin_url, twitter_handle,
    email_type, email_verified, confidence_score, num_sources,
    data_quality_score, outreach_priority, source_system, source_file, tags,
    hunter_sources,
    original_created_at
)
SELECT
    'enrichment.hunter_contact', id::text,
    domain, email, first_name, last_name, full_name,
    company_unique_id, outreach_id,
    job_title, title_normalized, position_raw, seniority_level,
    department, department_normalized, is_decision_maker,
    phone_number, linkedin_url, twitter_handle,
    email_type, email_verified, confidence_score, num_sources,
    data_quality_score, outreach_priority, source, source_file, tags,
    -- Collapse source_1..source_30 into array, filtering NULLs
    ARRAY_REMOVE(ARRAY[
        source_1, source_2, source_3, source_4, source_5,
        source_6, source_7, source_8, source_9, source_10,
        source_11, source_12, source_13, source_14, source_15,
        source_16, source_17, source_18, source_19, source_20,
        source_21, source_22, source_23, source_24, source_25,
        source_26, source_27, source_28, source_29, source_30
    ], NULL),
    created_at
FROM enrichment.hunter_contact;

-- Source 2: intake.people_raw_intake → vendor.people
INSERT INTO vendor.people (
    source_table, source_row_id,
    email, first_name, last_name, full_name,
    company_name, company_unique_id,
    job_title, seniority_level, department, slot_type,
    work_phone, personal_phone, linkedin_url, twitter_url, facebook_url,
    bio, skills, education, certifications,
    city, state, state_abbrev, country,
    source_system, source_record_id, import_batch_id, backfill_source,
    validated, validation_notes, validated_at, validated_by,
    enrichment_attempt, chronic_bad, last_enriched_at, enriched_by,
    b2_file_path, b2_uploaded_at,
    original_created_at, original_updated_at
)
SELECT
    'intake.people_raw_intake', id::text,
    email, first_name, last_name, full_name,
    company_name, company_unique_id,
    title, seniority, department, slot_type,
    work_phone, personal_phone, linkedin_url, twitter_url, facebook_url,
    bio, skills, education, certifications,
    city, state, state_abbrev, country,
    source_system, source_record_id, import_batch_id, backfill_source,
    validated, validation_notes, validated_at, validated_by,
    enrichment_attempt, chronic_bad, last_enriched_at, enriched_by,
    b2_file_path, b2_uploaded_at,
    created_at, updated_at
FROM intake.people_raw_intake;

-- Source 3: intake.people_staging → vendor.people
INSERT INTO vendor.people (
    source_table, source_row_id,
    company_unique_id,
    raw_name, first_name, last_name,
    job_title, title_normalized, mapped_slot_type,
    linkedin_url, email,
    confidence_score, status,
    source_url_id,
    original_created_at, processed_at
)
SELECT
    'intake.people_staging', id::text,
    company_unique_id,
    raw_name, first_name, last_name,
    raw_title, normalized_title, mapped_slot_type,
    linkedin_url, email,
    confidence_score, status,
    source_url_id,
    created_at, processed_at
FROM intake.people_staging;

-- Source 4: intake.people_raw_wv → vendor.people
INSERT INTO vendor.people (
    source_table, source_row_id,
    full_name, first_name, last_name, email, phone_number,
    job_title, company_name, company_unique_id,
    linkedin_url, city, state,
    original_created_at
)
SELECT
    'intake.people_raw_wv', unique_id,
    full_name, first_name, last_name, email, phone,
    title, company_name, company_unique_id,
    linkedin_url, city, state,
    created_at
FROM intake.people_raw_wv;


-- =============================================================================
-- VENDOR.BLOG — Blog/URL vendor data
-- =============================================================================

-- Source 1: outreach.sitemap_discovery → vendor.blog
INSERT INTO vendor.blog (
    source_table, source_row_id,
    domain, outreach_id,
    sitemap_url, sitemap_source, has_sitemap,
    domain_reachable, http_status, reachable_checked_at,
    discovered_at
)
SELECT
    'outreach.sitemap_discovery', outreach_id::text,
    domain, outreach_id,
    sitemap_url, sitemap_source, has_sitemap,
    domain_reachable, http_status, reachable_checked_at,
    discovered_at
FROM outreach.sitemap_discovery;

-- Source 2: outreach.source_urls → vendor.blog
INSERT INTO vendor.blog (
    source_table, source_row_id,
    outreach_id,
    source_type, source_url, discovered_from, discovered_at
)
SELECT
    'outreach.source_urls', id::text,
    outreach_id,
    source_type, source_url, discovered_from, discovered_at
FROM outreach.source_urls;

-- Source 3: company.company_source_urls → vendor.blog
INSERT INTO vendor.blog (
    source_table, source_row_id,
    company_unique_id,
    source_type, source_url, page_title,
    discovered_from, discovered_at,
    http_status, is_accessible, last_checked_at,
    content_checksum, last_content_change_at,
    extraction_status, extracted_at, extraction_error,
    people_extracted, requires_paid_enrichment,
    original_created_at, original_updated_at
)
SELECT
    'company.company_source_urls', source_id::text,
    company_unique_id,
    source_type, source_url, page_title,
    discovered_from, discovered_at,
    http_status, is_accessible, last_checked_at,
    content_checksum, last_content_change_at,
    extraction_status, extracted_at, extraction_error,
    people_extracted, requires_paid_enrichment,
    created_at, updated_at
FROM company.company_source_urls;


-- =============================================================================
-- VENDOR.CT_CLAUDE — CL enrichment outputs
-- =============================================================================

-- Source 1: cl.company_domains → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id, domain,
    domain_health, mx_present, domain_name_confidence,
    checked_at
)
SELECT
    'cl.company_domains', domain_id::text,
    company_unique_id, domain,
    domain_health, mx_present, domain_name_confidence,
    checked_at
FROM cl.company_domains;

-- Source 2: cl.company_domains_excluded → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id, domain,
    domain_health, mx_present, domain_name_confidence,
    checked_at
)
SELECT
    'cl.company_domains_excluded', domain_id::text,
    company_unique_id, domain,
    domain_health, mx_present, domain_name_confidence,
    checked_at
FROM cl.company_domains_excluded;

-- Source 3: cl.company_names → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id,
    name_value, name_type,
    original_created_at
)
SELECT
    'cl.company_names', name_id::text,
    company_unique_id,
    name_value, name_type,
    created_at
FROM cl.company_names;

-- Source 4: cl.company_names_excluded → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id,
    name_value, name_type,
    original_created_at
)
SELECT
    'cl.company_names_excluded', name_id::text,
    company_unique_id,
    name_value, name_type,
    created_at
FROM cl.company_names_excluded;

-- Source 5: cl.company_candidate → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id,
    source_system, source_record_id, state_code,
    raw_payload, ingestion_run_id,
    verification_status, verification_error,
    verified_at, original_created_at
)
SELECT
    'cl.company_candidate', candidate_id::text,
    company_unique_id,
    source_system, source_record_id, state_code,
    raw_payload, ingestion_run_id,
    verification_status, verification_error,
    verified_at, created_at
FROM cl.company_candidate;

-- Source 6: cl.identity_confidence → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id,
    confidence_score, confidence_bucket,
    computed_at
)
SELECT
    'cl.identity_confidence', company_unique_id::text,
    company_unique_id,
    confidence_score, confidence_bucket,
    computed_at
FROM cl.identity_confidence;

-- Source 7: cl.identity_confidence_excluded → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    company_unique_id,
    confidence_score, confidence_bucket,
    computed_at
)
SELECT
    'cl.identity_confidence_excluded', company_unique_id::text,
    company_unique_id,
    confidence_score, confidence_bucket,
    computed_at
FROM cl.identity_confidence_excluded;

-- Source 8: cl.domain_hierarchy → vendor.ct_claude
INSERT INTO vendor.ct_claude (
    source_table, source_row_id,
    domain,
    parent_company_id, child_company_id,
    relationship_type, confidence_score, resolution_method,
    original_created_at
)
SELECT
    'cl.domain_hierarchy', hierarchy_id::text,
    domain,
    parent_company_id, child_company_id,
    relationship_type, confidence_score, resolution_method,
    created_at
FROM cl.domain_hierarchy;


-- =============================================================================
-- VENDOR.PEOPLE_CLAUDE — People enrichment queue data
-- =============================================================================

-- Source 1: people.paid_enrichment_queue → vendor.people_claude
INSERT INTO vendor.people_claude (
    source_table, source_row_id,
    company_unique_id, company_name,
    source_url_id, source_url, url_type,
    failure_reason, empty_slots,
    priority, status, processed_via,
    queued_at, processed_at
)
SELECT
    'people.paid_enrichment_queue', id::text,
    company_unique_id, company_name,
    source_url_id, source_url, url_type,
    failure_reason, empty_slots,
    priority, status, processed_via,
    queued_at, processed_at
FROM people.paid_enrichment_queue;

-- Source 2: people.people_resolution_queue → vendor.people_claude
INSERT INTO vendor.people_claude (
    source_table, source_row_id,
    company_unique_id, company_slot_unique_id,
    slot_type, existing_email, issue_type,
    priority, status,
    resolved_contact_id, assigned_to, touched_by,
    notes, error_details, attempt_count,
    original_created_at, last_touched_at, resolved_at
)
SELECT
    'people.people_resolution_queue', queue_id::text,
    company_unique_id, company_slot_unique_id,
    slot_type, existing_email, issue_type,
    priority, status,
    resolved_contact_id, assigned_to, touched_by,
    notes, error_details, attempt_count,
    created_at, last_touched_at, resolved_at
FROM people.people_resolution_queue;


-- =============================================================================
-- VENDOR.DOL_CLAUDE — DOL enrichment data
-- =============================================================================

-- Source 1: outreach.dol_url_enrichment → vendor.dol_claude
INSERT INTO vendor.dol_claude (
    source_table, source_row_id,
    ein, legal_name, dba_name,
    matched_company_unique_id,
    enriched_url, search_query, confidence, match_status,
    participants, city, state, zip,
    original_created_at
)
SELECT
    'outreach.dol_url_enrichment', id::text,
    ein, legal_name, dba_name,
    matched_company_unique_id,
    enriched_url, search_query, confidence, match_status,
    participants, city, state, zip,
    created_at
FROM outreach.dol_url_enrichment;
