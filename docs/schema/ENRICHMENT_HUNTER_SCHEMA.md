# Enrichment Hunter Schema Reference

> **AUTHORITY**: Neon PostgreSQL (Production)
> **VERIFIED**: 2026-02-03
> **SCHEMA**: `enrichment`
> **STATUS**: AI-READY | HUMAN-READY | IMO-COMPLIANT

---

## Overview

The Hunter.io enrichment tables store contact and company data discovered through Hunter.io's domain search API. This data serves as the primary source for:

1. **Contact Discovery** - Executive emails for outreach
2. **Company Intelligence** - Organization metadata, headcount, industry
3. **Source URLs** - 30 source columns per contact for audit trail and blog processing
4. **DOL Integration** - EIN-to-domain mapping from DOL Form 5500 filings

---

## Table: `enrichment.hunter_company`

| Attribute | Value |
|-----------|-------|
| **Schema** | `enrichment` |
| **Table** | `hunter_company` |
| **Record Count** | 88,405 |
| **Primary Key** | `id` (SERIAL) |
| **Unique Key** | `domain` |
| **Last Updated** | 2026-02-03 |

### Column Definitions

| Column ID | Column Name | Data Type | Nullable | Description | Example |
|-----------|-------------|-----------|----------|-------------|---------|
| `HCO.01` | `id` | SERIAL | NO | Auto-increment primary key | `12345` |
| `HCO.02` | `domain` | VARCHAR(255) | NO | Company website domain (unique) | `acme.com` |
| `HCO.03` | `organization` | VARCHAR(500) | YES | Company legal/display name | `Acme Corporation` |
| `HCO.04` | `company_type` | VARCHAR(100) | YES | Organization type | `private`, `public` |
| `HCO.05` | `industry` | VARCHAR(255) | YES | Primary industry classification | `Manufacturing` |
| `HCO.06` | `headcount` | VARCHAR(50) | YES | Employee count range (raw) | `51-200` |
| `HCO.07` | `headcount_min` | INTEGER | YES | Minimum employee count | `51` |
| `HCO.08` | `headcount_max` | INTEGER | YES | Maximum employee count | `200` |
| `HCO.09` | `country` | VARCHAR(100) | YES | Company HQ country | `United States` |
| `HCO.10` | `state` | VARCHAR(100) | YES | Company HQ state/province | `California` |
| `HCO.11` | `city` | VARCHAR(255) | YES | Company HQ city | `San Francisco` |
| `HCO.12` | `postal_code` | VARCHAR(20) | YES | Company HQ postal code | `94105` |
| `HCO.13` | `street` | VARCHAR(500) | YES | Company HQ street address | `123 Main St` |
| `HCO.14` | `email_pattern` | VARCHAR(100) | YES | Detected email pattern | `{first}.{last}` |
| `HCO.15` | `source_file` | VARCHAR(255) | YES | CSV file source | `batch-2026-02-03.csv` |
| `HCO.16` | `created_at` | TIMESTAMPTZ | NO | Record creation time | `2026-02-03 15:30:00` |
| `HCO.17` | `updated_at` | TIMESTAMPTZ | NO | Last update time | `2026-02-03 15:30:00` |

### Indexes

| Index Name | Columns | Type |
|------------|---------|------|
| `hunter_company_pkey` | `id` | PRIMARY |
| `hunter_company_domain_key` | `domain` | UNIQUE |
| `idx_hunter_company_industry` | `industry` | BTREE |
| `idx_hunter_company_state` | `state` | BTREE |

---

## Table: `enrichment.hunter_contact`

| Attribute | Value |
|-----------|-------|
| **Schema** | `enrichment` |
| **Table** | `hunter_contact` |
| **Record Count** | 583,433 |
| **Primary Key** | `id` (SERIAL) |
| **Unique Key** | `(domain, email)` |
| **Last Updated** | 2026-02-03 |

### Column Definitions - Core Fields

| Column ID | Column Name | Data Type | Nullable | Description | Example |
|-----------|-------------|-----------|----------|-------------|---------|
| `HC.01` | `id` | SERIAL | NO | Auto-increment primary key | `123456` |
| `HC.02` | `domain` | VARCHAR(255) | NO | Company domain (FK) | `acme.com` |
| `HC.03` | `email` | VARCHAR(255) | NO | Contact email address | `john.doe@acme.com` |
| `HC.04` | `email_type` | VARCHAR(50) | YES | Email type classification | `personal`, `generic` |
| `HC.05` | `confidence_score` | INTEGER | YES | Hunter confidence (0-100) | `95` |
| `HC.06` | `num_sources` | INTEGER | YES | Number of discovery sources | `5` |
| `HC.07` | `first_name` | VARCHAR(100) | YES | Contact first name | `John` |
| `HC.08` | `last_name` | VARCHAR(100) | YES | Contact last name | `Doe` |
| `HC.09` | `department` | VARCHAR(100) | YES | Department classification | `executive`, `finance` |
| `HC.10` | `job_title` | VARCHAR(255) | YES | Job title (normalized) | `Chief Executive Officer` |
| `HC.11` | `position_raw` | VARCHAR(500) | YES | Raw position string | `CEO & Founder` |
| `HC.12` | `twitter_handle` | VARCHAR(100) | YES | Twitter/X handle | `@johndoe` |
| `HC.13` | `linkedin_url` | VARCHAR(500) | YES | LinkedIn profile URL | `linkedin.com/in/johndoe` |
| `HC.14` | `phone_number` | VARCHAR(50) | YES | Phone number | `+1-555-123-4567` |
| `HC.15` | `source_file` | VARCHAR(255) | YES | Import source file | `batch-2026-02-03.csv` |
| `HC.16` | `created_at` | TIMESTAMPTZ | NO | Record creation time | `2026-02-03 15:30:00` |
| `HC.17` | `updated_at` | TIMESTAMPTZ | NO | Last update time | `2026-02-03 15:30:00` |

### Column Definitions - Source URLs (HC.S01 - HC.S30)

| Column ID | Column Name | Data Type | Nullable | Description |
|-----------|-------------|-----------|----------|-------------|
| `HC.S01` | `source_1` | TEXT | YES | Primary discovery source URL |
| `HC.S02` | `source_2` | TEXT | YES | Secondary discovery source URL |
| `HC.S03` | `source_3` | TEXT | YES | Tertiary discovery source URL |
| `HC.S04` | `source_4` | TEXT | YES | Additional discovery source URL |
| `HC.S05` | `source_5` | TEXT | YES | Additional discovery source URL |
| `HC.S06` | `source_6` | TEXT | YES | Additional discovery source URL |
| `HC.S07` | `source_7` | TEXT | YES | Additional discovery source URL |
| `HC.S08` | `source_8` | TEXT | YES | Additional discovery source URL |
| `HC.S09` | `source_9` | TEXT | YES | Additional discovery source URL |
| `HC.S10` | `source_10` | TEXT | YES | Additional discovery source URL |
| `HC.S11` | `source_11` | TEXT | YES | Additional discovery source URL |
| `HC.S12` | `source_12` | TEXT | YES | Additional discovery source URL |
| `HC.S13` | `source_13` | TEXT | YES | Additional discovery source URL |
| `HC.S14` | `source_14` | TEXT | YES | Additional discovery source URL |
| `HC.S15` | `source_15` | TEXT | YES | Additional discovery source URL |
| `HC.S16` | `source_16` | TEXT | YES | Additional discovery source URL |
| `HC.S17` | `source_17` | TEXT | YES | Additional discovery source URL |
| `HC.S18` | `source_18` | TEXT | YES | Additional discovery source URL |
| `HC.S19` | `source_19` | TEXT | YES | Additional discovery source URL |
| `HC.S20` | `source_20` | TEXT | YES | Additional discovery source URL |
| `HC.S21` | `source_21` | TEXT | YES | Additional discovery source URL |
| `HC.S22` | `source_22` | TEXT | YES | Additional discovery source URL |
| `HC.S23` | `source_23` | TEXT | YES | Additional discovery source URL |
| `HC.S24` | `source_24` | TEXT | YES | Additional discovery source URL |
| `HC.S25` | `source_25` | TEXT | YES | Additional discovery source URL |
| `HC.S26` | `source_26` | TEXT | YES | Additional discovery source URL |
| `HC.S27` | `source_27` | TEXT | YES | Additional discovery source URL |
| `HC.S28` | `source_28` | TEXT | YES | Additional discovery source URL |
| `HC.S29` | `source_29` | TEXT | YES | Additional discovery source URL |
| `HC.S30` | `source_30` | TEXT | YES | Additional discovery source URL |

### Indexes

| Index Name | Columns | Type |
|------------|---------|------|
| `hunter_contact_pkey` | `id` | PRIMARY |
| `hunter_contact_domain_email_key` | `(domain, email)` | UNIQUE |
| `idx_hunter_contact_domain` | `domain` | BTREE |
| `idx_hunter_contact_email` | `email` | BTREE |
| `idx_hunter_contact_department` | `department` | BTREE |

---

## Views

### `enrichment.v_hunter_contact_sources`

Unpivots source_1 through source_30 into individual rows.

| Column | Type | Description |
|--------|------|-------------|
| `contact_id` | INTEGER | FK to hunter_contact.id |
| `domain` | VARCHAR | Company domain |
| `email` | VARCHAR | Contact email |
| `first_name` | VARCHAR | Contact first name |
| `last_name` | VARCHAR | Contact last name |
| `job_title` | VARCHAR | Contact job title |
| `linkedin_url` | VARCHAR | LinkedIn profile URL |
| `source_order` | INTEGER | Source column number (1-30) |
| `source_url` | TEXT | The actual source URL |

**Current Stats**: ~231,973 source URLs

### `enrichment.v_hunter_sources_by_type`

Adds source type classification based on URL patterns.

| Source Type | Pattern | Count |
|-------------|---------|-------|
| `linkedin` | `%linkedin.com%` | ~15,000 |
| `company_page` | `%/about%`, `%/team%` | ~45,000 |
| `press_release` | `%prnewswire.com%` | ~8,000 |
| `google_search` | `%google.com/search%` | ~95,000 |
| `other` | All others | ~68,973 |

### `enrichment.v_hunter_company_sources`

Unique sources aggregated per company domain.

---

## Data Flow

```
Hunter.io API / CSV Export
        |
        v
+-------------------+
| hunter_company    |  Domain-level company data
| (88,405 records)  |
+-------------------+
        |
        | domain (FK)
        v
+-------------------+
| hunter_contact    |  Person-level contact data
| (583,433 records) |  + 30 source URL columns
+-------------------+
        |
        | Unpivot via views
        v
+---------------------------+
| v_hunter_contact_sources  |  One row per source URL
| (231,973 source URLs)     |
+---------------------------+
        |
        | Classify
        v
+---------------------------+
| v_hunter_sources_by_type  |  Categorized for processing
+---------------------------+
```

---

## Foreign Key Relationships

```
enrichment.hunter_company (domain)
        ^
        |
enrichment.hunter_contact (domain)
        |
        | Matches to outreach via domain
        v
outreach.outreach (domain)
```

---

## IMO Compliance

| Attribute | Value |
|-----------|-------|
| **Hub Owner** | Enrichment (04.05) |
| **Doctrine ID** | 04.05.01 |
| **Downstream Consumers** | Blog Content (04.04.05), People Intelligence (04.04.02), DOL (04.04.03) |
| **Data Classification** | PII (contains names, emails, phone numbers) |
| **Retention Policy** | Permanent |
| **Update Frequency** | Batch import as needed |

---

## Change Log

| Date | Change | Records |
|------|--------|---------|
| 2026-02-03 | DOL Hunter batch import (files 1-6) | +283,926 contacts |
| 2026-02-03 | Added source_1 through source_30 columns | Schema change |
| 2026-02-03 | Created unpivot views | 3 views |
| 2026-02-02 | Outreach Hunter import (3 files) | +122,997 contacts |

---
