# Data Architecture - Outreach Pipeline

**Last Updated:** 2026-01-27  
**Status:** CANONICAL REFERENCE

---

## Overview

The outreach pipeline uses **`outreach_id` (UUID)** as the canonical join key across all tables. This document defines the authoritative join paths and data ownership.

---

## Master Table: outreach.outreach (The Spine)

| Column | Type | Description |
|--------|------|-------------|
| `outreach_id` | UUID | **PRIMARY KEY** - The canonical join key |
| `domain` | TEXT | Website domain (may include www. prefix) |
| `company_name` | TEXT | Company name |
| `created_at` | TIMESTAMP | Record creation |

**Current Count:** 52,771 records

This is the **spine table**. All sub-hubs join to it via `outreach_id`.

---

## Join Architecture

```
                    ┌─────────────────────────────┐
                    │    outreach.outreach        │
                    │    (52,771 - THE SPINE)     │
                    │    PK: outreach_id          │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│ outreach.company_ │   │   outreach.dol    │   │   outreach.blog   │
│     target        │   │   (34,173)        │   │   (52,771)        │
│   (51,180)        │   │   FK: outreach_id │   │   FK: outreach_id │
│ FK: outreach_id   │   │   Contains: EIN   │   │                   │
└───────────────────┘   └───────────────────┘   └───────────────────┘
        │
        │
        ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│  outreach.people  │   │ outreach.bit_     │   │ people.company_   │
│     (426)         │   │     scores        │   │      slot         │
│ FK: outreach_id   │   │   (17,000+)       │   │   (158,000+)      │
│                   │   │ FK: outreach_id   │   │ FK: outreach_id   │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

---

## Sub-Hub Definitions

### outreach.company_target (Company Sub-Hub)
- **Purpose:** Company targeting and segmentation data
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** 51,180 records
- **Contains:** Company metadata, targeting flags, industry codes

### outreach.dol (DOL Sub-Hub)
- **Purpose:** Department of Labor / EIN data
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** 34,173 records (after 2026-01-27 migration)
- **Contains:** EIN (18,026 unique), filing_present, funding_type, broker_or_advisor, carrier
- **Coverage:** 64.8% of outreach pipeline

### outreach.blog (Blog Sub-Hub)
- **Purpose:** Blog/content tracking
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** 52,771 records

### outreach.people (People Sub-Hub)
- **Purpose:** Contact/person data linked to companies
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** 426 records

### outreach.bit_scores (Scoring Sub-Hub)
- **Purpose:** Behavioral/intent scoring
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** ~17,000 records

### people.company_slot (People Schema)
- **Purpose:** Company slot assignments for people
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** ~158,000 records

### cl.company_identity (CL Schema)
- **Purpose:** Company identity resolution
- **Join Key:** `outreach_id` → `outreach.outreach`
- **Count:** ~53,000 records

---

## DISCONNECTED DATA: company.company_master

⚠️ **WARNING: This table does NOT connect to the outreach pipeline via outreach_id**

| Column | Type | Description |
|--------|------|-------------|
| `company_unique_id` | TEXT | Custom ID format: `04.04.01.xx.xxxxx.xxx` |
| `ein` | TEXT | EIN (23,430 records have this) |
| `website_url` | TEXT | Website URL |
| `company_name` | TEXT | Company name |

**Current Count:** 74,641 records  
**Source:** Clay imports (Dec 2025), Apollo import  
**ID Format:** `04.04.01.xx.xxxxx.xxx` (NOT UUIDs)

### Why It's Disconnected
- Uses a custom ID format incompatible with UUID-based `outreach_id`
- No `outreach_id` column exists
- Legacy import from Clay/Apollo before outreach pipeline was established

### Resolution
On 2026-01-27, we migrated EINs from `company.company_master` to `outreach.dol` via **domain matching**:
- Normalized domains on both sides (stripped `www.` prefix)
- Matched 18,026 EINs to outreach records
- Inserted 20,343 new records into `outreach.dol`
- See: [scripts/migrate_ein_to_dol.py](../scripts/migrate_ein_to_dol.py)

### Remaining Unmatched
~5,400 EINs in company.company_master cannot be matched because the companies don't exist in the 51K outreach pipeline. These are primarily:
- `.org` domains (non-profits)
- `.gov` domains (government)
- `.edu` domains (universities)
- Credit unions and similar entities

---

## Canonical Join Patterns

### Get company with EIN
```sql
SELECT 
    o.outreach_id,
    o.company_name,
    o.domain,
    d.ein,
    ct.industry_code
FROM outreach.outreach o
LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
WHERE d.ein IS NOT NULL;
```

### Get full company profile
```sql
SELECT 
    o.outreach_id,
    o.company_name,
    o.domain,
    d.ein,
    d.filing_present,
    d.funding_type,
    ct.*,
    b.blog_url
FROM outreach.outreach o
LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
LEFT JOIN outreach.blog b ON b.outreach_id = o.outreach_id;
```

---

## Foreign Key Constraints

All sub-hubs have foreign key constraints to the spine:

```sql
-- Example from outreach.dol
FOREIGN KEY (outreach_id) REFERENCES outreach.outreach(outreach_id) ON DELETE CASCADE
```

This ensures:
- Referential integrity
- Cascade deletes (if outreach record deleted, sub-hub records deleted)
- No orphaned records in sub-hubs

---

## Schema Ownership by Table

| Schema | Table | Owner | Purpose |
|--------|-------|-------|---------|
| outreach | outreach | Outreach Pipeline | Spine/Master |
| outreach | company_target | Outreach Pipeline | Company targeting |
| outreach | dol | Outreach Pipeline | DOL/EIN data |
| outreach | blog | Outreach Pipeline | Blog tracking |
| outreach | people | Outreach Pipeline | People contacts |
| outreach | bit_scores | Outreach Pipeline | Scoring |
| people | company_slot | People Pipeline | Slot assignments |
| people | people_master | People Pipeline | People master |
| cl | company_identity | CL Pipeline | Identity resolution |
| company | company_master | **LEGACY** | Clay/Apollo import |

---

## Data Quality Metrics (as of 2026-01-27)

| Metric | Value |
|--------|-------|
| Total outreach records | 52,771 |
| Records with EIN | 34,173 (64.8%) |
| Unique EINs | 18,026 |
| company_target coverage | 51,180 (97.0%) |
| blog coverage | 52,771 (100%) |

---

## Prohibited Patterns

❌ **Never join via domain directly** - Always use `outreach_id`
❌ **Never assume company_master connects** - It uses different IDs  
❌ **Never create cross-schema joins without outreach_id** - Breaks referential integrity
❌ **Never store outreach data in company schema** - Wrong ownership

---

## Migration History

| Date | Migration | Records | Script |
|------|-----------|---------|--------|
| 2026-01-27 | EIN from company_master to outreach.dol | +20,343 | `scripts/migrate_ein_to_dol.py` |

---

## Audit Scripts

Located in `scripts/`:

| Script | Purpose |
|--------|---------|
| `audit_join_paths.py` | Audit table structures and join keys |
| `audit_join_paths_v2.py` | Extended audit with counts |
| `investigate_74k.py` | Investigated company_master origin |
| `ein_bridge_analysis.py` | Initial EIN matching analysis |
| `full_ein_analysis.py` | Full EIN coverage analysis |
| `investigate_5227.py` | Found www. domain mismatch issue |
| `fixed_ein_matching.py` | Fixed domain normalization |
| `migrate_ein_to_dol.py` | Production EIN migration |
