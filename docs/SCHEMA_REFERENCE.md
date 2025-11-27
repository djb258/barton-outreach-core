# Neon PostgreSQL Schema Reference

**Generated:** 2025-11-27
**Database:** Marketing DB
**Host:** ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech

---

## Schema Overview

| Schema | Tables | Views | Purpose |
|--------|--------|-------|---------|
| **intake** | 4 | 3 | Raw data ingestion from external sources (Clay, CSV) |
| **marketing** | 23 | 11 | Core business data (companies, people, slots) |
| **bit** | 3 | 2 | Buyer Intent Tool scoring |
| **ple** | 3 | 2 | Perpetual Lead Engine cycles |
| **company** | 0 | 5 | Company-focused views |
| **people** | 0 | 5 | People/contact-focused views |
| **public** | 3 | 3 | System tables and shared views |
| **shq** | 1 | 0 | Audit logging |

---

## intake Schema (Data Ingestion)

### Tables

#### `intake.company_raw_from_clay` (NEW - 2025-11-27)
Enriched company data from Clay.com integration.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| company_unique_id | TEXT | Reference to company_master |
| company_name | TEXT | Original company name |
| website_original | TEXT | Original website |
| website_enriched | TEXT | Clay-enriched website |
| employee_count_enriched | INT | Clay-enriched employee count |
| industry_enriched | TEXT | Clay-enriched industry |
| linkedin_company_url | TEXT | Company LinkedIn URL |
| clay_enriched_at | TIMESTAMPTZ | When Clay enriched |
| clay_credits_used | INT | Credits consumed |
| enrichment_status | TEXT | received/processing/promoted/failed |
| created_at | TIMESTAMPTZ | Record creation |

#### `intake.people_raw_from_clay` (NEW - 2025-11-27)
Enriched people/contact data from Clay.com integration.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| person_unique_id | TEXT | Reference to people_master |
| company_unique_id | TEXT | Reference to company_master |
| slot_type | TEXT | CEO/CFO/HR |
| work_email | TEXT | Enriched work email |
| work_email_verified | BOOLEAN | Email verification status |
| linkedin_url_enriched | TEXT | Enriched LinkedIn URL |
| phone_direct | TEXT | Direct phone number |
| clay_credits_used | INT | Credits consumed |
| enrichment_status | TEXT | received/processing/promoted/failed |

#### `intake.company_raw_intake`
Raw company data from CSV uploads.

#### `intake.people_raw_intake`
Raw people data from CSV uploads.

### Views

#### `intake.v_companies_for_clay` (NEW)
Companies ready for Clay enrichment (not enriched in last 30 days).
- **Row Count:** ~453 companies

#### `intake.v_people_for_clay` (NEW)
People ready for Clay enrichment (not enriched in last 30 days).
- **Row Count:** ~1,300+ people

#### `intake.v_clay_enrichment_stats` (NEW)
Summary statistics for Clay enrichment pipeline.

---

## marketing Schema (Core Data)

### Core Tables

#### `marketing.company_master`
Master company records for the PLE pipeline.

| Column | Type | Description |
|--------|------|-------------|
| company_unique_id | TEXT | Primary key (Barton ID) |
| company_name | TEXT | Company name |
| website_url | TEXT | Company website |
| address_city | TEXT | City |
| address_state | TEXT | State (PA/VA/MD/OH/WV/KY) |
| employee_count | INT | Employee count (50-2000) |
| industry | TEXT | Industry classification |
| linkedin_url | TEXT | Company LinkedIn |
| created_at | TIMESTAMPTZ | Record creation |
| updated_at | TIMESTAMPTZ | Last update |

**Row Count:** 453

#### `marketing.people_master`
Master contact/executive records.

| Column | Type | Description |
|--------|------|-------------|
| unique_id | TEXT | Primary key (Barton ID) |
| full_name | TEXT | Full name |
| email | TEXT | Email address |
| linkedin_url | TEXT | LinkedIn profile URL |
| title | TEXT | Job title |
| company_unique_id | TEXT | FK to company_master |
| validation_status | TEXT | Generated validation status |
| last_verified_at | TIMESTAMPTZ | Last verification date |

**Row Count:** ~1,300+

#### `marketing.company_slot`
Executive slots (CEO/CFO/HR) per company.

| Column | Type | Description |
|--------|------|-------------|
| company_slot_unique_id | TEXT | Primary key |
| company_unique_id | TEXT | FK to company_master |
| person_unique_id | TEXT | FK to people_master |
| slot_type | TEXT | CEO/CFO/HR |
| is_filled | BOOLEAN | Slot filled status |
| filled_at | TIMESTAMPTZ | When filled |
| vacated_at | TIMESTAMPTZ | When vacated |

**Row Count:** ~1,359 (3 slots per 453 companies)

### Sidecar Tables (NEW - 2025-11-26)

#### `marketing.person_movement_history`
Tracks executive job changes.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master |
| company_from_id | TEXT | Previous company |
| company_to_id | TEXT | New company |
| title_from | TEXT | Previous title |
| title_to | TEXT | New title |
| movement_type | TEXT | company_change/title_change/contact_lost |
| detected_at | TIMESTAMPTZ | When detected |

#### `marketing.person_scores`
BIT (Buyer Intent Tool) scores per person.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| person_unique_id | TEXT | FK to people_master (UNIQUE) |
| bit_score | INT | Score 0-100 |
| confidence_score | INT | Confidence 0-100 |
| score_factors | JSONB | Score breakdown |
| calculated_at | TIMESTAMPTZ | When calculated |

#### `marketing.company_events`
Company news/events that impact BIT scores.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| company_unique_id | TEXT | FK to company_master |
| event_type | TEXT | funding/acquisition/ipo/layoff/leadership_change |
| event_date | DATE | Event date |
| source_url | TEXT | News source |
| bit_impact_score | INT | Impact on BIT (-100 to +100) |

### Validation Tables

#### `marketing.company_invalid`
Companies that failed validation.
- **Row Count:** 114 (West Virginia companies)

#### `marketing.people_invalid`
People that failed validation.

#### `marketing.validation_failures_log`
Detailed validation failure records.

### Views

- `marketing.v_companies_need_enrichment` - Companies needing enrichment
- `marketing.v_company_enrichment_status` - Enrichment status by company
- `marketing.v_phase_stats` - Pipeline phase statistics
- `marketing.marketing_ceo` - CEO contacts view
- `marketing.marketing_cfo` - CFO contacts view
- `marketing.marketing_hr` - HR contacts view

---

## bit Schema (Buyer Intent Tool)

### Tables

#### `bit.bit_signal`
Raw buyer intent signals.

| Column | Type | Description |
|--------|------|-------------|
| signal_id | TEXT | Primary key |
| company_unique_id | TEXT | FK to company_master |
| signal_type | TEXT | Signal category |
| signal_value | JSONB | Signal data |
| detected_at | TIMESTAMPTZ | Detection timestamp |

#### `bit.bit_company_score`
Aggregated BIT scores per company.

#### `bit.bit_contact_score`
BIT scores per contact.

### Views

- `bit.vw_hot_companies` - High-scoring companies
- `bit.vw_engaged_contacts` - Engaged contacts

---

## ple Schema (Perpetual Lead Engine)

### Tables

#### `ple.ple_cycle`
PLE execution cycles.

#### `ple.ple_step`
Individual steps within cycles.

#### `ple.ple_log`
Cycle execution logs.

### Views

- `ple.vw_active_cycles` - Currently running cycles
- `ple.vw_pending_steps` - Steps awaiting execution

---

## Data Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                         DATA FLOW                                 │
└──────────────────────────────────────────────────────────────────┘

CSV Upload                    Clay.com
    │                            │
    ▼                            ▼
intake.company_raw_intake    intake.company_raw_from_clay
intake.people_raw_intake     intake.people_raw_from_clay
    │                            │
    └─────────┬──────────────────┘
              │
              ▼ (Validation & Promotion)
    ┌─────────────────────┐
    │   marketing.        │
    │   company_master    │
    │   people_master     │
    │   company_slot      │
    └─────────────────────┘
              │
              ▼ (Enrichment & Scoring)
    ┌─────────────────────┐
    │   marketing.        │
    │   person_scores     │
    │   company_events    │
    │   person_movement   │
    └─────────────────────┘
              │
              ▼ (BIT Processing)
    ┌─────────────────────┐
    │   bit.              │
    │   bit_signal        │
    │   bit_company_score │
    │   bit_contact_score │
    └─────────────────────┘
              │
              ▼ (PLE Execution)
    ┌─────────────────────┐
    │   ple.              │
    │   ple_cycle         │
    │   ple_step          │
    │   ple_log           │
    └─────────────────────┘
```

---

## Recent Changes (2025-11-27)

### New Objects Created

1. **Tables:**
   - `intake.company_raw_from_clay` - Clay company enrichment intake
   - `intake.people_raw_from_clay` - Clay people enrichment intake

2. **Views:**
   - `intake.v_companies_for_clay` - Companies ready for Clay
   - `intake.v_people_for_clay` - People ready for Clay
   - `intake.v_clay_enrichment_stats` - Enrichment pipeline stats

3. **Triggers:**
   - `trg_clay_company_updated` - Auto-update timestamp
   - `trg_clay_people_updated` - Auto-update timestamp

### Migration Files

- `infra/migrations/002_create_clay_intake_tables.sql` - Clay integration tables

---

## Connection Details

```
Host:     ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Port:     5432
Database: Marketing DB
User:     Marketing DB_owner
Password: npg_OsE4Z2oPCpiT
SSL:      require
```

**Connection String:**
```
postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech:5432/Marketing%20DB?sslmode=require
```

---

## Related Documentation

- `docs/schema_map.json` - Machine-readable schema (auto-generated)
- `infra/docs/CLAY_NEON_INTEGRATION.md` - Clay.com setup guide
- `repo-data-diagrams/PLE_SCHEMA_ERD.md` - Visual ERD diagram
- `repo-data-diagrams/PLE_SCHEMA_REFERENCE.md` - Detailed column reference
- `ctb/sys/enrichment/SCHEMA_FIXES_REPORT.md` - Constraint audit results

---

**Last Updated:** 2025-11-27
**Total Tables:** 37 across 8 schemas
**Total Views:** 31 across 8 schemas
