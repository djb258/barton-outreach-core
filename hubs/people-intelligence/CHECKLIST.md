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

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
