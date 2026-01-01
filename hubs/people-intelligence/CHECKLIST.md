# People Intelligence — Compliance Checklist

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] No people records without company_sov_id
- [ ] outreach_context_id used for all operations

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state = TARGETABLE
- [ ] Requires verified pattern from Company Target
- [ ] Gate enforced before any processing

---

## Cost Discipline

- [ ] Enrichment only for measured slot deficit
- [ ] Tier-2 tools (Clay): Max ONE attempt per context
- [ ] MillionVerifier costs logged per verification
- [ ] All spend logged against context + company_sov_id

---

## Slot Model Compliance

- [ ] Slots defined: CHRO, HR_MANAGER, BENEFITS_LEAD, PAYROLL_ADMIN, HR_SUPPORT
- [ ] One person per slot per company
- [ ] Empty slots recorded in enrichment_queue
- [ ] SLOT_FILL_RATE metric tracked

---

## Output Compliance

- [ ] CSV is OUTPUT ONLY (never canonical storage)
- [ ] All canonical data in Neon PostgreSQL
- [ ] Phase 8 produces: people_final.csv, slot_assignments.csv, enrichment_queue.csv

---

## Error Handling Compliance

### When Errors Are Emitted

- [ ] Phase 5 email generation failure → `PI_EMAIL_GEN_FAIL` or `PI_NO_PATTERN_AVAILABLE`
- [ ] Phase 6 slot assignment failure → `PI_SLOT_COLLISION` or `PI_INVALID_TITLE`
- [ ] Phase 7 enrichment failure → `PI_TIER2_EXHAUSTED` or `PI_ENRICHMENT_NO_DEFICIT`
- [ ] Phase 8 output failure → `PI_OUTPUT_WRITE_FAIL`
- [ ] Verification failure → `PI_VERIFICATION_FAIL` or `PI_MILLIONVERIFIER_ERROR`
- [ ] Missing anchor → `PI_MISSING_COMPANY_ANCHOR` or `PI_MISSING_CONTEXT_ID`

### Blocking Failures

A failure is **blocking** if:
- [ ] No pattern available from Company Target
- [ ] Cannot generate valid email
- [ ] Slot collision unresolved
- [ ] Lifecycle gate not met (< TARGETABLE)
- [ ] Missing company anchor or context ID

### Resolution Authority

| Error Type | Resolver |
|------------|----------|
| Pattern errors | Resolve Company Target first |
| Slot errors | Human (choose winner) |
| Enrichment errors | Agent (new context) or Human |
| Verification errors | Agent (retry) or Human |
| Output errors | Agent (retry with new context) |

### Error Table

- [ ] All failures written to `outreach_errors.people_intelligence_errors`
- [ ] Error terminates execution immediately
- [ ] Spend frozen for context on blocking error

---

## 8. Kill-Switch Compliance

### UNKNOWN_ERROR Doctrine

- [ ] `PI_UNKNOWN_ERROR` triggers immediate FAIL
- [ ] Context is finalized with `final_state = 'FAIL'`
- [ ] Spend is frozen for that context
- [ ] Alert sent to on-call (PagerDuty/Slack)
- [ ] Stack trace captured in error table
- [ ] Human investigation required before retry

### Cross-Hub Repair Rules

| Upstream Dependency | Requirement |
|---------------------|-------------|
| Company Target | Pattern must exist before email generation |
| Company Target | Domain must be resolved before processing |

| Downstream Error | Resolution Required |
|------------------|---------------------|
| `OE_NO_CONTACTS_AVAILABLE` | Resolve PI slot assignment first |

### SLA Aging

- [ ] `sla_expires_at` enforced for all contexts
- [ ] Auto-ABORT on SLA expiry
- [ ] `outreach_ctx.abort_expired_sla()` runs every 5 minutes

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
