# PLE Schema - Complete Column Reference

## Overview

This document provides complete column-level documentation for all tables in the Barton Outreach Core database.

**Database**: Neon PostgreSQL
**Host**: `ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech`
**Total Tables**: 31
**Total Rows**: 2.4M+

---

## Schema: `marketing` (Company Hub)

### company_master

**Purpose**: Central anchor table for all company data. The AXLE of the hub-and-spoke architecture.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `company_unique_id` | TEXT | NO (PK) | Barton ID: 04.04.01.XX.XXXXX.XXX |
| `company_name` | TEXT | NO | Normalized company name |
| `website_url` | TEXT | YES | Primary website URL |
| `domain` | VARCHAR | NO | **ANCHOR FIELD** - Validated domain |
| `email_pattern` | VARCHAR | NO | **ANCHOR FIELD** - Email pattern |
| `ein` | VARCHAR | YES | Federal EIN (links to DOL) |
| `employee_count` | INTEGER | NO | Must be >= 50 |
| `address_state` | TEXT | NO | PA, VA, MD, OH, WV, KY only |
| `industry` | TEXT | YES | Industry classification |
| `founded_year` | INTEGER | YES | Year founded (1700+) |
| `linkedin_url` | TEXT | YES | Company LinkedIn page |
| `data_quality_score` | NUMERIC | YES | Overall quality 0-100 |
| `email_pattern_source` | VARCHAR | YES | hunter, manual, enrichment |
| `created_at` | TIMESTAMP | NO | Record creation |
| `updated_at` | TIMESTAMP | NO | Last modification |
| `validated_at` | TIMESTAMP | YES | When validated |

**Indexes**:
- `company_master_pkey` (company_unique_id)
- `idx_company_domain` (domain)
- `idx_company_ein` (ein)
- `idx_company_state` (address_state)

---

### company_slot

**Purpose**: Tracks executive position slots per company. Bridges to People Hub.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `company_slot_unique_id` | TEXT | NO (PK) | Barton ID: 04.04.05.XX.XXXXX |
| `company_unique_id` | TEXT | NO (FK) | Links to company_master |
| `person_unique_id` | TEXT | YES (FK) | Links to people_master |
| `slot_type` | TEXT | NO | CHRO, HR_MANAGER, BENEFITS_LEAD, PAYROLL_ADMIN, HR_SUPPORT |
| `is_filled` | BOOLEAN | NO | Is someone in this slot? |
| `status` | VARCHAR | NO | open, filled, vacated |
| `confidence_score` | NUMERIC | YES | Assignment confidence 0-100 |
| `filled_at` | TIMESTAMP | YES | When slot was filled |
| `vacated_at` | TIMESTAMP | YES | When person left |
| `enrichment_attempts` | INTEGER | YES | Enrichment attempt count |
| `last_refreshed_at` | TIMESTAMP | YES | Last enrichment refresh |

**Slot Type Hierarchy** (Seniority):
1. CHRO (100) - Chief HR Officer, VP HR, SVP HR
2. HR_MANAGER (80) - HR Director, HR Manager, HR Lead
3. BENEFITS_LEAD (60) - Benefits Manager, Benefits Director
4. PAYROLL_ADMIN (50) - Payroll Manager, Payroll Director
5. HR_SUPPORT (30) - HR Coordinator, Specialist, HRBP

---

### company_events

**Purpose**: News/blog signals that impact BIT scores.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `company_unique_id` | TEXT | NO (FK) | Links to company_master |
| `event_type` | TEXT | NO | funding, acquisition, layoff, expansion, leadership_change |
| `event_date` | DATE | YES | When event occurred |
| `source_url` | TEXT | YES | Source article |
| `summary` | TEXT | YES | Event summary |
| `detected_at` | TIMESTAMP | NO | When detected |
| `impacts_bit` | BOOLEAN | NO | Affects BIT score? |
| `bit_impact_score` | INTEGER | YES | Impact: -100 to +100 |

---

### pipeline_events

**Purpose**: Audit trail for all pipeline operations.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `event_type` | TEXT | NO | phase_start, phase_complete, error, retry |
| `phase` | INTEGER | YES | Pipeline phase 1-8 |
| `correlation_id` | TEXT | YES | Request tracing ID |
| `company_id` | TEXT | YES (FK) | Links to company_master |
| `person_id` | TEXT | YES (FK) | Links to people_master |
| `timestamp` | TIMESTAMP | NO | Event time |
| `metadata` | JSONB | YES | Event details |
| `duration_ms` | INTEGER | YES | Processing time in ms |

---

## Schema: `people` (People Hub)

### people_master

**Purpose**: Human identity and employment state. Owns slot ASSIGNMENTS.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `unique_id` | TEXT | NO (PK) | Barton ID: 04.04.02.XX.XXXXX |
| `company_unique_id` | TEXT | NO (FK) | Links to company_master (REQUIRED) |
| `company_slot_unique_id` | TEXT | NO (FK) | Links to company_slot (REQUIRED) |
| `first_name` | TEXT | NO | First name |
| `last_name` | TEXT | NO | Last name |
| `full_name` | TEXT | YES | Display name |
| `title` | TEXT | YES | Job title |
| `seniority` | TEXT | YES | CHRO > VP > Director > Manager |
| `department` | TEXT | YES | HR, Finance, etc. |
| `email` | TEXT | YES | Verified email address |
| `email_verified` | BOOLEAN | NO | Verification status |
| `email_verified_at` | TIMESTAMP | YES | When verified |
| `email_verification_src` | TEXT | YES | millionverifier, manual |
| `work_phone_e164` | TEXT | YES | Work phone (E.164 format) |
| `linkedin_url` | TEXT | YES | LinkedIn profile URL |
| `created_at` | TIMESTAMP | NO | Record creation |
| `updated_at` | TIMESTAMP | NO | Last modification |

---

### person_scores

**Purpose**: BIT (Buyer Intent Tool) scores per person.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `person_unique_id` | TEXT | NO (FK, UNIQUE) | Links to people_master |
| `bit_score` | INTEGER | YES | BIT score 0-100 |
| `confidence_score` | INTEGER | YES | Data confidence 0-100 |
| `calculated_at` | TIMESTAMP | YES | When calculated |
| `score_factors` | JSONB | YES | Breakdown of factors |

---

### person_movement_history

**Purpose**: Tracks job changes and company movements.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `person_unique_id` | TEXT | NO (FK) | Links to people_master |
| `linkedin_url` | TEXT | YES | LinkedIn URL at detection |
| `company_from_id` | TEXT | YES (FK) | Source company |
| `company_to_id` | TEXT | YES (FK) | Destination company |
| `title_from` | TEXT | YES | Previous title |
| `title_to` | TEXT | YES | New title |
| `movement_type` | TEXT | NO | company_change, title_change, promotion |
| `detected_at` | TIMESTAMP | NO | Detection time |
| `raw_payload` | JSONB | YES | Raw enrichment data |

---

### people_resolution_queue

**Purpose**: Manual review queue for problematic person records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `person_data` | JSONB | NO | Person data blob |
| `resolution_status` | TEXT | NO | pending, resolved, rejected |
| `hold_reason` | TEXT | YES | Why held for review |
| `created_at` | TIMESTAMP | NO | When queued |
| `resolved_at` | TIMESTAMP | YES | When resolved |
| `resolved_by` | TEXT | YES | Resolver |

---

## Schema: `dol` (DOL Filings Hub)

### form_5500

**Purpose**: Large retirement plan filings (100+ participants).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `ack_id` | TEXT | NO (PK) | DOL acknowledgment ID |
| `ein` | VARCHAR | NO | Employer ID (links to company) |
| `plan_number` | VARCHAR | YES | Plan identifier |
| `plan_name` | TEXT | YES | Plan name |
| `sponsor_dfe_name` | TEXT | YES | Sponsor/employer name |
| `sponsor_dfe_ein` | VARCHAR | YES | Sponsor EIN |
| `spons_dfe_mail_us_city` | TEXT | YES | City |
| `spons_dfe_mail_us_state` | TEXT | YES | State |
| `tot_partcp_boy_cnt` | INTEGER | YES | Participant count (BOY) |
| `tot_assets_boy_amt` | NUMERIC | YES | Total assets (BOY) |
| `plan_eff_date` | DATE | YES | Plan effective date |
| `form_plan_year_begin` | DATE | YES | Plan year begin |
| `form_plan_year_end` | DATE | YES | Plan year end (renewal date) |
| `type_pension_bnft_code` | VARCHAR | YES | Pension benefit type code |
| `type_welfare_bnft_code` | VARCHAR | YES | Welfare benefit type code |

**Row Count**: ~230,000

---

### form_5500_sf

**Purpose**: Small retirement plan filings (<100 participants).

Same structure as form_5500.

**Row Count**: ~760,000

---

### schedule_a

**Purpose**: Insurance contract information from Form 5500.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `ack_id` | TEXT | NO (PK) | DOL acknowledgment ID |
| `insurance_company_name` | TEXT | YES | Insurance carrier name |
| `prov_contract_num` | VARCHAR | YES | Contract number |
| `covered_persons_cnt` | INTEGER | YES | Covered lives |
| `premium_amount` | NUMERIC | YES | Premium information |
| `commission_amount` | NUMERIC | YES | Broker commission |

**Row Count**: ~337,000

---

## Schema: `intake` (Staging)

### company_raw_intake

**Purpose**: Raw company imports before validation.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `raw_company_name` | TEXT | YES | Raw company name |
| `raw_domain` | TEXT | YES | Raw domain |
| `raw_address` | TEXT | YES | Raw address |
| `source` | TEXT | YES | Import source |
| `import_date` | TIMESTAMP | NO | When imported |
| `processed` | BOOLEAN | NO | Has been processed? |
| `processed_at` | TIMESTAMP | YES | When processed |

---

### people_raw_intake

**Purpose**: Raw people imports before validation.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `raw_name` | TEXT | YES | Raw full name |
| `raw_title` | TEXT | YES | Raw job title |
| `raw_company` | TEXT | YES | Raw company name |
| `source` | TEXT | YES | Import source |
| `import_date` | TIMESTAMP | NO | When imported |

---

### quarantine

**Purpose**: Invalid/rejected company records.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO (PK) | Auto-increment |
| `company_data` | JSONB | NO | Invalid company data |
| `rejection_reason` | TEXT | NO | Why rejected |
| `quarantine_date` | TIMESTAMP | NO | When quarantined |
| `reviewed_by` | TEXT | YES | Reviewer |
| `resolution` | TEXT | YES | How resolved |

---

## Schema: `public` (System)

### shq_error_log

**Purpose**: System-wide error tracking.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `error_id` | TEXT | NO (PK) | Error ID |
| `error_code` | TEXT | NO | Error code |
| `error_message` | TEXT | NO | Error message |
| `severity` | TEXT | NO | info, warning, error, critical |
| `component` | TEXT | YES | Which component |
| `stack_trace` | TEXT | YES | Stack trace |
| `user_id` | TEXT | YES | User ID if applicable |
| `request_id` | TEXT | YES | Request ID for tracing |
| `resolution_status` | TEXT | YES | open, resolved, ignored |
| `created_at` | TIMESTAMP | NO | When logged |
| `updated_at` | TIMESTAMP | YES | Last update |

---

## Barton ID Format

| Entity | Schema Code | Format | Example |
|--------|-------------|--------|---------|
| Company | 01 | `04.04.01.XX.XXXXX.XXX` | 04.04.01.04.30001.001 |
| Person | 02 | `04.04.02.XX.XXXXX.XXX` | 04.04.02.04.20001.001 |
| Slot | 05 | `04.04.05.XX.XXXXX.XXX` | 04.04.05.04.10001.001 |

---

## Table Summary

| Schema | Table | Est. Rows | Hub Owner |
|--------|-------|-----------|-----------|
| marketing | company_master | 453 | Company Intelligence |
| marketing | company_slot | 1,359 | Company Intelligence |
| marketing | company_events | 0 | Company Intelligence |
| marketing | pipeline_events | 2,185 | Company Intelligence |
| people | people_master | 170 | People Intelligence |
| people | person_scores | 0 | People Intelligence |
| people | person_movement_history | 0 | People Intelligence |
| people | people_resolution_queue | 1,206 | People Intelligence |
| dol | form_5500 | 230,009 | DOL Filings |
| dol | form_5500_sf | 759,569 | DOL Filings |
| dol | schedule_a | 336,817 | DOL Filings |
| intake | quarantine | 114 | Intake |
| intake | company_raw_intake | 563 | Intake |
| intake | people_raw_intake | 0 | Intake |

**Total: ~1.3M rows in DOL data + operational tables**

---

*Generated: 2025-12-26 | Barton Outreach Core | Hub & Spoke Architecture v1.0*
