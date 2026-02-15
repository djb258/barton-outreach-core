# ADR: SUPPORTING Leaf Type + People Master Reclassification

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | ARCHITECTURE.md v2.1.0 |
| **CC Layer** | CC-03 |
| **Parent Rule** | OWN-10a, OWN-10c (ADR-001) |

---

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-020 |
| **Status** | [ ] Proposed / [x] Accepted / [ ] Superseded / [ ] Deprecated |
| **Date** | 2026-02-15 |

---

## Owning Hub (CC-02)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-outreach-core |
| **Hub Name** | Outreach (Main Hub) |
| **Sub-Hub** | People (04.04.02) |

---

## CC Layer Scope

| Layer | Affected | Description |
|-------|----------|-------------|
| CC-01 (Sovereign) | [ ] | |
| CC-02 (Hub) | [x] | New leaf type added to CTB registry CHECK constraint |
| CC-03 (Context) | [x] | People sub-hub table reclassification |
| CC-04 (Process) | [ ] | |

---

## IMO Layer Scope

| Layer | Affected |
|-------|----------|
| I — Ingress | [ ] |
| M — Middle | [x] |
| O — Egress | [ ] |

---

## Constant vs Variable

| Classification | Value |
|----------------|-------|
| **This decision defines** | [x] Constant (structure/meaning) |
| **Mutability** | [x] Immutable |

---

## Context

ARCHITECTURE.md v2.1.0 introduced sub-hub table cardinality rules:

> **OWN-10a**: Each sub-hub has exactly one CANONICAL table.
> **OWN-10c**: Additional table types (STAGING, MV, REGISTRY) require ADR justification.

The people sub-hub currently has **two** tables marked CANONICAL in the CTB registry:

| Schema | Table | Current Leaf Type | Rows |
|--------|-------|-------------------|------|
| `people` | `company_slot` | CANONICAL | 285,012 |
| `people` | `people_master` | CANONICAL | 182,946 |

This appears to violate OWN-10a. However, the violation is a **classification error**, not a structural problem.

### The Actual Relationship

`company_slot` is the **canonical table** of the people sub-hub. It defines the slot structure: 3 positions per company (CEO, CFO, HR). Slots exist whether or not anyone fills them.

`people_master` is a **supporting table**. It holds the person data (name, email, LinkedIn, phone) that fills slots. A person cannot exist in the sub-hub without a slot to attach to.

```
outreach.outreach (95,837 companies)
    │
    │  outreach_id (FK)
    ▼
people.company_slot (285,012 slots)        ← CANONICAL (the structure)
    │
    │  people_id (FK)
    ▼
people.people_master (182,946 people)      ← SUPPORTING (fills the structure)
```

The slot can exist empty (`is_filled = FALSE`). 107,255 slots have no person attached — those represent the enrichment gap backlog.

### Why the Existing Leaf Types Don't Fit

| Leaf Type | Why Not |
|-----------|---------|
| CANONICAL | Wrong — `company_slot` is the canonical table. Two CANONICAL violates OWN-10a. |
| REGISTRY | Wrong — `people_master` is 182K mutable operational records, not a lookup table. |
| MV | Wrong — `people_master` is not derived from other data. |
| STAGING | Wrong — `people_master` is production data, not intake. |

No existing leaf type describes a table that **supports a CANONICAL table with operational data**.

---

## Decision

### 1. Add SUPPORTING leaf type to CTB

Add `SUPPORTING` to the `table_registry_leaf_type_check` constraint in `ctb.table_registry`.

**Definition**: A SUPPORTING table holds operational data that serves a CANONICAL table. It cannot exist independently — it requires the CANONICAL table's structure to have meaning. It is mutable, production-grade data (not reference, not staging, not derived).

| Property | SUPPORTING |
|----------|------------|
| Operational data | Yes |
| Mutable | Yes |
| Depends on CANONICAL | Yes — FK or structural dependency |
| Can exist without CANONICAL | No |
| Requires ADR | Yes (OWN-10c) |

### 2. Reclassify people_master

| Table | Old Leaf Type | New Leaf Type |
|-------|---------------|---------------|
| `people.people_master` | CANONICAL | SUPPORTING |

After reclassification, the people sub-hub has:

| Table | Leaf Type |
|-------|-----------|
| `people.company_slot` | CANONICAL |
| `people.people_master` | SUPPORTING |
| `people.people_errors` | ERROR |

This makes the people sub-hub **fully compliant** with OWN-10a (exactly 1 CANONICAL table).

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Grant OWN-10a exception (2 CANONICAL) | Incorrect framing. `people_master` is not canonical — it supports `company_slot`. An exception would paper over a classification error. |
| Use REGISTRY leaf type | Semantically wrong. REGISTRY is for lookup/reference data. `people_master` is 182K mutable operational records with email, phone, LinkedIn. |
| Merge into one table | Loses unfilled slot tracking. 107,255 empty slots would become invisible. Coverage gap detection breaks. |

---

## Consequences

### Enables

- People sub-hub passes OWN-10a without exception
- Clean vocabulary for tables that support canonical data (reusable across repos)
- Accurate CTB leaf type classification
- Future sub-hubs with similar parent-child patterns can use SUPPORTING

### Prevents

- Misclassifying operational supporting data as CANONICAL, REGISTRY, or MV
- OWN-10a violations caused by leaf type vocabulary gaps
- Need for exceptions when the real issue is classification

---

## Migration

**File**: `neon/migrations/2026-02-15-ctb-supporting-leaf-type.sql`

```sql
-- ADR-020: Add SUPPORTING leaf type + reclassify people_master
-- 1. Drop old CHECK, add new one with SUPPORTING
-- 2. Temporarily unfreeze people_master
-- 3. Reclassify people_master from CANONICAL to SUPPORTING
-- 4. Re-freeze people_master
```

---

## PID Impact (if CC-04 affected)

| Field | Value |
|-------|-------|
| **New PID required** | [ ] Yes / [x] No |
| **PID pattern change** | [ ] Yes / [x] No |
| **Audit trail impact** | None — leaf type reclassification, not schema change |

---

## Guard Rails

| Type | Value | CC Layer |
|------|-------|----------|
| CHECK constraint | `table_registry_leaf_type_check` updated to include SUPPORTING | CC-02 |
| ADR required | SUPPORTING tables require ADR justification (OWN-10c) | CC-03 |
| Dependency | SUPPORTING table must reference a CANONICAL table | CC-03 |
| Audit | `_audit_subhub_cardinality.py` recognizes SUPPORTING as valid | CC-04 |

---

## Rollback

Revert CHECK constraint to 8 leaf types. UPDATE `people_master` back to CANONICAL. Accept OWN-10a violation (requires separate exception ADR).

---

## Traceability

| Artifact | Reference |
|----------|-----------|
| Parent Rule | OWN-10a, OWN-10c — ARCHITECTURE.md v2.1.0 Part X §3 |
| Parent ADR | ADR-001 (IMO-Creator) — Sub-Hub Table Cardinality Constraint |
| Migration | `neon/migrations/2026-02-15-ctb-supporting-leaf-type.sql` |
| CTB Registry | `ctb.table_registry` — `people_master` reclassified |
| Audit Script | `_audit_subhub_cardinality.py` |
| Sub-Hub PRD | `docs/prd/PRD_PEOPLE_SUBHUB.md` v3.2 |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner (CC-02) | | |
| Reviewer | | |
