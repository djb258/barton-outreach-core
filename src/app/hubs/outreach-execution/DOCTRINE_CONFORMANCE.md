# DOCTRINE_CONFORMANCE.md — Outreach Execution

## Conformance Declaration

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **Status** | CONFORMANT |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Marketing intelligence and executive enrichment operations |

---

## 2. Hub Identity (CC-03)

| Field | Value |
|-------|-------|
| **Parent Hub** | outreach-core |
| **Hub Name** | Outreach Execution |
| **Hub ID** | HUB-OUTREACH |
| **Doctrine ID** | 04.04.04 |
| **Type** | Sub-Hub (CC-03 relative to parent) |

---

## 3. CTB Placement

| Field | Value |
|-------|-------|
| **Trunk** | sys |
| **Branch** | outreach |
| **Leaf** | outreach-execution |
| **Full Path** | sys/outreach/outreach-execution |

---

## 4. Constants vs Variables

| Artifact | Type | Change Protocol |
|----------|------|-----------------|
| Hub ID | Constant | ADR required |
| Doctrine ID | Constant | ADR required |
| CTB Placement | Constant | ADR required |
| Primary Table | Constant | ADR required |
| State Machine States | Constant | ADR required |
| outreach_id | Variable | Runtime (per execution) |
| campaign_state | Variable | Runtime (state machine) |
| engagement_events | Variable | Runtime (tracked) |

---

## 5. PID Pattern

| Field | Value |
|-------|-------|
| **Pattern** | `HUB-OE-{TIMESTAMP}-{RANDOM_HEX}` |
| **Minted At** | CC-04 (per execution) |
| **Reuse** | Prohibited |

---

## 6. Authorization Subset

| Source | Target | Permission |
|--------|--------|------------|
| CC-03 (this hub) | CC-03 (own context) | Permitted |
| CC-03 (this hub) | CC-04 (own processes) | Permitted |
| CC-03 (this hub) | CC-01 (sovereign) | Denied |
| CC-03 (this hub) | CC-02 (parent hub) | Denied |

---

## 7. Lifecycle States

| State | Trigger Authority | Allowed From |
|-------|-------------------|--------------|
| DRAFT | CC-02 (Parent Hub) | (initial) |
| ACTIVE | CC-02 (Parent Hub) | DRAFT |
| SUSPENDED | CC-02 (Parent Hub) | ACTIVE |
| TERMINATED | CC-02 (Parent Hub) | DRAFT, ACTIVE, SUSPENDED |

---

## 8. Error Log Binding

| Field | Value |
|-------|-------|
| **Error Table** | outreach.outreach_execution_errors |
| **Master Log** | Sovereign-level (barton-enterprises) |
| **Required Fields** | timestamp, pid, cc_layer, violation_type, ctb_node, description |

---

## 9. Upstream Contracts

| Upstream | Contract | Required Signal |
|----------|----------|-----------------|
| Outreach Spine | outreach-spine | outreach_id |
| Company Target | company-outreach | outreach_id, domain, verified_pattern |
| People Intelligence | people-outreach | outreach_id, contact_records |
| Blog Content | blog-outreach | outreach_id, timing_signals |

---

## 10. Downstream Contracts

| Downstream | Contract | Emitted Signal |
|------------|----------|----------------|
| Company Lifecycle (CL) | outreach-cl | engagement_events |

---

## 11. Entities Owned

| Entity | Schema.Table | Write | Read |
|--------|--------------|-------|------|
| Campaigns | outreach.campaigns | YES | YES |
| Sequences | outreach.sequences | YES | YES |
| Send Log | outreach.send_log | YES | YES |
| Engagement Events | outreach.engagement_events | YES | YES |

---

## 12. Entities Read-Only

| Entity | Schema.Table | Owner |
|--------|--------------|-------|
| Outreach Spine | outreach.outreach | Outreach Spine |
| Company Target | outreach.company_target | Company Target |
| People Records | outreach.people | People Intelligence |
| Blog Records | outreach.blog | Blog Content |
