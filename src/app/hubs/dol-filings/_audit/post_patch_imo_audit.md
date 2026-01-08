# DOL Sub-Hub IMO Patch Audit — v1.1 Error-Only Enforcement

> **Document Version**: 1.1
> **Audit Date**: 2026-01-07
> **Process ID**: `01.04.02.04.22000`
> **Agent ID**: `DOL_EIN_SUBHUB`

---

## Doctrine Statement

> **The DOL Sub-Hub emits facts only.**
> **All failures are DATA DEFICIENCIES, not system failures.**
> **Therefore, the DOL Sub-Hub NEVER writes to AIR.**

---

## Executive Summary

This audit confirms the implementation of **IMO Doctrine v1.1 (Error-Only Enforcement)** for the DOL Sub-Hub:

| Requirement | Status |
|-------------|--------|
| AIR logging is FORBIDDEN | ✅ Enforced |
| All failures → shq.error_master ONLY | ✅ Implemented |
| Geographic filtering (8 states) | ✅ Implemented |
| Suppression key for deduplication | ✅ Implemented |
| No BIT signals | ✅ Enforced |
| No CL writes | ✅ Enforced |

---

## Key Changes from v1.0

| v1.0 | v1.1 |
|------|------|
| Dual-write: AIR + error_master | Error-only: shq.error_master ONLY |
| `write_air_info_event()` for facts | Direct table writes, no AIR |
| No geographic filter | 8-state scope filter |
| No suppression key | Suppression key for dedup |

---

## Files Modified

### [error_writer.py](../imo/output/error_writer.py)

**Changes**:
- Removed ALL AIR logging functions
- Added `write_error_master()` as sole error handler
- Added `generate_suppression_key()` for deduplication
- Added `is_in_scope()` geographic filter
- Added `TARGET_STATES` constant (8 states)
- Added `normalize_ein()` utility
- Added `write_air()` trap that raises RuntimeError

### [doctrine_guards.py](../imo/middle/doctrine_guards.py)

**Changes**:
- Updated docstring to v1.1 doctrine
- Removed `dol.air_log` from `_ALLOWED_DOL_TABLES`
- Added `assert_no_air_logging()` guard
- Added `_AIR_PATTERNS` regex list
- Updated `execute_with_guards()` to include AIR check

### [dol_hub.py](../imo/middle/dol_hub.py)

**Changes**:
- Updated docstring to v1.1 doctrine
- Changed import from `write_air_info_event` to `write_error_master`
- Removed all `write_air_info_event()` calls
- Added `skipped_out_of_scope` stat
- Changed `facts_logged` to `errors_written` stat
- Facts now stored directly in dol.* tables

### [pipeline.md](../pipeline.md)

**Changes**:
- Updated to v1.1 doctrine banner
- Changed OUTPUT section to show error-only pattern
- Added "AIR LOGGING IS FORBIDDEN" warning box
- Added Geographic Scope section

### [dol_imo_guards.sh](../\_audit/dol_imo_guards.sh)

**Changes**:
- Updated to v1.1 (Error-Only)
- Added GUARD 3: No AIR logging (FORBIDDEN)
- Added GUARD 7: Suppression key check
- Updated doctrine summary

---

## IMO Enforcement Boundaries (v1.1)

```
┌─────────────────────────────────────────────────────────────┐
│             DOL Sub-Hub IMO Doctrine v1.1                    │
│               (Error-Only Enforcement)                       │
└─────────────────────────────────────────────────────────────┘

READ OPERATIONS (Allowed):
  ✓ company.company_master — EIN lookup only

WRITE OPERATIONS (Allowed):
  ✓ dol.form_5500 — Append-only facts
  ✓ dol.schedule_a — Append-only facts
  ✓ dol.ein_linkage — Append-only (for CL consumption)
  ✓ dol.violations — Append-only facts
  ✓ shq.error_master — Errors ONLY

FORBIDDEN OPERATIONS:
  ✗ dol.air_log — AIR IS FORBIDDEN
  ✗ UPDATE company.company_master — CL sovereignty
  ✗ INSERT company.company_master — CL sovereignty
  ✗ DELETE company.company_master — CL sovereignty
  ✗ BIT signal emission — Facts-only spoke
  ✗ New company identity minting — CL sovereignty
```

---

## Geographic Scope

DOL processes **only 8 target states**:

| State | Code | Region |
|-------|------|--------|
| West Virginia | WV | Appalachian |
| Virginia | VA | Mid-Atlantic |
| Pennsylvania | PA | Mid-Atlantic |
| Maryland | MD | Mid-Atlantic |
| Ohio | OH | Midwest |
| Kentucky | KY | Appalachian |
| Delaware | DE | Mid-Atlantic |
| North Carolina | NC | Southeast |

**Out-of-scope records**: Silently skipped (no error, no counter, no AIR).

---

## Error Handling Pattern

```python
# CORRECT: Write to error_master ONLY
write_error_master(
    conn,
    error_code=DOLErrorCode.EIN_UNRESOLVED,
    message="Cannot resolve EIN",
    ein_raw=record.plan_ein,
    ein_normalized=normalize_ein(record.plan_ein),
    state=record.state,
    filing_year=record.year,
    eligible_for_enrichment=True,
)

# FORBIDDEN: These will raise RuntimeError
write_air(...)           # ❌ TRAP
write_air_log(...)       # ❌ TRAP  
write_air_info_event(...) # ❌ TRAP
```

---

## CI Regression Guards

The `dol_imo_guards.sh` script runs 7 guards:

| Guard | Check |
|-------|-------|
| 1 | No CL writes (`company_master`) |
| 2 | No BIT integration |
| 3 | **No AIR logging (FORBIDDEN)** |
| 4 | `doctrine_guards.py` exists with AIR prohibition |
| 5 | `error_writer.py` exists with AIR trap |
| 6 | No forbidden marketing writes |
| 7 | **Suppression key in error handling** |

**Usage**:
```bash
bash hubs/dol-filings/_audit/dol_imo_guards.sh
```

---

## Suppression Key

Errors are deduplicated using a suppression key:

```python
suppression_key = hash(ein_raw + state + filing_year + error_code)
```

Same (EIN, state, year, error) = same key = deduplicated.

---

## Migration Checklist

- [ ] Run migration: `003_create_shq_error_master.sql`
- [ ] Verify `shq.error_master` table exists
- [ ] Run CI guard: `bash hubs/dol-filings/_audit/dol_imo_guards.sh`
- [ ] Confirm all 7 guards pass
- [ ] Verify no AIR references in DOL code
- [ ] Tag release: `dol-imo-v1.1`

---

## Sign-Off

| Role | Name | Date |
|------|------|------|
| Doctrine Auditor | Claude (Barton) | 2026-01-07 |
| Process Owner | DOL Sub-Hub | — |
| CL Owner | Company Lifecycle | — |

---

**DOL Sub-Hub v1.1 (Error-Only)** — AIR is FORBIDDEN
