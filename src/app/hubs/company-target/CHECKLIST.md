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

- [x] `outreach_id` exists in `outreach.outreach` spine
- [x] Domain loaded from spine record (not CL)
- [x] `ENFORCE_OUTREACH_SPINE_ONLY = True` assertion present
- [x] Missing `outreach_id` → Write `CT-I-NOT-FOUND` error → STOP

### Explicit Prohibitions

- [x] Does NOT reference `sovereign_id`
- [x] Does NOT read from `cl.*` tables
- [x] Does NOT perform company matching
- [x] Does NOT use fuzzy logic
- [x] Does NOT retry failures
- [x] Does NOT mint any IDs

---

## 1. IMO Input Stage (I)

### Required Inputs

- [x] `outreach_id` received from spine (MANDATORY)
- [x] `domain` loaded from spine record
- [x] `correlation_id` for tracing (MANDATORY)

### Input Validation

- [x] FAIL IMMEDIATELY if `outreach_id` not found → `CT-I-NOT-FOUND`
- [x] FAIL IMMEDIATELY if `domain` is missing → `CT-I-NO-DOMAIN`
- [x] Check idempotency: if already PASS/FAIL, exit immediately

---

## 2. IMO Middle Stage (M)

### M1 — MX Gate (TOOL-004: MXLookup)

- [x] DNS MX record lookup performed
- [x] No MX records → `CT-M-NO-MX` → FAIL

### M2 — Pattern Generation

- [x] Patterns generated in FIXED order:
  1. `first.last@domain`
  2. `firstlast@domain`
  3. `f.last@domain`
  4. `first.l@domain`
  5. `first@domain`
  6. `last@domain`
  7. `info@domain`
  8. `contact@domain`

### M3 — SMTP Validation (TOOL-005: SMTPCheck)

- [x] SMTP RCPT TO check performed for each pattern
- [x] Accept → PASS (stop)
- [x] Reject → continue to next pattern
- [x] Catch-all detected → mark flag, use `first.last`

### M4 — Catch-All Handling

- [x] If catch-all: confidence reduced to 0.5
- [x] If catch-all: `is_catchall = true`
- [x] Pattern selected: `first.last@domain`

### M5 — Optional Tier-1 Verification (GATED) — DEFERRED

> **Note**: M5 is deferred. Core IMO (M1-M4) is complete. M5 can be added when MillionVerifier integration is needed.

- [ ] Only if Tier-0 inconclusive
- [ ] Only if `ALLOW_TIER1 = true`
- [ ] Only ONE verification attempt
- [ ] Uses TOOL-019: EmailVerifier
- [ ] Invalid → FAIL (no retry)

---

## 3. IMO Output Stage (O)

### PASS Output

- [x] Write to `outreach.company_target`
- [x] `execution_status = 'ready'`
- [x] `email_method` populated
- [x] `method_type` populated
- [x] `confidence_score` populated
- [x] `is_catchall` flag set
- [x] `imo_completed_at` timestamp set

### FAIL Output

- [x] Write to `outreach.company_target_errors`
- [x] `failure_code` populated
- [x] `blocking_reason` populated
- [x] `imo_stage` populated (I or M)
- [x] `retry_allowed = FALSE`
- [x] Execution STOPS (no downstream)

---

## 4. Write Hygiene (HARD LAW)

### Allowed Writes

- [x] `outreach.company_target` (PASS)
- [x] `outreach.company_target_errors` (FAIL)

### Forbidden Writes

- [x] **NO** writes to `marketing.*` tables
- [x] **NO** writes to `cl.*` tables
- [x] **NO** writes to `intake.*` tables
- [x] **NO** writes upstream

---

## 5. Tool Registry Compliance (SNAP_ON_TOOLBOX.yaml)

### Tier 0 (FREE) — ALLOWED

- [x] TOOL-004: MXLookup (dnspython)
- [x] TOOL-005: SMTPCheck (smtplib)

### Tier 2 (GATED) — CONDITIONAL — DEFERRED

> **Note**: Tied to M5. Deferred until MillionVerifier integration is needed.

- [ ] TOOL-019: EmailVerifier (MillionVerifier)
- [ ] Gate: `ALLOW_TIER1 = true`
- [ ] Gate: No prior verification for this `outreach_id`
- [ ] ONE attempt only

### Forbidden Tools

- [x] No tools outside SNAP_ON_TOOLBOX.yaml
- [x] No Tier-2 tools without gate check
- [x] No bulk enrichment

---

## 6. Forbidden Patterns (DEPRECATED)

The following are **permanently forbidden** in Company Target:

- [x] **NO** Phase 1 (Company Matching) — moved to CL
- [x] **NO** Phase 1b (Unmatched Hold) — moved to CL
- [x] **NO** fuzzy matching
- [x] **NO** fuzzy arbitration
- [x] **NO** retry/backoff logic
- [x] **NO** hold queues
- [x] **NO** rescue patterns
- [x] **NO** ID minting

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

- [x] `outreach_id`
- [x] IMO stage transitions (I → M → O)
- [x] Tool IDs used (TOOL-004, TOOL-005, etc.)
- [x] PASS or FAIL outcome
- [x] Duration in milliseconds
- [x] Error details (if FAIL)

---

## 9. CI Guard Compliance

The following guards run on every PR touching `hubs/company-target/**`:

- [x] No `sovereign_id` references
- [x] No CL table references
- [x] No `marketing.*` writes
- [x] No fuzzy matching imports
- [x] Spine guard assertion present
- [x] No retry logic
- [x] Doctrine lock comment present
- [x] Phase 1/1b files deleted

See: `.github/workflows/company_target_imo_guard.yml`

---

## 10. Terminal Failure Doctrine

> **FAIL is FOREVER. There are no retries.**

- [x] Failed records go to `outreach.company_target_errors`
- [x] `retry_allowed = FALSE` on all errors
- [x] Failed records do NOT proceed to downstream spokes
- [x] Resolution requires human intervention + new `outreach_id`

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
