# PRD - Sovereign Completion System

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.1 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-02 |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Outreach Program |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | Sovereign Completion |
| **Hub ID** | 04.04.02.04.SC |
| **Owner** | Barton Enterprises |
| **Version** | 1.0.0 |

---

## 3. Purpose

The Sovereign Completion System provides a single source of truth for company marketing eligibility by:

1. **Tracking Hub Completion** - Each company's status across all required hubs
2. **Computing Marketing Tier** - Eligibility tier based on hub completion
3. **Enforcing Kill Switches** - Manual overrides that take precedence
4. **Providing Audit Trail** - Full history of tier changes and overrides

This system answers the question: "Is this company ready for marketing, and at what intensity?"

---

## 4. CTB Placement

| Field | Value | CC Layer |
|-------|-------|----------|
| **Trunk** | sys | CC-02 |
| **Branch** | outreach | CC-02 |
| **Leaf** | sovereign-completion | CC-02 |

---

## 5. IMO Structure (CC-02)

| Layer | Role | Description | CC Layer |
|-------|------|-------------|----------|
| **I — Ingress** | Hub status updates | Receives status changes from sub-hubs | CC-02 |
| **M — Middle** | Tier computation | Computes marketing tier from hub statuses | CC-02 |
| **O — Egress** | Eligibility views | Exposes computed eligibility to consumers | CC-02 |

---

## 6. Spokes (CC-03 Interfaces)

| Spoke Name | Type | Direction | Contract | CC Layer |
|------------|------|-----------|----------|----------|
| hub-status-ingress | I | Inbound | Hub status updates | CC-03 |
| eligibility-egress | O | Outbound | Marketing tier data | CC-03 |

---

## 7. Constants vs Variables

| Element | Type | Mutability | CC Layer |
|---------|------|------------|----------|
| Hub Registry | Constant | ADR-gated | CC-02 |
| Hub Status Enum | Constant | Immutable | CC-02 |
| Marketing Tier Logic | Constant | ADR-gated | CC-02 |
| Override Types | Constant | Immutable | CC-02 |
| BIT Score Threshold | Variable | Configuration | CC-02 |

---

## 8. Tools

| Tool | Solution Type | CC Layer | IMO Layer | ADR Reference |
|------|---------------|----------|-----------|---------------|
| vw_sovereign_completion | Deterministic | CC-02 | M | ADR-006 |
| vw_marketing_eligibility | Deterministic | CC-02 | O | ADR-006 |
| vw_marketing_eligibility_with_overrides | Deterministic | CC-02 | O | ADR-007 |
| fn_get_completion | Deterministic | CC-02 | O | ADR-006 |

---

## 9. Guard Rails

| Guard Rail | Type | Threshold | CC Layer |
|------------|------|-----------|----------|
| Kill Switch | Override | manual_overrides table | CC-02 |
| BIT Gate | Threshold | >= 25 for PASS | CC-02 |
| Tier 3 Gate | Threshold | BIT >= 50 + all hubs PASS | CC-02 |

---

## 10. Kill Switch

| Field | Value |
|-------|-------|
| **Activation Criteria** | Any override in manual_overrides with is_active=TRUE |
| **Trigger Authority** | CC-02 (Hub) / CC-01 (Sovereign) |
| **Emergency Contact** | Hub Owner |

---

## 11. Promotion Gates

| Gate | Artifact | CC Layer | Requirement |
|------|----------|----------|-------------|
| G1 | PRD | CC-02 | Hub definition approved |
| G2 | ADR | CC-03 | ADR-006 accepted |
| G3 | Work Item | CC-04 | Migration deployment |
| G4 | PR | CC-04 | Code reviewed and merged |
| G5 | Checklist | CC-04 | Final certification PASS |

---

## 12. Failure Modes

| Failure | Severity | CC Layer | Remediation |
|---------|----------|----------|-------------|
| View query timeout | High | CC-02 | Add indexes, optimize joins |
| Kill switch bypass | Critical | CC-02 | RLS enforcement |
| Ghost PASS state | High | CC-02 | Validation checks |
| Missing hub status | Medium | CC-02 | Default to IN_PROGRESS |

---

## 13. PID Scope (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `sovereign-completion-${TIMESTAMP}-${RANDOM_HEX}` |
| **Retry Policy** | New PID per retry |
| **Audit Trail** | Required |

---

## 14. Human Override Rules

- Hub Owner (CC-02) can add/remove overrides
- Legal team can add legal_hold overrides
- Customer service can add customer_requested overrides
- Only Hub Owner can modify tier_cap overrides

---

## 15. Observability

| Type | Description | CC Layer |
|------|-------------|----------|
| **Logs** | Override changes logged to override_audit_log | CC-04 |
| **Metrics** | Tier distribution, override counts | CC-04 |
| **Alerts** | Anomaly detection on tier changes | CC-03 |

---

## Hub Registry

| Hub ID | Hub Name | Classification | Gates Completion | Waterfall Order |
|--------|----------|----------------|------------------|-----------------|
| company-target | Company Target | required | TRUE | 1 |
| dol-filings | DOL Filings | required | TRUE | 2 |
| people-intelligence | People Intelligence | required | TRUE | 3 |
| talent-flow | Talent Flow | required | TRUE | 4 |
| blog-content | Blog Content | optional | FALSE | 5 |
| bit-enrichment | BIT Enrichment | optional | FALSE | 6 |

---

## Marketing Tier Logic

| Tier | Name | Requirement | Description |
|------|------|-------------|-------------|
| -1 | INELIGIBLE | overall_status = BLOCKED | Any hub FAIL or BLOCKED |
| 0 | Cold | company_target = PASS | Basic company data only |
| 1 | Persona | people = PASS | People data available |
| 2 | Trigger | talent_flow = PASS | Movement signals available |
| 3 | Aggressive | ALL PASS + BIT >= 50 | Full data + high intent |

---

## Data Model

### Tables

| Table | Schema | Purpose |
|-------|--------|---------|
| hub_registry | outreach | Hub definitions |
| company_hub_status | outreach | Company status per hub |
| manual_overrides | outreach | Kill switches |
| override_audit_log | outreach | Audit trail |

### Views

| View | Schema | Purpose |
|------|--------|---------|
| vw_sovereign_completion | outreach | Hub status aggregation |
| vw_marketing_eligibility | outreach | Tier computation |
| vw_marketing_eligibility_with_overrides | outreach | Authoritative eligibility |

### Enums

| Enum | Values |
|------|--------|
| hub_status_enum | PASS, IN_PROGRESS, FAIL, BLOCKED |
| override_type_enum | marketing_disabled, tier_cap, hub_bypass, cooldown, legal_hold, customer_requested |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Sovereign (CC-01) | Barton Enterprises | 2026-01-19 |
| Hub Owner (CC-02) | Outreach Core | 2026-01-19 |
| Reviewer | Claude Code | 2026-01-19 |

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Canonical Doctrine | CANONICAL_ARCHITECTURE_DOCTRINE.md |
| Hub/Spoke Doctrine | HUB_SPOKE_ARCHITECTURE.md |
| ADR | ADR-006_Sovereign_Completion_Infrastructure.md |
| ADR | ADR-007_Kill_Switch_System.md |
