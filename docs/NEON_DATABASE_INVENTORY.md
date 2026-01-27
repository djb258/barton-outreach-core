# Neon PostgreSQL Database Inventory

**Generated:** January 23, 2026  
**Database:** Marketing DB  
**Host:** ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Total Schemas** | 18 |
| **Total Tables** | 221 |
| **Total Rows** | 3,720,303 |

### Schema Overview

| Schema | Tables | Rows | Purpose |
|--------|--------|------|---------|
| **dol** | 5 | 1,329,238 | Department of Labor filings & plan data |
| **cl** | 21 | 632,523 | Company Lifecycle pipeline data |
| **outreach** | 42 | 549,748 | Outreach spine & enrichment hub |
| **company** | 18 | 292,316 | Company master & slots |
| **people** | 24 | 260,824 | People master & resolution |
| **intake** | 7 | 257,409 | Data intake staging |
| **shq** | 6 | 146,352 | Signal HQ error tracking |
| **marketing** | 18 | 76,403 | Marketing data & contacts |
| **clay** | 3 | 74,641 | Clay enrichment results |
| **ref** | 2 | 49,863 | Reference data (counties, zips) |
| **archive** | 46 | 48,732 | Archived historical data |
| **catalog** | 7 | 2,218 | Domain catalog & URL tracking |
| **talent_flow** | 1 | 0 | Person movement tracking |
| **ple** | 5 | 0 | People Lifecycle Engine |
| **bit** | 5 | 0 | BIT signal processing |
| **outreach_ctx** | 3 | 3 | Outreach context tracking |
| **public** | 7 | 33 | Migration & garage runs |
| **neon_auth** | 1 | 0 | Neon authentication |

---

## Schema Details

### 1. `dol` Schema - DOL Filings (1,329,238 rows)

Primary source for Department of Labor 5500 filing data.

| Table | Rows | Description |
|-------|------|-------------|
| `dol_full` | 1,226,760 | Full DOL 5500 filings archive |
| `filings` | 51,245 | Active DOL filings linked to outreach |
| `plan_info` | 51,200 | Plan information details |
| `staging_dol_filings` | 0 | Staging for new filings |
| `v_company_latest_filing` | 33 | View: latest filing per company |

#### Key Columns & Coverage (dol.filings)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `filing_id` | uuid | 100% (51,245) | Primary Key |
| `outreach_id` | uuid | 100% (51,245) | FK → outreach.outreach |
| `ein` | text | 100% (51,245) | Employer ID Number |
| `plan_year_begin` | date | 100% (51,245) | |
| `plan_year_end` | date | 100% (51,245) | |
| `total_participants` | integer | 82.9% (42,485) | |
| `total_assets` | numeric | 74.5% (38,191) | |
| `sponsor_name` | text | 100% (51,245) | |
| `sponsor_state` | text | 97.9% (50,159) | |

#### Key Columns & Coverage (dol.dol_full)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `ack_id` | text | 100% | Primary Key |
| `ein` | text | 100% | Employer ID |
| `sponsor_dfe_name` | text | 100% | Sponsor name |
| `spons_dfe_mail_us_state` | text | 99.9% | State code |
| `tot_partcp_boy_cnt` | numeric | 99.2% | Participants count |
| `tot_assets_boy_amt` | numeric | 93.3% | Total assets |
| `plan_eff_date` | text | 100% | Plan effective date |

---

### 2. `cl` Schema - Company Lifecycle (632,523 rows)

Company lifecycle and state machine data.

| Table | Rows | Description |
|-------|------|-------------|
| `company_lifecycle` | 51,148 | Core lifecycle records |
| `sovereign_master` | 51,148 | Sovereign entity registry |
| `sovereign_intake_session` | 11 | Intake session tracking |
| `cl_target` | 51,148 | Enrichment target records |
| `cl_target_enrichment` | 51,149 | Enrichment results |
| `cl_target_progress` | 51,149 | Progress tracking |
| `company_contact` | 51,167 | Company contact info |
| `email_formats` | 63,568 | Email format patterns |
| `resolved_history` | 33,477 | Resolution history |
| `company_target_hub` | 51,212 | Company targeting hub |
| Views (11) | - | Various diagnostic views |

#### Key Columns & Coverage (cl.sovereign_master)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `sovereign_id` | uuid | 100% (51,148) | Primary Key |
| `domain` | varchar | 100% (51,148) | Company domain |
| `company_name` | text | 99.9% (51,071) | |
| `ein` | text | 27.3% (13,984) | From DOL match |
| `state_code` | text | 31.9% (16,333) | |
| `industry` | text | 0.4% (185) | Low coverage |

#### Key Columns & Coverage (cl.cl_target_enrichment)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `company_unique_id` | text | 100% (51,149) | FK |
| `email_method` | varchar | 92.0% (47,035) | Email pattern |
| `confidence` | numeric | 92.0% (47,035) | Confidence score |
| `is_catchall` | boolean | 79.6% (40,697) | |

---

### 3. `outreach` Schema - Outreach Spine (549,748 rows)

Central outreach coordination and enrichment hub.

| Table | Rows | Description |
|-------|------|-------------|
| `outreach` | 51,148 | Core outreach spine |
| `outreach_hub_status` | 51,148 | Hub completion status |
| `hub_progress` | 306,888 | Hub-by-hub progress |
| `context_signal` | 51,148 | Blog/context signals |
| `dol_enrichment` | 13,829 | DOL enrichment results |
| `people_hub` | 50,989 | People hub data |
| `people_master_mirror` | 0 | Mirror of people.people_master |
| `tier_override` | 0 | Manual tier overrides |
| Views (34) | - | Diagnostic and reporting views |

#### Key Columns & Coverage (outreach.outreach)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `outreach_id` | uuid | 100% (51,148) | Primary Key |
| `sovereign_id` | uuid | 100% (51,148) | FK → cl.sovereign_master |
| `domain` | varchar | 100% (51,148) | Company domain |
| `ct_status` | varchar | 100% (51,148) | Company target status |
| `created_at` | timestamp | 100% (51,148) | |

#### Key Columns & Coverage (outreach.hub_progress)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `progress_id` | uuid | 100% (306,888) | Primary Key |
| `outreach_id` | uuid | 100% (306,888) | FK |
| `hub_name` | varchar | 100% (306,888) | Hub identifier |
| `status` | varchar | 100% (306,888) | completed/pending/error |

#### Key Views

| View | Rows | Purpose |
|------|------|---------|
| `v_outreach_diagnostic` | 51,148 | Full diagnostic per outreach |
| `v_context_current` | 51,148 | Current enrichment state |
| `vw_marketing_eligibility` | 17,228 | Marketing tier calculation |
| `vw_sovereign_completion` | 17,228 | Hub completion summary |
| `v_blog_ready` | 51,148 | Blog signal readiness |

---

### 4. `company` Schema - Company Master (292,316 rows)

Company master data and slot assignments.

| Table | Rows | Description |
|-------|------|-------------|
| `company_master` | 51,212 | Master company records |
| `company_slots` | 153,444 | Role slots per company |
| `company_sidecar` | 17,264 | Extended company data |
| `email_patterns` | 51,212 | Email format patterns |
| `company_dol_link` | 13,944 | DOL filing links |
| `company_scores` | 0 | Scoring data |
| `enrichment_tasks` | 2,032 | Pending enrichments |
| Views (11) | - | Diagnostic views |

#### Key Columns & Coverage (company.company_master)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `company_unique_id` | text | 100% (51,212) | Primary Key |
| `outreach_id` | uuid | 100% (51,212) | FK → outreach.outreach |
| `company_name` | text | 100% (51,212) | |
| `domain` | text | 100% (51,212) | |
| `ein` | text | 27.3% (13,988) | From DOL |
| `state` | text | 33.9% (17,353) | |
| `employees_count` | integer | 0% (0) | Not populated |
| `industry` | text | 0% (0) | Not populated |

#### Key Columns & Coverage (company.company_slots)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `company_slot_unique_id` | text | 100% (153,444) | Primary Key |
| `company_unique_id` | text | 100% (153,444) | FK |
| `slot_type` | text | 100% (153,444) | HR_DIRECTOR, CFO, etc. |
| `person_unique_id` | text | 17.5% (26,884) | Filled slots |
| `is_filled` | boolean | 17.5% (26,884) | |

---

### 5. `people` Schema - People Master (260,824 rows)

People/contact master data and resolution.

| Table | Rows | Description |
|-------|------|-------------|
| `people_master` | 26,299 | Master contact records |
| `company_slot` | 153,444 | Slot assignments (legacy) |
| `company_slot_archive` | 69,075 | Archived slots |
| `people_master_archive` | 5,675 | Archived contacts |
| `people_resolution_queue` | 1,206 | Pending resolutions |
| `slot_assignment_history` | 1,370 | Assignment history |
| `people_errors` | 1,053 | Resolution errors |
| `people_invalid` | 21 | Invalid contacts |
| Views (8) | - | Monitoring views |

#### Key Columns & Coverage (people.people_master)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `unique_id` | text | 100% (26,299) | Primary Key |
| `company_unique_id` | text | 100% (26,299) | FK |
| `company_slot_unique_id` | text | 100% (26,299) | FK |
| `first_name` | text | 100% (26,299) | |
| `last_name` | text | 100% (26,299) | |
| `full_name` | text | 100% (26,299) | |
| `title` | text | 100% (26,299) | Job title |
| `email` | text | 95.9% (25,215) | Verified email |
| `linkedin_url` | text | 100% (26,299) | |
| `email_verified` | boolean | 100% (26,299) | |
| `email_verified_at` | timestamp | 94.4% (24,824) | |

---

### 6. `clay` Schema - Clay Enrichment (74,641 rows)

Clay.com enrichment results.

| Table | Rows | Description |
|-------|------|-------------|
| `clay_enrichment_results` | 74,536 | Raw Clay results |
| `clay_people_results` | 105 | People enrichment |
| `clay_run_log` | 0 | Run tracking |

#### Key Columns & Coverage (clay.clay_enrichment_results)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `result_id` | uuid | 100% (74,536) | Primary Key |
| `company_unique_id` | text | 100% (74,536) | FK |
| `enrichment_type` | varchar | 100% (74,536) | |
| `raw_response` | jsonb | 100% (74,536) | Full Clay response |
| `processed` | boolean | 100% (74,536) | |

---

### 7. `intake` Schema - Data Intake (257,409 rows)

Staging area for incoming data.

| Table | Rows | Description |
|-------|------|-------------|
| `intake_companies` | 57,233 | Company intake |
| `intake_companies_dedupe` | 51,247 | Deduped companies |
| `intake_clay_master` | 148,929 | Clay intake master |
| `staging_people_intake` | 0 | People staging |

#### Key Columns (intake.intake_companies_dedupe)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `company_unique_id` | text | 100% | Primary Key |
| `company_name` | text | 100% | |
| `domain` | text | 100% | |
| `source_system` | text | 100% | |

---

### 8. `marketing` Schema - Marketing Data (76,403 rows)

Marketing contacts and companies.

| Table | Rows | Description |
|-------|------|-------------|
| `contacts` | 4 | Marketing contacts |
| `companies` | 72,820 | Marketing companies |
| `company` | 1 | Legacy single record |
| `contact` | 0 | Legacy contacts |
| `email_verification_log` | 4 | Verification history |
| Various views | - | Marketing reporting |

---

### 9. `shq` Schema - Signal HQ (146,352 rows)

Error tracking and signal processing.

| Table | Rows | Description |
|-------|------|-------------|
| `error_master` | 95,125 | All system errors |
| `audit_log` | 5 | Audit events |
| Views (4) | - | Error analysis views |

#### Key Columns (shq.error_master)

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `error_id` | uuid | 100% | Primary Key |
| `process_id` | varchar | 100% | Process identifier |
| `agent_id` | varchar | 100% | Agent/hub identifier |
| `company_unique_id` | varchar | 18.4% (17,505) | Related company |
| `outreach_context_id` | varchar | 100% | Context ID |
| `created_at` | timestamp | 100% | |
| `resolved_at` | timestamp | 0% | Mostly unresolved |

---

### 10. `ref` Schema - Reference Data (49,863 rows)

Reference/lookup tables.

| Table | Rows | Description |
|-------|------|-------------|
| `county_fips` | 3,222 | US county FIPS codes |
| `zip_county_map` | 46,641 | ZIP to county mapping |

---

### 11. `catalog` Schema - Domain Catalog (2,218 rows)

Domain and URL cataloging.

| Table | Rows | Description |
|-------|------|-------------|
| `domain_catalog` | 2,184 | Domain registry |
| `blog_url_queue` | 0 | Blog URL queue |
| `url_check_queue` | 34 | URL validation queue |

---

## Key Relationships (Foreign Keys)

### Primary Entity Relationships

```
cl.sovereign_master (sovereign_id)
    ↓
outreach.outreach (outreach_id, sovereign_id)
    ↓
company.company_master (company_unique_id, outreach_id)
    ↓
company.company_slots (company_slot_unique_id, company_unique_id)
    ↓
people.people_master (unique_id, company_slot_unique_id)
```

### Hub Relationships

```
outreach.outreach
    ├── outreach.hub_progress (progress per hub)
    ├── outreach.outreach_hub_status (completion status)
    ├── outreach.dol_enrichment (DOL data)
    ├── outreach.people_hub (people data)
    ├── outreach.context_signal (blog signals)
    ├── dol.filings (DOL filings)
    └── company.company_master (company data)
```

### Cross-Schema References

| From | To | Relationship |
|------|-----|--------------|
| outreach.outreach | cl.sovereign_master | sovereign_id |
| company.company_master | outreach.outreach | outreach_id |
| company.company_slots | company.company_master | company_unique_id |
| people.people_master | company.company_slots | company_slot_unique_id |
| people.company_slot | outreach.outreach | outreach_id |
| dol.filings | outreach.outreach | outreach_id |
| clay.clay_enrichment_results | company.company_master | company_unique_id |
| people.people_resolution_queue | company.company_master | company_unique_id |
| people.people_resolution_queue | company.company_slots | company_slot_unique_id |

---

## Data Quality Summary

### High Coverage Fields (>90%)

| Schema.Table | Column | Coverage |
|--------------|--------|----------|
| people.people_master | email | 95.9% |
| people.people_master | email_verified_at | 94.4% |
| cl.cl_target_enrichment | email_method | 92.0% |
| outreach.v_context_current | ct_email_method | 91.4% |

### Low Coverage Fields (<30%)

| Schema.Table | Column | Coverage | Notes |
|--------------|--------|----------|-------|
| company.company_master | ein | 27.3% | Only DOL-matched |
| cl.sovereign_master | ein | 27.3% | Only DOL-matched |
| outreach.dol_enrichment | * | 27.0% | DOL match rate |
| company.company_master | employees_count | 0% | Not populated |
| company.company_master | industry | 0% | Not populated |
| people.people_master | twitter_url | 0% | Not populated |

### Slot Fill Rate

| Metric | Value |
|--------|-------|
| Total Slots | 153,444 |
| Filled Slots | 26,884 (17.5%) |
| Empty Slots | 126,560 (82.5%) |
| People with Email | 25,215 (95.9% of filled) |
| People with Verified Email | 24,824 (94.4% of filled) |

---

## Key Metrics

### Pipeline Health

| Metric | Count |
|--------|-------|
| Sovereign entities | 51,148 |
| Outreach records | 51,148 |
| Companies in master | 51,212 |
| Active company slots | 153,444 |
| People in master | 26,299 |
| DOL filings linked | 51,245 |
| DOL companies matched | 13,829 (27%) |
| Clay enrichments | 74,536 |
| Pending resolutions | 1,206 |
| System errors (unresolved) | ~95,000 |

### Tier Distribution (from vw_marketing_eligibility)

Marketing tier eligibility: **17,228 companies**

---

## Notes

1. **Empty Tables**: Several tables are empty (0 rows):
   - `bit.*` (signal processing not active)
   - `ple.*` (lifecycle engine not active)
   - `talent_flow.movement_history`
   - Various staging tables

2. **Archive Schema**: Contains 46 tables with ~49K rows of historical/archived data

3. **Views**: Many schemas contain views for reporting and diagnostics

4. **Data Flow**: Data flows from `intake` → `cl` → `outreach` → `company`/`people`

---

## JSON Inventory

Full inventory exported to: `neon_inventory.json` (33,699 lines)
