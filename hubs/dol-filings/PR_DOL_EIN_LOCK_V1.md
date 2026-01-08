# PR: DOL EIN Lock-In Backfill v1.0

**Tag**: `dol-ein-lock-v1.0`
**Commit**: `c4fa5ad`
**Date**: 2026-01-07
**Author**: Agent (DOL_EIN_BACKFILL_V1)

---

## Summary

One-time deterministic backfill to populate `dol.ein_linkage` table, locking `outreach_id → EIN` bindings using existing Form 5500 data only.

---

## Changes

### Files Added

| File | Purpose |
|------|---------|
| `hubs/dol-filings/imo/middle/dol_ein_backfill.py` | Main backfill script |

### Files Updated

| File | Changes |
|------|---------|
| (none) | First-time implementation |

---

## Execution Results

| Metric | Count |
|--------|-------|
| Outreach IDs scanned | 60,577 |
| **Linked successfully** | **9,365** (15.5%) |
| Missing EIN | 51,192 |
| Ambiguous EIN | 20 |

### Database Writes

| Table | Rows | Purpose |
|-------|------|---------|
| `dol.ein_linkage` | 9,365 | Successful EIN bindings |
| `shq.error_master` | 51,212 | Failed resolutions |

---

## IMO Compliance

### Input (I)

- ✅ Loads from `outreach.outreach` spine
- ✅ Joins via `cl.company_identity_bridge`
- ✅ Resolves to `company.company_master.company_unique_id`
- ✅ Filters by target states (WV, VA, PA, MD, OH, KY, DE, NC)

### Middle (M)

- ✅ Priority 1: `company_master.ein` (direct EIN)
- ✅ Priority 2: `form_5500.sponsor_dfe_ein` (exact name match)
- ✅ Canonical rule: 0 EIN = FAIL, 1 EIN = PASS, 2+ EIN = FAIL
- ✅ No fuzzy logic
- ✅ No retries

### Output (O)

- ✅ PASS → `dol.ein_linkage`
- ✅ FAIL → `shq.error_master`
- ✅ Hash-based deduplication
- ✅ All required columns populated

---

## Doctrine Compliance

| Rule | Status |
|------|--------|
| No fuzzy logic | ✅ Exact match only |
| No AIR | ✅ No automated resolution |
| Errors only | ✅ Failures to shq.error_master |
| Single-pass | ✅ No retry loops |
| Deterministic | ✅ Same input → same output |
| IMO structure | ✅ Input → Middle → Output |

---

## Testing

### Dry Run

```bash
python hubs/dol-filings/imo/middle/dol_ein_backfill.py
```

Output:
```
DOL EIN LOCK-IN BACKFILL COMPLETE (DRY RUN)
Outreach IDs scanned:   60577
Linked successfully:    9365
Missing EIN:            51192
Ambiguous EIN:          20
```

### Production Run

```bash
python hubs/dol-filings/imo/middle/dol_ein_backfill.py --confirm
```

Output:
```
DOL EIN LOCK-IN BACKFILL COMPLETE
Outreach IDs scanned:   60577
Linked successfully:    9365
Missing EIN:            51192
Ambiguous EIN:          20
Rows inserted:
  - dol.ein_linkage:    9365
  - shq.error_master:   51212
✓ All safety assertions passed
```

### Verification

```sql
SELECT COUNT(*) FROM dol.ein_linkage;  -- 9365
SELECT COUNT(*) FROM shq.error_master WHERE agent_id = 'DOL_EIN_BACKFILL_V1';  -- 51212
SELECT source, COUNT(*) FROM dol.ein_linkage GROUP BY source;  -- BACKFILL_5500_V1: 9365
```

---

## Rollback Plan

If rollback is needed:

```sql
-- Remove backfill data
DELETE FROM dol.ein_linkage WHERE source = 'BACKFILL_5500_V1';
DELETE FROM shq.error_master WHERE agent_id = 'DOL_EIN_BACKFILL_V1';
```

---

## Related Artifacts

| Artifact | Reference |
|----------|-----------|
| PRD | `hubs/dol-filings/PRD.md` |
| ADR | `hubs/dol-filings/ADR.md` (ADR-DOL-002) |
| ERD | `hubs/dol-filings/imo/DOL_SUBHUB_ERD.md` |
| Checklist | `hubs/dol-filings/CHECKLIST.md` |
| Tag | `dol-ein-lock-v1.0` |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Author | Agent | 2026-01-07 |
| Reviewer | | |
| Approver | | |

---

## Post-Merge Actions

- [x] Tag created: `dol-ein-lock-v1.0`
- [x] Documentation updated
- [x] Verification completed
- [ ] Push to origin (pending)

---

**Last Updated**: 2026-01-08
