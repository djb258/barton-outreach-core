# ADR-TF-001: Talent Flow Legacy Code Quarantine

**Status:** ✅ ACCEPTED → PRODUCTION-READY
**Date:** 2026-01-08
**Production Release:** 2026-01-08
**Deciders:** Architecture Team
**Technical Story:** Talent Flow Doctrine Enforcement (TF-001)
**Certification ID:** TF-001 (ENFORCED)
**Author:** Claude Code (IMO-Creator)

---

## Context and Problem Statement

The Talent Flow system's `movement_engine` module was developed before the establishment of Talent Flow Doctrine v1.0.1. During CI enforcement implementation, the Talent Flow Guard detected **8 violations** in this legacy code.

The violations included:
1. **Forbidden Signal Emissions**: JOB_CHANGE, STARTUP, PROMOTION, LATERAL, COMPANY_CHANGE
2. **Scoring Logic in Sensor Module**: BIT score calculations within movement detection

These violations conflict with the core doctrine principle: **Talent Flow is a SENSOR, not an ACTOR.**

---

## Decision Drivers

1. **Doctrine Integrity**: TF-001 invariants must be enforced without exception
2. **CI Green Path**: Legacy violations should not block CI for new compliant code
3. **Audit Trail**: Preserve legacy code for reference and refactor planning
4. **Regression Prevention**: Prevent forbidden patterns from re-entering the codebase

---

## Considered Options

### Option 1: Fix Legacy Code In-Place

**Pros:**
- Immediate compliance
- No quarantine folder needed

**Cons:**
- High refactor risk
- May introduce regressions
- Delays CI enforcement

**Decision:** REJECTED

### Option 2: Delete Legacy Code

**Pros:**
- Immediate compliance
- Clean codebase

**Cons:**
- Loss of reference material
- No audit trail
- May need to rewrite from scratch

**Decision:** REJECTED

### Option 3: Quarantine Legacy Code (CHOSEN)

**Pros:**
- Immediate CI compliance (quarantined code excluded from scans)
- Preserves code for reference
- Clear audit trail
- Refactor can be scheduled separately

**Cons:**
- Additional folder to manage
- Must ensure no production imports

**Decision:** ACCEPTED

---

## Decision Outcome

**Chosen option:** "Quarantine Legacy Code"

The legacy `movement_engine` module has been moved to:
```
meta/legacy_quarantine/movement_engine/
```

### Quarantined Files

| File | Lines | Violations |
|------|-------|------------|
| `movement_engine.py` | 796 | TF-001-F (scoring logic) |
| `movement_rules.py` | 764 | TF-001-B (forbidden signals), TF-001-F (scoring) |
| `state_machine.py` | 600+ | Auxiliary to movement_engine |
| `__init__.py` | 27 | Module exports |

### Forbidden Signals Quarantined

| Signal | Doctrine Violation |
|--------|-------------------|
| `JOB_CHANGE` | TF-001-B |
| `STARTUP` | TF-001-B |
| `PROMOTION` | TF-001-B |
| `LATERAL` | TF-001-B |
| `COMPANY_CHANGE` | TF-001-B |

### Positive Consequences

- CI is green for all compliant code paths
- Doctrine guard scans exclude quarantine folder
- Regression test locks forbidden signals
- Legacy code preserved for refactor reference

### Negative Consequences

- Additional folder to maintain
- Must document quarantine clearly
- Import guards required

---

## Enforcement Measures

### 1. Quarantine Location

```
meta/legacy_quarantine/movement_engine/
├── README.md          # Quarantine documentation
├── movement_engine.py # QUARANTINED
├── movement_rules.py  # QUARANTINED
├── state_machine.py   # QUARANTINED
└── __init__.py        # QUARANTINED
```

### 2. Regression Lock

**File:** `ops/tests/test_forbidden_signals_never_return.py`

This test will FAIL if any of these signals appear in production code:
- JOB_CHANGE
- STARTUP
- PROMOTION
- LATERAL
- COMPANY_CHANGE

### 3. CI Exclusion

The quarantine folder is excluded from Talent Flow Guard scans:
- Path `meta/legacy_quarantine/**` is not in scan scope
- Only `hubs/people-intelligence/**` and related paths are scanned

---

## Technical Details

### Import Guard

The quarantined module is NOT imported by any production code:

```python
# REMOVED from hubs/people-intelligence/imo/middle/__init__.py
# from .movement_engine import MovementEngine  # QUARANTINED
```

### Permitted Signals (Per Doctrine)

| Signal | Purpose |
|--------|---------|
| `SLOT_VACATED` | Departure from company |
| `SLOT_BIND_REQUEST` | Arrival at known company |
| `COMPANY_RESOLUTION_REQUIRED` | Arrival at unknown company |
| `MOVEMENT_RECORDED` | Audit confirmation |

---

## Refactor Intent

When refactoring is scheduled:

1. **Signal Alignment**: Replace forbidden signals with doctrine-compliant signals
2. **Remove Scoring Logic**: Move BIT scoring to Company Target Hub (bit_engine.py)
3. **Phase Gate Structure**: Implement DETECT → RECON → SIGNAL phases
4. **Idempotency**: Add SHA256 deduplication hash

---

## Links

- **Doctrine:** `hubs/people-intelligence/imo/TALENT_FLOW_DOCTRINE.md`
- **CI Enforcement:** `hubs/people-intelligence/imo/TALENT_FLOW_CI_ENFORCEMENT.md`
- **Guard:** `ops/enforcement/talent_flow_guard.py`
- **Tests:** `ops/tests/test_talent_flow_doctrine.py`
- **Regression Lock:** `ops/tests/test_forbidden_signals_never_return.py`
- **Workflow:** `.github/workflows/talent_flow_guard.yml`

---

## Supersedes

This ADR establishes that:

1. Legacy `movement_engine` code is **NOT production code**
2. Forbidden signals are **permanently rejected** for Talent Flow
3. Scoring logic in Talent Flow is **permanently rejected**
4. Quarantine location is **official and documented**

---

**Approved By:** Architecture Team
**Date:** 2026-01-08
**Author:** Claude Code (IMO-Creator)
**Certification ID:** TF-001 (ENFORCED)
**Doctrine Version:** 1.0.1
**Status:** 🚀 PRODUCTION-READY
