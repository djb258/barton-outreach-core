# LIVE SYSTEM STATE

**Date:** 2026-01-20  
**Author:** System Automation  
**Status:** PRODUCTION LIVE

---

## WHAT IS LIVE

| Component | Status | Description |
|-----------|--------|-------------|
| `outreach.hub_registry` | ✅ LIVE | 6 hubs registered (4 required, 2 optional) |
| `outreach.company_hub_status` | ✅ LIVE | 135,684 rows (33,921 companies × 4 hubs) |
| `outreach.manual_overrides` | ✅ LIVE | Kill switch table, 0 active overrides |
| `outreach.vw_sovereign_completion` | ✅ LIVE | Real-time completion status |
| `outreach.vw_marketing_eligibility` | ✅ LIVE | Tier computation |
| `outreach.vw_marketing_eligibility_with_overrides` | ✅ LIVE | Override-aware tiers |
| `outreach.bit_scores` | ✅ LIVE | BIT scores for 33,921 companies |
| Company Target Hub | ✅ LIVE | All companies at PASS |
| BIT Gate | ✅ LIVE | Scores computed, gate active |

---

## WHAT IS DEFERRED

| Component | Status | Reason |
|-----------|--------|--------|
| DOL Enrichment Hub | ⏸️ DEFERRED | Awaiting DOL filing data pipeline |
| People Intelligence Hub | ⏸️ DEFERRED | Awaiting people data enrichment |
| Talent Flow Hub | ⏸️ DEFERRED | Awaiting movement signal pipeline |
| Blog Content Hub | ⏸️ DEFERRED | Optional hub, low priority |

**Note:** All deferred hubs are initialized at `IN_PROGRESS` status. Companies cannot advance past Tier 0 until these hubs are activated.

---

## WHAT IS FORBIDDEN

### DO NOT MODIFY without audit approval:

| Resource | Reason |
|----------|--------|
| `outreach.hub_registry` | Hub definitions are static |
| `outreach.vw_sovereign_completion` | Core completion logic |
| `outreach.vw_marketing_eligibility` | Tier computation formula |
| `outreach.vw_marketing_eligibility_with_overrides` | Override enforcement |
| Kill switch SQL functions | `set_marketing_override()`, `remove_marketing_override()` |
| IMO middle layer contracts | `hubs/*/imo/middle/hub_status.py` |

### NO WRITES allowed from:

| Path | Enforcement |
|------|-------------|
| `spokes/` | MutationGuardViolation |
| `ctb/ui/` | MutationGuardViolation |
| `ops/` | MutationGuardViolation |
| `scripts/` | MutationGuardViolation |
| `src/` | MutationGuardViolation |
| `enrichment-hub/` | MutationGuardViolation |
| `integrations/` | MutationGuardViolation |

---

## WHERE TRUTH LIVES

### Authoritative Tables

| Table | Truth For |
|-------|-----------|
| `outreach.company_hub_status` | Which hubs are complete for which companies |
| `outreach.manual_overrides` | Kill switches and tier caps |
| `outreach.hub_registry` | Hub definitions and requirements |
| `outreach.bit_scores` | BIT intent scores |

### Authoritative Views

| View | Truth For |
|------|-----------|
| `outreach.vw_sovereign_completion` | Overall completion status per company |
| `outreach.vw_marketing_eligibility_with_overrides` | **THE** marketing eligibility source |

### DO NOT read from:

- Raw hub tables directly for marketing decisions
- Any view without `_with_overrides` suffix for production use
- Cached/derived tables that may be stale

---

## SANCTIONED WRITERS

Only these code paths may write to sovereign tables:

```
hubs/*/imo/middle/hub_status.py   → company_hub_status
infra/migrations/*.sql             → Schema changes only
SQL: set_marketing_override()      → manual_overrides
SQL: remove_marketing_override()   → manual_overrides
```

Everything else is READ-ONLY.

---

## CURRENT STATE SNAPSHOT

| Metric | Value |
|--------|-------|
| Total Companies | 33,921 |
| Companies at Tier 0 | 33,921 (100%) |
| Companies at Tier 1+ | 0 (0%) |
| Active Overrides | 0 |
| BIT Scores Computed | 33,921 |
| Avg BIT Score | ~8.5 |

---

## MUTATION GUARD

Test: `tests/guards/test_no_illegal_writers.py`

This test statically scans the codebase for any code that attempts to write to sovereign tables outside of sanctioned IMO middle layers. Run before every deployment.

```bash
python -m pytest tests/guards/test_no_illegal_writers.py -v
```

---

## SMOKE TEST

Script: `ops/smoke_test.py`

Validates end-to-end pipeline by:
1. Picking 5 random companies
2. Reading completion + eligibility views
3. Running safety gate in dry-run
4. Logging to audit

```bash
python ops/smoke_test.py
```

---

## AUDIT TRAIL

All system actions logged to `shq.audit_log`:
- Error hygiene runs
- Smoke test results
- Override changes (via SQL functions)

---

**END OF LIVE SYSTEM STATE**
