# DOL Sub-Hub Entity Relationship Diagram

**Version:** 1.0.0
**Generated:** 2026-01-08
**Tag:** `dol-ein-lock-v1.0`

---

## Overview

The DOL Sub-Hub operates on Department of Labor filing data to enrich companies with EIN linkage
and regulatory intelligence. This ERD documents the data model and relationships specific to
the DOL processing domain.

---

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DOL SUB-HUB DATA MODEL                                         │
│                                                                                             │
│  ┌────────────────────┐                      ┌───────────────────────────────────────────┐  │
│  │ OUTREACH SPINE     │                      │           COMPANY LIFECYCLE (CL)          │  │
│  │ (outreach.outreach)│                      │                                           │  │
│  │                    │                      │  ┌─────────────────────────────────┐      │  │
│  │ • outreach_id (PK) │                      │  │ cl.company_identity_bridge      │      │  │
│  │ • sovereign_id (FK)│◄─────────────────────┼──│ • bridge_id (PK)                │      │  │
│  │ • domain           │                      │  │ • source_company_id ─────────────┼──┐   │  │
│  │ • created_at       │                      │  │ • company_sov_id (FK) ──────────┼──┼───│  │
│  └────────┬───────────┘                      │  │ • source_system                 │  │   │  │
│           │                                  │  └─────────────────────────────────┘  │   │  │
│           │ sovereign_id                     │                                       │   │  │
│           │                                  └───────────────────────────────────────┼───┘  │
│           ▼                                                                          │      │
│  ┌────────────────────────────────────────────────────────────────────────────────┐  │      │
│  │                          DOL SCHEMA (dol.*)                                    │  │      │
│  │                                                                                │  │      │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │  │      │
│  │  │                        dol.ein_linkage (9,365 rows)                     │   │  │      │
│  │  │                                                                         │   │  │      │
│  │  │  • linkage_id (PK)          VARCHAR NOT NULL                           │   │  │      │
│  │  │  • company_unique_id (FK)   VARCHAR NOT NULL ─────────────────────────────────┘      │
│  │  │  • ein                      VARCHAR NOT NULL ─────────────────────┐     │   │        │
│  │  │  • source                   VARCHAR NOT NULL  (BACKFILL_5500_V1)  │     │   │        │
│  │  │  • source_url               TEXT NOT NULL                         │     │   │        │
│  │  │  • filing_year              INT NOT NULL                          │     │   │        │
│  │  │  • hash_fingerprint         VARCHAR NOT NULL                      │     │   │        │
│  │  │  • outreach_context_id (FK) VARCHAR NOT NULL                      │     │   │        │
│  │  │  • created_at               TIMESTAMPTZ NOT NULL                  │     │   │        │
│  │  └───────────────────────────────────────────────────────────────────┼─────┘   │        │
│  │                                                                      │         │        │
│  │                              ┌───────────────────────────────────────┘         │        │
│  │                              │ EIN Match                                       │        │
│  │                              ▼                                                 │        │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │        │
│  │  │                      dol.form_5500 (230,009 rows)                       │   │        │
│  │  │                                                                         │   │        │
│  │  │  • id (PK)                INT NOT NULL                                 │   │        │
│  │  │  • ack_id                 VARCHAR NOT NULL (unique filing ID)          │   │        │
│  │  │  • company_unique_id      TEXT NULL (linked after backfill)            │   │        │
│  │  │  • sponsor_dfe_ein        VARCHAR NOT NULL ◄───────────────────────────┤   │        │
│  │  │  • sponsor_dfe_name       VARCHAR NULL                                 │   │        │
│  │  │  • spons_dfe_mail_us_state VARCHAR NULL                                │   │        │
│  │  │  • form_year              INT NULL                                     │   │        │
│  │  │  • tot_active_partcp_cnt  INT NULL                                     │   │        │
│  │  │  • plan_name              VARCHAR NULL                                 │   │        │
│  │  │  • ... (70+ columns)                                                   │   │        │
│  │  │  • raw_payload            JSONB NULL                                   │   │        │
│  │  └───────────────────────────────────────────────────────────────────┬─────┘   │        │
│  │                                                                      │ ack_id  │        │
│  │                                                                      ▼         │        │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │        │
│  │  │                      dol.schedule_a (336,817 rows)                      │   │        │
│  │  │                                                                         │   │        │
│  │  │  • id (PK)                  INT NOT NULL                               │   │        │
│  │  │  • ack_id (FK)              VARCHAR NOT NULL ─────────────────────────►│   │        │
│  │  │  • insurance_company_name   VARCHAR NULL                               │   │        │
│  │  │  • insurance_company_ein    VARCHAR NULL                               │   │        │
│  │  │  • renewal_month            INT NULL                                   │   │        │
│  │  │  • renewal_year             INT NULL                                   │   │        │
│  │  │  • total_premiums_paid      NUMERIC NULL                               │   │        │
│  │  │  • covered_lives            INT NULL                                   │   │        │
│  │  │  • wlfr_bnft_health_ind     VARCHAR NULL                               │   │        │
│  │  │  • raw_payload              JSONB NULL                                 │   │        │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │        │
│  │                                                                                │        │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │        │
│  │  │                    dol.form_5500_sf (759,569 rows)                      │   │        │
│  │  │                        (Small Plan Filings)                             │   │        │
│  │  │                                                                         │   │        │
│  │  │  • id (PK)                INT NOT NULL                                 │   │        │
│  │  │  • ack_id                 VARCHAR NOT NULL                             │   │        │
│  │  │  • sponsor_dfe_ein        VARCHAR NOT NULL                             │   │        │
│  │  │  • ... (simplified columns)                                            │   │        │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │        │
│  │                                                                                │        │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │        │
│  │  │                    dol.ebsa_violations (9,585 rows)                     │   │        │
│  │  │                                                                         │   │        │
│  │  │  • id (PK)                INT NOT NULL                                 │   │        │
│  │  │  • ein                    VARCHAR NULL                                 │   │        │
│  │  │  • violation_type         VARCHAR NULL                                 │   │        │
│  │  │  • penalty_amount         NUMERIC NULL                                 │   │        │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │        │
│  └────────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────┐        │
│  │                          COMPANY SCHEMA (company.*)                            │        │
│  │                                                                                │        │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │        │
│  │  │               company.company_master (200K+ rows)                       │   │        │
│  │  │                                                                         │   │        │
│  │  │  • company_unique_id (PK) TEXT NOT NULL ◄─────────────────────────────────────────┘  │
│  │  │  • company_name           TEXT NULL                                    │   │        │
│  │  │  • ein                    VARCHAR NULL ◄── EIN Match Priority 1        │   │        │
│  │  │  • website_url            TEXT NULL                                    │   │        │
│  │  │  • address_state          VARCHAR NULL                                 │   │        │
│  │  │  • employee_count         INT NULL                                     │   │        │
│  │  │  • ... (30+ columns)                                                   │   │        │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │        │
│  └────────────────────────────────────────────────────────────────────────────────┘        │
│                                                                                             │
│  ┌────────────────────────────────────────────────────────────────────────────────┐        │
│  │                           SHQ SCHEMA (shq.*)                                   │        │
│  │                        (System Health Queue)                                   │        │
│  │                                                                                │        │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │        │
│  │  │                 shq.error_master (51,212 DOL rows)                      │   │        │
│  │  │                                                                         │   │        │
│  │  │  • error_id (PK)         UUID NOT NULL                                 │   │        │
│  │  │  • process_id            VARCHAR NOT NULL (01.04.02.04.22000)          │   │        │
│  │  │  • agent_id              VARCHAR NOT NULL (DOL_EIN_BACKFILL_V1)        │   │        │
│  │  │  • severity              VARCHAR NOT NULL (INFO/WARN/ERROR)            │   │        │
│  │  │  • error_type            VARCHAR NOT NULL                              │   │        │
│  │  │  • message               TEXT NOT NULL                                 │   │        │
│  │  │  • company_unique_id     VARCHAR NULL                                  │   │        │
│  │  │  • outreach_context_id   VARCHAR NULL                                  │   │        │
│  │  │  • context               JSONB NULL                                    │   │        │
│  │  │  • created_at            TIMESTAMPTZ NOT NULL                          │   │        │
│  │  │  • resolved_at           TIMESTAMPTZ NULL                              │   │        │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │        │
│  └────────────────────────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Table Summary

| Schema | Table | Rows | Purpose |
|--------|-------|------|---------|
| `dol` | `ein_linkage` | 9,365 | Locked outreach_id → EIN bindings |
| `dol` | `form_5500` | 230,009 | Annual benefit plan filings |
| `dol` | `form_5500_sf` | 759,569 | Small plan filings (<100 participants) |
| `dol` | `schedule_a` | 336,817 | Insurance broker/carrier data |
| `dol` | `ebsa_violations` | 9,585 | EBSA enforcement actions |
| `dol` | `violations` | 0 | (Reserved) |
| `company` | `company_master` | 200K+ | Company master data (EIN source) |
| `outreach` | `outreach` | 63K+ | Outreach spine records |
| `cl` | `company_identity_bridge` | 63K+ | CL identity linkage |
| `shq` | `error_master` | 51,212 | DOL backfill errors |

---

## Key Relationships

### Primary Join Path (EIN Backfill)

```
outreach.outreach.sovereign_id
    │
    ▼
cl.company_identity_bridge.company_sov_id
    │
    └── source_company_id
            │
            ▼
company.company_master.company_unique_id
    │
    └── ein (Priority 1)
            │
            ▼
dol.form_5500.sponsor_dfe_ein (Priority 2 - exact name match)
    │
    ▼
dol.ein_linkage (OUTPUT)
```

### EIN Resolution Priority

| Priority | Source | Condition |
|----------|--------|-----------|
| 1 | `company.company_master.ein` | Direct EIN from company record |
| 2 | `dol.form_5500.sponsor_dfe_ein` | Exact company name match |

---

## Views

| View | Purpose |
|------|---------|
| `dol.v_5500_summary` | Aggregated 5500 filing summary |
| `dol.v_schedule_a_carriers` | Insurance carrier summary |
| `shq.v_dol_enrichment_queue` | DOL records pending enrichment |
| `shq.v_error_summary_24h` | Error summary (last 24 hours) |

---

## Staging Tables

| Table | Purpose |
|-------|---------|
| `dol.form_5500_staging` | Staging for Form 5500 ingestion |
| `dol.form_5500_sf_staging` | Staging for SF-5500 ingestion |
| `dol.schedule_a_staging` | Staging for Schedule A ingestion |

---

## Column Details

### dol.ein_linkage

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `linkage_id` | VARCHAR | NOT NULL | Primary key (UUID) |
| `company_unique_id` | VARCHAR | NOT NULL | FK to company_master |
| `ein` | VARCHAR | NOT NULL | Employer Identification Number |
| `source` | VARCHAR | NOT NULL | Linkage source (e.g., BACKFILL_5500_V1) |
| `source_url` | TEXT | NOT NULL | Source documentation URL |
| `filing_year` | INT | NOT NULL | Filing year for the EIN match |
| `hash_fingerprint` | VARCHAR | NOT NULL | Dedup hash |
| `outreach_context_id` | VARCHAR | NOT NULL | Context reference |
| `created_at` | TIMESTAMPTZ | NOT NULL | Row creation timestamp |

### dol.form_5500 (Key Columns)

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INT | NOT NULL | Primary key |
| `ack_id` | VARCHAR | NOT NULL | DOL acknowledgment ID |
| `company_unique_id` | TEXT | NULL | Linked company (post-backfill) |
| `sponsor_dfe_ein` | VARCHAR | NOT NULL | Employer EIN |
| `sponsor_dfe_name` | VARCHAR | NULL | Company name |
| `spons_dfe_mail_us_state` | VARCHAR | NULL | State code |
| `form_year` | INT | NULL | Filing year |
| `tot_active_partcp_cnt` | INT | NULL | Active participants |
| `plan_name` | VARCHAR | NULL | Benefit plan name |

### shq.error_master

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `error_id` | UUID | NOT NULL | Primary key |
| `process_id` | VARCHAR | NOT NULL | Barton process ID |
| `agent_id` | VARCHAR | NOT NULL | Agent identifier |
| `severity` | VARCHAR | NOT NULL | INFO/WARN/ERROR |
| `error_type` | VARCHAR | NOT NULL | Error classification |
| `message` | TEXT | NOT NULL | Human-readable message |
| `company_unique_id` | VARCHAR | NULL | Company reference |
| `outreach_context_id` | VARCHAR | NULL | Context reference |
| `context` | JSONB | NULL | Additional context |
| `created_at` | TIMESTAMPTZ | NOT NULL | Error timestamp |
| `resolved_at` | TIMESTAMPTZ | NULL | Resolution timestamp |

---

## Backfill Results (v1.0)

| Metric | Count |
|--------|-------|
| Outreach IDs scanned | 60,577 |
| **Linked successfully** | **9,365** (15.5%) |
| Missing EIN | 51,192 |
| Ambiguous EIN | 20 |

---

**Last Updated:** 2026-01-08
**Author:** DOL Sub-Hub Team
**Tag:** `dol-ein-lock-v1.0`
