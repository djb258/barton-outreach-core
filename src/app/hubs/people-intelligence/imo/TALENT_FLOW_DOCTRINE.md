# Talent Flow Doctrine v1.0.1

**System:** Talent Flow (People Intelligence — Seal B)
**Version:** 1.0.1
**Status:** 🚀 PRODUCTION-READY
**Certification ID:** TF-001 (ENFORCED)
**Enforcement:** CI + Tests + Guard Active
**Author:** Claude Code (Doctrine Enforcer)
**Certifying Authority:** Doctrine Certifier
**Certification Date:** 2026-01-08
**Production Release:** 2026-01-08
**Production Release:** 2026-01-08

---

## Production Readiness

| Criterion | Status |
|-----------|--------|
| All doctrine invariants enforced | ✅ PASS |
| Legacy behavior quarantined | ✅ PASS |
| Regression locked by tests | ✅ PASS |
| No known open violations | ✅ PASS |

**Enforcement Files:**
- CI Guard: `ops/enforcement/talent_flow_guard.py`
- CI Workflow: `.github/workflows/talent_flow_guard.yml`
- Doctrine Tests: `ops/tests/test_talent_flow_doctrine.py`
- Regression Lock: `ops/tests/test_forbidden_signals_never_return.py`
- Quarantine: `meta/legacy_quarantine/movement_engine/`

**Status:** This doctrine is SEALED. Changes require formal doctrine review.

---

## Mini-Cert: Talent Flow (Seal B)

### Purpose

- Detect executive movement on canonical slots (CEO, CFO, HR)
- Log movement immutably to `people.person_movement_history`
- Emit resolution signals when movement implies organizational pressure

### Authority

| Action | Status |
|--------|--------|
| Write to `people.person_movement_history` | ✅ PERMITTED |
| Write to `people.people_errors` | ✅ PERMITTED |
| Emit `SLOT_VACATED` signal | ✅ PERMITTED |
| Emit `SLOT_BIND_REQUEST` signal | ✅ PERMITTED |
| Emit `COMPANY_RESOLUTION_REQUIRED` signal | ✅ PERMITTED |
| Mint company IDs | ❌ FORBIDDEN |
| Create outreach records | ❌ FORBIDDEN |
| Perform enrichment | ❌ FORBIDDEN |
| Perform scoring | ❌ FORBIDDEN |
| Bind slots directly | ❌ FORBIDDEN |
| Auto-resolve companies | ❌ FORBIDDEN |

### Completion Definition

| Outcome | Condition | Action |
|---------|-----------|--------|
| **PROMOTED** | All phase gates passed, movement logged, signal emitted | Execution complete — no further action by Talent Flow |
| **QUARANTINED** | Any phase gate failed | Error logged to `people.people_errors`, execution halted |

There is no third state. Partial completion is not possible.

### Kill Switch Behavior

| Switch | Variable | Default | Behavior |
|--------|----------|---------|----------|
| Movement Detection | `PEOPLE_MOVEMENT_DETECT_ENABLED` | `true` | **HALT** — never SKIP |

When disabled, Talent Flow does not process. It does not queue, defer, or silently skip.

### Idempotency Guarantee

A movement event is uniquely identified by:
```
SHA256(person_unique_id + movement_type + company_from_id + company_to_id + movement_date)
```

If this hash exists in `person_movement_history`, the event is discarded silently. No error is logged for duplicates. This guarantees:
- Same input → same output (determinism)
- Reprocessing is safe (no double-writes)
- Replay is idempotent (audit-safe)

---

## Explicit Out-of-Scope Declaration

The following are **NOT** responsibilities of Talent Flow:

- LinkedIn scraping or polling
- Watch list management
- Company existence verification
- Company ID minting
- Outreach record creation
- Enrichment of any kind
- Scoring of any kind
- Slot binding (emits request only)
- Replacement hiring
- Resolution of ambiguous companies
- Downstream pipeline execution
- SLA enforcement on emitted signals

These responsibilities belong to external systems and are deferred to their respective doctrines.

---

## Locked Invariants

The following invariants are **non-negotiable** and must be preserved in all implementations:

| Invariant | Definition |
|-----------|------------|
| **Sensor Only** | Talent Flow observes and emits — it does not act |
| **Append-Only** | Writes to `person_movement_history` are immutable |
| **Slot-Aware** | Only CEO, CFO, HR slots are tracked |
| **Bidirectional** | Both departures and arrivals are logged |
| **Phase-Gated** | Three phases: DETECT → RECON → SIGNAL |
| **Binary Outcome** | PROMOTED or QUARANTINED — no third state |
| **Idempotent** | Same movement cannot fire twice |
| **Deterministic** | Same inputs → same outputs |
| **Auditable** | Every action logged |
| **No Guessing** | Ambiguous data → QUARANTINE, not inference |

---

## Final Certification Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   CERTIFICATION: TALENT FLOW DOCTRINE v1.0.1                                  ║
║                                                                               ║
║   Certification ID: TF-001                                                    ║
║   Status: CERTIFIED                                                           ║
║   Date: 2026-01-08                                                            ║
║                                                                               ║
║   This doctrine is LOCKED.                                                    ║
║   Scope expansion requires new certification.                                 ║
║   Implementation must conform to stated invariants.                           ║
║                                                                               ║
║   Certifying Authority: Doctrine Certifier                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## Core Identity

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

Talent Flow is a **movement-detection and pressure-discovery engine** inside the People Intelligence Sub-Hub. Its responsibility is to:

1. **Observe** executive movement
2. **Log** movement immutably
3. **Emit** resolution signals when movement implies organizational pressure

---

## Boundary Definition

### WHAT TALENT FLOW IS

| Capability | Description |
|------------|-------------|
| Movement Tracking | Tracks executive movement events (hire, exit, promotion, title_change) |
| Append-Only | No updates, no overwrites — immutable history |
| Slot-Aware | Operates on canonical slots only: CEO, CFO, HR |
| Bidirectional | Departures and arrivals both matter |
| Signal Emission | Emits signals into existing downstream pipelines |

### WHAT TALENT FLOW IS NOT

| Anti-Pattern | Status |
|--------------|--------|
| Mint company IDs | ❌ FORBIDDEN |
| Create outreach records | ❌ FORBIDDEN |
| Perform enrichment | ❌ FORBIDDEN |
| Perform scoring | ❌ FORBIDDEN |
| Guess or infer missing data | ❌ FORBIDDEN |
| Recurse infinitely | ❌ FORBIDDEN |
| Auto-resolve companies | ❌ FORBIDDEN |

**All identity creation and resolution is delegated outward.**

---

## Write Authority

Talent Flow may ONLY write to:

| Table | Schema | Purpose |
|-------|--------|---------|
| `person_movement_history` | `people` | Immutable movement log |
| `people_errors` | `people` | Failure capture |

### Write Invariants

| Invariant | Enforcement |
|-----------|-------------|
| Idempotent | Same movement cannot fire twice |
| Deterministic | Same inputs → same outputs |
| Auditable | Every action logged |
| Phase-gated | Must pass gates to progress |
| Binary outcomes | PROMOTED or QUARANTINED only |

---

## Phase Gates

Talent Flow operates in three sequential phases. Each phase has exactly one outcome: **PROMOTED** (continue) or **QUARANTINED** (stop + log error).

### Phase 1: DETECT

**Purpose:** Identify that a movement event has occurred.

| Input | Validation | PROMOTED | QUARANTINED |
|-------|------------|----------|-------------|
| LinkedIn profile change | Change detected on watched identity | Movement type identified | No change detected |
| Person unique_id | Valid, exists in people_master | Person confirmed | Person not found |
| Slot membership | Person is in CEO, CFO, or HR slot | Slot-aware movement | Non-canonical slot |

**Gate:** Movement must be on a canonical slot (CEO/CFO/HR).

**On QUARANTINE:**
- Error code: `TF-E101` (non_canonical_slot)
- Error code: `TF-E102` (person_not_found)
- Error code: `TF-E103` (no_change_detected)

---

### Phase 2: RECON

**Purpose:** Determine movement type and affected parties.

| Movement Type | Origin Effect | Destination Effect |
|---------------|---------------|-------------------|
| `exit` | Vacate slot at Company A | None (person left workforce) |
| `hire` | None (person entered workforce) | Arrival at Company B |
| `move` | Vacate slot at Company A | Arrival at Company B |
| `promotion` | Slot change within Company A | N/A |
| `title_change` | Metadata update only | N/A |

**Gate:** Movement type must be determinable. Ambiguous movements → QUARANTINE.

**On QUARANTINE:**
- Error code: `TF-E201` (ambiguous_movement_type)
- Error code: `TF-E202` (incomplete_movement_data)
- Error code: `TF-E203` (conflicting_signals)

---

### Phase 3: SIGNAL

**Purpose:** Emit appropriate downstream signals based on movement type.

| Condition | Signal Emitted | Target |
|-----------|----------------|--------|
| Exit from Company A | `SLOT_VACATED` | Replacement Watch Queue |
| Arrival at Company B (exists) | `SLOT_BIND_REQUEST` | People Intelligence |
| Arrival at Company B (not exists) | `COMPANY_RESOLUTION_REQUIRED` | Company Lifecycle |
| Movement logged | `MOVEMENT_RECORDED` | Audit Log |

**Gate:** Signals must be emittable. If destination company lookup fails → QUARANTINE.

**On QUARANTINE:**
- Error code: `TF-E301` (signal_emission_failed)
- Error code: `TF-E302` (company_lookup_timeout)
- Error code: `TF-E303` (invalid_destination_data)

---

## Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TALENT FLOW EXECUTION MODEL                           │
│                                                                                 │
│  ┌─────────────────┐                                                           │
│  │ Slots Filled    │                                                           │
│  │ (CEO/CFO/HR)    │                                                           │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │ Watched Identity│ ◄─── LinkedIn URL is external anchor                      │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           │ LinkedIn Change Detected                                            │
│           ▼                                                                     │
│  ┌─────────────────┐     ┌─────────────────┐                                   │
│  │ PHASE 1: DETECT │────►│ QUARANTINE      │ (non-canonical, not found)        │
│  └────────┬────────┘     └─────────────────┘                                   │
│           │ PROMOTED                                                            │
│           ▼                                                                     │
│  ┌─────────────────┐                                                           │
│  │ Append to       │                                                           │
│  │ person_movement_│                                                           │
│  │ history         │ ◄─── IMMUTABLE WRITE                                      │
│  └────────┬────────┘                                                           │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐     ┌─────────────────┐                                   │
│  │ PHASE 2: RECON  │────►│ QUARANTINE      │ (ambiguous, incomplete)           │
│  └────────┬────────┘     └─────────────────┘                                   │
│           │ PROMOTED                                                            │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │                    Movement Type Dispatch                       │           │
│  │                                                                 │           │
│  │  ┌───────────┐         ┌───────────┐                           │           │
│  │  │ Exit/Move │         │ Hire/Move │                           │           │
│  │  └─────┬─────┘         └─────┬─────┘                           │           │
│  │        │                     │                                  │           │
│  │        ▼                     ▼                                  │           │
│  │  ┌───────────────┐    ┌───────────────────┐                    │           │
│  │  │ Vacate Slot   │    │ Company B Exists? │                    │           │
│  │  │ at Company A  │    └─────────┬─────────┘                    │           │
│  │  └───────┬───────┘              │                              │           │
│  │          │                      │                              │           │
│  │          ▼               ┌──────┴──────┐                       │           │
│  │  ┌───────────────┐       │             │                       │           │
│  │  │ Replacement   │       ▼             ▼                       │           │
│  │  │ Watch Queue   │   ┌───────┐    ┌────────────┐               │           │
│  │  │ (NO AUTO-FILL)│   │  YES  │    │    NO      │               │           │
│  │  └───────────────┘   └───┬───┘    └──────┬─────┘               │           │
│  │                          │               │                      │           │
│  │                          ▼               ▼                      │           │
│  │                    ┌───────────┐  ┌────────────────┐           │           │
│  │                    │ Bind Slot │  │ Emit           │           │           │
│  │                    │ Company B │  │ COMPANY_       │           │           │
│  │                    └───────────┘  │ RESOLUTION_    │           │           │
│  │                                   │ REQUIRED       │           │           │
│  │                                   └───────┬────────┘           │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                                              │                                  │
│           ┌──────────────────────────────────┘                                  │
│           ▼                                                                     │
│  ┌─────────────────┐     ┌─────────────────┐                                   │
│  │ PHASE 3: SIGNAL │────►│ QUARANTINE      │ (emission failed)                 │
│  └────────┬────────┘     └─────────────────┘                                   │
│           │ PROMOTED                                                            │
│           ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐           │
│  │                    Downstream Pipelines                         │           │
│  │                                                                 │           │
│  │  ┌───────────────────┐    ┌───────────────────────────────────┐ │           │
│  │  │ Company Lifecycle │    │ Enrichment Pipeline               │ │           │
│  │  │ (existence check) │    │ (if company exists)               │ │           │
│  │  └─────────┬─────────┘    └───────────────────────────────────┘ │           │
│  │            │                                                    │           │
│  │            ▼                                                    │           │
│  │  ┌─────────────────────────────────────────────────────────────┐│           │
│  │  │ PASS: Mint Company + Outreach ID                           ││           │
│  │  │ FAIL: Log to people.people_errors                          ││           │
│  │  └─────────────────────────────────────────────────────────────┘│           │
│  │                                                                 │           │
│  │  ⚠️ Talent Flow DOES NOT execute these — only emits signals    │           │
│  └─────────────────────────────────────────────────────────────────┘           │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Idempotency Rules

### Movement Deduplication

| Field | Rule |
|-------|------|
| `person_unique_id` | Required — identifies who moved |
| `movement_type` | Required — identifies what happened |
| `detected_at` | Required — when we detected it |
| `movement_date` | Optional — when it actually happened |

**Deduplication Key:**
```
SHA256(person_unique_id + movement_type + company_from_id + company_to_id + movement_date)
```

**Rule:** If hash already exists in `person_movement_history`, the event is a duplicate and MUST be discarded silently (no error, no re-insert).

### TTL Rules

| Event Type | TTL | Action on Expiry |
|------------|-----|------------------|
| `COMPANY_RESOLUTION_REQUIRED` signal | 72 hours | Escalate to manual review |
| Replacement Watch | 30 days | Close watch, log `TF-E401` |
| Pending movement confirmation | 24 hours | Auto-QUARANTINE |

---

## Error Codes

### Talent Flow Error Registry

| Code | Stage | Type | Message | Retry Strategy |
|------|-------|------|---------|----------------|
| `TF-E101` | detect | validation | Non-canonical slot | discard |
| `TF-E102` | detect | missing_data | Person not found in people_master | manual_fix |
| `TF-E103` | detect | validation | No change detected | discard |
| `TF-E201` | recon | ambiguity | Ambiguous movement type | manual_fix |
| `TF-E202` | recon | missing_data | Incomplete movement data | manual_fix |
| `TF-E203` | recon | conflict | Conflicting signals from sources | manual_fix |
| `TF-E301` | signal | external_fail | Signal emission failed | auto_retry |
| `TF-E302` | signal | external_fail | Company lookup timeout | auto_retry |
| `TF-E303` | signal | validation | Invalid destination data | manual_fix |
| `TF-E401` | watch | stale_data | Replacement watch TTL expired | manual_fix |

---

## Schema Specification

### `people.person_movement_history` (Existing — Verified)

This table already exists in Neon (0 rows). Schema confirmed:

| Column | Type | Nullable | Purpose |
|--------|------|----------|---------|
| `id` | INT | NOT NULL | PK — auto-increment |
| `person_unique_id` | TEXT | NOT NULL | FK → people_master.unique_id |
| `linkedin_url` | TEXT | NULL | External identity anchor |
| `company_from_id` | TEXT | NULL | Origin company (exits/moves) |
| `company_to_id` | TEXT | NULL | Destination company (hires/moves) |
| `title_from` | TEXT | NULL | Previous title |
| `title_to` | TEXT | NULL | New title |
| `movement_type` | TEXT | NOT NULL | hire/exit/move/promotion/title_change |
| `detected_at` | TIMESTAMP | NOT NULL | When TF detected the change |
| `raw_payload` | JSONB | NULL | Source data for audit |
| `created_at` | TIMESTAMP | NOT NULL | Row creation time |

**Required Index (if missing):**
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_movement_dedup 
ON people.person_movement_history (
    person_unique_id, 
    movement_type, 
    company_from_id, 
    company_to_id, 
    DATE(detected_at)
);
```

### `people.people_errors` (Existing — Verified)

Error rows written by Talent Flow use:

| Field | Value |
|-------|-------|
| `error_stage` | `movement_detect` (Phase 1–3) |
| `error_code` | `TF-Exxx` format |
| `retry_strategy` | `manual_fix`, `auto_retry`, or `discard` |

**Note:** Existing `chk_error_stage` constraint already includes `movement_detect`.

---

## Kill Switches

| Switch | Env Variable | Default | Effect |
|--------|--------------|---------|--------|
| Movement Detection | `PEOPLE_MOVEMENT_DETECT_ENABLED` | true | Disables all Talent Flow processing |

**Kill switch behavior:** HALT, never SKIP.

---

## Ambiguities — Deferred to External Doctrine

The following items are **not resolved** by this doctrine and are explicitly deferred:

| Item | Deferred To |
|------|-------------|
| LinkedIn scraping frequency | External: Enrichment Pipeline Doctrine |
| Company B identification method | External: Company Lifecycle Doctrine |
| Slot binding execution | External: People Intelligence Doctrine |
| Multi-slot movement handling | External: People Intelligence Doctrine |
| Watch list management | External: People Intelligence Doctrine |

These will not be guessed. Implementation must await resolution from the owning doctrine.

---

## Certification Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   TALENT FLOW DOCTRINE v1.0.1 — CERTIFIED                                     ║
║                                                                               ║
║   This document defines the canonical behavior of the Talent Flow system.     ║
║   It is a SENSOR, not an ACTOR.                                               ║
║                                                                               ║
║   Boundary: Movement detection and signal emission only.                      ║
║   Authority: Write to person_movement_history and people_errors only.         ║
║   Invariants: Idempotent, deterministic, auditable, phase-gated, binary.      ║
║                                                                               ║
║   Status: CERTIFIED                                                           ║
║   Certification ID: TF-001                                                    ║
║   Scope expansion requires re-certification.                                  ║
║                                                                               ║
║   Certifying Authority: Doctrine Certifier                                    ║
║   Date: 2026-01-08                                                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

**Last Updated:** 2026-01-08
**Author:** Claude Code (Doctrine Enforcer)
**Certifying Authority:** Doctrine Certifier
**Parent Hub:** People Intelligence (FULL PASS)
**Doctrine Version:** Barton IMO v1.1
