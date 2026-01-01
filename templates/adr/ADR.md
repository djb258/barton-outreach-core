# ADR: [Decision Title]

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-XXX |
| **Status** | [ ] Proposed / [ ] Accepted / [ ] Superseded / [ ] Deprecated |
| **Date** | YYYY-MM-DD |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | |
| **Hub ID** | |

---

## Scope

| Layer | Affected |
|-------|----------|
| I — Ingress | [ ] |
| M — Middle | [ ] |
| O — Egress | [ ] |

---

## Context

_What problem prompted this decision? Why must a decision be made now?_

---

## Decision

_State the decision clearly. Document WHY this choice was made, not WHAT to build._

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| | |
| Do Nothing | |

---

## Consequences

### Enables

-

### Prevents

-

---

## Guard Rails

_Constraints that bound this decision. Do not define logic or implementation._

| Type | Value |
|------|-------|
| Rate Limit | |
| Timeout | |
| Kill Switch | |

---

## Rollback

_How is this decision reversed if it fails? Do not define remediation logic._

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| PRD | |
| Sub-PRD | |
| Linear Issue | |
| PR(s) | |

---

## Lifecycle Impact

_Does this decision affect lifecycle gate requirements?_

| Current Gate | Proposed Gate | Justification |
|--------------|---------------|---------------|
| | | |

---

## Cost Impact

_Does this decision introduce or modify tool usage?_

| Tool | Tier | Cost Class | Usage Limit |
|------|------|------------|-------------|
| | 0 / 1 / 2 | Free / Low / Premium | |

### Cost Rules Compliance

- [ ] No new Tier-2 tools without explicit approval
- [ ] Tool scoped to specific sub-hub(s) only
- [ ] Firewall rules updated to enforce limits
- [ ] Spend logging configured for context + company

---

## Sovereign ID Impact

_Does this decision affect identity handling?_

- [ ] No new company identifiers created
- [ ] Uses Company Sovereign ID as sole authority
- [ ] Context IDs remain disposable (not permanent)
- [ ] No mutation of lifecycle state

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |
