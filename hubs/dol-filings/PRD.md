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
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Purpose

Attach regulatory filings (Form 5500, Schedule A) to **existing companies**. Source of truth for plan renewal dates and broker relationships. Bulk CSV processing only — no paid enrichment tools.

**Waterfall Position**: 2nd sub-hub in canonical waterfall (after Company Target, before People Intelligence).

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | dol-filings | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Dumb input only | Receives outreach_id, domain from Company Target; DOL CSV files | CC-02 |
| **M — Middle** | Logic, decisions, state | EIN matching, filing parsing, signal generation | CC-02 |
| **O — Egress** | Output only | Emits filing_signals, regulatory_data to downstream | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| company-dol | I | Inbound | outreach_id, domain | CC-03 |
| dol-people | O | Outbound | outreach_id, filing_signals, ein | CC-03 |
| dol-blog | O | Outbound | outreach_id, regulatory_data | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.03) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| filing_data | Variable | Runtime (from CSV) | CC-04 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| DOL CSV Parser | Deterministic | CC-02 | M | N/A (Bulk) |
| EIN Matcher | Deterministic | CC-02 | M | N/A (Local) |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| Company Target PASS | Validation | MUST have upstream PASS | CC-03 |
| Exact EIN match | Validation | No fuzzy matching allowed | CC-03 |
| No retries on mismatch | Rate Limit | Single attempt per EIN | CC-04 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | EIN match fails (exact match only) |
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
| Company Target not PASS | CRITICAL | CC-03 | STOP - upstream dependency |
| EIN match fails | MEDIUM | CC-04 | Log to error table, emit FAIL |
| CSV parse error | HIGH | CC-04 | Log error, skip record |
| Duplicate filing detected | LOW | CC-04 | Dedupe, log warning |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-DOL-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Manual EIN assignment for edge cases
- Force filing attachment despite mismatch
- Bulk re-processing of CSV files

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | CSV processing, EIN match attempts, filing attachments | CC-04 |
| **Metrics** | FILING_MATCH_RATE (target >= 90%), records_processed | CC-04 |
| **Alerts** | Match rate below threshold, CSV parse failures | CC-03/CC-04 |

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
