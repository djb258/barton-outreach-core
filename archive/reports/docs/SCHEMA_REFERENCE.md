# Neon PostgreSQL Schema Reference

> **Generated:** 2026-02-03
> **Database:** Marketing DB
> **Host:** ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
> **Status:** AI-READY | HUMAN-READY | IMO-COMPLIANT

---

## Schema Overview

| Schema | Tables | Purpose | Key Metric |
|--------|--------|---------|------------|
| **outreach** | 30+ | Outreach operational spine | 42,192 records |
| **enrichment** | 3 | Hunter.io enrichment data | 583,433 contacts |
| **dol** | 8 | DOL Form 5500/5500-SF filings | 991,321 filings |
| **cl** | 3 | Company Lifecycle authority | Sovereign IDs |
| **people** | 5 | People/slot management | 153,444 slots |
| **company** | 3 | Company master data | 74,641 records |
| **bit** | 3 | Buyer Intent scoring | 13,226 scored |

---

## Critical Tables Summary

### Operational Core

| Schema.Table | Records | Purpose | Primary Key |
|--------------|---------|---------|-------------|
| `outreach.outreach` | 42,192 | Outreach spine | `outreach_id` |
| `outreach.company_target` | 41,425 | Company targeting | `target_id` |
| `outreach.dol` | 17,338 | DOL sub-hub | `dol_id` |
| `outreach.people` | 324 | People sub-hub | `person_id` |
| `outreach.blog` | 41,425 | Blog sub-hub | `blog_id` |
| `outreach.bit_scores` | 13,226 | BIT scoring | `outreach_id` |

### Enrichment

| Schema.Table | Records | Purpose | Primary Key |
|--------------|---------|---------|-------------|
| `enrichment.hunter_company` | 88,405 | Hunter company data | `domain` |
| `enrichment.hunter_contact` | 583,433 | Hunter contacts + 30 sources | `(domain, email)` |

### DOL Filings

| Schema.Table | Records | Purpose | Primary Key |
|--------------|---------|---------|-------------|
| `dol.form_5500` | 230,482 | Full Form 5500 filings | `filing_id` |
| `dol.form_5500_sf` | 760,839 | Short Form 5500-SF | `filing_id` |
| `dol.schedule_a` | 337,476 | Insurance schedule | `schedule_id` |
| `dol.ein_urls` | 127,909 | EIN to domain mapping | `ein` |

---

## outreach Schema

### `outreach.outreach` (Operational Spine)

| Column | Type | Description |
|--------|------|-------------|
| `outreach_id` | UUID | Primary key (minted here) |
| `sovereign_id` | UUID | FK to cl.company_identity |
| `domain` | VARCHAR(255) | Company domain |
| `ein` | VARCHAR(20) | EIN (if known) |
| `created_at` | TIMESTAMPTZ | Record creation |
| `updated_at` | TIMESTAMPTZ | Last update |

**Records:** 42,192

### `outreach.dol` (DOL Sub-Hub)

| Column | Type | Description |
|--------|------|-------------|
| `dol_id` | UUID | Primary key |
| `outreach_id` | UUID | FK to outreach.outreach |
| `ein` | TEXT | Employer ID Number |
| `filing_present` | BOOLEAN | Has DOL filing |
| `funding_type` | TEXT | Funding classification |
| `broker_or_advisor` | TEXT | B/A presence |
| `carrier` | TEXT | Insurance carrier |

**Records:** 17,338 (41% of outreach)

### `outreach.company_target` (Company Targeting)

| Column | Type | Description |
|--------|------|-------------|
| `target_id` | UUID | Primary key |
| `company_unique_id` | TEXT | Legacy company ID |
| `outreach_id` | UUID | FK to outreach |
| `outreach_status` | TEXT | Targeting status |
| `bit_score_snapshot` | INTEGER | BIT score at targeting |
| `email_method` | VARCHAR | Email discovery method |
| `confidence_score` | NUMERIC | Pattern confidence |

**Records:** 41,425

---

## enrichment Schema

### `enrichment.hunter_company`

| Column ID | Column | Type | Description |
|-----------|--------|------|-------------|
| HCO.02 | `domain` | VARCHAR(255) | Company domain (UNIQUE) |
| HCO.03 | `organization` | VARCHAR(500) | Company name |
| HCO.05 | `industry` | VARCHAR(255) | Industry classification |
| HCO.06 | `headcount` | VARCHAR(50) | Employee count range |
| HCO.10 | `state` | VARCHAR(100) | HQ state |
| HCO.14 | `email_pattern` | VARCHAR(100) | Email pattern |

**Records:** 88,405

### `enrichment.hunter_contact`

| Column ID | Column | Type | Description |
|-----------|--------|------|-------------|
| HC.02 | `domain` | VARCHAR(255) | Company domain (FK) |
| HC.03 | `email` | VARCHAR(255) | Contact email |
| HC.05 | `confidence_score` | INTEGER | Hunter confidence (0-100) |
| HC.07 | `first_name` | VARCHAR(100) | First name |
| HC.08 | `last_name` | VARCHAR(100) | Last name |
| HC.10 | `job_title` | VARCHAR(255) | Job title |
| HC.13 | `linkedin_url` | VARCHAR(500) | LinkedIn URL |
| HC.S01-S30 | `source_1..30` | TEXT | 30 discovery source URLs |

**Records:** 583,433
**Source URLs:** 231,973

### Views

| View | Purpose | Records |
|------|---------|---------|
| `v_hunter_contact_sources` | Unpivoted source URLs | 231,973 |
| `v_hunter_sources_by_type` | Classified sources | 231,973 |
| `v_hunter_company_sources` | Sources per domain | ~88,000 |

---

## dol Schema

### `dol.form_5500`

| Column | Type | Description |
|--------|------|-------------|
| `filing_id` | UUID | Primary key |
| `ack_id` | VARCHAR | DOL acknowledgment ID |
| `sponsor_dfe_ein` | VARCHAR | Sponsor EIN |
| `sponsor_dfe_name` | VARCHAR | Sponsor name |
| `plan_name` | VARCHAR | Plan name |
| `tot_active_partcp_cnt` | INTEGER | Active participants |

**Records:** 230,482
**Columns:** 147

### `dol.form_5500_sf`

| Column | Type | Description |
|--------|------|-------------|
| `filing_id` | UUID | Primary key |
| `sf_spons_dfe_ein` | VARCHAR | Sponsor EIN |
| `sf_spons_dfe_name` | VARCHAR | Sponsor name |
| `sf_tot_partcp_boy_cnt` | INTEGER | Participants BOY |

**Records:** 760,839
**Columns:** 196

### `dol.ein_urls`

| Column ID | Column | Type | Description |
|-----------|--------|------|-------------|
| DEU.01 | `ein` | VARCHAR(20) | EIN (PRIMARY KEY) |
| DEU.02 | `company_name` | TEXT | Legal name from DOL |
| DEU.04 | `state` | VARCHAR(10) | State code |
| DEU.05 | `domain` | TEXT | Discovered domain |
| DEU.08 | `discovery_method` | TEXT | Source method |

**Records:** 127,909
**Hunter DOL EINs:** 58,069
**Matched to Outreach:** 830
**New (not in outreach):** 54,166

---

## Key Relationships

```
cl.company_identity (sovereign_id)
        |
        | sovereign_id
        v
outreach.outreach (outreach_id, domain)
        |
        +---> outreach.company_target (outreach_id)
        +---> outreach.dol (outreach_id, ein)
        +---> outreach.people (outreach_id)
        +---> outreach.blog (outreach_id)
        +---> outreach.bit_scores (outreach_id)
        |
        | domain match
        v
enrichment.hunter_company (domain)
        |
        +---> enrichment.hunter_contact (domain)
        |
        | domain match
        v
dol.ein_urls (ein, domain)
        |
        | ein match
        v
dol.form_5500 / dol.form_5500_sf
```

---

## Current Metrics (2026-02-03)

### Outreach Coverage

| Metric | Count | % |
|--------|-------|---|
| Total outreach records | 42,192 | 100% |
| With DOL/EIN | 17,338 | 41.1% |
| With company_target | 41,425 | 98.2% |
| With BIT score | 13,226 | 31.3% |
| With blog | 41,425 | 98.2% |

### Hunter Enrichment

| Metric | Count |
|--------|-------|
| Hunter companies | 88,405 |
| Hunter contacts | 583,433 |
| Contacts with sources | 124,693 |
| Total source URLs | 231,973 |

### DOL Filing Coverage

| Metric | Count |
|--------|-------|
| Form 5500 filings | 230,482 |
| Form 5500-SF filings | 760,839 |
| EINs with domains | 127,909 |
| Hunter DOL EINs | 58,069 |
| Matched to outreach | 830 |
| New companies (clean) | 54,166 |

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/schema/ENRICHMENT_HUNTER_SCHEMA.md` | Hunter tables full spec |
| `docs/schema/DOL_EIN_URLS_SCHEMA.md` | DOL EIN URLs full spec |
| `docs/diagrams/HUNTER_DOL_ERD.md` | ERD diagram |
| `docs/AUTHORITATIVE_TABLE_REFERENCE.md` | Key table reference |
| `docs/HUNTER_SOURCE_COLUMNS_REFERENCE.md` | Source columns spec |

---

## Connection Details

```
Host:     ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
Port:     5432
Database: Marketing DB
SSL:      require
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-03 | Hunter DOL import: 58,069 EINs, 283,926 contacts |
| 2026-02-03 | Updated all metrics and counts |
| 2026-02-02 | Hunter outreach import: 122,997 contacts |
| 2026-01-27 | EIN migration complete |
| 2026-01-21 | Sovereign cleanup: 23,025 archived |

---

**Last Updated:** 2026-02-03
**Total Records:** 2M+ across all schemas
