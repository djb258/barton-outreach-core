---
id: dol-ein-linkage
title: EIN Linkage
desc: EIN-to-Company binding table and resolution process
updated: 2026-01-08
created: 2026-01-07
tags:
  - dol
  - ein
  - linkage
  - backfill
---

# EIN Linkage

## Overview

The `dol.ein_linkage` table stores the locked bindings between Outreach records and Employer Identification Numbers (EINs). This is the primary output of the DOL Sub-Hub EIN Lock-In process.

## Table Schema

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

## Statistics

| Metric | Value |
|--------|-------|
| Total Rows | 9,365 |
| Source | BACKFILL_5500_V1 |
| Agent | DOL_EIN_BACKFILL_V1 |
| Created | 2026-01-07 |

## EIN Resolution Priority

### Priority 1: Company Master

```sql
SELECT ein FROM company.company_master 
WHERE company_unique_id = :company_id 
  AND ein IS NOT NULL
```

### Priority 2: Form 5500 Exact Match

```sql
SELECT DISTINCT sponsor_dfe_ein 
FROM dol.form_5500 
WHERE UPPER(sponsor_dfe_name) = UPPER(:company_name)
  AND spons_dfe_mail_us_state IN ('WV', 'VA', 'PA', 'MD', 'OH', 'KY', 'DE', 'NC')
```

## Canonical Rule

```
0 EIN = FAIL → shq.error_master (DOL_EIN_MISSING)
1 EIN = PASS → dol.ein_linkage
2+ EIN = FAIL → shq.error_master (DOL_EIN_AMBIGUOUS)
```

## Related Tables

- `dol.form_5500` - Source of Form 5500 EINs
- `company.company_master` - Source of direct EINs
- `outreach.outreach` - Outreach spine records
- `shq.error_master` - Failed resolutions

## Links

- [[dol-subhub]] - Parent hub
- [[form-5500]] - DOL filing format
- [[company-master]] - Company identity
