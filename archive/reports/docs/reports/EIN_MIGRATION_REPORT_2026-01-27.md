# EIN Migration Report

**Date:** 2026-01-27  
**Status:** COMPLETED  
**Author:** Automated Migration

---

## Executive Summary

Migrated 20,343 EIN records from `company.company_master` to `outreach.dol` via domain matching. This increased EIN coverage from 27% to 64.8% of the outreach pipeline.

---

## Problem Statement

The `company.company_master` table contained 23,430 EINs from Clay/Apollo imports, but these were **disconnected** from the main outreach pipeline because:

1. `company.company_master` uses a custom ID format (`04.04.01.xx.xxxxx.xxx`)
2. The outreach pipeline uses `outreach_id` (UUID) as the join key
3. No direct relationship existed between the tables

### Before Migration

| Metric | Value |
|--------|-------|
| outreach.outreach (spine) | 52,771 |
| outreach.dol records | 13,830 |
| outreach.dol with EIN | 13,830 |
| EIN coverage | 27.0% |
| company.company_master | 74,641 |
| company.company_master with EIN | 23,430 |

---

## Solution: Domain-Based Matching

Since both tables contain website/domain information, we matched records by **normalized domain**:

### Domain Normalization Logic

```sql
-- company.company_master (website_url field)
LOWER(REGEXP_REPLACE(
    REGEXP_REPLACE(
        REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),  -- Strip protocol + www.
        '/.*$', ''                                               -- Strip path
    ),
    '^www\.', ''                                                 -- Strip any remaining www.
))

-- outreach.outreach (domain field)  
LOWER(REGEXP_REPLACE(domain, '^www\.', ''))                     -- Strip www.
```

### Why Domain Normalization Was Necessary

The same company appeared differently in each table:
- `company.company_master`: `castotech.com`
- `outreach.outreach`: `www.castotech.com`

Without normalization, ~3,800 valid matches would have been missed.

---

## Migration Results

### After Migration

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| outreach.dol records | 13,830 | 34,173 | +20,343 |
| outreach.dol with EIN | 13,830 | 34,173 | +20,343 |
| Unique EINs | ~13,600 | 18,026 | +4,426 |
| EIN coverage | 27.0% | 64.8% | +37.8% |

### Breakdown

- **Matched EINs from company_master:** 18,026
- **Already in outreach.dol:** 13,627 (no insert needed)
- **NEW inserts:** 20,343 (includes duplicates from multi-location companies)
- **Unmatched:** ~5,400 (companies not in 51K pipeline)

---

## Unmatched Records Analysis

~5,400 EINs in `company.company_master` could not be matched because the companies don't exist in the outreach pipeline. These are:

| Domain Type | Reason |
|-------------|--------|
| `.org` | Non-profits not in target market |
| `.gov` | Government entities not in target market |
| `.edu` | Universities not in target market |
| Credit unions | Different industry vertical |

**Decision:** These records remain in `company.company_master` but are not migrated since they're outside the outreach target market.

---

## Migration Script

**Location:** `scripts/migrate_ein_to_dol.py`

### Key Features
- Raw string SQL to avoid regex escape issues
- Individual inserts with error handling
- Before/after verification
- No `ein_source` column (doesn't exist in schema)

### Execution Command
```bash
doppler run -- python scripts/migrate_ein_to_dol.py
```

### Execution Time
~11 minutes for 20,343 inserts

---

## Verification Queries

### Check current state
```sql
SELECT 
    COUNT(*) as total_dol,
    COUNT(ein) as with_ein,
    COUNT(DISTINCT ein) as unique_ein
FROM outreach.dol;
```

### Check coverage
```sql
SELECT 
    (SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL) as ein_count,
    (SELECT COUNT(*) FROM outreach.outreach) as total_outreach,
    ROUND(
        (SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL)::numeric / 
        (SELECT COUNT(*) FROM outreach.outreach) * 100, 
        1
    ) as coverage_pct;
```

---

## Related Documentation

- [Data Architecture](DATA_ARCHITECTURE.md) - Full join path documentation
- [scripts/migrate_ein_to_dol.py](../scripts/migrate_ein_to_dol.py) - Migration script
- [scripts/fixed_ein_matching.py](../scripts/fixed_ein_matching.py) - Matching analysis

---

## Lessons Learned

1. **Domain normalization is critical** - `www.` prefix differences caused significant match failures
2. **Legacy imports need audit** - `company.company_master` had no join path to the pipeline
3. **Don't assume ID compatibility** - Different ID formats (`04.04.01.xx` vs UUID) can't join
4. **Document disconnected data** - Mark tables that don't connect to prevent future confusion

---

## Future Recommendations

1. **Don't import to company.company_master** - Use outreach pipeline directly
2. **Always include outreach_id** - Any new data needs the canonical join key
3. **Normalize domains on ingress** - Strip `www.`, protocols, paths at import time
4. **Audit quarterly** - Check for disconnected data accumulating
