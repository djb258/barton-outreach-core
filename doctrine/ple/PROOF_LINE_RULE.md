# Proof Line Rule

**Authority:** ADR-017
**Status:** ACTIVE
**Version:** 1.0

---

## Definition

A **proof line** is a mandatory citation of detected organizational pressure that authorizes a marketing message. It is **NOT** a talking point. It is the **legal basis for contact**.

---

## When Required

| Band | Proof Required | Proof Type |
|------|----------------|------------|
| 0-2 | No | - |
| 3 | Yes | Single-source |
| 4 | Yes | Multi-source |
| 5 | Yes | Full-chain |

---

## Proof Types

### Single-Source Proof (Band 3)

One domain provides evidence of pressure.

**Format:**
```
[PRESSURE_CLASS] detected via [SOURCE]: [SPECIFIC_EVIDENCE]
```

**Example:**
```
COST_PRESSURE detected via DOL: employer contribution +18% YoY, renewal in 75 days
```

### Multi-Source Proof (Band 4)

Two or more domains converge on same pressure.

**Format:**
```
[PRESSURE_CLASS] convergence: [DOL_EVIDENCE] + [PEOPLE_EVIDENCE] + [BLOG_EVIDENCE if present]
```

**Example:**
```
VENDOR_DISSATISFACTION convergence: broker changed YoY (DOL) + new HR leader 90 days (People)
```

### Full-Chain Proof (Band 5)

All available domains align on phase transition.

**Format:**
```
PHASE TRANSITION: [PRESSURE_CLASS] — [DOL] + [PEOPLE] + [BLOG] — Decision window: [X] days
```

**Example:**
```
PHASE TRANSITION: DEADLINE_PROXIMITY — renewal in 45 days (DOL) + new CHRO 60 days (People) + funding announced (Blog) — Decision window: 45 days
```

---

## Machine-Readable Twin

Every proof line MUST have a machine-readable counterpart for audit and traceability.

**Schema:**
```json
{
  "proof_id": "prf_xxxxx",
  "band": 3,
  "pressure_class": "COST_PRESSURE",
  "sources": ["DOL"],
  "evidence": {
    "dol": {
      "signal": "EMPLOYER_COST_RISING",
      "employer_contribution_yoy_pct": 18,
      "renewal_days": 75,
      "source_record_id": "ack_12345"
    }
  },
  "company_unique_id": "ACME-MFG-001",
  "generated_at": "2026-01-25T14:32:00Z",
  "valid_until": "2026-04-25T14:32:00Z",
  "movement_ids": ["mv_abc123", "mv_def456"]
}
```

---

## Proof Validity

### Generation

Proofs are generated from active movement events. A proof inherits the shortest validity window from its source movements.

### Expiration

- Proofs expire when their `valid_until` timestamp passes
- Proofs expire when source movements expire
- Proofs expire when evidence chain breaks (source records deleted/modified)

### Refresh

Expired proofs cannot be refreshed. New proof must be generated from current movements.

---

## Proof Validation

Before any Band 3+ message send, the system MUST:

1. **Verify proof exists** — `proof_id` must be provided
2. **Verify proof not expired** — `valid_until > NOW()`
3. **Verify proof band sufficient** — `proof.band >= requested_band`
4. **Verify evidence chain intact** — All `movement_ids` still exist and are valid

If ANY check fails: **HARD_FAIL**. No send. No fallback.

---

## Proof in Messages

### What Proof Enables

The proof line enables the message to contain:
- Reference to the detected pressure
- Evidence-based "why now" framing
- Specific details from the proof evidence

### What Proof Does NOT Enable

- Fabricated urgency beyond evidence
- Speculation beyond detected facts
- Claims not traceable to source records

### Example Message Flow

**Proof:**
```
COST_PRESSURE detected via DOL: employer contribution +18% YoY, renewal in 75 days
```

**Valid Message:**
```
"Your employer contribution rose 18% last year while headcount stayed flat —
that's a cost visibility gap. With renewal in 75 days, there's still time
to model alternatives."
```

**Invalid Message (fabrication):**
```
"Your costs are out of control and you need to act immediately or
you'll lose your best employees."
```

---

## Pressure Classes

| Class | Primary Source | Evidence Pattern |
|-------|----------------|------------------|
| COST_PRESSURE | DOL | Cost increases, contribution spikes, fee growth |
| VENDOR_DISSATISFACTION | DOL + People | Broker changes, carrier changes, advisor churn |
| DEADLINE_PROXIMITY | DOL | Renewal windows, filing deadlines |
| ORGANIZATIONAL_RECONFIGURATION | People | Leadership changes, slot vacancies, authority gaps |
| OPERATIONAL_CHAOS | DOL | Filing irregularities, compliance gaps, multi-carrier complexity |

---

## Audit Requirements

All proof usage MUST be logged:

```sql
INSERT INTO bit.authorization_log (
    company_unique_id,
    requested_action,
    requested_band,
    authorized,
    actual_band,
    proof_id,
    proof_valid,
    requested_at,
    requested_by
)
```

---

## Enforcement

### Code Pattern

```python
def send_message(company_id: str, action: str, proof_id: str = None):
    band = band_calculator.get_current_band(company_id)

    if band >= 3:
        if not proof_id:
            raise MissingProofLineError("Band 3+ requires proof")

        validation = proof_validator.validate_for_send(proof_id, band)
        if not validation.valid:
            raise InvalidProofError(validation.reason)

    # Proceed with send
    ...
```

### Never Do

1. **Never fabricate proof lines** — Proof must trace to real movement events
2. **Never backfill proof** — Proof must exist BEFORE message creation
3. **Never copy proof between companies** — Each company needs its own proof
4. **Never send with expired proof** — Check validity at send time
5. **Never exceed proof band** — Proof for Band 3 cannot authorize Band 4 action

---

**Document Control:**
| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Authority | ADR-017 |
| Status | ACTIVE |
