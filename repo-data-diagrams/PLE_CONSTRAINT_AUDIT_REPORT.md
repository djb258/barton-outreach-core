# PLE CONSTRAINT AUDIT REPORT

**Generated:** 11/26/2025, 7:44:29 AM
**Barton ID:** 04.04.02.04.50000.001
**Purpose:** Constraint compliance audit for PLE schema tables

---

## 1. NOT NULL CONSTRAINT AUDIT

### company_master

| Column Name | Data Type | Required | Current Status | Action Needed |
|-------------|-----------|----------|----------------|---------------|
| **company_unique_id** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| **company_name** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| website_url | text | No | NOT NULL ✅ | No action |
| industry | text | No | Nullable | No action |
| employee_count | integer | No | Nullable | No action |
| company_phone | text | No | Nullable | No action |
| address_street | text | No | Nullable | No action |
| address_city | text | No | Nullable | No action |
| address_state | text | No | Nullable | No action |
| address_zip | text | No | Nullable | No action |
| address_country | text | No | Nullable | No action |
| linkedin_url | text | No | Nullable | No action |
| facebook_url | text | No | Nullable | No action |
| twitter_url | text | No | Nullable | No action |
| sic_codes | text | No | Nullable | No action |
| founded_year | integer | No | Nullable | No action |
| keywords | ARRAY | No | Nullable | No action |
| description | text | No | Nullable | No action |
| **source_system** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| source_record_id | text | No | Nullable | No action |
| promoted_from_intake_at | timestamp with time zone | No | NOT NULL ✅ | No action |
| promotion_audit_log_id | integer | No | Nullable | No action |
| **created_at** | timestamp with time zone | Yes | Nullable | ⚠️ ADD NOT NULL |
| updated_at | timestamp with time zone | No | Nullable | No action |
| state_abbrev | text | No | Nullable | No action |
| import_batch_id | text | No | Nullable | No action |
| validated_at | timestamp with time zone | No | Nullable | No action |
| validated_by | text | No | Nullable | No action |
| data_quality_score | numeric | No | Nullable | No action |

### company_slot

| Column Name | Data Type | Required | Current Status | Action Needed |
|-------------|-----------|----------|----------------|---------------|
| **company_slot_unique_id** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| **company_unique_id** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| person_unique_id | text | No | Nullable | No action |
| **slot_type** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| is_filled | boolean | No | Nullable | No action |
| confidence_score | numeric | No | Nullable | No action |
| created_at | timestamp with time zone | No | Nullable | No action |
| filled_at | timestamp with time zone | No | Nullable | No action |
| last_refreshed_at | timestamp with time zone | No | Nullable | No action |
| filled_by | text | No | Nullable | No action |
| source_system | text | No | Nullable | No action |
| enrichment_attempts | integer | No | Nullable | No action |
| status | character varying | No | Nullable | No action |

### people_master

| Column Name | Data Type | Required | Current Status | Action Needed |
|-------------|-----------|----------|----------------|---------------|
| **unique_id** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| **company_unique_id** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| company_slot_unique_id | text | No | NOT NULL ✅ | No action |
| **first_name** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| **last_name** | text | Yes | NOT NULL ✅ | ✅ Compliant |
| full_name | text | No | Nullable | No action |
| title | text | No | Nullable | No action |
| seniority | text | No | Nullable | No action |
| department | text | No | Nullable | No action |
| email | text | No | Nullable | No action |
| work_phone_e164 | text | No | Nullable | No action |
| personal_phone_e164 | text | No | Nullable | No action |
| linkedin_url | text | No | Nullable | No action |
| twitter_url | text | No | Nullable | No action |
| facebook_url | text | No | Nullable | No action |
| bio | text | No | Nullable | No action |
| skills | ARRAY | No | Nullable | No action |
| education | text | No | Nullable | No action |
| certifications | ARRAY | No | Nullable | No action |
| source_system | text | No | NOT NULL ✅ | No action |
| source_record_id | text | No | Nullable | No action |
| promoted_from_intake_at | timestamp with time zone | No | NOT NULL ✅ | No action |
| promotion_audit_log_id | integer | No | Nullable | No action |
| **created_at** | timestamp with time zone | Yes | Nullable | ⚠️ ADD NOT NULL |
| updated_at | timestamp with time zone | No | Nullable | No action |
| email_verified | boolean | No | Nullable | No action |
| message_key_scheduled | text | No | Nullable | No action |
| email_verification_source | text | No | Nullable | No action |
| email_verified_at | timestamp with time zone | No | Nullable | No action |

## 2. CHECK CONSTRAINT AUDIT

| Table | Constraint Name | Required | Current Status | Action Needed |
|-------|-----------------|----------|----------------|---------------|
| company_master | chk_employee_range | Yes | ❌ MISSING | ⚠️ CREATE CONSTRAINT |
| company_master | chk_state_valid | Yes | ❌ MISSING | ⚠️ CREATE CONSTRAINT |
| company_slot | chk_slot_type | Yes | ❌ MISSING | ⚠️ CREATE CONSTRAINT |
| people_master | chk_contact_required | Yes | ❌ MISSING | ⚠️ CREATE CONSTRAINT |

### Required CHECK Constraint Details:

**chk_employee_range** (company_master)
- Description: Employee count must be between 50 and 2000
- Condition: `(employee_count >= 50 AND employee_count <= 2000)`

**chk_state_valid** (company_master)
- Description: State must be valid mid-Atlantic abbreviation or full name
- Condition: `(address_state IN ('PA','VA','MD','OH','WV','KY','Pennsylvania','Virginia','Maryland','Ohio','West Virginia','Kentucky'))`

**chk_slot_type** (company_slot)
- Description: Slot type must be CEO, CFO, or HR (case-insensitive)
- Condition: `(LOWER(slot_type) IN ('ceo','cfo','hr'))`

**chk_contact_required** (people_master)
- Description: At least one of LinkedIn URL or email must be provided
- Condition: `(linkedin_url IS NOT NULL OR email IS NOT NULL)`

## 3. UNIQUE CONSTRAINT AUDIT

| Table | Constraint Name | Type | Columns | Required | Current Status | Action Needed |
|-------|-----------------|------|---------|----------|----------------|---------------|
| company_master | company_master_pkey | PRIMARY KEY | company_unique_id | Yes | ✅ PRIMARY KEY | ✅ Compliant |
| company_slot | uq_company_slot_type | UNIQUE | company_unique_id, slot_type | Yes | ✅ UNIQUE | ✅ Compliant |
| people_master | people_master_pkey | PRIMARY KEY | unique_id | Yes | ✅ PRIMARY KEY | ✅ Compliant |

## 4. DATA VIOLATION REPORT

### Violations That Would Prevent Constraint Creation

#### Employee Count Range (50-2000)
- **Violations:** 16
- **Impact:** ⚠️ Cannot add chk_employee_range until fixed

#### State Validation
- **Violations:** 0
- **Impact:** ✅ No violations

#### Slot Type Validation
- **Violations:** 0
- **Impact:** ✅ No violations

#### Contact Info Required
- **Violations:** 0
- **Impact:** ✅ No violations

#### NULL Values in Required Columns

| Table | Column | NULL Count | Impact |
|-------|--------|------------|--------|
| company_master | company_name | 0 | ✅ OK |
| company_master | source_system | 0 | ✅ OK |
| company_slot | company_unique_id | 0 | ✅ OK |
| company_slot | slot_type | 0 | ✅ OK |
| people_master | company_unique_id | 0 | ✅ OK |
| people_master | first_name | 0 | ✅ OK |
| people_master | last_name | 0 | ✅ OK |

### Summary

- **Total Violations:** 16
- **Status:** ⚠️ Data cleanup required before adding constraints

## 5. RECOMMENDATIONS

### Data Cleanup Required (Priority Order)

1. **Fix NULL values in required columns** - Highest priority
2. **Resolve duplicate company_slot records** - Prevents unique constraint
3. **Fix employee_count range violations** - Out of 50-2000 range
4. **Fix state abbreviation violations** - Invalid state codes
5. **Fix slot_type violations** - Must be CEO/CFO/HR
6. **Fix missing contact info** - Need LinkedIn OR email

### After Data Cleanup

1. Run data cleanup queries (see migration SQL)
2. Re-run this audit to verify 0 violations
3. Execute constraint migration SQL in transaction
4. Verify all constraints are active

## 6. EXISTING CONSTRAINTS INVENTORY

### CHECK Constraints Currently Defined

| Table | Constraint Name | Check Clause |
|-------|-----------------|--------------|
| company_invalid | 81920_1474561_14_not_null | reason_code IS NOT NULL |
| company_invalid | 81920_1474561_15_not_null | validation_errors IS NOT NULL |
| company_invalid | 81920_1474561_1_not_null | id IS NOT NULL |
| company_invalid | 81920_1474561_2_not_null | company_unique_id IS NOT NULL |
| company_master | 81920_344068_19_not_null | source_system IS NOT NULL |
| company_master | 81920_344068_1_not_null | company_unique_id IS NOT NULL |
| company_master | 81920_344068_21_not_null | promoted_from_intake_at IS NOT NULL |
| company_master | 81920_344068_2_not_null | company_name IS NOT NULL |
| company_master | 81920_344068_3_not_null | website_url IS NOT NULL |
| company_master | company_master_barton_id_format | (company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'::text) |
| company_master | company_master_employee_count_positive | ((employee_count IS NULL) OR (employee_count >= 0)) |
| company_master | company_master_founded_year_reasonable | ((founded_year IS NULL) OR ((founded_year >= 1700) AND ((founded_year)::numeric <= EXTRACT(year FROM now())))) |
| company_raw_wv | 81920_1458308_1_not_null | company_unique_id IS NOT NULL |
| company_sidecar | 81920_2383930_1_not_null | company_unique_id IS NOT NULL |
| company_slot | 81920_1474605_1_not_null | company_slot_unique_id IS NOT NULL |
| company_slot | 81920_1474605_2_not_null | company_unique_id IS NOT NULL |
| company_slot | 81920_1474605_4_not_null | slot_type IS NOT NULL |
| company_slot | company_slot_slot_type_check | (slot_type = ANY (ARRAY['CEO'::text, 'CFO'::text, 'HR'::text])) |
| company_slot | company_slot_slot_type_check | (slot_type = ANY (ARRAY['CEO'::text, 'CFO'::text, 'HR'::text, 'CTO'::text, 'CMO'::text, 'COO'::text, 'VP_SALES'::text, 'VP_MARKETING'::text, 'DIRECTOR'::text, 'MANAGER'::text])) |
| company_slots | 81920_360457_1_not_null | company_slot_unique_id IS NOT NULL |
| company_slots | 81920_360457_2_not_null | company_unique_id IS NOT NULL |
| contact_enrichment | 81920_409620_1_not_null | id IS NOT NULL |
| contact_enrichment | 81920_409620_2_not_null | company_slot_unique_id IS NOT NULL |
| contact_enrichment | contact_enrichment_enrichment_status_check | (enrichment_status = ANY (ARRAY['pending'::text, 'processing'::text, 'completed'::text, 'failed'::text])) |
| email_verification | 81920_409640_1_not_null | id IS NOT NULL |
| email_verification | 81920_409640_2_not_null | enrichment_id IS NOT NULL |
| email_verification | 81920_409640_3_not_null | email IS NOT NULL |
| email_verification | email_verification_verification_status_check | (verification_status = ANY (ARRAY['pending'::text, 'valid'::text, 'invalid'::text, 'risky'::text, 'unknown'::text])) |
| message_key_reference | 81920_1146880_1_not_null | message_key IS NOT NULL |
| message_key_reference | 81920_1146880_2_not_null | role IS NOT NULL |
| message_key_reference | 81920_1146880_3_not_null | message_type IS NOT NULL |
| message_key_reference | message_channel_valid | (message_channel = ANY (ARRAY['email'::text, 'linkedin'::text, 'sms'::text, 'both'::text, 'multi'::text])) |
| message_key_reference | message_key_format | (message_key ~ '^MSG\.[A-Z]+\.[0-9]{3}\.[A-Z]$'::text) |
| message_key_reference | message_role_valid | (role = ANY (ARRAY['CEO'::text, 'CFO'::text, 'HR'::text, 'ALL'::text])) |
| people_invalid | 81920_1474578_15_not_null | reason_code IS NOT NULL |
| people_invalid | 81920_1474578_16_not_null | validation_errors IS NOT NULL |
| people_invalid | 81920_1474578_1_not_null | id IS NOT NULL |
| people_invalid | 81920_1474578_2_not_null | unique_id IS NOT NULL |
| people_master | 81920_344090_1_not_null | unique_id IS NOT NULL |
| people_master | 81920_344090_20_not_null | source_system IS NOT NULL |
| people_master | 81920_344090_22_not_null | promoted_from_intake_at IS NOT NULL |
| people_master | 81920_344090_2_not_null | company_unique_id IS NOT NULL |
| people_master | 81920_344090_3_not_null | company_slot_unique_id IS NOT NULL |
| people_master | 81920_344090_4_not_null | first_name IS NOT NULL |
| people_master | 81920_344090_5_not_null | last_name IS NOT NULL |
| people_master | people_master_barton_id_format | (unique_id ~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'::text) |
| people_master | people_master_company_barton_id_format | (company_unique_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'::text) |
| people_master | people_master_email_format | ((email IS NULL) OR (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'::text)) |
| people_master | people_master_slot_barton_id_format | (company_slot_unique_id ~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'::text) |
| people_raw_wv | 81920_1458316_1_not_null | unique_id IS NOT NULL |
| people_resolution_queue | 81920_1138689_1_not_null | queue_id IS NOT NULL |
| people_resolution_queue | 81920_1138689_2_not_null | company_unique_id IS NOT NULL |
| people_resolution_queue | 81920_1138689_3_not_null | company_slot_unique_id IS NOT NULL |
| people_resolution_queue | 81920_1138689_6_not_null | issue_type IS NOT NULL |
| people_resolution_queue | people_resolution_queue_status_check | (status = ANY (ARRAY['pending'::text, 'in_progress'::text, 'resolved'::text, 'escalated'::text, 'failed'::text])) |
| people_resolution_queue | queue_issue_type_valid | (issue_type = ANY (ARRAY['missing_contact'::text, 'bad_email'::text, 'duplicate'::text, 'invalid_data'::text, 'unverified_email'::text, 'incomplete_profile'::text])) |
| people_sidecar | 81920_2383952_1_not_null | person_unique_id IS NOT NULL |
| pipeline_errors | 81920_409661_1_not_null | id IS NOT NULL |
| pipeline_errors | 81920_409661_2_not_null | event_type IS NOT NULL |
| pipeline_errors | 81920_409661_3_not_null | record_id IS NOT NULL |
| pipeline_errors | 81920_409661_4_not_null | error_message IS NOT NULL |
| pipeline_errors | pipeline_errors_severity_check | (severity = ANY (ARRAY['warning'::text, 'error'::text, 'critical'::text])) |
| pipeline_events | 81920_409601_1_not_null | id IS NOT NULL |
| pipeline_events | 81920_409601_2_not_null | event_type IS NOT NULL |
| pipeline_events | 81920_409601_3_not_null | payload IS NOT NULL |
| pipeline_events | pipeline_events_status_check | (status = ANY (ARRAY['pending'::text, 'processing'::text, 'processed'::text, 'failed'::text])) |
| validation_failures_log | 81920_2285569_10_not_null | failure_type IS NOT NULL |
| validation_failures_log | 81920_2285569_1_not_null | id IS NOT NULL |
| validation_failures_log | 81920_2285569_6_not_null | fail_reason IS NOT NULL |
| validation_failures_log | 81920_2285569_9_not_null | pipeline_id IS NOT NULL |
| validation_failures_log | validation_failures_log_failure_type_check | (failure_type = ANY (ARRAY['company'::text, 'person'::text])) |

### UNIQUE/PRIMARY KEY Constraints Currently Defined

| Table | Constraint Name | Type | Columns |
|-------|-----------------|------|---------|
| company_master | company_master_pkey | PRIMARY KEY | company_unique_id |
| company_slot | company_slot_pkey | PRIMARY KEY | company_slot_unique_id |
| company_slot | unique_company_slot | UNIQUE | company_unique_id, slot_type |
| people_master | people_master_pkey | PRIMARY KEY | unique_id |

---

**Next Steps:**
1. Review this audit report
2. Execute data cleanup if violations found
3. Review and execute `ple_constraint_migration.sql`
4. Verify constraints with follow-up audit

**Generated by:** PLE Constraint Audit Script (Barton ID: 04.04.02.04.50000.001)