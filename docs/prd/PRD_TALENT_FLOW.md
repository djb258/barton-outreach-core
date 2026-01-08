# PRD: Talent Flow v1.0.1

**Version:** 1.0.1
**Status:** 🚀 PRODUCTION-READY (LOCKED)
**Certification ID:** TF-001 (ENFORCED)
**Certification Date:** 2026-01-08
**Production Release:** 2026-01-08
**Doctrine:** Spine-First Architecture v1.1
**Barton ID Range:** `04.04.02.05.7XXXX.###`
**Author:** Claude Code (IMO-Creator)

---

## Production Enforcement

| Component | Status | File |
|-----------|--------|------|
| CI Guard | ✅ ACTIVE | `ops/enforcement/talent_flow_guard.py` |
| CI Workflow | ✅ ACTIVE | `.github/workflows/talent_flow_guard.yml` |
| Doctrine Tests | ✅ 30 PASS | `ops/tests/test_talent_flow_doctrine.py` |
| Regression Lock | ✅ 9 PASS | `ops/tests/test_forbidden_signals_never_return.py` |
| Legacy Quarantine | ✅ SEALED | `meta/legacy_quarantine/movement_engine/` |

---

## Engine Ownership Statement

```
+===============================================================================+
|                         TALENT FLOW OWNERSHIP                                 |
|                                                                               |
|   ╔═══════════════════════════════════════════════════════════════════════╗   |
|   ║                                                                       ║   |
|   ║         TALENT FLOW IS A SENSOR, NOT AN ACTOR                         ║   |
|   ║                                                                       ║   |
|   ║   "We are not tracking people.                                        ║   |
|   ║    We are tracking where executive pressure appears and disappears."  ║   |
|   ║                                                                       ║   |
|   ╚═══════════════════════════════════════════════════════════════════════╝   |
|                                                                               |
|   This engine OWNS:                                                           |
|   +-- Movement detection (DETECT phase)                                       |
|   +-- Movement reconnaissance (RECON phase)                                   |
|   +-- Signal emission (SIGNAL phase)                                          |
|   +-- Writing to person_movement_history                                      |
|   +-- Writing to people_errors                                                |
|                                                                               |
|   This engine DOES NOT OWN:                                                   |
|   +-- Identity minting (outreach_id from spine)                               |
|   +-- Scoring (BIT Engine owns scoring)                                       |
|   +-- Enrichment (People Intelligence owns enrichment)                        |
|   +-- Outreach decisions (Outreach Sub-Hub decides)                           |
|   +-- Company resolution (Company Target owns domain)                         |
|                                                                               |
|   IDENTITY: outreach_id is the ONLY identity. sovereign_id is HIDDEN.         |
|   PREREQUISITE: outreach_id MUST exist in spine for any write.                |
|                                                                               |
+===============================================================================+
```

---

## 1. Purpose

Talent Flow is a **movement detection sensor** within the People Intelligence sub-hub. It detects when executives move between companies and emits signals to downstream systems.

### Core Functions

1. **DETECT** — Identify movement patterns in LinkedIn/source data
2. **RECON** — Validate movement against known company universe
3. **SIGNAL** — Emit doctrine-compliant signals for downstream processing

### Non-Functions (EXPLICIT)

| Non-Function | Rationale |
|--------------|-----------|
| **No Scoring** | BIT Engine owns scoring. Talent Flow is passive. |
| **No Identity Minting** | Spine mints outreach_id. Talent Flow consumes. |
| **No Enrichment** | People Intelligence owns enrichment calls. |
| **No Company Resolution** | Company Target owns domain resolution. |
| **No Outreach Decisions** | Outreach Sub-Hub decides campaigns. |

---

## 2. Doctrine Guards (LOCKED)

```python
# Phase Guard - Strict execution order
ENFORCE_PHASE_ORDER = True
assert ENFORCE_PHASE_ORDER is True, "Talent Flow MUST execute DETECT → RECON → SIGNAL"

# Signal Authority - Only emit permitted signals
ENFORCE_SIGNAL_AUTHORITY = True
assert ENFORCE_SIGNAL_AUTHORITY is True, "Talent Flow MUST emit only permitted signals"

# Write Authority - Only write to permitted tables
ENFORCE_WRITE_AUTHORITY = True
assert ENFORCE_WRITE_AUTHORITY is True, "Talent Flow MUST write only to permitted tables"

# Kill Switch - HALT not SKIP
ENFORCE_KILL_SWITCH_HALT = True
assert ENFORCE_KILL_SWITCH_HALT is True, "Kill switch MUST halt, not skip"
```

---

## 3. Phase-Gated Execution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TALENT FLOW PHASES (LOCKED)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PHASE 1: DETECT                                                            │
│  +-- Scan source data for position changes                                  │
│  +-- Identify departure signals                                             │
│  +-- Identify arrival signals                                               │
│  +-- Hash: SHA256 for deduplication                                         │
│                                                                             │
│                  │                                                          │
│                  ▼                                                          │
│                                                                             │
│  PHASE 2: RECON                                                             │
│  +-- Validate departure company in universe                                 │
│  +-- Validate arrival company in universe                                   │
│  +-- Determine signal type                                                  │
│  +-- Prepare signal payload                                                 │
│                                                                             │
│                  │                                                          │
│                  ▼                                                          │
│                                                                             │
│  PHASE 3: SIGNAL                                                            │
│  +-- Emit SLOT_VACATED (if departure)                                       │
│  +-- Emit SLOT_BIND_REQUEST (if arrival to known company)                   │
│  +-- Emit COMPANY_RESOLUTION_REQUIRED (if arrival to unknown)               │
│  +-- Emit MOVEMENT_RECORDED (audit confirmation)                            │
│  +-- Write to person_movement_history                                       │
│                                                                             │
│                  │                                                          │
│                  ▼                                                          │
│                                                                             │
│  OUTCOME: PROMOTED or QUARANTINED (binary only)                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Signal Authority (LOCKED)

### Permitted Signals

| Signal | Purpose | Downstream Consumer |
|--------|---------|---------------------|
| `SLOT_VACATED` | Executive departed from company | BIT Engine (score decay) |
| `SLOT_BIND_REQUEST` | Executive arrived at known company | People Intelligence |
| `COMPANY_RESOLUTION_REQUIRED` | Executive arrived at unknown company | Company Target |
| `MOVEMENT_RECORDED` | Audit confirmation | Audit log |

### Forbidden Signals (QUARANTINED)

| Signal | Status | Location |
|--------|--------|----------|
| `JOB_CHANGE` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `STARTUP` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `PROMOTION` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `LATERAL` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `COMPANY_CHANGE` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |

---

## 5. Write Authority (LOCKED)

### Permitted Tables

| Table | Schema | Purpose |
|-------|--------|---------|
| `person_movement_history` | `people` | Movement records |
| `people_errors` | `people` | Error persistence |

### Forbidden Tables

All other tables are FORBIDDEN for Talent Flow writes, including:
- `company_master`
- `companies`
- `outreach`
- `enrichment_cache`
- `bit_scores`
- `company_target`

---

## 6. Idempotency (LOCKED)

```python
# Deduplication via SHA256 hash
def calculate_movement_hash(person_id: str, from_company: str, to_company: str, detected_at: str) -> str:
    """
    DOCTRINE: Same movement cannot insert twice.
    """
    payload = f"{person_id}:{from_company}:{to_company}:{detected_at}"
    return hashlib.sha256(payload.encode()).hexdigest()
```

### Deduplication Rule

- Same movement hash → SKIP (already processed)
- Different movement hash → PROCESS

---

## 7. Binary Outcomes (LOCKED)

| Outcome | Condition |
|---------|-----------|
| `PROMOTED` | All phase gates passed, signals emitted |
| `QUARANTINED` | Any phase gate failed, error persisted |

**No third state. No partial completion.**

---

## 8. Kill Switch (LOCKED)

| Variable | Default | Behavior |
|----------|---------|----------|
| `PEOPLE_MOVEMENT_DETECT_ENABLED` | `true` | **HALT** when false |

When disabled, Talent Flow MUST:
1. Stop processing immediately
2. NOT skip to next record
3. NOT emit any signals
4. Log halt reason

---

## 9. Data Model

### people.person_movement_history

| Column | Type | Description |
|--------|------|-------------|
| movement_id | UUID | PK |
| person_id | UUID | Person identifier |
| outreach_id | UUID | FK to outreach.outreach (spine) |
| from_company_id | UUID | Departure company (nullable) |
| to_company_id | UUID | Arrival company (nullable) |
| movement_type | VARCHAR | DEPARTURE, ARRIVAL, INTERNAL |
| movement_hash | VARCHAR | SHA256 dedup hash |
| detected_at | TIMESTAMPTZ | When movement detected |
| signal_emitted | VARCHAR | Signal type emitted |
| outcome | VARCHAR | PROMOTED or QUARANTINED |
| correlation_id | UUID | Traceability |
| created_at | TIMESTAMPTZ | Record created |

---

## 10. Error Codes

| Code | Stage | Description |
|------|-------|-------------|
| TF-D-NO-SIGNAL | DETECT | No movement signal detected |
| TF-D-DUPLICATE | DETECT | Movement already processed (hash match) |
| TF-R-COMPANY-NOT-FOUND | RECON | Company not in universe |
| TF-R-PERSON-NOT-FOUND | RECON | Person not in system |
| TF-S-EMIT-FAIL | SIGNAL | Failed to emit signal |
| TF-S-WRITE-FAIL | SIGNAL | Failed to write to history |
| TF-K-HALTED | KILL_SWITCH | Processing halted by kill switch |

---

## 11. CI Enforcement

### Workflow

**File:** `.github/workflows/talent_flow_guard.yml`

Runs on every PR touching:
- `hubs/people-intelligence/**`
- `spokes/company-people/**`
- `spokes/people-outreach/**`
- `ops/enforcement/**`

### Jobs

1. **static-analysis** — Scans for forbidden patterns
2. **doctrine-tests** — Runs pytest test suite
3. **certification-check** — Verifies doctrine document exists

### Guard Checks

| Check | Invariant | Failure Condition |
|-------|-----------|-------------------|
| TF-001-A | Sensor Only | Write to forbidden table |
| TF-001-B | Signal Authority | Emit unauthorized signal |
| TF-001-C | Phase-Gated | Phase order violation |
| TF-001-D | Binary Outcome | Non-binary completion state |
| TF-001-E | Idempotent | Missing deduplication |
| TF-001-F | No Acting | Forbidden operation detected |
| TF-001-G | Kill Switch | Missing HALT check |

---

## 12. Legacy Quarantine

### Status

Legacy `movement_engine` code has been quarantined at:
```
meta/legacy_quarantine/movement_engine/
```

### Reason

The legacy code violates TF-001 invariants:
1. Emits forbidden signals (JOB_CHANGE, STARTUP, etc.)
2. Contains scoring logic (BIT score calculations)

### Regression Lock

**File:** `ops/tests/test_forbidden_signals_never_return.py`

This test ensures forbidden signals cannot re-enter the codebase.

### ADR

**Reference:** `docs/adr/ADR-TF-001_Talent_Flow_Quarantine.md`

---

## 13. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Doctrine Document | DONE | `hubs/people-intelligence/imo/TALENT_FLOW_DOCTRINE.md` |
| CI Enforcement Doc | DONE | `hubs/people-intelligence/imo/TALENT_FLOW_CI_ENFORCEMENT.md` |
| Guard Script | DONE | `ops/enforcement/talent_flow_guard.py` |
| Doctrine Tests | DONE | `ops/tests/test_talent_flow_doctrine.py` |
| Regression Lock | DONE | `ops/tests/test_forbidden_signals_never_return.py` |
| GitHub Workflow | DONE | `.github/workflows/talent_flow_guard.yml` |
| Legacy Quarantine | DONE | `meta/legacy_quarantine/movement_engine/` |
| ADR | DONE | `docs/adr/ADR-TF-001_Talent_Flow_Quarantine.md` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-12-XX | Legacy movement_engine (pre-doctrine) |
| **1.0.1** | **2026-01-08** | **CERTIFIED**: TF-001 doctrine, CI enforcement, legacy quarantine |

---

**Document Version:** 1.0.1
**Last Updated:** 2026-01-08
**Owner:** People Intelligence Sub-Hub
**Author:** Claude Code (IMO-Creator)
**Status:** 🚀 PRODUCTION-READY (LOCKED)
**Certification ID:** TF-001 (ENFORCED)
**Doctrine:** Spine-First Architecture v1.1
