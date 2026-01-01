# PRD — Hub

## 1. Overview

- **System Name:**
- **Hub Name:**
- **Owner:**
- **Version:**

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | _(unique, immutable identifier)_ |
| **Process ID** | _(execution / trace ID)_ |

---

## 3. Purpose

_What does this hub do? What boundary does it own? A hub is the application — it owns logic, state, CTB structure, altitude, and full IMO._

---

## 4. CTB Placement

| CTB Path | Branch Level | Parent Hub |
|----------|--------------|------------|
| | sys / ui / ai / infra | |

---

## 5. Altitude Scope

| Level | Description | Selected |
|-------|-------------|----------|
| 30,000 ft | Strategic vision, system-wide boundaries | [ ] |
| 20,000 ft | Domain architecture, hub relationships | [ ] |
| 10,000 ft | Component design, interface contracts | [ ] |
| 5,000 ft | Implementation detail, execution logic | [ ] |

---

## 6. IMO Structure

_This hub owns all three IMO layers internally. Spokes are external interfaces only._

| Layer | Role | Description |
|-------|------|-------------|
| **I — Ingress** | Dumb input only | Receives data; no logic, no state |
| **M — Middle** | Logic, decisions, state | All processing occurs here inside the hub |
| **O — Egress** | Output only | Emits results; no logic, no state |

---

## 7. Spokes

_Spokes are interfaces ONLY. They carry no logic, tools, or state. Each spoke is typed as Ingress (I) or Egress (O)._

| Spoke Name | Type | Direction | Contract |
|------------|------|-----------|----------|
| | I | Inbound | |
| | O | Outbound | |

---

## 8. Connectors

| Connector | Type | Direction | Contract |
|-----------|------|-----------|----------|
| | API / CSV / Event | Inbound / Outbound | |

---

## 9. Tools

_All tools are scoped strictly INSIDE this hub. Spokes do not own tools._

| Tool | Doctrine ID | Scoped To | ADR |
|------|-------------|-----------|-----|
| | | This Hub (M layer) | |

---

## 10. Guard Rails

| Guard Rail | Type | Threshold |
|------------|------|-----------|
| | Rate Limit / Timeout / Validation | |

---

## 11. Kill Switch

- **Endpoint:**
- **Activation Criteria:**
- **Emergency Contact:**

---

## 12. Promotion Gates

| Gate | Artifact | Requirement |
|------|----------|-------------|
| G1 | PRD | Hub definition approved |
| G2 | ADR | Architecture decision recorded |
| G3 | Linear Issue | Work item created and assigned |
| G4 | PR | Code reviewed and merged |
| G5 | Checklist | Deployment verification complete |

---

## 13. Failure Modes

| Failure | Severity | Remediation |
|---------|----------|-------------|
| | | |

---

## 14. Human Override Rules

_When can a human bypass automation? Who approves?_

---

## 15. Observability

- **Logs:**
- **Metrics:**
- **Alerts:**

---

## 16. Constants

_Immutable values that define system behavior. These never change during execution._

### Upstream Dependencies (Read-Only)

| Dependency | Source | Authority |
|------------|--------|-----------|
| **Company Sovereign ID** | External (Company Lifecycle) | Globally unique, immutable |
| **Lifecycle State** | External (Company Lifecycle) | Authoritative, read-only |

### Tool Registry

_Only these tools are authorized. No additions without ADR._

| Tool | Tier | Allowed Sub-Hubs | Cost Class |
|------|------|------------------|------------|
| | 0 / 1 / 2 / Bulk / Local / Core | | Free / Low / Premium / Per-use |

### Global Invariants

- [ ] One sovereign company ID only
- [ ] Context IDs are disposable (TTL-bound)
- [ ] No paid tools before lifecycle allows
- [ ] No enrichment without measured deficit
- [ ] No retries without new context or TTL
- [ ] BIT never mutates lifecycle
- [ ] CSV is never canonical storage

---

## 17. Variables

_Runtime values that change per execution context._

### Context Identifiers

| Variable | Scope | TTL | Purpose |
|----------|-------|-----|---------|
| **outreach_context_id** | Per run/epoch/campaign | Bounded | Cost accounting, retry isolation, audit |
| | | | |

### Variable Rules

- Context IDs are **disposable** — not permanent identity
- Always scoped to a **Company Sovereign ID**
- Kill-switchable
- Used for: cost accounting, retry isolation, audit logs, experimentation

---

## 18. Lifecycle Gate

_What lifecycle state is required before this hub can operate?_

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| | INTAKE / SOVEREIGN_MINTED / ACTIVE / TARGETABLE / ENGAGED / CLIENT |

### Lifecycle States Reference

```
INTAKE → SOVEREIGN_MINTED → ACTIVE → TARGETABLE → ENGAGED → CLIENT
                                                           ↓
                                                       DORMANT → DEAD
```

---

## 19. Cost Rules

_Hard cost discipline by construction._

| Rule | Enforcement |
|------|-------------|
| Tier-0 tools | Unlimited (free) |
| Tier-1 tools | Gated by lifecycle ≥ ACTIVE |
| Tier-2 tools | Max ONE attempt per outreach_context |
| All spend | Logged against context + company |
| Firewall | Must block illegal calls |

---

## 20. Failure Mode

_What happens when instructions conflict or ambiguity arises?_

1. **STOP** — Do not proceed
2. **EXPLAIN** — Document the conflict clearly
3. **PROPOSE** — Offer ONE deterministic resolution

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
