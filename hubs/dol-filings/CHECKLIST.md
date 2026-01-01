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

## 8. Kill-Switch Compliance

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

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
