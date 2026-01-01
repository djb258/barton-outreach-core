# DOL Filings — Compliance Checklist

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] Filings attached to existing companies only
- [ ] No company minting from DOL data

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state = ACTIVE
- [ ] Gate enforced before filing attachment

---

## EIN Matching Compliance

- [ ] Exact EIN match only
- [ ] No fuzzy matching
- [ ] No retries on mismatch
- [ ] Unmatched filings logged but not attached

---

## Data Compliance

- [ ] Bulk CSV processing only
- [ ] No paid enrichment tools
- [ ] Form 5500, 5500-SF, Schedule A supported
- [ ] Filing match rate tracked

---

## Signal Compliance

- [ ] FORM_5500_FILED signal emitted correctly
- [ ] LARGE_PLAN signal for >= 100 participants
- [ ] BROKER_CHANGE signal for year-over-year changes

---

## Error Handling Compliance

### When Errors Are Emitted

- [ ] CSV ingest failure → `DOL_CSV_NOT_FOUND` or `DOL_CSV_FORMAT_ERROR`
- [ ] Parse failure → `DOL_MISSING_EIN` or `DOL_INVALID_EIN_FORMAT`
- [ ] EIN match failure → `DOL_EIN_NO_MATCH` (expected for some)
- [ ] Attach failure → `DOL_ATTACH_DUPLICATE` or `DOL_NEON_WRITE_FAIL`
- [ ] Lifecycle gate failure → `DOL_LIFECYCLE_GATE_FAIL`

### Blocking Failures

A failure is **blocking** if:
- [ ] CSV file not found or corrupted
- [ ] Database write fails
- [ ] Multiple companies match same EIN (data integrity issue)

### Non-Blocking Failures

These are **expected** and logged but do not block:
- [ ] EIN not found in company_master (skip record)
- [ ] Filing already attached (idempotent)
- [ ] Missing non-critical field (skip record)

### Resolution Authority

| Error Type | Resolver |
|------------|----------|
| CSV errors | Human (locate/fix file) |
| EIN no match | N/A (expected) |
| Multiple match | Human (fix duplicate companies) |
| Write errors | Agent (retry with new context) |

### Error Table

- [ ] All failures written to `outreach_errors.dol_filings_errors`
- [ ] EIN no-match logged as `info` severity (not blocking)
- [ ] Duplicates logged as `info` severity (idempotent)

---

## 8. Signal Validity Compliance

### Execution Order

- [ ] Executes SECOND in canonical order (after CT)
- [ ] Verifies Company Target PASS before proceeding
- [ ] Verifies company_sov_id exists before EIN matching

### Signal Origin

- [ ] company_sov_id sourced via Company Target (origin: CL)
- [ ] domain sourced from Company Target only
- [ ] No signals consumed from People Intelligence
- [ ] No signals consumed from Blog Content

### Signal Validity

- [ ] Signals are origin-bound (declared source only)
- [ ] Signals are run-bound to current outreach_context_id
- [ ] Signals from prior contexts are NOT authoritative
- [ ] Signal age does NOT justify action

### Non-Refreshing

- [ ] Does NOT fix Company Target errors
- [ ] Does NOT retry EIN matches (exact match or FAIL)
- [ ] Does NOT refresh signals from prior contexts
- [ ] Missing upstream signal → FAIL (not retry)

### Downstream Effects

- [ ] On PASS: People Intelligence may execute
- [ ] On FAIL: People, Blog do NOT execute
- [ ] FAIL propagates forward (no skip-and-continue)
- [ ] Does NOT unlock People alone (CT must also PASS)

---

## 9. Kill-Switch Compliance

### UNKNOWN_ERROR Doctrine

- [ ] `DOL_UNKNOWN_ERROR` triggers immediate FAIL
- [ ] Context is finalized with `final_state = 'FAIL'`
- [ ] Spend is frozen for that context
- [ ] Alert sent to on-call (PagerDuty/Slack)
- [ ] Stack trace captured in error table
- [ ] Human investigation required before retry

### Cross-Hub Repair Rules

This hub operates independently with no cross-hub dependencies.

| Error Type | Resolution |
|------------|------------|
| `DOL_EIN_NO_MATCH` | N/A (cannot mint companies) |
| `DOL_CSV_*` | Human: Fix source file |

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

- [ ] This hub repairs only DOL_* errors
- [ ] Does NOT repair CT_*, PI_*, OE_*, BC_* errors
- [ ] Repairs unblock, they do not rewrite

### Context Lineage

- [ ] All retries create new `outreach_context_id`
- [ ] New contexts do NOT inherit signals from prior contexts
- [ ] Prior context remains for audit (never deleted)

---

## 11. CI Doctrine Compliance

### Tool Usage (DG-001, DG-002)

- [ ] No paid tools in this hub (bulk CSV only)
- [ ] All tools listed in `tooling/tool_registry.md`

### Hub Boundaries (DG-003)

- [ ] No imports from downstream hubs (People, Blog)
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
