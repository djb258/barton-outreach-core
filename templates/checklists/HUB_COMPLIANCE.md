# Hub Compliance Checklist

This checklist must be completed before any hub can ship.
No exceptions. No partial compliance.

---

## Hub Identity

- [ ] Hub ID assigned (unique, immutable)
- [ ] Process ID assigned (execution / trace ID)
- [ ] Hub Name defined
- [ ] Hub Owner assigned

---

## CTB Placement

- [ ] CTB path defined
- [ ] Branch level specified (sys / ui / ai / infra)
- [ ] Parent hub identified (if applicable)

---

## Altitude Scope

- [ ] Altitude level declared (30k / 20k / 10k / 5k)
- [ ] Scope appropriate for declared altitude

---

## IMO Structure

### Ingress (I Layer)

- [ ] Ingress points defined
- [ ] Ingress contains no logic
- [ ] Ingress contains no state
- [ ] UI (if present) is dumb ingress only

### Middle (M Layer)

- [ ] All logic resides in M layer
- [ ] All state resides in M layer
- [ ] All decisions occur in M layer
- [ ] Tools scoped to M layer only

### Egress (O Layer)

- [ ] Egress points defined
- [ ] Egress contains no logic
- [ ] Egress contains no state

---

## Spokes

- [ ] All spokes typed as I or O only
- [ ] No spoke contains logic
- [ ] No spoke contains state
- [ ] No spoke owns tools
- [ ] No spoke performs decisions

---

## Tools

- [ ] All tools scoped inside this hub
- [ ] All tools have Doctrine ID
- [ ] All tools have ADR reference
- [ ] No tools exposed to spokes

---

## Connectors

- [ ] Connectors (API / CSV / Event) defined
- [ ] Connector direction specified (Inbound / Outbound)
- [ ] Connector contracts documented

---

## Cross-Hub Isolation

- [ ] No sideways hub-to-hub calls
- [ ] No cross-hub logic
- [ ] No shared mutable state between hubs

---

## Guard Rails

- [ ] Rate limits defined
- [ ] Timeouts defined
- [ ] Validation implemented
- [ ] Permissions enforced

---

## Kill Switch

- [ ] Kill switch endpoint defined
- [ ] Kill switch activation criteria documented
- [ ] Kill switch tested and verified
- [ ] Emergency contact assigned

---

## Rollback

- [ ] Rollback plan documented
- [ ] Rollback tested and verified

---

## Observability

- [ ] Logging implemented
- [ ] Metrics implemented
- [ ] Alerts configured
- [ ] Shipping without observability is forbidden

---

## Failure Modes

- [ ] Failure modes documented
- [ ] Severity levels assigned
- [ ] Remediation steps defined

---

## Human Override

- [ ] Override conditions defined
- [ ] Override approvers assigned

---

## Traceability

- [ ] PRD exists and is current
- [ ] ADR exists (if decisions required)
- [ ] Linear issue linked
- [ ] PR linked

---

## Sovereign ID Compliance

- [ ] Uses Company Sovereign ID as sole company identity
- [ ] No hub-specific company ID created
- [ ] Company Lifecycle treated as read-only dependency
- [ ] Context IDs are disposable (TTL-bound, kill-switchable)
- [ ] No minting, reviving, or mutating company existence

---

## Lifecycle Gate Compliance

- [ ] Minimum lifecycle state declared
- [ ] Gate enforced before any processing
- [ ] Lifecycle state never modified by this hub
- [ ] BIT signals do not mutate lifecycle

### Lifecycle States Reference

```
INTAKE → SOVEREIGN_MINTED → ACTIVE → TARGETABLE → ENGAGED → CLIENT → DORMANT → DEAD
```

---

## Cost Discipline

### Tool Registry Compliance

- [ ] All tools registered in tool_registry.md
- [ ] No unauthorized tools used
- [ ] Each tool scoped to specific sub-hub(s)

### Tier Enforcement

- [ ] Tier-0 tools: Used freely (no gate)
- [ ] Tier-1 tools: Gated by lifecycle ≥ ACTIVE
- [ ] Tier-2 tools: Max ONE attempt per outreach_context
- [ ] All spend logged against context + company
- [ ] Firewall blocks illegal tool calls

### Cost Rules

- [ ] No paid tools before lifecycle allows
- [ ] No enrichment without measured deficit
- [ ] No retries without new context or TTL

---

## Global Invariants

- [ ] One sovereign company ID only
- [ ] Context IDs are disposable (not permanent identity)
- [ ] CSV is never canonical storage
- [ ] Sub-hubs are independently testable and killable

---

## Compliance Rule

If any box is unchecked, this hub may not ship.
