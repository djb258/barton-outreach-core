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

## 8. Kill-Switch Compliance

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

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
