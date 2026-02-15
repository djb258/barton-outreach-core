# Database Query Results - Complete Schema Export

**Generated**: 2026-01-28T10:51:17
**Database**: Marketing DB (Neon PostgreSQL)
**Export Script**: `scripts/database_erd_export.py`
**Full JSON Export**: `docs/database_erd_export.json`

---

## Query 1: All Schemas

```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
ORDER BY schema_name;
```

**Results**: 50 schemas found

| Schema Name | Type | Notes |
|-------------|------|-------|
| archive | Operational | Archive tables from migrations |
| bit | Operational | Buyer Intent Tracking |
| blog | Operational | Content & Pressure Signals |
| catalog | Operational | Schema metadata catalog |
| cl | **Operational** | **Company Lifecycle Authority Registry** |
| client | Operational | Client hub (future) |
| company | Operational | Company Master & Events |
| company_target | Legacy | Migrated to outreach schema |
| dol | **Operational** | **DOL Filings & EIN Resolution** |
| intake | Operational | Data intake & validation |
| marketing | Legacy | Legacy marketing schema |
| outreach | **Operational** | **Marketing Outreach Operational Spine** |
| outreach_ctx | Operational | Outreach context tracking |
| people | **Operational** | **People Intelligence & Slot Management** |
| public | System | Default PostgreSQL schema |
| ref | Operational | Reference data |
| shq | Operational | Schema Headquarters (metadata) |
| talent_flow | Operational | Talent flow tracking |
| pg_temp_* | System | 24 temporary schemas |
| pg_toast_temp_* | System | 10 TOAST temporary schemas |

---

## Query 2: All Tables with Schemas

```sql
SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
AND table_type = 'BASE TABLE'
ORDER BY table_schema, table_name;
```

**Results**: 172 tables found

### CL Schema Tables (13 tables)

| Table Name | Purpose |
|------------|---------|
| cl_err_existence | Existence verification errors |
| cl_errors_archive | Archived errors |
| company_candidate | Company candidates for identity resolution |
| company_domains | Company domains (multi-domain support) |
| company_domains_archive | Archived domains |
| **company_identity** | **Authority registry (PRIMARY)** |
| company_identity_archive | Archived identities |
| company_identity_bridge | Bridge table for merges |
| company_names | Company name variants |
| company_names_archive | Archived names |
| domain_hierarchy | Domain parent-child relationships |
| domain_hierarchy_archive | Archived hierarchies |
| identity_confidence | Identity confidence scores |
| identity_confidence_archive | Archived confidence scores |

### Outreach Schema Tables (45+ tables)

| Table Name | Purpose | Sub-Hub |
|------------|---------|---------|
| **outreach** | **Operational spine (PRIMARY)** | Spine |
| outreach_archive | Archived outreach records | Archive |
| outreach_excluded | Excluded from outreach | Control |
| outreach_legacy_quarantine | Legacy quarantine | Archive |
| **company_target** | **Company targeting data** | 04.04.01 |
| company_target_archive | Archived targets | Archive |
| company_target_errors | Target errors | Errors |
| **dol** | **DOL filings data** | 04.04.03 |
| dol_audit_log | DOL audit trail | Audit |
| dol_errors | DOL errors | Errors |
| dol_url_enrichment | DOL URL enrichment | Enrichment |
| **people** | **People in outreach** | 04.04.02 |
| people_archive | Archived people | Archive |
| people_errors | People errors | Errors |
| **blog** | **Blog monitoring** | 04.04.05 |
| blog_errors | Blog errors | Errors |
| blog_ingress_control | Blog ingress control | Control |
| blog_source_history | Blog source history | History |
| **bit_scores** | **BIT scoring results** | BIT Engine |
| bit_signals | BIT signals log | BIT Engine |
| bit_errors | BIT errors | Errors |
| bit_input_history | BIT input history | History |
| **manual_overrides** | **Kill switches** | Control |
| **override_audit_log** | **Override audit trail** | Audit |
| campaigns | Campaign management | Execution |
| sequences | Sequence management | Execution |
| send_log | Send log | Execution |
| engagement_events | Engagement tracking | Execution |
| company_hub_status | Hub status tracking | System |
| hub_registry | Hub registry | System |
| pipeline_audit_log | Pipeline audit log | Audit |
| entity_resolution_queue | Entity resolution queue | Queue |
| mv_credit_usage | Credit usage tracking | Metrics |
| column_registry | Column metadata | System |

### People Schema Tables (20+ tables)

| Table Name | Purpose |
|------------|---------|
| **people_master** | **Primary people records** |
| people_sidecar | Additional people metadata |
| **company_slot** | **Slot assignments (CEO/CFO/HR)** |
| company_slot_archive | Archived slots |
| slot_assignment_history | Slot assignment history |
| slot_ingress_control | Slot ingress control |
| slot_orphan_snapshot_r0_002 | Orphan slot snapshot |
| slot_quarantine_r0_002 | Quarantined slots |
| people_candidate | People candidates |
| people_errors | People errors |
| people_invalid | Invalid people records |
| people_staging | Staging table for imports |
| people_promotion_audit | Promotion audit trail |
| people_resolution_history | Resolution history |
| people_resolution_queue | Resolution queue |
| person_movement_history | Job movement history |
| person_scores | Person quality scores |
| pressure_signals | Pressure signals (blog/news) |
| company_resolution_log | Company resolution log |
| paid_enrichment_queue | Paid enrichment queue |
| title_slot_mapping | Title to slot mapping |

### DOL Schema Tables (8 tables)

| Table Name | Purpose |
|------------|---------|
| **form_5500** | **Form 5500 filings (PRIMARY)** |
| form_5500_sf | Form 5500 SF format |
| form_5500_icp_filtered | ICP-filtered filings |
| **schedule_a** | **Schedule A insurance data** |
| **ein_urls** | **EIN to URL mappings** |
| **renewal_calendar** | **Plan renewal calendar** |
| column_metadata | Column metadata |
| pressure_signals | DOL pressure signals |

### Company Schema Tables (12 tables)

| Table Name | Purpose |
|------------|---------|
| **company_master** | **Company master records** |
| company_sidecar | Additional company metadata |
| company_events | Company events log |
| **company_slots** | **Company slot definitions** |
| company_source_urls | Source URLs for companies |
| contact_enrichment | Contact enrichment queue |
| email_verification | Email verification results |
| message_key_reference | Message key reference |
| pipeline_errors | Pipeline errors |
| pipeline_events | Pipeline events |
| url_discovery_failures | URL discovery failures |
| validation_failures_log | Validation failures log |

### BIT Schema Tables (4 tables)

| Table Name | Purpose |
|------------|---------|
| movement_events | People movement events |
| proof_lines | BIT proof lines |
| authorization_log | BIT authorization log |
| phase_state | Phase state tracking |

### Archive Schema Tables (46 tables)

All tables in this schema are archived versions of production tables with timestamp suffixes.

---

## Query 3: Foreign Key Relationships

```sql
SELECT
    tc.table_schema AS source_schema,
    tc.table_name AS source_table,
    kcu.column_name AS source_column,
    ccu.table_schema AS target_schema,
    ccu.table_name AS target_table,
    ccu.column_name AS target_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_schema, tc.table_name;
```

**Results**: 62 foreign key relationships found

### CL Schema Foreign Keys

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| cl.company_domains | company_unique_id | cl.company_identity | company_unique_id |
| cl.company_names | company_unique_id | cl.company_identity | company_unique_id |
| cl.identity_confidence | company_unique_id | cl.company_identity | company_unique_id |

### Outreach Schema Foreign Keys

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| outreach.bit_scores | outreach_id | outreach.outreach | outreach_id |
| outreach.bit_signals | outreach_id | outreach.outreach | outreach_id |
| outreach.bit_errors | outreach_id | outreach.outreach | outreach_id |
| outreach.bit_input_history | outreach_id | outreach.outreach | outreach_id |
| outreach.company_target | outreach_id | outreach.outreach | outreach_id |
| outreach.company_target_errors | outreach_id | outreach.outreach | outreach_id |
| outreach.dol | outreach_id | outreach.outreach | outreach_id |
| outreach.dol_errors | outreach_id | outreach.outreach | outreach_id |
| outreach.people | outreach_id | outreach.outreach | outreach_id |
| outreach.people_errors | outreach_id | outreach.outreach | outreach_id |
| outreach.blog | outreach_id | outreach.outreach | outreach_id |
| outreach.blog_errors | outreach_id | outreach.outreach | outreach_id |
| outreach.outreach_errors | outreach_id | outreach.outreach | outreach_id |
| outreach.campaigns | outreach_id | outreach.outreach | outreach_id |
| outreach.sequences | outreach_id | outreach.outreach | outreach_id |
| outreach.send_log | outreach_id | outreach.outreach | outreach_id |
| outreach.engagement_events | outreach_id | outreach.outreach | outreach_id |
| outreach.manual_overrides | outreach_id | outreach.outreach | outreach_id |

### People Schema Foreign Keys

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| people.people_master | company_unique_id | marketing.company_master | company_unique_id |

### DOL Schema Foreign Keys

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| dol.renewal_calendar | filing_id | dol.form_5500 | filing_id |

### Company Schema Foreign Keys

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| company.company_events | company_unique_id | company.company_master | company_unique_id |
| company.company_sidecar | company_unique_id | company.company_master | company_unique_id |
| company.company_slots | company_unique_id | company.company_master | company_unique_id |
| company.contact_enrichment | company_slot_unique_id | company.company_slots | company_slot_unique_id |
| company.email_verification | enrichment_id | company.contact_enrichment | id |

### Catalog Schema Foreign Keys

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| catalog.columns | table_id | catalog.tables | table_id |
| catalog.tables | schema_id | catalog.schemas | schema_id |

---

## Query 4: Primary Keys

```sql
SELECT
    tc.table_schema,
    tc.table_name,
    kcu.column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
ORDER BY tc.table_schema, tc.table_name;
```

**Results**: 159 primary keys found

### CL Schema Primary Keys

| Table | Primary Key Column | Type |
|-------|-------------------|------|
| company_identity | company_unique_id | UUID |
| company_domains | domain_id | UUID |
| company_names | name_id | UUID |
| identity_confidence | company_unique_id | UUID |
| cl_err_existence | error_id | UUID |
| company_candidate | candidate_id | UUID |
| company_identity_bridge | bridge_id | UUID |
| domain_hierarchy | hierarchy_id | UUID |

### Outreach Schema Primary Keys

| Table | Primary Key Column | Type |
|-------|-------------------|------|
| **outreach** | **outreach_id** | **UUID** |
| company_target | target_id | UUID |
| dol | dol_id | UUID |
| people | person_id | UUID |
| blog | blog_id | UUID |
| bit_scores | outreach_id | UUID (also FK) |
| bit_signals | signal_id | UUID |
| bit_errors | error_id | UUID |
| bit_input_history | history_id | UUID |
| company_target_errors | error_id | UUID |
| dol_errors | error_id | UUID |
| people_errors | error_id | UUID |
| blog_errors | error_id | UUID |
| outreach_errors | error_id | UUID |
| manual_overrides | override_id | UUID |
| override_audit_log | audit_id | UUID |
| campaigns | campaign_id | UUID |
| sequences | sequence_id | UUID |
| send_log | send_id | UUID |
| engagement_events | event_id | UUID |
| company_hub_status | hub_id, company_unique_id | COMPOSITE |
| hub_registry | hub_id | UUID |
| pipeline_audit_log | log_id | UUID |
| entity_resolution_queue | id | UUID |

### People Schema Primary Keys

| Table | Primary Key Column | Type |
|-------|-------------------|------|
| **people_master** | **unique_id** | **UUID** |
| **company_slot** | **slot_id** | **UUID** |
| people_candidate | candidate_id | UUID |
| people_errors | error_id | UUID |
| people_invalid | id | UUID |
| people_promotion_audit | audit_id | UUID |
| people_resolution_history | history_id | UUID |
| people_resolution_queue | queue_id | UUID |
| people_sidecar | person_unique_id | UUID |
| people_staging | id | UUID |
| person_movement_history | id | UUID |
| person_scores | id | UUID |
| pressure_signals | signal_id | UUID |
| slot_assignment_history | history_id | UUID |
| slot_ingress_control | switch_id | UUID |
| slot_orphan_snapshot_r0_002 | snapshot_id | UUID |
| slot_quarantine_r0_002 | quarantine_id | UUID |
| company_resolution_log | log_id | UUID |
| paid_enrichment_queue | id | UUID |
| title_slot_mapping | id | UUID |

### DOL Schema Primary Keys

| Table | Primary Key Column | Type |
|-------|-------------------|------|
| **form_5500** | **filing_id** | **TEXT** |
| schedule_a | schedule_id | UUID |
| ein_urls | ein | TEXT |
| renewal_calendar | renewal_id | UUID |
| form_5500_sf | filing_id | TEXT |
| pressure_signals | signal_id | UUID |
| column_metadata | id | UUID |

### Company Schema Primary Keys

| Table | Primary Key Column | Type |
|-------|-------------------|------|
| **company_master** | **company_unique_id** | **UUID** |
| company_sidecar | company_unique_id | UUID |
| company_events | event_id | UUID |
| company_slots | company_slot_unique_id | UUID |
| company_source_urls | id | UUID |
| contact_enrichment | id | UUID |
| email_verification | id | UUID |
| message_key_reference | id | UUID |
| pipeline_errors | error_id | UUID |
| pipeline_events | event_id | UUID |
| url_discovery_failures | id | UUID |
| validation_failures_log | id | UUID |

---

## Query 5: Key Table Columns

```sql
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default,
    character_maximum_length,
    numeric_precision,
    ordinal_position
FROM information_schema.columns
WHERE (table_schema = 'cl' AND table_name = 'company_identity')
   OR (table_schema = 'outreach' AND table_name IN ('outreach', 'company_target', 'dol', 'people', 'blog', 'bit_scores', 'bit_signals', 'manual_overrides'))
   OR (table_schema = 'people' AND table_name IN ('company_slot', 'people_master'))
   OR (table_schema = 'dol' AND table_name IN ('form_5500', 'schedule_a', 'ein_urls'))
ORDER BY table_schema, table_name, ordinal_position;
```

**Results**: 427 columns across 15 key tables

### cl.company_identity (33 columns)

| # | Column Name | Type | Nullable | Default | Notes |
|---|-------------|------|----------|---------|-------|
| 1 | company_unique_id | UUID | NO | gen_random_uuid() | **PK** |
| 2 | company_name | TEXT | NO | - | |
| 3 | company_domain | TEXT | YES | - | |
| 4 | linkedin_company_url | TEXT | YES | - | |
| 5 | source_system | TEXT | NO | - | |
| 6 | created_at | TIMESTAMPTZ | NO | now() | |
| 7 | company_fingerprint | TEXT | YES | - | |
| 8 | lifecycle_run_id | TEXT | YES | - | |
| 9 | existence_verified | BOOLEAN | YES | false | |
| 10 | verification_run_id | TEXT | YES | - | |
| 11 | verified_at | TIMESTAMPTZ | YES | - | |
| 12 | domain_status_code | INTEGER | YES | - | |
| 13 | name_match_score | INTEGER | YES | - | |
| 14 | state_match_result | TEXT | YES | - | |
| 15 | canonical_name | TEXT | YES | - | |
| 16 | state_verified | TEXT | YES | - | |
| 17 | employee_count_band | TEXT | YES | - | |
| 18 | identity_pass | INTEGER | YES | 0 | |
| 19 | identity_status | TEXT | YES | 'PENDING' | |
| 20 | last_pass_at | TIMESTAMPTZ | YES | - | |
| 21 | eligibility_status | TEXT | YES | - | |
| 22 | exclusion_reason | TEXT | YES | - | |
| 23 | entity_role | TEXT | YES | - | |
| 24 | sovereign_company_id | UUID | YES | - | Sovereign ID |
| 25 | final_outcome | TEXT | YES | - | |
| 26 | final_reason | TEXT | YES | - | |
| 27 | **outreach_id** | **UUID** | **YES** | **-** | **WRITE-ONCE pointer** |
| 28 | sales_process_id | UUID | YES | - | WRITE-ONCE pointer |
| 29 | client_id | UUID | YES | - | WRITE-ONCE pointer |
| 30 | outreach_attached_at | TIMESTAMPTZ | YES | - | |
| 31 | sales_opened_at | TIMESTAMPTZ | YES | - | |
| 32 | client_promoted_at | TIMESTAMPTZ | YES | - | |
| 33 | normalized_domain | TEXT | YES | - | |

### outreach.outreach (5 columns)

| # | Column Name | Type | Nullable | Default | Notes |
|---|-------------|------|----------|---------|-------|
| 1 | **outreach_id** | **UUID** | **NO** | **gen_random_uuid()** | **PK** |
| 2 | sovereign_id | UUID | NO | - | FK to CL |
| 3 | created_at | TIMESTAMPTZ | NO | now() | |
| 4 | updated_at | TIMESTAMPTZ | NO | now() | |
| 5 | domain | VARCHAR(255) | YES | - | |

### outreach.company_target (18 columns)

| # | Column Name | Type | Nullable | Default | Notes |
|---|-------------|------|----------|---------|-------|
| 1 | target_id | UUID | NO | gen_random_uuid() | **PK** |
| 2 | company_unique_id | TEXT | YES | - | Legacy |
| 3 | outreach_status | TEXT | NO | 'queued' | |
| 4 | bit_score_snapshot | INTEGER | YES | - | |
| 5 | first_targeted_at | TIMESTAMPTZ | YES | - | |
| 6 | last_targeted_at | TIMESTAMPTZ | YES | - | |
| 7 | sequence_count | INTEGER | NO | 0 | |
| 8 | active_sequence_id | TEXT | YES | - | |
| 9 | source | TEXT | YES | - | |
| 10 | created_at | TIMESTAMPTZ | NO | now() | |
| 11 | updated_at | TIMESTAMPTZ | NO | now() | |
| 12 | **outreach_id** | **UUID** | **YES** | **-** | **FK** |
| 13 | **email_method** | **VARCHAR(100)** | **YES** | **-** | **Email pattern** |
| 14 | method_type | VARCHAR(50) | YES | - | Pattern type |
| 15 | confidence_score | NUMERIC(5,2) | YES | - | 0.00-1.00 |
| 16 | execution_status | VARCHAR(50) | YES | 'pending' | |
| 17 | imo_completed_at | TIMESTAMPTZ | YES | - | |
| 18 | is_catchall | BOOLEAN | YES | false | |

### outreach.dol (Full column list in JSON export)

Key columns: dol_id, outreach_id, ein, filing_id, form_5500_matched, schedule_a_matched

### outreach.people (Full column list in JSON export)

Key columns: person_id, outreach_id, person_unique_id, slot_type, email, email_verified

### outreach.blog (Full column list in JSON export)

Key columns: blog_id, outreach_id, blog_url, rss_feed_url, signal_count

### outreach.bit_scores (Full column list in JSON export)

Key columns: outreach_id (PK/FK), bit_score, bit_tier, signal_count

### outreach.bit_signals (Full column list in JSON export)

Key columns: signal_id, outreach_id, signal_type, signal_impact, signal_hash

### outreach.manual_overrides (Full column list in JSON export)

Key columns: override_id, outreach_id, override_type, reason, is_active

### people.company_slot (Full column list in JSON export)

Key columns: slot_id, company_unique_id, slot_type, person_unique_id, is_filled

### people.people_master (Full column list in JSON export)

Key columns: unique_id, company_unique_id, full_name, email, title, slot_type

### dol.form_5500 (Full column list in JSON export)

Key columns: filing_id, ein, plan_name, sponsor_name, plan_year

### dol.schedule_a (Full column list in JSON export)

Key columns: schedule_id, filing_id, ein, insurance_carrier_name

### dol.ein_urls (Full column list in JSON export)

Key columns: ein (PK), company_name, url, source

---

## Row Counts (Key Tables)

```sql
-- Executed for each key table:
SELECT COUNT(*) FROM "schema"."table";
```

| Schema.Table | Rows | Coverage Notes |
|--------------|------|----------------|
| cl.company_identity | 52,675 | Authority registry |
| outreach.outreach | 49,737 | Operational spine |
| outreach.company_target | 45,816 | 91.4% have email_method |
| outreach.dol | 18,575 | 27% DOL coverage |
| outreach.people | 379 | People in pipeline |
| outreach.blog | 46,468 | 100% coverage |
| outreach.bit_scores | 15,032 | BIT scores assigned |
| outreach.bit_signals | 0 | Empty |
| outreach.manual_overrides | 0 | Empty |
| outreach.override_audit_log | 0 | Empty |
| people.company_slot | 149,172 | Slot assignments |
| people.people_master | 71,237 | People records |
| dol.form_5500 | 230,482 | Form 5500 filings |
| dol.schedule_a | 337,476 | Schedule A records |
| dol.ein_urls | - | Not queried (error) |

**Note**: dol.ein_registry does not exist (table was not created or was dropped)

---

## Views

**Total Views**: 56 across all schemas

### Outreach Schema Views (23 views)

| View Name | Purpose |
|-----------|---------|
| **vw_marketing_eligibility_with_overrides** | **AUTHORITATIVE - Marketing eligibility** |
| **vw_sovereign_completion** | **Sovereign entity completion** |
| vw_bit_tier_distribution | BIT tier distribution |
| vw_company_target_status | Company target status |
| vw_dol_coverage | DOL coverage summary |
| vw_people_slot_coverage | People slot coverage |
| vw_outreach_pipeline | Outreach pipeline status |
| vw_email_pattern_coverage | Email pattern coverage |
| vw_blog_signal_summary | Blog signal summary |
| vw_campaign_performance | Campaign performance |
| vw_sequence_metrics | Sequence metrics |
| vw_engagement_funnel | Engagement funnel |
| (and 11 more) | - |

### CL Schema Views (8 views)

| View Name | Purpose |
|-----------|---------|
| **v_company_lifecycle_status** | **READ-ONLY - Hub claim status** |
| v_company_domains | Company domains |
| v_company_names | Company names |
| v_identity_resolution_status | Identity resolution status |
| v_existence_verification_status | Existence verification status |
| (and 3 more) | - |

### People Schema Views (12 views)

| View Name | Purpose |
|-----------|---------|
| v_slot_fill_rates | Slot fill rates by type |
| v_people_quality_scores | People quality scores |
| v_title_distribution | Title distribution |
| v_seniority_distribution | Seniority distribution |
| (and 8 more) | - |

### DOL Schema Views (6 views)

| View Name | Purpose |
|-----------|---------|
| v_form_5500_summary | Form 5500 summary |
| v_schedule_a_summary | Schedule A summary |
| v_renewal_calendar_upcoming | Upcoming renewals |
| (and 3 more) | - |

---

## Indexes

**Total Indexes**: 677 across all schemas

### Critical Performance Indexes

#### CL Schema

- `company_identity_pkey` (company_unique_id)
- `idx_company_identity_outreach_id` (outreach_id)
- `idx_company_identity_sovereign_id` (sovereign_company_id)
- `idx_company_identity_domain` (normalized_domain)
- `idx_company_identity_eligibility` (eligibility_status)

#### Outreach Schema

- `outreach_pkey` (outreach_id)
- `idx_outreach_sovereign_id` (sovereign_id)
- `company_target_pkey` (target_id)
- `idx_company_target_outreach_id` (outreach_id)
- `idx_company_target_email_method` (email_method)
- `dol_pkey` (dol_id)
- `idx_dol_outreach_id` (outreach_id)
- `idx_dol_ein` (ein)
- `people_pkey` (person_id)
- `idx_people_outreach_id` (outreach_id)
- `blog_pkey` (blog_id)
- `idx_blog_outreach_id` (outreach_id)
- `bit_scores_pkey` (outreach_id)
- `idx_bit_scores_tier` (bit_tier)

#### People Schema

- `people_master_pkey` (unique_id)
- `idx_people_master_company_id` (company_unique_id)
- `idx_people_master_email` (email)
- `company_slot_pkey` (slot_id)
- `idx_company_slot_company_id` (company_unique_id)
- `idx_company_slot_type` (slot_type)
- `idx_company_slot_person_id` (person_unique_id)

#### DOL Schema

- `form_5500_pkey` (filing_id)
- `idx_form_5500_ein` (ein)
- `idx_form_5500_plan_year` (plan_year)
- `schedule_a_pkey` (schedule_id)
- `idx_schedule_a_filing_id` (filing_id)
- `ein_urls_pkey` (ein)

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Schemas** | 50 |
| **Tables** | 172 |
| **Views** | 56 |
| **Foreign Keys** | 62 |
| **Primary Keys** | 159 |
| **Indexes** | 677 |
| **Total Rows (Key Tables)** | 1,180,147 |

### Row Distribution

| Schema | Tables | Rows | % of Total |
|--------|--------|------|------------|
| dol | 3 | 568,337 | 48.2% |
| people | 2 | 220,409 | 18.7% |
| cl | 1 | 52,675 | 4.5% |
| outreach | 9 | 176,007 | 14.9% |
| **TOTAL** | **15** | **1,017,428** | **86.3%** |

---

## Export Files

1. **Full JSON Export**: `docs/database_erd_export.json`
   - Contains complete schema information
   - All 427 columns with full metadata
   - All foreign keys and constraints
   - All indexes and views

2. **ERD Summary**: `docs/ERD_SUMMARY.md`
   - Human-readable summary
   - Table descriptions and relationships
   - Row counts and coverage statistics

3. **ERD Diagrams**: `docs/ERD_DIAGRAM.md`
   - Mermaid format diagrams
   - Visual representations of relationships
   - Waterfall architecture diagram

4. **Query Results**: `docs/DATABASE_QUERY_RESULTS.md` (this file)
   - All query results in tabular format
   - Complete schema documentation

---

**Document Generated**: 2026-01-28
**Script**: `scripts/database_erd_export.py`
**Status**: v1.0 OPERATIONAL BASELINE (CERTIFIED + FROZEN)
