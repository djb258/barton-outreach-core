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
| **Hub Name** | Company Target |
| **Hub ID** | HUB-COMPANY-TARGET |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Purpose

Determine **outreach readiness** for lifecycle-qualified companies. Internal anchor table that links all other sub-hubs together. Receives `sovereign_id` from Company Lifecycle parent — does NOT mint companies.

**Waterfall Position**: 1st sub-hub in canonical waterfall (after Outreach Spine, before DOL Filings).

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | company-target | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Dumb input only | Receives outreach_id, sovereign_id from spine | CC-02 |
| **M — Middle** | Logic, decisions, state | Domain resolution, email pattern waterfall, BIT scoring | CC-02 |
| **O — Egress** | Output only | Emits verified_pattern, domain, BIT signals | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| outreach-spine | I | Inbound | outreach_id, sovereign_id | CC-03 |
| company-dol | O | Outbound | outreach_id, domain | CC-03 |
| company-people | O | Outbound | outreach_id, verified_pattern | CC-03 |
| company-blog | O | Outbound | outreach_id, domain | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.01) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| BIT_SCORE | Variable | Runtime | CC-04 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| Firecrawl | Deterministic | CC-02 | M | N/A (Tier-0) |
| Google Places | Deterministic | CC-02 | M | N/A (Tier-0) |
| Hunter.io | Deterministic | CC-02 | M | ADR-CT-001 |
| Clearbit | Deterministic | CC-02 | M | ADR-CT-001 |
| Apollo | Deterministic | CC-02 | M | ADR-CT-001 |
| Prospeo | Deterministic | CC-02 | M | ADR-CT-002 |
| Snov | Deterministic | CC-02 | M | ADR-CT-002 |
| Clay | Deterministic | CC-02 | M | ADR-CT-002 |
| SMTP Check | Deterministic | CC-02 | M | N/A (Local) |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| Tier-2 tool limit | Rate Limit | Max 1 per outreach_id | CC-03 |
| CL existence check | Validation | MUST pass before any logic | CC-03 |
| Lifecycle gate | Validation | lifecycle_state >= ACTIVE | CC-03 |
| Spend logging | Validation | All spend logged to spend_log | CC-04 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | BIT_SCORE < 25 after pattern waterfall |
| **Trigger Authority** | CC-02 (Hub) |
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
| CL existence check fails | CRITICAL | CC-03 | STOP - CT_UPSTREAM_CL_NOT_VERIFIED |
| Domain resolution fails | HIGH | CC-04 | Log to error table, emit FAIL |
| Pattern waterfall exhausted | MEDIUM | CC-04 | Check BIT threshold, queue or STOP |
| Tier-2 limit exceeded | HIGH | CC-03 | Block call, log violation |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-CT-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Bypass Tier-2 limit for specific outreach_id
- Force pattern verification skip
- Manual BIT score adjustment

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | All phase transitions, tool calls, spend events | CC-04 |
| **Metrics** | BIT_SCORE, pattern_match_rate, tool_success_rate | CC-04 |
| **Alerts** | Tier-2 exhaustion, CL gate failures, spend anomalies | CC-03/CC-04 |

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
