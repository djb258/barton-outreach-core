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

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
