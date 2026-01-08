---
id: dol-backfill-v1
title: DOL EIN Backfill v1.0
desc: One-time deterministic EIN backfill execution record
updated: 2026-01-08
created: 2026-01-07
tags:
  - dol
  - backfill
  - ein
  - execution
---

# DOL EIN Backfill v1.0

## Execution Summary

| Field | Value |
|-------|-------|
| **Tag** | `dol-ein-lock-v1.0` |
| **Commit** | `c4fa5ad` |
| **Executed** | 2026-01-07 |
| **Process ID** | 01.04.02.04.22000 |
| **Agent ID** | DOL_EIN_BACKFILL_V1 |

## Results

| Metric | Count |
|--------|-------|
| Outreach IDs scanned | 60,577 |
| **Linked successfully** | **9,365** (15.5%) |
| Missing EIN | 51,192 |
| Ambiguous EIN | 20 |

## Database Writes

| Table | Rows | Purpose |
|-------|------|---------|
| `dol.ein_linkage` | 9,365 | Successful EIN bindings |
| `shq.error_master` | 51,212 | Failed resolutions |

## Join Path

```
outreach.outreach.sovereign_id
    ↓
cl.company_identity_bridge.company_sov_id
    ↓
cl.company_identity_bridge.source_company_id
    ↓
company.company_master.company_unique_id
    ↓
company.company_master.ein (Priority 1)
    OR
dol.form_5500.sponsor_dfe_ein (Priority 2)
```

## Target States

- WV, VA, PA, MD, OH, KY, DE, NC

## Compliance

| Rule | Status |
|------|--------|
| No fuzzy logic | ✅ |
| No AIR | ✅ |
| Errors only | ✅ |
| Single-pass | ✅ |
| Deterministic | ✅ |

## Script

```
hubs/dol-filings/imo/middle/dol_ein_backfill.py
```

### Dry Run
```bash
python hubs/dol-filings/imo/middle/dol_ein_backfill.py
```

### Production Run
```bash
python hubs/dol-filings/imo/middle/dol_ein_backfill.py --confirm
```

## Rollback

```sql
DELETE FROM dol.ein_linkage WHERE source = 'BACKFILL_5500_V1';
DELETE FROM shq.error_master WHERE agent_id = 'DOL_EIN_BACKFILL_V1';
```

## Future Work

| Task | Owner | Priority |
|------|-------|----------|
| EIN Enrichment Hub | Enrichment Team | Medium |
| Manual resolution (20 ambiguous) | Data Team | Low |

## Links

- [[dol-subhub]] - Parent hub
- [[dol-ein-linkage]] - Output table
- [[shq-error-master]] - Error table
