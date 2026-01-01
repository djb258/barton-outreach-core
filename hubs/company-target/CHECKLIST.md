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

## Compliance Rule

**If any box is unchecked, this hub may not ship.**
