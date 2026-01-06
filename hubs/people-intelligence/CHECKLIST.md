# People Intelligence — Compliance Checklist

---

## Sovereign ID Compliance

- [ ] Uses company_sov_id as sole company identity
- [ ] No people records without company_sov_id
- [ ] outreach_id used for all operations

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

## 8. Signal Validity Compliance

### Execution Order

- [ ] Executes THIRD in canonical order (after CT, DOL)
- [ ] Verifies Company Target PASS before proceeding
- [ ] Verifies verified_pattern exists before proceeding

### Signal Origin

- [ ] company_sov_id sourced via Company Target (origin: CL)
- [ ] verified_pattern sourced from Company Target only
- [ ] domain sourced from Company Target only
- [ ] regulatory_signals sourced from DOL Filings only
- [ ] No signals consumed from Blog Content

### Signal Validity

- [ ] Signals are origin-bound (declared source only)
- [ ] Signals are run-bound to current outreach_id
- [ ] Signals from prior contexts are NOT authoritative
- [ ] Signal age does NOT justify action

### Non-Refreshing

- [ ] Does NOT fix Company Target errors (pattern missing → FAIL)
- [ ] Does NOT re-enrich Company Target domain
- [ ] Does NOT use stale pattern from prior context
- [ ] Missing upstream signal → FAIL (not retry)

### Downstream Effects

- [ ] On PASS: Blog Content may execute
- [ ] On FAIL: Blog does NOT execute
- [ ] FAIL propagates forward (no skip-and-continue)

---

## 9. Kill-Switch Compliance

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

## 10. Repair Doctrine Compliance

### History Immutability

- [ ] Error rows are never deleted (only `resolved_at` set)
- [ ] Signals once emitted are never modified
- [ ] Prior contexts are never edited or reopened
- [ ] Cost logs are never adjusted retroactively

### Repair Scope

- [ ] This hub repairs only PI_* errors
- [ ] Does NOT repair CT_*, DOL_*, OE_*, BC_* errors
- [ ] Repairs unblock, they do not rewrite

### Context Lineage

- [ ] All retries create new `outreach_id`
- [ ] New contexts do NOT inherit signals from prior contexts
- [ ] Prior context remains for audit (never deleted)

---

## 11. CI Doctrine Compliance

### Tool Usage (DG-001, DG-002)

- [ ] All paid tools called with `outreach_id`
- [ ] All tools listed in `tooling/tool_registry.md`
- [ ] Tier-2 tools use `can_attempt_tier2()` guard

### Hub Boundaries (DG-003)

- [ ] No imports from downstream hubs (Blog)
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

- [ ] CONSUMES verified_pattern from Company Target (does NOT discover patterns)
- [ ] CONSUMES domain from Company Target (does NOT resolve domains)
- [ ] CONSUMES regulatory_signals from DOL Filings (does NOT fetch DOL data)
- [ ] Does NOT duplicate upstream enrichment

### Program Boundary Compliance

| Boundary | This Hub | Action |
|----------|----------|--------|
| CL (external) | People Intelligence | NO DIRECT ACCESS |
| Company Target (upstream) | People Intelligence | CONSUME pattern, domain |
| DOL Filings (upstream) | People Intelligence | CONSUME regulatory_signals |
| Blog Content (downstream) | People Intelligence | EMIT slot_assignments |

---

## Compliance Rule

**If any box is unchecked, this hub may not ship.**

---

**Last Updated**: 2026-01-02
**Hub**: People Intelligence (04.04.02)
**Doctrine Version**: External CL + Outreach Program v1.0
