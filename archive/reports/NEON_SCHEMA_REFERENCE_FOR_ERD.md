# Neon Schema Reference for ERD Documentation

**Generated**: 2026-02-02
**Purpose**: Exact column definitions from Neon PostgreSQL for ERD updates
**Source**: Live introspection via `information_schema.columns`

---

## 1. CL AUTHORITY REGISTRY (HIGHEST PRIORITY)

### cl.company_identity (33 columns)

**Purpose**: CL Authority Registry - Identity pointers only (WRITE-ONCE)

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| company_unique_id | uuid | NO | gen_random_uuid() | Legacy PK (pre-sovereign) |
| company_name | text | NO | | |
| company_domain | text | YES | | |
| linkedin_company_url | text | YES | | |
| source_system | text | NO | | |
| created_at | timestamp with time zone | NO | now() | |
| company_fingerprint | text | YES | | |
| lifecycle_run_id | text | YES | | |
| existence_verified | boolean | YES | false | |
| verification_run_id | text | YES | | |
| verified_at | timestamp with time zone | YES | | |
| domain_status_code | integer(32) | YES | | |
| name_match_score | integer(32) | YES | | |
| state_match_result | text | YES | | |
| canonical_name | text | YES | | |
| state_verified | text | YES | | |
| employee_count_band | text | YES | | |
| identity_pass | integer(32) | YES | 0 | |
| identity_status | text | YES | 'PENDING'::text | |
| last_pass_at | timestamp with time zone | YES | | |
| eligibility_status | text | YES | | |
| exclusion_reason | text | YES | | |
| entity_role | text | YES | | |
| **sovereign_company_id** | **uuid** | **YES** | | **ACTUAL PK (minted by CL)** |
| final_outcome | text | YES | | |
| final_reason | text | YES | | |
| **outreach_id** | **uuid** | **YES** | | **WRITE-ONCE (minted by Outreach)** |
| **sales_process_id** | **uuid** | **YES** | | **WRITE-ONCE (minted by Sales)** |
| **client_id** | **uuid** | **YES** | | **WRITE-ONCE (minted by Client)** |
| outreach_attached_at | timestamp with time zone | YES | | |
| sales_opened_at | timestamp with time zone | YES | | |
| client_promoted_at | timestamp with time zone | YES | | |
| normalized_domain | text | YES | | |

**Key Doctrine Rules**:
- CL mints `sovereign_company_id` (IMMUTABLE)
- Each hub mints its own ID and writes ONCE to CL
- CL stores identity pointers ONLY - never workflow state

---

### cl.company_domains (7 columns)

**Purpose**: Multi-domain tracking per company

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| domain_id | uuid | NO | gen_random_uuid() | PK |
| company_unique_id | uuid | NO | | FK to cl.company_identity |
| domain | text | NO | | Domain string |
| domain_health | text | YES | | Health status |
| mx_present | boolean | YES | | MX record check |
| domain_name_confidence | integer(32) | YES | | Confidence score |
| checked_at | timestamp with time zone | YES | now() | Last health check |

---

## 2. KILL SWITCH SYSTEM (v1.0 FROZEN)

### outreach.manual_overrides (12 columns)

**Purpose**: Manual override controls for marketing eligibility

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| override_id | uuid | NO | gen_random_uuid() | PK |
| company_unique_id | text | NO | | Company identifier |
| override_type | USER-DEFINED | NO | | Enum: HARD_FAIL, SKIP, etc. |
| reason | text | NO | | Human-readable reason |
| metadata | jsonb | YES | '{}'::jsonb | Additional context |
| created_at | timestamp with time zone | NO | now() | |
| created_by | text | NO | CURRENT_USER | Who created |
| expires_at | timestamp with time zone | YES | | Optional expiration |
| is_active | boolean | NO | true | Active flag |
| deactivated_at | timestamp with time zone | YES | | Deactivation time |
| deactivated_by | text | YES | | Who deactivated |
| deactivation_reason | text | YES | | Why deactivated |

**Key Features**:
- Supports temporary overrides (expires_at)
- Audit trail (created_by, deactivated_by)
- Soft delete (is_active flag)

---

### outreach.override_audit_log (9 columns)

**Purpose**: Immutable audit trail for all override actions

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| audit_id | uuid | NO | gen_random_uuid() | PK |
| company_unique_id | text | NO | | Company identifier |
| override_id | uuid | YES | | FK to manual_overrides |
| action | text | NO | | Action taken |
| override_type | USER-DEFINED | YES | | Override type |
| old_value | jsonb | YES | | Previous state |
| new_value | jsonb | YES | | New state |
| performed_by | text | NO | CURRENT_USER | Actor |
| performed_at | timestamp with time zone | NO | now() | Timestamp |

**Key Features**:
- Immutable (no updates/deletes)
- Captures old/new state diffs
- Links to override record

---

## 3. HUB REGISTRY

### outreach.hub_registry (12 columns)

**Purpose**: Waterfall order and health metrics for all hubs

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| hub_id | character varying(50) | NO | | PK |
| hub_name | character varying(100) | NO | | Display name |
| doctrine_id | character varying(20) | NO | | Doctrine reference |
| classification | character varying(20) | NO | | Type: ANCHOR, SUB-HUB |
| gates_completion | boolean | NO | false | Blocks downstream? |
| waterfall_order | integer(32) | NO | | Execution order |
| core_metric | character varying(50) | NO | | Key metric name |
| metric_healthy_threshold | numeric(5) | YES | | Green threshold |
| metric_critical_threshold | numeric(5) | YES | | Red threshold |
| description | text | YES | | Purpose |
| created_at | timestamp with time zone | NO | now() | |
| updated_at | timestamp with time zone | NO | now() | |

**Waterfall Order** (as of v1.0):
1. Company Lifecycle (CL) - PARENT
2. Company Target (04.04.01) - ANCHOR
3. DOL Filings (04.04.03) - SUB-HUB
4. People Intelligence (04.04.02) - SUB-HUB
5. Blog Content (04.04.05) - SUB-HUB

---

## 4. OUTREACH SPINE

### outreach.outreach (5 columns)

**Purpose**: Operational spine - workflow state lives here

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| **outreach_id** | **uuid** | **NO** | **gen_random_uuid()** | **PK (minted here)** |
| **sovereign_id** | **uuid** | **NO** | | **FK to cl.company_identity** |
| created_at | timestamp with time zone | NO | now() | |
| updated_at | timestamp with time zone | NO | now() | |
| domain | character varying(255) | YES | | Primary domain |

**Key Doctrine Rules**:
- Outreach mints `outreach_id` (PK)
- Registers `outreach_id` in CL (WRITE-ONCE)
- All sub-hubs FK to `outreach_id`
- Workflow state stays in Outreach, not CL

**Alignment Rule** (v1.0 FROZEN):
```sql
SELECT COUNT(*) FROM outreach.outreach = 51,148
SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL = 51,148
-- MUST ALWAYS BE EQUAL
```

---

### outreach.outreach_excluded (10 columns)

**Purpose**: Exclusion tracking for non-eligible companies

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| outreach_id | uuid | NO | | PK/FK |
| company_name | text | YES | | |
| domain | text | YES | | |
| exclusion_reason | text | YES | | Why excluded |
| excluded_at | timestamp with time zone | YES | now() | |
| created_at | timestamp with time zone | YES | | |
| updated_at | timestamp with time zone | YES | | |
| sovereign_id | uuid | YES | | FK to CL |
| cl_status | text | YES | | CL lifecycle status |
| excluded_by | text | YES | 'consolidation_migration'::text | Who/what excluded |

---

## 5. OUTREACH BLOG

### outreach.blog (8 columns)

**Purpose**: Content signals for outreach intelligence

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| blog_id | uuid | NO | gen_random_uuid() | PK |
| outreach_id | uuid | NO | | FK to outreach.outreach |
| context_summary | text | YES | | AI-generated summary |
| source_type | text | YES | | Signal type |
| source_url | text | YES | | Source link |
| context_timestamp | timestamp with time zone | YES | | Signal timestamp |
| created_at | timestamp with time zone | YES | now() | |
| source_type_enum | USER-DEFINED | YES | | Enum version |

**Coverage** (as of v1.0):
- 51,148 records (100% of outreach spine)

---

## 6. BIT TABLES

### bit.authorization_log (12 columns)

**Purpose**: Authorization requests for BIT band changes

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| log_id | uuid | NO | gen_random_uuid() | PK |
| company_unique_id | text | NO | | Company identifier |
| requested_action | text | NO | | Action type |
| requested_band | integer(32) | NO | | Requested tier |
| authorized | boolean | NO | | Approved? |
| actual_band | integer(32) | NO | | Granted tier |
| denial_reason | text | YES | | Why denied |
| proof_id | text | YES | | FK to proof_lines |
| proof_valid | boolean | YES | | Proof validation |
| requested_at | timestamp with time zone | NO | now() | |
| requested_by | text | NO | | Requester |
| correlation_id | text | YES | | Request trace |

---

### bit.movement_events (17 columns)

**Purpose**: Buyer intent movement detection

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| movement_id | uuid | NO | gen_random_uuid() | PK |
| company_unique_id | text | NO | | Company identifier |
| source_hub | text | NO | | Hub that detected |
| source_table | text | NO | | Table source |
| source_fields | ARRAY | NO | | Fields monitored |
| movement_class | text | NO | | Movement type |
| pressure_class | text | NO | | Pressure category |
| domain | text | NO | | Signal domain |
| direction | text | NO | | UP/DOWN/STABLE |
| magnitude | numeric(5) | NO | | Signal strength |
| detected_at | timestamp with time zone | NO | now() | |
| valid_from | timestamp with time zone | NO | | Validity start |
| valid_until | timestamp with time zone | NO | | Validity end |
| comparison_period | text | YES | | Time window |
| evidence | jsonb | NO | | Supporting data |
| source_record_ids | jsonb | NO | | Source records |
| created_at | timestamp with time zone | NO | now() | |

---

### bit.phase_state (14 columns)

**Purpose**: Current BIT phase state per company

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| company_unique_id | text | NO | | PK |
| current_band | integer(32) | NO | 0 | Current tier |
| phase_status | text | NO | 'SILENT'::text | Phase status |
| dol_active | boolean | NO | false | DOL signals? |
| people_active | boolean | NO | false | People signals? |
| blog_active | boolean | NO | false | Blog signals? |
| primary_pressure | text | YES | | Dominant pressure |
| aligned_domains | integer(32) | NO | 0 | Signal alignment |
| last_movement_at | timestamp with time zone | YES | | Last signal |
| last_band_change_at | timestamp with time zone | YES | | Last tier change |
| phase_entered_at | timestamp with time zone | YES | | Phase entry |
| stasis_start | timestamp with time zone | YES | | Stasis start |
| stasis_years | numeric(3) | YES | 0 | Years in stasis |
| updated_at | timestamp with time zone | NO | now() | |

**Phase Status Values**:
- SILENT - No activity
- EMERGING - Early signals
- ACTIVE - Clear signals
- STASIS - Prolonged silence

---

### bit.proof_lines (11 columns)

**Purpose**: Human-readable proof of BIT band authorization

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| proof_id | text | NO | | PK |
| company_unique_id | text | NO | | Company identifier |
| band | integer(32) | NO | | Authorized band |
| pressure_class | text | NO | | Pressure type |
| sources | ARRAY | NO | | Source hubs |
| evidence | jsonb | NO | | Supporting data |
| movement_ids | ARRAY | NO | | FK to movement_events |
| human_readable | text | NO | | Plain text proof |
| generated_at | timestamp with time zone | NO | now() | |
| valid_until | timestamp with time zone | NO | | Expiration |
| generated_by | text | NO | | Generator |

---

## KEY RELATIONSHIPS

### 1. CL → Outreach (Parent-Child)

```
cl.company_identity (sovereign_company_id)
    ↓ (1:1, FK: sovereign_id)
outreach.outreach (outreach_id)
    ↓ (1:N, FK: outreach_id)
[outreach.company_target, outreach.people, outreach.dol, outreach.blog]
```

### 2. Kill Switch → Companies (Overlay)

```
cl.company_identity (company_unique_id or sovereign_id)
    ← (N:1, lookup)
outreach.manual_overrides (company_unique_id)
    ↓ (1:N, FK: override_id)
outreach.override_audit_log (override_id)
```

### 3. BIT → Companies (Analytics)

```
cl.company_identity (company_unique_id)
    ← (N:1, lookup)
bit.phase_state (company_unique_id) [1:1]
bit.movement_events (company_unique_id) [N:1]
bit.proof_lines (company_unique_id) [N:1]
bit.authorization_log (company_unique_id) [N:1]
```

---

## CRITICAL NOTES FOR ERD

1. **sovereign_company_id** is the ACTUAL primary key in CL (not company_unique_id)
2. **outreach_id** is WRITE-ONCE in CL, minted by Outreach
3. **outreach.outreach** is the operational spine (workflow state)
4. **Kill switch tables** are v1.0 FROZEN components
5. **Hub registry** defines waterfall execution order
6. **BIT tables** are separate analytics layer

---

## 7. DOL FILING TABLES (26 tables, 10,970,626 rows)

**Updated**: 2026-02-10
**Schema**: `dol`
**Years**: 2023, 2024, 2025
**Universal Join Key**: `ack_id` (links all schedule tables to form_5500)
**Metadata**: 100% column comments (1,081 columns), dol.column_metadata catalog

### dol.form_5500 (~432K rows)

**Purpose**: Full Form 5500 filings from DOL FOIA data

| Column Name | Data Type | Nullable | Default | Notes |
|------------|-----------|----------|---------|-------|
| id | bigint | NO | generated | Surrogate PK |
| ack_id | varchar | NO | | DOL acknowledgment ID (universal join key) |
| sponsor_dfe_ein | varchar | NO | | Plan sponsor EIN |
| sponsor_dfe_name | varchar | NO | | Plan sponsor name |
| spons_dfe_dba_name | varchar | YES | | DBA name |
| plan_name | varchar | YES | | Plan name |
| plan_number | varchar | YES | | Plan number |
| spons_dfe_mail_us_state | varchar | YES | | Sponsor state |
| tot_active_partcp_cnt | integer | YES | | Active participants |
| form_year | varchar | YES | | Filing year (2023/2024/2025) |
| filing_status | varchar | YES | | Filing status |

### dol.form_5500_sf (~1.5M rows)

**Purpose**: Short Form 5500-SF filings

| Column Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| id | bigint | NO | Surrogate PK |
| ack_id | varchar | NO | DOL acknowledgment ID |
| sf_sponsor_name | varchar | YES | Sponsor name |
| sf_spons_ein | varchar | YES | Sponsor EIN |
| sf_plan_name | varchar | YES | Plan name |
| sf_tot_partcp_boy_cnt | numeric | YES | Participants BOY |
| sf_tot_assets_eoy_amt | numeric | YES | Total assets EOY |
| form_year | varchar | YES | Filing year |

### dol.schedule_a (~625K rows)

**Purpose**: Schedule A insurance contracts and broker commissions

| Column Name | Data Type | Nullable | Notes |
|------------|-----------|----------|-------|
| id | bigint | NO | Surrogate PK |
| ack_id | varchar | YES | Links to form_5500 |
| ins_carrier_name | varchar | YES | Insurance carrier name |
| ins_carrier_ein | varchar | YES | Carrier EIN |
| ins_prsn_covered_eoy_cnt | numeric | YES | Persons covered EOY |
| ins_policy_from_date | varchar | YES | Policy start date |
| ins_policy_to_date | varchar | YES | Policy end date |
| ins_broker_comm_tot_amt | numeric | YES | Broker commissions |
| ins_broker_fees_tot_amt | numeric | YES | Broker fees |
| form_year | varchar | YES | Filing year |

### dol.schedule_c + 8 sub-tables (~4.3M rows total)

**Purpose**: Service provider compensation disclosure

All Schedule C tables share: `id` (bigint PK), `ack_id` (varchar FK), `form_year` (varchar)

| Table | Additional Key Columns |
|-------|----------------------|
| schedule_c | sponsor_dfe_ein |
| schedule_c_part1_item1 | Direct compensation to service providers |
| schedule_c_part1_item2 | Indirect compensation |
| schedule_c_part1_item3 | Terminated service provider info |
| schedule_c_part1_item4 | Failures to provide required info |
| schedule_c_part2 | Other compensation arrangements |
| schedule_c_part1_item1_ele | P1I1 compensation elements |
| schedule_c_part1_item2_ele | P1I2 compensation elements |
| schedule_c_part1_item4_ele | P1I4 failure elements |

### dol.schedule_d + 3 sub-tables (~3.3M rows total)

**Purpose**: Direct Filing Entity (DFE) participation

All Schedule D tables share: `id` (bigint PK), `ack_id` (varchar FK), `form_year` (varchar)

| Table | Additional Key Columns |
|-------|----------------------|
| schedule_d | sponsor_dfe_ein |
| schedule_d_part1 | DFE investment participation detail |
| schedule_d_part2 | DFE filing participation detail |
| schedule_dcg | D/C/G cross-reference data |

### dol.schedule_g + 3 sub-tables (~1.9K rows total)

**Purpose**: Financial transactions requiring disclosure

All Schedule G tables share: `id` (bigint PK), `ack_id` (varchar FK), `form_year` (varchar)

| Table | Additional Key Columns |
|-------|----------------------|
| schedule_g | sponsor_dfe_ein |
| schedule_g_part1 | Loans/fixed income in default |
| schedule_g_part2 | Fixed income obligations in default |
| schedule_g_part3 | Non-exempt transactions |

### dol.schedule_h + 1 sub-table (~189K rows total)

**Purpose**: Large plan financial information

| Table | Key Columns |
|-------|-------------|
| schedule_h | id, ack_id, sponsor_dfe_ein, form_year |
| schedule_h_part1 | id, ack_id, form_year |

### dol.schedule_i + 1 sub-table (~117K rows total)

**Purpose**: Small plan financial information

| Table | Key Columns |
|-------|-------------|
| schedule_i | id, ack_id, sponsor_dfe_ein, form_year |
| schedule_i_part1 | id, ack_id, form_year |

### DOL Indexes

| Index Type | Tables Covered | Purpose |
|-----------|---------------|---------|
| form_year | 23 of 26 | Year-based partition filtering |
| (ack_id, form_year) composite | 18 | Cross-table joins with year filter |
| sponsor_dfe_ein | 8 (schedule_c, d, g, h, i headers) | EIN-based company lookup |

### DOL Column Metadata Catalog

`dol.column_metadata` contains 1,081 entries describing every column across all 26 filing tables:

| Column Name | Data Type | Purpose |
|------------|-----------|---------|
| id | int (PK) | Catalog entry ID |
| table_name | varchar | Table name (without schema) |
| column_name | varchar | Column name |
| description | text | AI-ready column description |
| category | varchar | Category (identifier, attribute, metric, etc.) |
| data_type | varchar | PostgreSQL data type |
| is_pii | boolean | PII flag |
| is_searchable | boolean | Search index candidate |

---

**Last Updated**: 2026-02-10
**CL-Outreach Alignment**: 51,148 = 51,148 ✓
**DOL Filing Tables**: 26 | Total DOL Rows: 10,970,626 | Years: 2023, 2024, 2025
**Safe for Live Marketing**: YES (v1.0 CERTIFIED)
