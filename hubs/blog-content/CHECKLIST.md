# Blog Content — Compliance Checklist

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] Cannot mint new companies
- [ ] Cannot revive dead companies
- [ ] Company Lifecycle read-only

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state = ACTIVE
- [ ] Gate enforced before signal emission
- [ ] Lifecycle state never modified by this hub

---

## Signal-Only Compliance

- [ ] BIT modulation only
- [ ] Cannot trigger enrichment
- [ ] No paid tools used
- [ ] Signals emitted to BIT engine only

---

## Signal Types

- [ ] FUNDING_EVENT (+15.0) — configured correctly
- [ ] ACQUISITION (+12.0) — configured correctly
- [ ] LEADERSHIP_CHANGE (+8.0) — configured correctly
- [ ] EXPANSION (+7.0) — configured correctly
- [ ] PRODUCT_LAUNCH (+5.0) — configured correctly
- [ ] PARTNERSHIP (+5.0) — configured correctly
- [ ] LAYOFF (-3.0) — configured correctly
- [ ] NEGATIVE_NEWS (-5.0) — configured correctly

---

## Error Handling Compliance

### When Errors Are Emitted

- [ ] Content ingest failure → `BC_SOURCE_UNAVAILABLE` or `BC_PARSE_ERROR`
- [ ] Company match failure → `BC_COMPANY_NOT_FOUND` (expected for some)
- [ ] Classification failure → `BC_UNKNOWN_EVENT_TYPE`
- [ ] Lifecycle gate failure → `BC_LIFECYCLE_GATE_FAIL`
- [ ] Signal emission failure → `BC_SIGNAL_EMIT_FAIL`

### Blocking Failures

A failure is **blocking** if:
- [ ] Content source completely unavailable
- [ ] BIT engine error prevents signal emission
- [ ] Critical parse error

### Non-Blocking Failures

These are **expected** and logged but do not block:
- [ ] Company not found (cannot mint, just skip)
- [ ] Unknown event type (log and skip)
- [ ] Company not in ACTIVE lifecycle (skip signal)

### Resolution Authority

| Error Type | Resolver |
|------------|----------|
| Source errors | Agent (retry with new context) |
| Company not found | N/A (cannot mint) |
| Classification errors | Human (update rules) |
| Signal errors | Agent (retry with new context) |

### Error Table

- [ ] All failures written to `outreach_errors.blog_content_errors`
- [ ] Company not found logged as `info` (not blocking)
- [ ] Unknown event type logged as `warning`

---

## 8. Signal Validity Compliance

### Execution Order

- [ ] Executes LAST in canonical order (after CT, DOL, PI)
- [ ] Verifies all upstream hubs PASS before proceeding
- [ ] Halts on any upstream FAIL

### Signal Origin

- [ ] company_sov_id sourced via Company Target (origin: CL)
- [ ] domain sourced from Company Target only
- [ ] BIT_SCORE sourced from Company Target only
- [ ] regulatory_signals sourced from DOL Filings only
- [ ] slot_assignments sourced from People Intelligence only

### Signal Validity

- [ ] Signals are origin-bound (declared source only)
- [ ] Signals are run-bound to current outreach_id
- [ ] Signals from prior contexts are NOT authoritative
- [ ] Signal age does NOT justify action
- [ ] Signal age does NOT trigger enrichment
- [ ] Signal age does NOT trigger spend

### Non-Refreshing

- [ ] Does NOT fix upstream errors
- [ ] Does NOT refresh signals from prior contexts
- [ ] Does NOT re-enrich upstream data
- [ ] Missing upstream signal → FAIL (not retry)

### Downstream Effects

- [ ] On PASS: Context finalized as PASS
- [ ] On FAIL: Context finalized as FAIL
- [ ] No downstream hubs (last in order)
- [ ] Emits timing signals to BIT Engine only

### Blog-Specific Prohibitions

- [ ] Does NOT trigger enrichment
- [ ] Does NOT trigger spend
- [ ] Does NOT mint or revive companies
- [ ] Timing signals only — no authority signals

---

## 9. Kill-Switch Compliance

### UNKNOWN_ERROR Doctrine

- [ ] `BC_UNKNOWN_ERROR` triggers immediate FAIL
- [ ] Context is finalized with `final_state = 'FAIL'`
- [ ] Spend is frozen for that context
- [ ] Alert sent to on-call (PagerDuty/Slack)
- [ ] Stack trace captured in error table
- [ ] Human investigation required before retry

### Cross-Hub Repair Rules

This hub operates independently with no cross-hub dependencies.

| Error Type | Resolution |
|------------|------------|
| `BC_COMPANY_NOT_FOUND` | N/A (cannot mint companies) |
| `BC_SOURCE_UNAVAILABLE` | Agent: Retry with new context |

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

- [ ] This hub repairs only BC_* errors
- [ ] Does NOT repair CT_*, PI_*, DOL_*, OE_* errors
- [ ] Repairs unblock, they do not rewrite

### Context Lineage

- [ ] All retries create new `outreach_id`
- [ ] New contexts do NOT inherit signals from prior contexts
- [ ] Prior context remains for audit (never deleted)

---

## 11. CI Doctrine Compliance

### Tool Usage (DG-001, DG-002)

- [ ] No paid tools in this hub (signal processing only)
- [ ] All tools listed in `tooling/tool_registry.md`

### Hub Boundaries (DG-003)

- [ ] Last in order — no downstream hubs to import from
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

## 12. External CL + Program Scope Compliance

### CL is External

- [ ] Understands CL is NOT part of Outreach program
- [ ] Does NOT invoke Company Lifecycle (CL is external)
- [ ] Does NOT gate on CL operations (CL already verified existence)
- [ ] Receives company_unique_id via Company Target (not directly from CL)

### Outreach Context Authority

- [ ] outreach_id sourced from Outreach Orchestration (not CL)
- [ ] All operations bound by outreach_id
- [ ] Does NOT mint outreach_id (Orchestration does)
- [ ] Reads from outreach.outreach_context table

### Consumer-Only Compliance

- [ ] CONSUMES all upstream data (does NOT enrich)
- [ ] Provides TIMING signals only (no authority signals)
- [ ] Does NOT trigger enrichment
- [ ] Does NOT trigger spend
- [ ] Does NOT duplicate upstream enrichment

### Program Boundary Compliance

| Boundary | This Hub | Action |
|----------|----------|--------|
| CL (external) | Blog Content | NO DIRECT ACCESS |
| Company Target (upstream) | Blog Content | CONSUME company_unique_id, domain |
| DOL Filings (upstream) | Blog Content | CONSUME regulatory_signals |
| People Intelligence (upstream) | Blog Content | CONSUME slot_assignments |
| BIT Engine (downstream) | Blog Content | EMIT timing_signals |

### Explicit Prohibitions

- [ ] Does NOT call CL APIs or endpoints
- [ ] Does NOT verify company existence (CL did that)
- [ ] Does NOT retry CL operations
- [ ] Does NOT create outreach_id
- [ ] Does NOT trigger any paid enrichment

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-02
**Hub**: Blog Content (04.04.05)
**Doctrine Version**: External CL + Outreach Program v1.0
