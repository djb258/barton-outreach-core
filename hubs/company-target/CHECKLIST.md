# Company Target — Compliance Checklist

This checklist must be completed before any changes can ship.
No exceptions. No partial compliance.

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] Does NOT mint company identifiers
- [ ] Does NOT revive dead companies
- [ ] Company Lifecycle treated as read-only dependency
- [ ] outreach_context_id used for all operations

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state = ACTIVE
- [ ] Gate enforced before any processing
- [ ] Lifecycle state never modified by this hub
- [ ] BIT signals do not mutate lifecycle

---

## Cost Discipline

### Tool Registry Compliance

- [ ] All tools registered in tool_registry.md
- [ ] No unauthorized tools used
- [ ] Each tool scoped to this sub-hub only

### Tier Enforcement

- [ ] Tier-0 tools: Used freely (no gate)
- [ ] Tier-1 tools: Gated by lifecycle >= ACTIVE
- [ ] Tier-2 tools: Max ONE attempt per outreach_context
- [ ] All spend logged against context + company_sov_id
- [ ] Firewall blocks illegal tool calls

---

## Pipeline Compliance

- [ ] Phase 1: Company Matching (no identity minting)
- [ ] Phase 2: Domain Resolution (DNS/MX only)
- [ ] Phase 3: Email Pattern Waterfall (tiered correctly)
- [ ] Phase 4: Pattern Verification (local checks)

---

## IMO Structure

- [ ] Ingress contains no logic
- [ ] Middle contains all logic
- [ ] Egress contains no logic
- [ ] Spokes are I/O only

---

## Global Invariants

- [ ] One sovereign company ID only
- [ ] Context IDs are disposable
- [ ] No enrichment without deficit
- [ ] CSV is never canonical storage

---

## Error Handling Compliance

### When Errors Are Emitted

- [ ] Phase 1 match failure → `CT_MATCH_*` error
- [ ] Phase 2 domain failure → `CT_DOMAIN_*` error
- [ ] Phase 3 pattern failure → `CT_PATTERN_*` or `CT_TIER2_EXHAUSTED`
- [ ] Phase 4 verification failure → `CT_VERIFICATION_*` error
- [ ] Lifecycle gate failure → `CT_LIFECYCLE_GATE_FAIL`
- [ ] Missing identity → `CT_MISSING_SOV_ID` or `CT_MISSING_CONTEXT_ID`

### Blocking Failures

A failure is **blocking** if:
- [ ] No company match found (cannot proceed without anchor)
- [ ] Domain unresolved after all attempts
- [ ] Pattern not found after Tier-2 exhausted
- [ ] Lifecycle gate not met
- [ ] Missing sovereign ID or context ID

### Resolution Authority

| Error Type | Resolver |
|------------|----------|
| Match errors | Human (investigate source) |
| Domain errors | Agent (retry with new context) |
| Pattern errors | Human (manual research) |
| Lifecycle errors | Wait (automatic on state change) |
| Provider errors | Agent (retry with new context) |

### Error Table

- [ ] All failures written to `outreach_errors.company_target_errors`
- [ ] Error terminates execution immediately
- [ ] Spend frozen for context on blocking error

---

## 8. Signal Validity Compliance

### Execution Order

- [ ] Executes FIRST in canonical order
- [ ] No upstream sub-hub dependencies (CL is external)
- [ ] Verifies CL lifecycle_state >= ACTIVE before proceeding

### Signal Origin

- [ ] company_sov_id sourced from Company Lifecycle only
- [ ] lifecycle_state sourced from Company Lifecycle only
- [ ] No signals consumed from DOL, People, or Blog

### Signal Validity

- [ ] Signals are origin-bound (declared source only)
- [ ] Signals are run-bound to current outreach_context_id
- [ ] Signals from prior contexts are NOT authoritative
- [ ] Signal age does NOT justify action

### Non-Refreshing

- [ ] Does NOT re-query CL for "fresher" data within same context
- [ ] Does NOT re-enrich on stale signal
- [ ] Missing signal → FAIL (not retry)

### Downstream Effects

- [ ] On PASS: DOL Filings may execute
- [ ] On FAIL: DOL, People, Blog do NOT execute
- [ ] FAIL propagates forward (no skip-and-continue)

---

## 9. Kill-Switch Compliance

### UNKNOWN_ERROR Doctrine

- [ ] `CT_UNKNOWN_ERROR` triggers immediate FAIL
- [ ] Context is finalized with `final_state = 'FAIL'`
- [ ] Spend is frozen for that context
- [ ] Alert sent to on-call (PagerDuty/Slack)
- [ ] Stack trace captured in error table
- [ ] Human investigation required before retry

### Cross-Hub Repair Rules

| Downstream Error | Resolution Required |
|------------------|---------------------|
| `PI_NO_PATTERN_AVAILABLE` | Resolve CT pattern discovery first |
| `OE_MISSING_DOMAIN` | Resolve CT domain resolution first |
| `OE_MISSING_PATTERN` | Resolve CT pattern discovery first |

### SLA Aging

- [ ] `sla_expires_at` enforced for all contexts
- [ ] Auto-ABORT on SLA expiry
- [ ] `outreach_ctx.abort_expired_sla()` runs every 5 minutes

---

## 10. Repair Doctrine Compliance

### History Immutability

- [ ] Error rows are never deleted (only `resolved_at` set)
- [ ] Signals once emitted are never modified
- [ ] Prior contexts are never edited or reopened
- [ ] Cost logs are never adjusted retroactively

### Repair Scope

- [ ] This hub repairs only CT_* errors
- [ ] Does NOT repair PI_*, DOL_*, OE_*, BC_* errors
- [ ] Repairs unblock, they do not rewrite

### Context Lineage

- [ ] All retries create new `outreach_context_id`
- [ ] New contexts do NOT inherit signals from prior contexts
- [ ] Prior context remains for audit (never deleted)

---

## 11. CI Doctrine Compliance

### Tool Usage (DG-001, DG-002)

- [ ] All paid tools called with `outreach_context_id`
- [ ] All tools listed in `tooling/tool_registry.md`
- [ ] Tier-2 tools use `can_attempt_tier2()` guard

### Hub Boundaries (DG-003)

- [ ] No imports from downstream hubs (DOL, People, Blog)
- [ ] No lateral hub-to-hub imports (only spoke imports)

### Doctrine Sync (DG-005, DG-006)

- [ ] PRD changes accompanied by CHECKLIST changes
- [ ] Error codes registered in `docs/error_codes.md`

### Signal Validity (DG-007, DG-008)

- [ ] No old/prior context signal usage
- [ ] No signal refresh patterns

### Immutability (DG-009, DG-010, DG-011, DG-012)

- [ ] No lifecycle state mutations
- [ ] No error row deletions
- [ ] No context resurrection
- [ ] No signal mutations

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
