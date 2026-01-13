# DOCTRINE_CONFORMANCE.md — Company Target

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

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Parent Hub** | outreach-core |
| **Hub Name** | Company Target |
| **Hub ID** | HUB-COMPANY-TARGET |
| **Doctrine ID** | 04.04.01 |
| **Type** | Sub-Hub (CC-03 relative to parent) |

---

## 3. CTB Placement

| Field | Value |
|-------|-------|
| **Trunk** | sys |
| **Branch** | outreach |
| **Leaf** | company-target |
| **Full Path** | sys/outreach/company-target |

---

## 4. Constants vs Variables

| Artifact | Type | Change Protocol |
|----------|------|-----------------|
| Hub ID | Constant | ADR required |
| Doctrine ID | Constant | ADR required |
| CTB Placement | Constant | ADR required |
| Primary Table | Constant | ADR required |
| outreach_id | Variable | Runtime (per execution) |
| BIT_SCORE | Variable | Runtime (calculated) |

---

## 5. PID Pattern

| Field | Value |
|-------|-------|
| **Pattern** | `HUB-CT-{TIMESTAMP}-{RANDOM_HEX}` |
| **Minted At** | CC-04 (per execution) |
| **Reuse** | Prohibited |

---

## 6. Authorization Subset

| Source | Target | Permission |
|--------|--------|------------|
| CC-02 (this hub) | CC-03 (own contexts) | Permitted |
| CC-02 (this hub) | CC-04 (own processes) | Permitted |
| CC-02 (this hub) | CC-01 (sovereign) | Denied |
| CC-02 (this hub) | CC-02 (other hubs) | Denied |

---

## 7. Lifecycle States

| State | Trigger Authority | Allowed From |
|-------|-------------------|--------------|
| DRAFT | CC-02 (Hub) | (initial) |
| ACTIVE | CC-02 (Hub) | DRAFT |
| SUSPENDED | CC-02 (Hub) | ACTIVE |
| TERMINATED | CC-02 (Hub) | DRAFT, ACTIVE, SUSPENDED |

---

## 8. Error Log Binding

| Field | Value |
|-------|-------|
| **Error Table** | outreach.company_target_errors |
| **Master Log** | Sovereign-level (barton-enterprises) |
| **Required Fields** | timestamp, pid, cc_layer, violation_type, ctb_node, description |

---

## 9. Upstream Contracts

| Upstream | Contract | Required Signal |
|----------|----------|-----------------|
| Company Lifecycle (CL) | cl-identity | sovereign_id (identity_status = 'PASS') |
| Outreach Spine | outreach-spine | outreach_id |

---

## 10. Downstream Contracts

| Downstream | Contract | Emitted Signal |
|------------|----------|----------------|
| DOL Filings | company-dol | outreach_id, domain |
| People Intelligence | company-people | outreach_id, verified_pattern |
| Blog Content | company-blog | outreach_id, domain |

---

## 11. Entities Owned

| Entity | Schema.Table | Write | Read |
|--------|--------------|-------|------|
| Company Target | outreach.company_target | YES | YES |
| Column Registry | outreach.column_registry | YES | YES |
| Target Errors | outreach.company_target_errors | YES | YES |

---

## 12. Entities Read-Only

| Entity | Schema.Table | Owner |
|--------|--------------|-------|
| Company Identity | cl.company_identity | CL (CC-01) |
| Outreach Spine | outreach.outreach | Outreach Spine |
