---
id: talent-flow
title: Talent Flow (TF-001)
desc: Executive movement sensor - detects departures/arrivals, emits doctrine signals
updated: 2026-01-08
created: 2026-01-08
tags:
  - engine
  - sensor
  - movement
  - certified
  - production-ready
  - tf-001
---

# Talent Flow (TF-001)

## Overview

Talent Flow is a **movement detection sensor** within the People Intelligence sub-hub. It detects when executives move between companies and emits signals to downstream systems.

**Talent Flow is a SENSOR, not an ACTOR.**

## Quick Reference

| Field | Value |
|-------|-------|
| **Certification ID** | TF-001 |
| **Doctrine Version** | 1.0.1 |
| **Status** | 🚀 PRODUCTION-READY |
| **Production Release** | 2026-01-08 |
| **Parent Hub** | People Intelligence (04.04.02) |
| **Enforcement** | CI + Tests + Guard Active |

## Ownership

### Owns (Write Access)

- `people.person_movement_history` — Movement records (append-only)
- `people.people_errors` — Error capture

### Does NOT Own (FORBIDDEN)

- Identity minting (outreach_id from spine)
- Scoring (BIT Engine owns)
- Enrichment (People Intelligence owns)
- Outreach decisions (Outreach Sub-Hub decides)
- Company resolution (Company Target owns)

## Phase-Gated Execution

```
DETECT → RECON → SIGNAL → [PROMOTED | QUARANTINED]
```

| Phase | Purpose |
|-------|---------|
| **DETECT** | Scan source data for position changes |
| **RECON** | Validate company/person against universe |
| **SIGNAL** | Emit doctrine-compliant signals |
| **OUTCOME** | Binary: PROMOTED or QUARANTINED |

## Permitted Signals

| Signal | Purpose | Consumer |
|--------|---------|----------|
| `SLOT_VACATED` | Executive departed | BIT Engine |
| `SLOT_BIND_REQUEST` | Executive arrived (known company) | People Intelligence |
| `COMPANY_RESOLUTION_REQUIRED` | Executive arrived (unknown company) | Company Target |
| `MOVEMENT_RECORDED` | Audit confirmation | Audit log |

## Forbidden Signals (QUARANTINED)

| Signal | Status | Location |
|--------|--------|----------|
| `JOB_CHANGE` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `STARTUP` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `PROMOTION` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `LATERAL` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |
| `COMPANY_CHANGE` | QUARANTINED | meta/legacy_quarantine/movement_engine/ |

## CI Enforcement

| Component | Status | File |
|-----------|--------|------|
| CI Guard | ✅ ACTIVE | `ops/enforcement/talent_flow_guard.py` |
| CI Workflow | ✅ ACTIVE | `.github/workflows/talent_flow_guard.yml` |
| Doctrine Tests | ✅ 30 PASS | `ops/tests/test_talent_flow_doctrine.py` |
| Regression Lock | ✅ 9 PASS | `ops/tests/test_forbidden_signals_never_return.py` |

## Invariants (LOCKED)

| ID | Invariant | Definition |
|----|-----------|------------|
| TF-001-A | Sensor Only | Write to permitted tables only |
| TF-001-B | Signal Authority | Emit permitted signals only |
| TF-001-C | Phase-Gated | DETECT → RECON → SIGNAL |
| TF-001-D | Binary Outcome | PROMOTED or QUARANTINED |
| TF-001-E | Idempotent | SHA256 deduplication |
| TF-001-F | No Acting | No scoring, no enrichment, no minting |
| TF-001-G | Kill Switch | HALT, not SKIP |

## Key Files

| File | Purpose |
|------|---------|
| [TALENT_FLOW_DOCTRINE.md](../../hubs/people-intelligence/imo/TALENT_FLOW_DOCTRINE.md) | Doctrine document |
| [TALENT_FLOW_CI_ENFORCEMENT.md](../../hubs/people-intelligence/imo/TALENT_FLOW_CI_ENFORCEMENT.md) | CI enforcement doc |
| [PRD_TALENT_FLOW.md](../prd/PRD_TALENT_FLOW.md) | Product requirements |
| [ADR-TF-001](../adr/ADR-TF-001_Talent_Flow_Quarantine.md) | Quarantine decision |
| [talent_flow_guard.py](../../ops/enforcement/talent_flow_guard.py) | Guard script |
| [test_talent_flow_doctrine.py](../../ops/tests/test_talent_flow_doctrine.py) | Doctrine tests |

## Legacy Quarantine

Legacy `movement_engine` code has been quarantined at:

```
meta/legacy_quarantine/movement_engine/
├── README.md
├── movement_engine.py   (QUARANTINED)
├── movement_rules.py    (QUARANTINED)
├── state_machine.py     (QUARANTINED)
└── __init__.py          (QUARANTINED)
```

**Reason:** Violates TF-001 invariants (forbidden signals + scoring logic)
**Refactor:** Explicitly deferred — requires new certification

## Related

- [[people-intelligence]] — Parent hub
- [[company-target]] — Company resolution consumer
- [[outreach-execution]] — Downstream consumer

---

**Last Updated:** 2026-01-08
**Author:** Claude Code (IMO-Creator)
**Doctrine Version:** 1.0.1
**Certification:** TF-001 (ENFORCED)

