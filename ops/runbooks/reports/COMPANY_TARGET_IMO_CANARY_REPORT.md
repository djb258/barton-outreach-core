# Company Target IMO Canary Run Report

**Date**: 2026-01-07
**Branch**: `cc-purification/v1.1.0`
**PRD**: Company Target (Execution Prep Sub-Hub) v3.0
**Doctrine**: Spine-First Architecture

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Canary Size** | 100 IDs |
| **PASS** | 93 (93%) |
| **FAIL** | 7 (7%) |
| **Duration** | 66.2 seconds |
| **Rate** | 1.51 records/sec |
| **Validation** | **8/8 PASS** |

**Status**: CANARY VALIDATED - Ready for production run

---

## Canary Selection Criteria

| Domain Type | Target | Actual |
|-------------|--------|--------|
| .com | 40 | 40 |
| .io | 20 | 20 |
| .org | 20 | 20 |
| Other | 20 | 20 |
| **Total** | 100 | 100 |

---

## Validation Checklist

| # | Check | Result |
|---|-------|--------|
| 1 | All IDs processed | PASS (100/100) |
| 2 | PASS records have required fields | PASS (93/93) |
| 3 | FAILs in error table | PASS (7/7) |
| 4 | Error codes valid | PASS |
| 5 | Waterfall progression | PASS |
| 6 | Method types present | PASS |
| 7 | Confidence range valid | PASS |
| 8 | No sovereign_id leakage | PASS |

---

## Results Distribution

### Waterfall State
| State | Count | Percentage |
|-------|-------|------------|
| PENDING_DOL | 93 | 93% |
| PENDING_CT | 7 | 7% |

### Error Codes (for FAILs)
| Code | Count | Description |
|------|-------|-------------|
| CT-M-NO-MX | 7 | Domain has no MX records |

### Method Type Distribution
| Type | Count |
|------|-------|
| first.last | 93 |

### Confidence Score
| Metric | Value |
|--------|-------|
| Min | 0.70 |
| Max | 0.70 |
| Avg | 0.70 |

> Note: Confidence is 0.70 for all because this was an MX-only run (SMTP blocked in test environment). Production runs with full SMTP verification will have varied confidence scores.

---

## Pipeline Flow Verified

```
INPUT STAGE (I)
├── Load from outreach.outreach spine    ✓
├── Validate domain present              ✓
└── Check not already processed          ✓

MIDDLE STAGE (M)
├── MX Lookup (TOOL-004)                 ✓
├── Pattern Generation                   ✓
└── SMTP Validation (blocked*)           —

OUTPUT STAGE (O)
├── PASS → outreach.company_target       ✓
└── FAIL → outreach.company_target_errors ✓
```

*SMTP port 25 blocked in test environment. Full SMTP validation requires server environment.

---

## Schema Migrations Applied

1. **2026-01-07-company-target-imo-columns.sql**
   - Added `domain` to `outreach.outreach`
   - Added `email_method`, `method_type`, `confidence_score`, `execution_status`, `imo_completed_at`, `is_catchall` to `outreach.company_target`

2. **2026-01-08-outreach-context-view.sql**
   - Created `outreach.v_context_current` read-only view

3. **Schema Fix**
   - Made `company_unique_id` nullable (doctrine: operate on `outreach_id` only)

---

## Doctrine Compliance

| Rule | Status |
|------|--------|
| Operates ONLY on outreach_id | ✓ |
| NEVER references sovereign_id | ✓ |
| NEVER mints IDs | ✓ |
| NO fuzzy matching | ✓ |
| NO retries | ✓ |
| FAIL is terminal | ✓ |

---

## Production Run Estimates

| Metric | Value |
|--------|-------|
| Records to process | ~45,609 (PENDING_CT) |
| Estimated duration | ~8.4 hours at 1.5/sec |
| Recommended batch size | 1,000/batch |

### Recommendations for Production

1. **Run in server environment** with SMTP port 25 open for full email pattern discovery
2. **Use batch processing** to allow monitoring and restart capability
3. **Schedule during off-peak hours** to minimize API throttling impacts
4. **Monitor error rate** - expect ~5-10% NO_MX failures

---

## Files Created

| File | Purpose |
|------|---------|
| `ops/runbooks/sql/select_company_target_canary.sql` | Canary selection query |
| `temp_canary_ids.txt` | Canary ID list |
| `temp_canary_fast.py` | MX-only canary runner |
| `temp_canary_validate.py` | Validation script |

---

## Next Steps

1. [ ] Merge PR #9 to main (CI guards active)
2. [ ] Schedule full production run in server environment
3. [ ] Create production run script with batching
4. [ ] Monitor and generate production run report

---

**Prepared by**: Claude Code
**Reviewed by**: Pending
**Approved for Production**: Pending
