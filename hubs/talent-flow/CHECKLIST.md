# Talent Flow — Compliance Checklist

**DOCTRINE LOCK**: This checklist is the freeze line for Talent Flow.
No code ships unless every box is checked. No exceptions. No partial compliance.

---

## 0. CL Upstream Gate (FIRST CHECK)

> Talent Flow assumes Company Life Cycle existence verification has already passed.
> Talent Flow will not execute without an `EXISTENCE_PASS` signal from CL.

### Gate Enforcement

- [ ] `CLGate.enforce_or_fail()` called BEFORE any Talent Flow logic
- [ ] Checks `company_unique_id` exists in `cl.company_identity`
- [ ] EXISTS → `EXISTENCE_PASS` → proceed
- [ ] MISSING → Write `TF_UPSTREAM_CL_NOT_VERIFIED` error → STOP

### Explicit Prohibitions

- [ ] Does NOT implement CL existence checks
- [ ] Does NOT add CL error tables
- [ ] Does NOT retry or "repair" missing CL signals
- [ ] Does NOT infer existence from LinkedIn or names
- [ ] Does NOT soft-fail or partially proceed

### Error Routing

- [ ] Missing CL company → `outreach_errors` table
- [ ] `failure_code`: `TF_UPSTREAM_CL_NOT_VERIFIED`
- [ ] `pipeline_stage`: `upstream_cl_gate`
- [ ] `severity`: `blocking`
- [ ] Error terminates execution immediately

---

## 1. Hard Input Contract (MANDATORY)

### Required Inputs

- [ ] `company_unique_id` received (read-only, pre-minted from CL)
- [ ] `outreach_context_id` received (MANDATORY, scope boundary)
- [ ] `correlation_id` received (MANDATORY, tracing only)
- [ ] `person_identifier` received (LinkedIn URL or person ID)

### Input Validation

- [ ] FAIL IMMEDIATELY if `company_unique_id` is missing
- [ ] FAIL IMMEDIATELY if `outreach_context_id` is missing
- [ ] FAIL IMMEDIATELY if `correlation_id` is missing
- [ ] No identity minting (CL owns company_unique_id)

---

## 2. Upstream Dependency (MANDATORY)

### People Intelligence Dependency

- [ ] Check People Intelligence hub status BEFORE processing
- [ ] If People Intelligence status == `BLOCKED` → status = `BLOCKED`
- [ ] If People Intelligence status == `FAIL` → status = `BLOCKED`
- [ ] Movement signals must reference valid person_unique_id from People hub

### Dependency Chain

```
Company Lifecycle (CL) → Company Target → DOL → People Intelligence → Talent Flow
```

---

## 3. Sensor-Only Mode (CRITICAL)

> Talent Flow ONLY detects movements. It NEVER triggers enrichment.
> All signals must reference a valid company_unique_id from upstream.

### Explicit Prohibitions

- [ ] Does NOT trigger any paid API calls
- [ ] Does NOT enrich person data
- [ ] Does NOT mint new person records
- [ ] Does NOT create new company records
- [ ] Does NOT modify upstream hub data
- [ ] Does NOT retry failed detections with enrichment

### What Talent Flow Does

- [ ] Monitors LinkedIn profile changes
- [ ] Detects job title changes
- [ ] Detects company transitions
- [ ] Emits movement signals to BIT engine
- [ ] Computes hub PASS/IN_PROGRESS status

---

## 4. Movement Detection Rules (IMMUTABLE)

### Valid Movement Types

- [ ] `joined` - Executive joined from another company
- [ ] `left` - Executive departed
- [ ] `title_change` - Title changed within same company

### Movement Validation

- [ ] Movement must have `person_identifier` (non-null)
- [ ] Movement must have `detected_at` timestamp
- [ ] Movement must have `movement_type` from valid set
- [ ] Movement `confidence` must be >= 0.70 (CONFIDENCE_THRESHOLD)

### Deduplication

- [ ] Hash: `(company_unique_id, person_id, event_type, date)`
- [ ] Duplicate movements within same day are ignored
- [ ] Re-detection on different day creates new signal

---

## 5. PASS Criteria (DETERMINISTIC)

> No fuzzy logic. No guessing. No human judgment.

### PASS Requirements (ALL must be true)

- [ ] `company_unique_id` exists and is valid
- [ ] Upstream People Intelligence hub is NOT `BLOCKED`
- [ ] At least `MIN_MOVEMENTS` (1) valid movement signals
- [ ] At least one signal within freshness window

### Configuration (LOCKED)

- [ ] `FRESHNESS_DAYS = 60` (signals expire after 60 days)
- [ ] `MIN_MOVEMENTS = 1` (minimum movements to PASS)
- [ ] `CONFIDENCE_THRESHOLD = 0.70` (minimum confidence)

### Status Transitions

| From | To | Condition |
|------|-----|-----------|
| IN_PROGRESS | PASS | Fresh movement detected |
| PASS | IN_PROGRESS | All signals expired |
| * | BLOCKED | Upstream is BLOCKED |
| * | FAIL | Reserved (not used - sensor mode) |

---

## 6. Signal Emission (STRICT)

### BIT Signal Contract

Movement signals MUST emit to BIT engine with:

- [ ] `outreach_id` - Target company outreach reference
- [ ] `signal_type` - `TALENT_MOVEMENT`
- [ ] `signal_impact` - Numeric impact value
- [ ] `source_spoke` - `talent-flow`
- [ ] `correlation_id` - Tracing ID
- [ ] `decay_period_days` - 90 days default
- [ ] `signal_timestamp` - When movement was detected

### Signal Values

| Movement Type | BIT Impact |
|---------------|------------|
| `joined` | +10 |
| `left` | +5 |
| `title_change` | +3 |

---

## 7. Output Contract (STRICT)

Must emit exactly:

- [ ] `company_unique_id`
- [ ] `outreach_context_id`
- [ ] `status` (PASS | IN_PROGRESS | BLOCKED)
- [ ] `status_reason`
- [ ] `metric_value` (movement detection rate)
- [ ] `fresh_movements` count
- [ ] `total_movements` count

No partial success. No soft states.

---

## 8. Forbidden Actions

- [ ] **NO** identity minting
- [ ] **NO** paid API calls
- [ ] **NO** enrichment triggers
- [ ] **NO** person record creation
- [ ] **NO** company record creation
- [ ] **NO** upstream data modification
- [ ] **NO** retry loops with enrichment
- [ ] **NO** writing to CL tables

---

## 9. Kill Switch

Pipeline MUST exit immediately if:

- [ ] `company_unique_id` is null
- [ ] `outreach_context_id` is missing
- [ ] `correlation_id` is missing
- [ ] Upstream People Intelligence is BLOCKED
- [ ] Movement validation fails

---

## 10. Error Handling Compliance

### Error Codes

| Code | Description | Severity |
|------|-------------|----------|
| `TF_UPSTREAM_CL_NOT_VERIFIED` | CL gate failure | blocking |
| `TF_UPSTREAM_PEOPLE_BLOCKED` | People hub blocked | blocking |
| `TF_MISSING_PERSON_IDENTIFIER` | No person reference | warning |
| `TF_INVALID_MOVEMENT_TYPE` | Unknown movement type | warning |
| `TF_LOW_CONFIDENCE` | Below threshold | info |
| `TF_UNKNOWN_ERROR` | Unexpected error | blocking |

### Error Table

- [ ] All failures written to `people.people_errors` (shared)
- [ ] Error terminates execution for blocking severity
- [ ] Low-severity errors logged but execution continues

---

## 11. Freshness Decay Compliance

### Decay Rules

- [ ] Movement signals decay after `FRESHNESS_DAYS` (60)
- [ ] PASS status expires when all signals are stale
- [ ] Status reverts to IN_PROGRESS on expiry
- [ ] No automatic re-enrichment on expiry

### Freshness Check

- [ ] `detected_at >= NOW() - INTERVAL '60 days'`
- [ ] Only fresh signals count toward PASS criteria
- [ ] Expired signals remain in history (not deleted)

---

## 12. CI Doctrine Compliance

### Hub Boundaries (DG-003)

- [ ] No imports from Company Target (upstream)
- [ ] No imports from DOL (upstream)
- [ ] No lateral hub-to-hub imports (only spoke imports)

### Signal Validity (DG-007, DG-008)

- [ ] No old/prior context signal usage
- [ ] No signal refresh patterns
- [ ] Signals are origin-bound (declared source only)

### Immutability (DG-009, DG-010, DG-011)

- [ ] No movement record deletions
- [ ] No signal mutations
- [ ] Error rows never deleted (only resolved_at set)

---

## 13. External CL + Program Scope Compliance

### CL is External

- [ ] Understands CL is NOT part of Outreach program
- [ ] Does NOT invoke Company Lifecycle
- [ ] Does NOT gate on CL operations
- [ ] Consumes company_unique_id as read-only input

### Program Boundary Compliance

| Boundary | This Hub | Action |
|----------|----------|--------|
| CL (external) | Talent Flow | CONSUME company_unique_id |
| People Intelligence | Talent Flow | CONSUME person data |
| BIT Engine | Talent Flow | EMIT movement signals |

---

## Prime Directive

> **Talent Flow is a SENSOR. It detects movements. It NEVER enriches.**

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-25
**Hub**: Talent Flow (04.04.06)
**Doctrine Version**: 1.0
