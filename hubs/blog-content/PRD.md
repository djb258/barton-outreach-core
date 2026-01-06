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
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Purpose

Provide **timing signals** from news, funding events, and content sources. BIT modulation only — cannot mint, revive, or trigger enrichment. FINAL hub in waterfall — context is finalized after this hub.

**Waterfall Position**: 4th (LAST) sub-hub in canonical waterfall (after People Intelligence).

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | blog-content | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Dumb input only | Receives outreach_id, slot_assignments from People; news feeds | CC-02 |
| **M — Middle** | Logic, decisions, state | Signal processing, BIT modulation | CC-02 |
| **O — Egress** | Output only | Emits timing_signals to BIT Engine | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| company-blog | I | Inbound | outreach_id, domain | CC-03 |
| dol-blog | I | Inbound | outreach_id, regulatory_data | CC-03 |
| people-blog | I | Inbound | outreach_id, slot_assignments | CC-03 |
| blog-bit | O | Outbound | outreach_id, timing_signals | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub ID | Constant | Immutable | CC-02 |
| Hub Name | Constant | ADR-gated | CC-02 |
| Doctrine ID (04.04.05) | Constant | Immutable | CC-02 |
| CTB Placement | Constant | ADR-gated | CC-02 |
| Primary Table | Constant | ADR-gated | CC-02 |
| Signal Types | Constant | ADR-gated | CC-02 |
| BIT Impact Values | Constant | ADR-gated | CC-02 |
| outreach_id | Variable | Runtime | CC-04 |
| timing_signals | Variable | Runtime (from feeds) | CC-04 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| News Feed Parser | Deterministic | CC-02 | M | N/A (Free) |
| Signal Classifier | Deterministic | CC-02 | M | N/A (Local) |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| People Intelligence PASS | Validation | MUST have upstream PASS | CC-03 |
| No paid tools | Validation | Free signals only | CC-03 |
| No enrichment trigger | Validation | Timing signals only | CC-03 |
| No company minting | Validation | MUST NOT mint or revive | CC-03 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | People Intelligence not PASS |
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
| Upstream hub not PASS | CRITICAL | CC-03 | STOP - upstream dependency |
| Feed parse error | LOW | CC-04 | Log warning, continue |
| Signal classification fails | LOW | CC-04 | Default to no BIT impact |
| Context finalization fails | HIGH | CC-04 | Log error, mark context FAIL |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-BC-{TIMESTAMP}-{RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

Override requires CC-02 (Hub Owner) or CC-01 (Sovereign) approval:
- Manual signal injection for known events
- Force context finalization despite feed errors
- Adjust BIT impact values for specific signals

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | Feed processing, signal emissions, context finalization | CC-04 |
| **Metrics** | SIGNAL_COVERAGE, signals_per_company, BIT_modulation_rate | CC-04 |
| **Alerts** | Feed unavailable, context finalization failures | CC-03/CC-04 |

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
