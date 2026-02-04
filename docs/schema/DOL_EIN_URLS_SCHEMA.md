# DOL EIN URLs Schema Reference

> **AUTHORITY**: Neon PostgreSQL (Production)
> **VERIFIED**: 2026-02-03
> **SCHEMA**: `dol`
> **STATUS**: AI-READY | HUMAN-READY | IMO-COMPLIANT

---

## Overview

The `dol.ein_urls` table stores the mapping between Employer Identification Numbers (EINs) and discovered company domains/URLs. This table serves as the bridge between:

1. **DOL Form 5500 filings** - Official government data with verified EINs
2. **Company domains** - Discovered via Hunter.io enrichment
3. **Outreach records** - Domain-based matching to existing companies

---

## Table: `dol.ein_urls`

| Attribute | Value |
|-----------|-------|
| **Schema** | `dol` |
| **Table** | `ein_urls` |
| **Record Count** | 127,909 |
| **Primary Key** | `ein` |
| **Unique Key** | `ein` |
| **Last Updated** | 2026-02-03 |

### Column Definitions

| Column ID | Column Name | Data Type | Nullable | Description | Example |
|-----------|-------------|-----------|----------|-------------|---------|
| `DEU.01` | `ein` | VARCHAR(20) | NO | Employer Identification Number (9 digits, no dashes) | `123456789` |
| `DEU.02` | `company_name` | TEXT | YES | Company legal name from DOL filing | `Acme Corporation` |
| `DEU.03` | `city` | TEXT | YES | Company city from DOL filing | `Pittsburgh` |
| `DEU.04` | `state` | VARCHAR(10) | YES | Company state code | `PA` |
| `DEU.05` | `domain` | TEXT | YES | Discovered company domain | `acme.com` |
| `DEU.06` | `url` | TEXT | YES | Full URL (https://domain) | `https://acme.com` |
| `DEU.07` | `discovered_at` | TIMESTAMP | YES | When the URL was discovered | `2026-02-03 15:30:00` |
| `DEU.08` | `discovery_method` | TEXT | YES | How the URL was discovered | `hunter_dol_enrichment` |
| `DEU.09` | `normalized_domain` | TEXT | YES | Normalized domain (lowercase, no www) | `acme.com` |

### Discovery Methods

| Method | Description | Count |
|--------|-------------|-------|
| `hunter_dol_enrichment` | Hunter.io DOL batch enrichment | 58,069 |
| `manual_lookup` | Manual research | varies |
| `clay_enrichment` | Clay.com enrichment | varies |

### Indexes

| Index Name | Columns | Type |
|------------|---------|------|
| `ein_urls_pkey` | `ein` | PRIMARY/UNIQUE |
| `idx_ein_urls_domain` | `domain` | BTREE |
| `idx_ein_urls_state` | `state` | BTREE |
| `idx_ein_urls_discovery` | `discovery_method` | BTREE |

---

## Data Sources

### Hunter DOL Enrichment (2026-02-03)

| Batch | File | EINs | Domain Coverage |
|-------|------|------|-----------------|
| 1 | `dol-match-1-2129612.csv` | 10,333 | 100% |
| 2 | `dol-match-2-2129613.csv` | 11,056 | 100% |
| 3 | `dol-match-3-2129614.csv` | 11,074 | 100% |
| 4 | `dol-match-4-2129615.csv` | 11,165 | 100% |
| 5 | `dol-match-5-2129616.csv` | 11,225 | 100% |
| 6 | `dol-match-6-2129617.csv` | 3,216 | 100% |
| **Total** | | **58,069** | |

### Geographic Coverage (Hunter DOL)

| State | EIN Count | % of Total |
|-------|-----------|------------|
| OH | 12,321 | 21.2% |
| PA | 11,934 | 20.6% |
| VA | 8,235 | 14.2% |
| MD | 7,363 | 12.7% |
| NC | 7,293 | 12.6% |
| KY | 3,521 | 6.1% |
| DC | 2,602 | 4.5% |
| WV | 897 | 1.5% |

---

## Matching to Outreach

### Domain Match Statistics

| Category | Count | % |
|----------|-------|---|
| Hunter EINs with domains | 58,069 | 100% |
| Matched to outreach (domain) | 830 | 1.4% |
| NEW (not in outreach) | 57,239 | 98.6% |

### Match Query

```sql
-- Find outreach records that match Hunter EINs by domain
SELECT
    eu.ein,
    eu.company_name,
    eu.domain,
    o.outreach_id
FROM dol.ein_urls eu
JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment';
```

---

## Data Quality

### Domain Collision Analysis

Some domains have multiple EINs (different companies incorrectly matched to same domain):

| Category | Domains | EINs |
|----------|---------|------|
| Clean (1 EIN per domain) | 54,853 | 54,853 |
| Collisions (2+ EINs per domain) | 1,388 | 3,216 |
| **Total** | 56,241 | 58,069 |

**Recommendation**: Use only "clean" domains (1 EIN each) for automated processing.

### Clean Domain Query

```sql
-- Get clean domains (exactly 1 EIN each)
SELECT domain, MIN(ein) as ein, MIN(company_name) as company_name
FROM dol.ein_urls
WHERE discovery_method = 'hunter_dol_enrichment'
GROUP BY domain
HAVING COUNT(DISTINCT ein) = 1;
```

---

## Foreign Key Relationships

```
dol.form_5500 (sponsor_dfe_ein)
        |
        | EIN match
        v
+-------------------+
| dol.ein_urls      |  EIN -> Domain mapping
| (127,909 records) |
+-------------------+
        |
        | Domain match
        v
outreach.outreach (domain)
        |
        | outreach_id FK
        v
outreach.dol (ein)
```

---

## Related Tables

### `dol.form_5500`

| Attribute | Value |
|-----------|-------|
| **Records** | 230,482 |
| **Key Column** | `sponsor_dfe_ein` |
| **Purpose** | Full Form 5500 filing data |

### `dol.form_5500_sf`

| Attribute | Value |
|-----------|-------|
| **Records** | 760,839 |
| **Key Column** | `sf_spons_dfe_ein` |
| **Purpose** | Short Form 5500-SF filing data |

### `dol.schedule_a`

| Attribute | Value |
|-----------|-------|
| **Records** | 337,476 |
| **Key Column** | `filing_id` (FK to form_5500) |
| **Purpose** | Insurance schedule data |

---

## IMO Compliance

| Attribute | Value |
|-----------|-------|
| **Hub Owner** | DOL Filings (04.04.03) |
| **Doctrine ID** | 04.04.03.02 |
| **Upstream Source** | Hunter.io, DOL EFAST |
| **Downstream Consumers** | Outreach (04.04.04), Company Target (04.04.01) |
| **Data Classification** | Public (government filing data) |
| **Retention Policy** | Permanent |

---

## Quick Reference Queries

```sql
-- Count by discovery method
SELECT discovery_method, COUNT(*) as cnt
FROM dol.ein_urls
GROUP BY discovery_method
ORDER BY cnt DESC;

-- Get NEW companies not in outreach
SELECT eu.ein, eu.company_name, eu.domain, eu.city, eu.state
FROM dol.ein_urls eu
LEFT JOIN outreach.outreach o ON LOWER(eu.domain) = LOWER(o.domain)
WHERE eu.discovery_method = 'hunter_dol_enrichment'
  AND o.outreach_id IS NULL;

-- Count by state
SELECT state, COUNT(*) as cnt
FROM dol.ein_urls
WHERE discovery_method = 'hunter_dol_enrichment'
GROUP BY state
ORDER BY cnt DESC;
```

---

## Change Log

| Date | Change | Impact |
|------|--------|--------|
| 2026-02-03 | Hunter DOL enrichment import (6 batches) | +58,069 EINs |
| 2026-02-03 | Linked 830 EINs to existing outreach | Domain matching |
| 2026-02-03 | Updated 715 EIN conflicts (Hunter authoritative) | EIN overwrite |

---
