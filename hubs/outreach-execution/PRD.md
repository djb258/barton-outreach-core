# PRD — Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-02 |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Marketing intelligence and executive enrichment operations |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Outreach Execution |
| **Hub ID** | HUB-OUTREACH |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Purpose

Own campaign state, sequence execution, send logs, and engagement tracking. Manage outreach state machine: draft → scheduled → sent → opened → replied. Consumes fully enriched companies from upstream waterfall.

**Golden Rule:** No outreach without sovereign_id, domain, AND email_pattern.

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | outreach-execution | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Dumb input only | Receives outreach_id, slot_assignments, contact_records | CC-02 |
| **M — Middle** | Logic, decisions, state | Campaign orchestration, sequence execution, engagement tracking | CC-02 |
| **O — Egress** | Output only | Emits engagement_events to Company Lifecycle | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| outreach-spine | I | Inbound | outreach_id | CC-03 |
| company-outreach | I | Inbound | outreach_id, domain, verified_pattern | CC-03 |
| people-outreach | I | Inbound | outreach_id, contact_records | CC-03 |
| outreach-cl | O | Outbound | engagement_events | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.04) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| State Machine States | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| campaign_state | Variable | Runtime (state machine) | CC-04 |
| engagement_events | Variable | Runtime (tracked) | CC-04 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| Email Sender | Deterministic | CC-02 | M | ADR-OE-001 |
| Engagement Tracker | Deterministic | CC-02 | M | N/A (Local) |
| Sequence Engine | Deterministic | CC-02 | M | ADR-OE-002 |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| BIT score minimum | Validation | BIT_SCORE >= 25 | CC-03 |
| Verified pattern required | Validation | MUST have from upstream | CC-03 |
| Slotted people required | Validation | MUST have from People Intelligence | CC-03 |
| Cooling-off period | Rate Limit | Enforced between contacts | CC-04 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | BIT_SCORE < 25 OR missing required signals |
| **Trigger Authority** | CC-02 (Hub) / CC-01 (Sovereign) |
| **Emergency Contact** | Outreach Team |

---

## 11. Promotion Gates

| Gate | Artifact | CC Layer | Requirement |
|------|----------|----------|-------------|
| G1 | PRD | CC-02 | Hub definition approved |
| G2 | ADR | CC-03 | Architecture decision recorded |
| G3 | Work Item | CC-04 | Execution item created |
| G4 | PR | CC-04 | Code reviewed and merged |
| G5 | Checklist | CC-04 | Compliance verification complete |

---

## 12. Failure Modes

| Failure | Severity | CC Layer | Remediation |
|---------|----------|----------|-------------|
| Missing sovereign_id | CRITICAL | CC-03 | STOP - DO_NOT_CONTACT |
| Missing domain | CRITICAL | CC-03 | STOP - DO_NOT_CONTACT |
| Missing email_pattern | CRITICAL | CC-03 | STOP - DO_NOT_CONTACT |
| BIT below threshold | HIGH | CC-03 | Downgrade to NEWSLETTER/CONTENT |
| Send failure | MEDIUM | CC-04 | Log error, retry with backoff |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-OE-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Bypass BIT threshold for priority targets
- Manual campaign state transition
- Force cooling-off period skip

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | Campaign transitions, sends, engagement events | CC-04 |
| **Metrics** | ENGAGEMENT_RATE (target >= 30%), send_success_rate | CC-04 |
| **Alerts** | Engagement rate drop, send failures, threshold violations | CC-03/CC-04 |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Sovereign (CC-01) | | |
| Hub Owner (CC-02) | | |
| Reviewer | | |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| Hub/Spoke Doctrine | HUB_SPOKE_ARCHITECTURE.md |
