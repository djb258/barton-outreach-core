# Legacy Quarantine: Movement Engine

**Quarantine Date:** 2026-01-08
**Certification ID:** TF-001
**Status:** QUARANTINED — Do Not Execute
**Refactor Deferred:** Yes

---

## Reason for Quarantine

This code was quarantined because it violates **Talent Flow Doctrine v1.0.1 (TF-001)**.

The Talent Flow Guard (ops/enforcement/talent_flow_guard.py) detected 8 violations in this module on 2026-01-08.

---

## Violated TF-001 Rules

### 1. Forbidden Signal Emissions (TF-001-B)

The `TalentFlowSignalType` enum in `movement_rules.py` defines signals that are **NOT PERMITTED** by doctrine:

| Signal | Line | Status |
|--------|------|--------|
| `JOB_CHANGE` | 550 | ❌ FORBIDDEN |
| `STARTUP` | 551 | ❌ FORBIDDEN |
| `PROMOTION` | 552 | ❌ FORBIDDEN |
| `LATERAL` | 553 | ❌ FORBIDDEN |
| `COMPANY_CHANGE` | 554 | ❌ FORBIDDEN |

**Permitted Signals (per TF-001):**
- `SLOT_VACATED`
- `SLOT_BIND_REQUEST`
- `COMPANY_RESOLUTION_REQUIRED`
- `MOVEMENT_RECORDED`

### 2. Forbidden Operations (TF-001-F)

The module contains **scoring logic** which violates the "Sensor Only" invariant:

| File | Line | Issue |
|------|------|-------|
| `movement_engine.py` | 87 | `current_bit_score: int = 0` |
| `movement_rules.py` | 494 | `met = bit_score >= threshold` |

**Doctrine Violation:** Talent Flow is a SENSOR, not an ACTOR. It must not perform scoring.

---

## Files Quarantined

| File | Lines | Purpose |
|------|-------|---------|
| `movement_engine.py` | 750+ | Core movement detection engine |
| `movement_rules.py` | 764 | Business rules with BIT scoring |
| `state_machine.py` | 600+ | Movement state management |
| `__init__.py` | 27 | Module exports |

---

## Import Status

**DISABLED:** This module is no longer imported by any production code.

The original import in `hubs/people-intelligence/imo/middle/__init__.py` was:
```python
from .movement_engine import MovementEngine  # REMOVED
```

---

## CI Enforcement

This directory is **excluded from Talent Flow Guard scans** because:
1. It is in `meta/legacy_quarantine/` (not in guard scan path)
2. It is preserved for reference only
3. Refactor is scheduled separately

---

## Refactor Intent

When refactoring is scheduled:

1. **Signal Alignment**: Replace forbidden signals with doctrine-compliant signals:
   - `JOB_CHANGE` → `SLOT_VACATED` + `SLOT_BIND_REQUEST`
   - `PROMOTION` → Movement event (not signal)
   - `LATERAL` → Movement event (not signal)
   - etc.

2. **Remove Scoring Logic**: Move BIT scoring to Company Target Hub (bit_engine.py)

3. **Phase Gate Structure**: Implement DETECT → RECON → SIGNAL phases

4. **Idempotency**: Add SHA256 deduplication hash

---

## Regression Lock

A regression test exists to prevent these forbidden signals from re-entering the codebase:

```
ops/tests/test_forbidden_signals_never_return.py
```

This test will FAIL if any of the forbidden signals appear in:
- Signal registries
- Emit calls
- Enum definitions
- Constants

---

## Do NOT

- ❌ Import this module in production code
- ❌ Fix violations here (do in new module)
- ❌ Delete without refactor complete
- ❌ Use as reference for new implementations
- ❌ Copy-paste code from here

---

## Contact

For refactor questions, refer to:
- Talent Flow Doctrine: `hubs/people-intelligence/imo/TALENT_FLOW_DOCTRINE.md`
- CI Enforcement: `hubs/people-intelligence/imo/TALENT_FLOW_CI_ENFORCEMENT.md`
- Certification ID: TF-001

---

**Quarantined By:** Claude Code (Refactor Containment Engineer)
**Quarantine Date:** 2026-01-08
**Review Date:** On refactor scheduling
