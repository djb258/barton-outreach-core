# Talent Flow CI Enforcement — TF-001

## Overview

This directory contains CI enforcement for Talent Flow Doctrine v1.0.1.

**Certification ID:** TF-001
**Status:** ✅ CERTIFIED
**Date:** 2026-01-08

---

## Enforcement Components

### 1. Static Analysis Guard

**File:** `ops/enforcement/talent_flow_guard.py`

Scans Talent Flow code paths for doctrine violations:

| Check | Invariant | Failure Condition |
|-------|-----------|-------------------|
| TF-001-A | Sensor Only | Write to forbidden table |
| TF-001-B | Signal Authority | Emit unauthorized signal |
| TF-001-C | Phase-Gated | Phase order violation |
| TF-001-D | Binary Outcome | Non-binary completion state |
| TF-001-E | Idempotent | Missing deduplication |
| TF-001-F | No Acting | Forbidden operation detected |
| TF-001-G | Kill Switch | Missing HALT check |

**Usage:**
```bash
# Human-readable report
python ops/enforcement/talent_flow_guard.py --path .

# CI mode (GitHub Actions annotations)
python ops/enforcement/talent_flow_guard.py --path . --ci

# JSON output
python ops/enforcement/talent_flow_guard.py --path . --json
```

---

### 2. GitHub Actions Workflow

**File:** `.github/workflows/talent_flow_guard.yml`

Runs on every PR touching:
- `hubs/people-intelligence/**`
- `spokes/company-people/**`
- `spokes/people-outreach/**`
- `ops/enforcement/**`

**Jobs:**
1. **static-analysis** — Scans for forbidden patterns
2. **doctrine-tests** — Runs pytest test suite
3. **certification-check** — Verifies doctrine document exists and is certified

---

### 3. Doctrine Test Suite

**File:** `ops/tests/test_talent_flow_doctrine.py`

Validates invariants via pytest:

| Test Class | Invariant |
|------------|-----------|
| `TestIdempotencyEnforcement` | Same movement cannot insert twice |
| `TestBinaryCompletionState` | PROMOTED or QUARANTINED only |
| `TestKillSwitchEnforcement` | HALT behavior, not SKIP |
| `TestPhaseGateEnforcement` | DETECT → RECON → SIGNAL |
| `TestWriteAuthorityEnforcement` | Only permitted tables |
| `TestSignalAuthorityEnforcement` | Only permitted signals |
| `TestForbiddenOperations` | No minting, enrichment, scoring |
| `TestFullFlowIntegration` | End-to-end flow validation |

**Run Tests:**
```bash
pytest ops/tests/test_talent_flow_doctrine.py -v
```

---

## Hard Constraints (NON-NEGOTIABLE)

### Permitted Tables

| Table | Schema |
|-------|--------|
| `person_movement_history` | `people` |
| `people_errors` | `people` |

**All other tables are FORBIDDEN for Talent Flow writes.**

### Permitted Signals

| Signal | Purpose |
|--------|---------|
| `SLOT_VACATED` | Departure from company |
| `SLOT_BIND_REQUEST` | Arrival at known company |
| `COMPANY_RESOLUTION_REQUIRED` | Arrival at unknown company |
| `MOVEMENT_RECORDED` | Audit confirmation |

**All other signals are FORBIDDEN.**

### Valid Outcomes

| Outcome | Condition |
|---------|-----------|
| `PROMOTED` | All phase gates passed |
| `QUARANTINED` | Any phase gate failed |

**No third state. No partial completion.**

### Required Phase Order

```
DETECT → RECON → SIGNAL
```

**No skipping. No reordering.**

---

## Failure Messages

All violations produce structured error messages:

```
[TF-001] VIOLATION_TYPE: Description | Invariant: invariant_name
```

Example:
```
::error file=hubs/people-intelligence/movement.py,line=42::[TF-001] FORBIDDEN_TABLE_WRITE: INSERT to forbidden table: company_master | Invariant: Sensor Only — TF writes ONLY to person_movement_history and people_errors
```

---

## Kill Switch

| Variable | Default | Behavior |
|----------|---------|----------|
| `PEOPLE_MOVEMENT_DETECT_ENABLED` | `true` | **HALT** when false |

When disabled, Talent Flow must HALT execution entirely — not silently skip.

---

## Doctrine Reference

Full doctrine: [TALENT_FLOW_DOCTRINE.md](./TALENT_FLOW_DOCTRINE.md)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   TALENT FLOW IS A SENSOR, NOT AN ACTOR                                       ║
║                                                                               ║
║   "We are not tracking people.                                                ║
║    We are tracking where executive pressure appears and disappears."          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Legacy Quarantine

### Overview

On 2026-01-08, the Talent Flow Guard detected **8 violations** in the legacy `movement_engine` module. These violations were **by design** — the code predates TF-001 doctrine certification.

Rather than blocking all CI or loosening enforcement, the violating code was **quarantined**.

### Quarantine Location

```
meta/legacy_quarantine/movement_engine/
```

| File | Violations |
|------|------------|
| `movement_rules.py` | 6 (forbidden signals, scoring logic) |
| `movement_engine.py` | 2 (scoring logic) |
| `state_machine.py` | 0 (auxiliary) |

### Forbidden Signals Quarantined

| Signal | Status |
|--------|--------|
| `JOB_CHANGE` | ❌ QUARANTINED |
| `STARTUP` | ❌ QUARANTINED |
| `PROMOTION` | ❌ QUARANTINED |
| `LATERAL` | ❌ QUARANTINED |
| `COMPANY_CHANGE` | ❌ QUARANTINED |

These signals violated TF-001-B (Signal Authority) and were moved out of production paths.

### Regression Lock

A regression test prevents these signals from re-entering:

**File:** `ops/tests/test_forbidden_signals_never_return.py`

This test will FAIL if any forbidden signal appears in:
- Signal registries
- Emit calls
- Enum definitions
- Constants

### Refactor Status

| Item | Status |
|------|--------|
| Code quarantined | ✅ Complete |
| Regression test added | ✅ Complete |
| CI guard updated | ✅ Complete |
| Refactor scheduled | ⏳ Deferred |

### Intent Statement

> Violations were detected by design, not by accident.
> The legacy code was written before TF-001 certification.
> Refactor is scheduled separately and will not loosen doctrine constraints.

---

**Last Updated:** 2026-01-08
**Certification ID:** TF-001
**Doctrine Version:** 1.0.1
