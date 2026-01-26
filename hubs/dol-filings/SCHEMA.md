# DOL Filings Hub - Schema Documentation

> **AUTHORITY**: Neon PostgreSQL (Production)
> **VERIFIED**: 2026-01-25 via READ-ONLY connection
> **HUB ID**: 04.04.03
> **STATUS**: NEON VERIFIED

---

## Schema Overview

The DOL Filings hub manages Department of Labor Form 5500 data, Schedule A insurance information, and renewal calendar tracking. It provides EIN resolution and filing signals to downstream hubs.

## Primary Tables

| Schema | Table | Purpose |
|--------|-------|---------|
| `dol` | `form_5500` | Full Form 5500 filings |
| `dol` | `form_5500_sf` | Short Form 5500-SF filings |
| `dol` | `schedule_a` | Schedule A insurance contracts |
| `dol` | `renewal_calendar` | Upcoming renewal tracking |
| `dol` | `column_metadata` | Field documentation |
| `dol` | `pressure_signals` | **BIT v2.0** STRUCTURAL_PRESSURE signals |
| `outreach` | `dol` | Outreach-scoped DOL data |
| `outreach` | `dol_audit_log` | DOL processing audit trail |
| `outreach` | `dol_errors` | DOL pipeline errors |

---

## Entity Relationship Diagram

```mermaid
erDiagram
    OUTREACH_OUTREACH ||--o{ OUTREACH_DOL : "outreach_id"
    OUTREACH_OUTREACH ||--o{ OUTREACH_DOL_ERRORS : "outreach_id"

    DOL_FORM_5500 ||--o{ DOL_SCHEDULE_A : "filing_id"
    DOL_FORM_5500 ||--o{ DOL_RENEWAL_CALENDAR : "filing_id"
    DOL_RENEWAL_CALENDAR ||--o{ DOL_PRESSURE_SIGNALS : "source_record_id"

    DOL_PRESSURE_SIGNALS {
        uuid signal_id PK
        text company_unique_id FK
        varchar signal_type
        enum pressure_domain
        enum pressure_class
        jsonb signal_value
        int magnitude
        timestamptz detected_at
        timestamptz expires_at
        uuid correlation_id
        text source_record_id
    }

    OUTREACH_OUTREACH {
        uuid outreach_id PK
        uuid sovereign_id FK
        varchar domain
        timestamp created_at
    }

    DOL_FORM_5500 {
        uuid filing_id PK
        varchar ack_id UK
        text company_unique_id
        varchar sponsor_dfe_ein
        varchar sponsor_dfe_name
        varchar spons_dfe_dba_name
        varchar plan_name
        varchar plan_number
        varchar spons_dfe_mail_us_city
        varchar spons_dfe_mail_us_state
        varchar spons_dfe_mail_us_zip
        int tot_active_partcp_cnt
        varchar sch_a_attached_ind
        int num_sch_a_attached_cnt
        varchar admin_name
        varchar admin_ein
        varchar form_year
        varchar filing_status
    }

    DOL_FORM_5500_SF {
        uuid filing_id PK
        text company_unique_id
        varchar ack_id
        varchar sf_sponsor_name
        varchar sf_spons_ein
        varchar sf_plan_name
        varchar sf_spons_us_city
        varchar sf_spons_us_state
        varchar sf_spons_us_zip
        numeric sf_tot_partcp_boy_cnt
        numeric sf_tot_assets_eoy_amt
        varchar form_year
        varchar filing_status
    }

    DOL_SCHEDULE_A {
        uuid schedule_id PK
        uuid filing_id FK
        text company_unique_id
        varchar sponsor_state
        varchar sponsor_name
        varchar ack_id
        varchar ins_carrier_name
        varchar ins_carrier_ein
        varchar ins_carrier_naic_code
        varchar ins_contract_num
        numeric ins_prsn_covered_eoy_cnt
        varchar ins_policy_from_date
        varchar ins_policy_to_date
        numeric ins_broker_comm_tot_amt
        numeric ins_broker_fees_tot_amt
        varchar form_year
    }

    DOL_RENEWAL_CALENDAR {
        uuid renewal_id PK
        text company_unique_id
        uuid schedule_id FK
        uuid filing_id FK
        int renewal_month
        int renewal_year
        date renewal_date
        varchar plan_name
        varchar carrier_name
        boolean is_upcoming
        int days_until_renewal
    }

    DOL_COLUMN_METADATA {
        int id PK
        varchar table_name
        varchar column_name
        varchar column_id
        text description
        varchar category
        varchar data_type
        boolean is_pii
        boolean is_searchable
    }

    OUTREACH_DOL {
        uuid dol_id PK
        uuid outreach_id FK
        text ein
        boolean filing_present
        text funding_type
        text broker_or_advisor
        text carrier
    }

    OUTREACH_DOL_AUDIT_LOG {
        int log_id PK
        text company_id
        text state
        boolean attempted
        text outcome
        text ein
        text fail_reason
        text run_id
    }

    OUTREACH_DOL_ERRORS {
        uuid error_id PK
        uuid outreach_id FK
        varchar pipeline_stage
        varchar failure_code
        text blocking_reason
        varchar severity
        boolean retry_allowed
        jsonb raw_input
    }
```

---

## Table Details

### dol.form_5500

Full Form 5500 filings from the Department of Labor.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `filing_id` | uuid | NOT NULL | gen_random_uuid() | Primary key |
| `ack_id` | varchar | NOT NULL | - | DOL acknowledgment ID |
| `company_unique_id` | text | NULL | - | Matched company reference |
| `sponsor_dfe_ein` | varchar | NOT NULL | - | Plan sponsor EIN |
| `sponsor_dfe_name` | varchar | NOT NULL | - | Plan sponsor name |
| `spons_dfe_dba_name` | varchar | NULL | - | DBA name if different |
| `plan_name` | varchar | NULL | - | Name of the plan |
| `plan_number` | varchar | NULL | - | Plan number |
| `spons_dfe_mail_us_city` | varchar | NULL | - | Sponsor city |
| `spons_dfe_mail_us_state` | varchar | NULL | - | Sponsor state |
| `spons_dfe_mail_us_zip` | varchar | NULL | - | Sponsor ZIP |
| `tot_active_partcp_cnt` | integer | NULL | - | Total active participants |
| `sch_a_attached_ind` | varchar | NULL | - | Has Schedule A attached |
| `num_sch_a_attached_cnt` | integer | NULL | - | Number of Schedule A forms |
| `admin_name` | varchar | NULL | - | Plan administrator name |
| `admin_ein` | varchar | NULL | - | Administrator EIN |
| `form_year` | varchar | NULL | - | Filing year |
| `filing_status` | varchar | NULL | - | Filing status |
| `date_received` | varchar | NULL | - | Date received by DOL |
| `created_at` | timestamptz | NOT NULL | now() | Record creation time |
| `updated_at` | timestamptz | NOT NULL | now() | Last update time |

### dol.schedule_a

Schedule A insurance contract information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `schedule_id` | uuid | NOT NULL | gen_random_uuid() | Primary key |
| `filing_id` | uuid | NULL | - | FK to form_5500 |
| `company_unique_id` | text | NULL | - | Matched company reference |
| `sponsor_state` | varchar | NULL | - | Sponsor state |
| `sponsor_name` | varchar | NULL | - | Sponsor name |
| `ins_carrier_name` | varchar | NULL | - | Insurance carrier name |
| `ins_carrier_ein` | varchar | NULL | - | Carrier EIN |
| `ins_carrier_naic_code` | varchar | NULL | - | NAIC code |
| `ins_contract_num` | varchar | NULL | - | Contract number |
| `ins_prsn_covered_eoy_cnt` | numeric | NULL | - | Persons covered EOY |
| `ins_policy_from_date` | varchar | NULL | - | Policy start date |
| `ins_policy_to_date` | varchar | NULL | - | Policy end date |
| `ins_broker_comm_tot_amt` | numeric | NULL | - | Broker commissions |
| `ins_broker_fees_tot_amt` | numeric | NULL | - | Broker fees |
| `wlfr_bnft_health_ind` | varchar | NULL | - | Health benefit indicator |
| `wlfr_bnft_dental_ind` | varchar | NULL | - | Dental benefit indicator |
| `wlfr_bnft_vision_ind` | varchar | NULL | - | Vision benefit indicator |
| `wlfr_bnft_life_insur_ind` | varchar | NULL | - | Life insurance indicator |
| `form_year` | varchar | NULL | - | Filing year |
| `created_at` | timestamptz | NULL | now() | Record creation time |

### dol.renewal_calendar

Upcoming benefit renewal tracking.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `renewal_id` | uuid | NOT NULL | gen_random_uuid() | Primary key |
| `company_unique_id` | text | NOT NULL | - | Company reference |
| `schedule_id` | uuid | NULL | - | FK to schedule_a |
| `filing_id` | uuid | NULL | - | FK to form_5500 |
| `renewal_month` | integer | NULL | - | Renewal month (1-12) |
| `renewal_year` | integer | NULL | - | Renewal year |
| `renewal_date` | date | NULL | - | Exact renewal date |
| `plan_name` | varchar | NULL | - | Plan name |
| `carrier_name` | varchar | NULL | - | Carrier name |
| `is_upcoming` | boolean | NOT NULL | true | Is in future |
| `days_until_renewal` | integer | NULL | - | Days until renewal |
| `created_at` | timestamptz | NOT NULL | now() | Record creation time |
| `updated_at` | timestamptz | NOT NULL | now() | Last update time |

### dol.pressure_signals (BIT v2.0)

**AI-Ready Data Metadata (per Canonical Architecture Doctrine §12):**

| Field | Value |
|-------|-------|
| `table_unique_id` | `TBL-DOL-PRESSURE-001` |
| `owning_hub_unique_id` | `HUB-DOL-001` |
| `owning_subhub_unique_id` | `SUBHUB-DOL-001` |
| `description` | STRUCTURAL_PRESSURE domain signals for BIT authorization. Highest trust level - required for Band 3+ authorization. |
| `source_of_truth` | DOL Hub processing (renewal calendar, cost analysis, broker changes) |
| `row_identity_strategy` | UUID primary key (signal_id) |

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `signal_id` | uuid | NOT NULL | gen_random_uuid() | Primary key - unique signal identifier |
| `company_unique_id` | text | NOT NULL | - | Company reference |
| `signal_type` | varchar(50) | NOT NULL | - | Signal classification (renewal_proximity, cost_increase, broker_change) |
| `pressure_domain` | enum | NOT NULL | 'STRUCTURAL_PRESSURE' | Domain constraint (always STRUCTURAL_PRESSURE for DOL) |
| `pressure_class` | enum | NULL | - | Pressure classification (COST_PRESSURE, DEADLINE_PROXIMITY, etc) |
| `signal_value` | jsonb | NOT NULL | '{}' | Domain-specific payload with evidence |
| `magnitude` | integer | NOT NULL | 0 | Impact score (0-100) |
| `detected_at` | timestamptz | NOT NULL | now() | When signal was detected |
| `expires_at` | timestamptz | NOT NULL | - | Validity window end |
| `correlation_id` | uuid | NULL | - | PID binding / trace ID |
| `source_record_id` | text | NULL | - | Traceability (e.g., ack_id, renewal_id) |
| `created_at` | timestamptz | NOT NULL | now() | Record creation time |

**Column Metadata (per §12.3):**

| Column | column_unique_id | semantic_role | format |
|--------|------------------|---------------|--------|
| `signal_id` | COL-DOL-PS-001 | identifier | UUID |
| `company_unique_id` | COL-DOL-PS-002 | foreign_key | TEXT |
| `signal_type` | COL-DOL-PS-003 | attribute | ENUM |
| `pressure_domain` | COL-DOL-PS-004 | attribute | ENUM |
| `pressure_class` | COL-DOL-PS-005 | attribute | ENUM |
| `signal_value` | COL-DOL-PS-006 | attribute | JSON |
| `magnitude` | COL-DOL-PS-007 | metric | INTEGER |
| `detected_at` | COL-DOL-PS-008 | attribute | ISO-8601 |
| `expires_at` | COL-DOL-PS-009 | attribute | ISO-8601 |
| `correlation_id` | COL-DOL-PS-010 | identifier | UUID |
| `source_record_id` | COL-DOL-PS-011 | foreign_key | TEXT |
| `created_at` | COL-DOL-PS-012 | attribute | ISO-8601 |

**Authority:** ADR-017
**Migration:** `neon/migrations/2026-01-26-bit-v2-phase1-distributed-signals.sql`

### dol.backfill_renewal_signals() (BIT v2.0 Phase 1.5)

Idempotent backfill function for DOL renewal signals.

**Function Metadata:**

| Field | Value |
|-------|-------|
| `function_unique_id` | `FUNC-DOL-BACKFILL-001` |
| `owning_hub_unique_id` | `HUB-DOL-001` |
| `description` | Processes dol.renewal_calendar rows into dol.pressure_signals |
| `signature` | `backfill_renewal_signals() RETURNS TABLE (processed INT, skipped INT, errors INT)` |

**Magnitude Calculation:**

| days_until_renewal | magnitude |
|--------------------|-----------|
| <= 30 | 70 |
| <= 60 | 55 |
| <= 90 | 45 |
| <= 120 | 35 |
| > 120 | 25 |

**Idempotent:** Safe to run multiple times - skips already processed records via `source_record_id`.

**Authority:** ADR-017
**Migration:** `neon/migrations/2026-01-26-bit-v2-phase1.5-backfill-and-movements.sql`

---

### outreach.dol

Outreach-scoped DOL summary data.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `dol_id` | uuid | NOT NULL | gen_random_uuid() | Primary key |
| `outreach_id` | uuid | NOT NULL | - | FK to outreach.outreach |
| `ein` | text | NULL | - | Matched EIN |
| `filing_present` | boolean | NULL | - | Has DOL filing |
| `funding_type` | text | NULL | - | Plan funding type |
| `broker_or_advisor` | text | NULL | - | Broker/advisor info |
| `carrier` | text | NULL | - | Insurance carrier |
| `created_at` | timestamptz | NULL | now() | Record creation time |
| `updated_at` | timestamptz | NULL | now() | Last update time |

---

## Foreign Key Relationships

| Source Table | Source Column | Target Table | Target Column |
|--------------|---------------|--------------|---------------|
| dol.renewal_calendar | filing_id | dol.form_5500 | filing_id |
| dol.schedule_a | filing_id | dol.form_5500 | filing_id |
| outreach.dol | outreach_id | outreach.outreach | outreach_id |
| outreach.dol_errors | outreach_id | outreach.outreach | outreach_id |

---

## Key DOL Fields for Outreach

### EIN Matching
- `sponsor_dfe_ein` - Primary EIN for company matching
- `admin_ein` - Secondary EIN (administrator)
- `ins_carrier_ein` - Carrier EIN for enrichment

### Renewal Intelligence
- `ins_policy_to_date` - Policy expiration date
- `renewal_month` / `renewal_year` - Calculated renewal window
- `days_until_renewal` - Time-sensitive targeting

### Benefit Types
- `wlfr_bnft_health_ind` - Health coverage
- `wlfr_bnft_dental_ind` - Dental coverage
- `wlfr_bnft_vision_ind` - Vision coverage
- `wlfr_bnft_life_insur_ind` - Life insurance

---

## Data Import Sources

| Year | Form Type | Table | Status |
|------|-----------|-------|--------|
| 2023 | 5500 | dol.form_5500 | Active |
| 2023 | 5500-SF | dol.form_5500_sf | Active |
| 2023 | Schedule A | dol.schedule_a | Active |

---

*Generated from Neon PostgreSQL via READ-ONLY connection*
*Last verified: 2026-01-25*
