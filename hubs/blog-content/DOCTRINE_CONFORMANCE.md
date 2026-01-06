# DOCTRINE_CONFORMANCE.md — Blog Content

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
| **Hub Name** | Blog Content |
| **Hub ID** | HUB-BLOG-001 |
| **Doctrine ID** | 04.04.05 |
| **Type** | Sub-Hub (CC-03 relative to parent) |

---

## 3. CTB Placement

| Field | Value |
|-------|-------|
| **Trunk** | sys |
| **Branch** | outreach |
| **Leaf** | blog-content |
| **Full Path** | sys/outreach/blog-content |

---

## 4. Constants vs Variables

| Artifact | Type | Change Protocol |
|----------|------|-----------------|
| Hub ID | Constant | ADR required |
| Doctrine ID | Constant | ADR required |
| CTB Placement | Constant | ADR required |
| Primary Table | Constant | ADR required |
| Signal Types | Constant | ADR required |
| BIT Impact Values | Constant | ADR required |
| outreach_id | Variable | Runtime (per execution) |
| timing_signals | Variable | Runtime (from feeds) |

---

## 5. PID Pattern

| Field | Value |
|-------|-------|
| **Pattern** | `HUB-BC-{TIMESTAMP}-{RANDOM_HEX}` |
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
| **Error Table** | outreach.blog_errors |
| **Master Log** | Sovereign-level (barton-enterprises) |
| **Required Fields** | timestamp, pid, cc_layer, violation_type, ctb_node, description |

---

## 9. Upstream Contracts

| Upstream | Contract | Required Signal |
|----------|----------|-----------------|
| Outreach Spine | outreach-spine | outreach_id |
| Company Target | company-blog | outreach_id, domain |
| DOL Filings | dol-blog | outreach_id, regulatory_data |
| People Intelligence | people-blog | outreach_id, slot_assignments |

---

## 10. Downstream Contracts

| Downstream | Contract | Emitted Signal |
|------------|----------|----------------|
| BIT Engine | blog-bit | outreach_id, timing_signals |

---

## 11. Entities Owned

| Entity | Schema.Table | Write | Read |
|--------|--------------|-------|------|
| Blog Records | outreach.blog | YES | YES |
| Blog Errors | outreach.blog_errors | YES | YES |

---

## 12. Entities Read-Only

| Entity | Schema.Table | Owner |
|--------|--------------|-------|
| Outreach Spine | outreach.outreach | Outreach Spine |
| Company Target | outreach.company_target | Company Target |
| DOL Records | outreach.dol | DOL Filings |
| People Records | outreach.people | People Intelligence |
