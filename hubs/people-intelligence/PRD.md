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
| **Hub Name** | People Intelligence |
| **Hub ID** | HUB-PEOPLE |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Purpose

Populate **role slots**, not raw contacts. Own human identity, employment state, and slot assignments. Track human lifecycle independently from company lifecycle. CONSUMER of upstream patterns — does NOT discover patterns or resolve domains.

**Waterfall Position**: 3rd sub-hub in canonical waterfall (after DOL Filings, before Blog Content).

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | people-intelligence | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Dumb input only | Receives outreach_id, verified_pattern from CT; filing_signals from DOL | CC-02 |
| **M — Middle** | Logic, decisions, state | Email generation, slot assignment, enrichment queue | CC-02 |
| **O — Egress** | Output only | Emits slot_assignments, contact_records to downstream | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| company-people | I | Inbound | outreach_id, verified_pattern | CC-03 |
| dol-people | I | Inbound | outreach_id, filing_signals | CC-03 |
| people-blog | O | Outbound | outreach_id, slot_assignments | CC-03 |
| people-outreach | O | Outbound | outreach_id, contact_records | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.02) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| Slot Types | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| slot_assignments | Variable | Runtime (calculated) | CC-04 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| Apollo | Deterministic | CC-02 | M | ADR-PI-001 |
| Clay | Deterministic | CC-02 | M | ADR-PI-001 |
| MillionVerifier | Deterministic | CC-02 | M | ADR-PI-002 |
| Title Classifier | Deterministic | CC-02 | M | N/A (Local) |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| Verified pattern required | Validation | MUST have from Company Target | CC-03 |
| DOL Filings PASS | Validation | MUST have upstream PASS | CC-03 |
| Clay limit | Rate Limit | Max 1 per outreach_id | CC-03 |
| Enrichment budget | Rate Limit | Only for measured slot deficit | CC-04 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | No verified pattern from Company Target |
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
| No verified pattern | CRITICAL | CC-03 | STOP - upstream dependency |
| DOL Filings not PASS | CRITICAL | CC-03 | STOP - upstream dependency |
| Slot assignment fails | HIGH | CC-04 | Log to error table, emit FAIL |
| Enrichment budget exceeded | MEDIUM | CC-04 | Queue for next context |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-PI-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Manual slot assignment for edge cases
- Bypass enrichment budget for priority targets
- Force email verification skip

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | Phase transitions (5-8), slot assignments, enrichment calls | CC-04 |
| **Metrics** | SLOT_FILL_RATE (target >= 80%), email_verification_rate | CC-04 |
| **Alerts** | Fill rate below threshold, enrichment budget exhaustion | CC-03/CC-04 |

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
