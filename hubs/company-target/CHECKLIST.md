# Company Target — IMO Compliance Checklist (v3.0)

**DOCTRINE LOCK**: This checklist enforces the Company Target IMO gate.
No code ships unless every box is checked. No exceptions. No partial compliance.

**Architecture**: Single-Pass IMO Gate
**PRD**: Company Target (Execution Prep Sub-Hub) v3.0
**ADR**: ADR-CT-IMO-001

---

## 0. Spine-First Gate (FIRST CHECK)

> Company Target operates ONLY on `outreach_id` from the Outreach Spine.
> It NEVER references `sovereign_id` or touches CL tables directly.

### Gate Enforcement

- [ ] `outreach_id` exists in `outreach.outreach` spine
- [ ] Domain loaded from spine record (not CL)
- [ ] `ENFORCE_OUTREACH_SPINE_ONLY = True` assertion present
- [ ] Missing `outreach_id` → Write `CT-I-NOT-FOUND` error → STOP

### Explicit Prohibitions

- [ ] Does NOT reference `sovereign_id`
- [ ] Does NOT read from `cl.*` tables
- [ ] Does NOT perform company matching
- [ ] Does NOT use fuzzy logic
- [ ] Does NOT retry failures
- [ ] Does NOT mint any IDs

---

## 1. IMO Input Stage (I)

### Required Inputs

- [ ] `outreach_id` received from spine (MANDATORY)
- [ ] `domain` loaded from spine record
- [ ] `correlation_id` for tracing (MANDATORY)

### Input Validation

- [ ] FAIL IMMEDIATELY if `outreach_id` not found → `CT-I-NOT-FOUND`
- [ ] FAIL IMMEDIATELY if `domain` is missing → `CT-I-NO-DOMAIN`
- [ ] Check idempotency: if already PASS/FAIL, exit immediately

---

## 2. IMO Middle Stage (M)

### M1 — MX Gate (TOOL-004: MXLookup)

- [ ] DNS MX record lookup performed
- [ ] No MX records → `CT-M-NO-MX` → FAIL

### M2 — Pattern Generation

- [ ] Patterns generated in FIXED order:
  1. `first.last@domain`
  2. `firstlast@domain`
  3. `f.last@domain`
  4. `first.l@domain`
  5. `first@domain`
  6. `last@domain`
  7. `info@domain`
  8. `contact@domain`

### M3 — SMTP Validation (TOOL-005: SMTPCheck)

- [ ] SMTP RCPT TO check performed for each pattern
- [ ] Accept → PASS (stop)
- [ ] Reject → continue to next pattern
- [ ] Catch-all detected → mark flag, use `first.last`

### M4 — Catch-All Handling

- [ ] If catch-all: confidence reduced to 0.5
- [ ] If catch-all: `is_catchall = true`
- [ ] Pattern selected: `first.last@domain`

### M5 — Optional Tier-1 Verification (GATED)

- [ ] Only if Tier-0 inconclusive
- [ ] Only if `ALLOW_TIER1 = true`
- [ ] Only ONE verification attempt
- [ ] Uses TOOL-019: EmailVerifier
- [ ] Invalid → FAIL (no retry)

---

## 3. IMO Output Stage (O)

### PASS Output

- [ ] Write to `outreach.company_target`
- [ ] `execution_status = 'ready'`
- [ ] `email_method` populated
- [ ] `method_type` populated
- [ ] `confidence_score` populated
- [ ] `is_catchall` flag set
- [ ] `imo_completed_at` timestamp set

### FAIL Output

- [ ] Write to `outreach.company_target_errors`
- [ ] `failure_code` populated
- [ ] `blocking_reason` populated
- [ ] `imo_stage` populated (I or M)
- [ ] `retry_allowed = FALSE`
- [ ] Execution STOPS (no downstream)

---

## 4. Write Hygiene (HARD LAW)

### Allowed Writes

- [ ] `outreach.company_target` (PASS)
- [ ] `outreach.company_target_errors` (FAIL)

### Forbidden Writes

- [ ] **NO** writes to `marketing.*` tables
- [ ] **NO** writes to `cl.*` tables
- [ ] **NO** writes to `intake.*` tables
- [ ] **NO** writes upstream

---

## 5. Tool Registry Compliance (SNAP_ON_TOOLBOX.yaml)

### Tier 0 (FREE) — ALLOWED

- [ ] TOOL-004: MXLookup (dnspython)
- [ ] TOOL-005: SMTPCheck (smtplib)

### Tier 2 (GATED) — CONDITIONAL

- [ ] TOOL-019: EmailVerifier (MillionVerifier)
- [ ] Gate: `ALLOW_TIER1 = true`
- [ ] Gate: No prior verification for this `outreach_id`
- [ ] ONE attempt only

### Forbidden Tools

- [ ] No tools outside SNAP_ON_TOOLBOX.yaml
- [ ] No Tier-2 tools without gate check
- [ ] No bulk enrichment

---

## 6. Forbidden Patterns (DEPRECATED)

The following are **permanently forbidden** in Company Target:

- [ ] **NO** Phase 1 (Company Matching) — moved to CL
- [ ] **NO** Phase 1b (Unmatched Hold) — moved to CL
- [ ] **NO** fuzzy matching
- [ ] **NO** fuzzy arbitration
- [ ] **NO** retry/backoff logic
- [ ] **NO** hold queues
- [ ] **NO** rescue patterns
- [ ] **NO** ID minting

---

## 7. Error Codes (v3.0)

### Input Stage Errors

| Code | Stage | Description |
|------|-------|-------------|
| `CT-I-NOT-FOUND` | I | outreach_id not in spine |
| `CT-I-NO-DOMAIN` | I | No domain in spine record |
| `CT-I-ALREADY-PROCESSED` | I | Already PASS or FAIL |

### Middle Stage Errors

| Code | Stage | Description |
|------|-------|-------------|
| `CT-M-NO-MX` | M | No MX records for domain |
| `CT-M-NO-PATTERN` | M | All patterns rejected |
| `CT-M-SMTP-FAIL` | M | SMTP connection failure |
| `CT-M-VERIFY-FAIL` | M | Tier-1 verification failed |

---

## 8. Logging (MANDATORY)

Every IMO run MUST log:

- [ ] `outreach_id`
- [ ] IMO stage transitions (I → M → O)
- [ ] Tool IDs used (TOOL-004, TOOL-005, etc.)
- [ ] PASS or FAIL outcome
- [ ] Duration in milliseconds
- [ ] Error details (if FAIL)

---

## 9. CI Guard Compliance

The following guards run on every PR touching `hubs/company-target/**`:

- [ ] No `sovereign_id` references
- [ ] No CL table references
- [ ] No `marketing.*` writes
- [ ] No fuzzy matching imports
- [ ] Spine guard assertion present
- [ ] No retry logic
- [ ] Doctrine lock comment present
- [ ] Phase 1/1b files deleted

See: `.github/workflows/company_target_imo_guard.yml`

---

## 10. Terminal Failure Doctrine

> **FAIL is FOREVER. There are no retries.**

- [ ] Failed records go to `outreach.company_target_errors`
- [ ] `retry_allowed = FALSE` on all errors
- [ ] Failed records do NOT proceed to downstream spokes
- [ ] Resolution requires human intervention + new `outreach_id`

---

## Prime Directive (v3.0)

> **Company Target is an execution-readiness gate, not an identity authority.**
> **If the code does anything outside I → M → O, it is WRONG.**

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-07
**Hub**: Company Target (04.04.01)
**Architecture**: Single-Pass IMO Gate
**Doctrine Version**: 3.0
