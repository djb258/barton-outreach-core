# ADR: People Intelligence Slot-Based Model

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-PI-001 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | People Intelligence |
| **Hub ID** | HUB-PI-001 |

---

## Context

People data is expensive to acquire and verify. Without structure, enrichment
becomes a cost sink with diminishing returns.

---

## Decision

People Intelligence uses a **slot-based model**:
- Define target slots per company (CHRO, HR_MANAGER, BENEFITS_LEAD, etc.)
- Only enrich when measured slot deficit exists
- Track fill rate as core metric

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Unlimited enrichment | Cost explosion |
| Contact-first approach | No structure, no metrics |
| Do Nothing | Would continue cost leakage |

---

## Consequences

### Enables

- Measured enrichment spending
- Clear fill rate metric
- Slot-based prioritization

### Prevents

- Unbounded enrichment costs
- Raw contact accumulation without purpose

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |

---

# ADR: Table Ownership and ERD Documentation

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-PI-002 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-02 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | People Intelligence |
| **Hub ID** | HUB-PI-001 |

---

## Context

People Intelligence table ownership was not clearly documented. The relationship between
`outreach.people` and related tables (slot_assignments, email_verification, movement_history)
needed explicit ERD documentation to clarify data flow and prevent scope creep.

---

## Decision

Add explicit table ownership documentation to PRD with:

1. **Primary Tables** - Tables this sub-hub owns and writes to
2. **Shared Tables** - Tables shared during migration
3. **Read-Only Tables** - Tables from upstream hubs (Company Target, CL)
4. **ERD Diagram** - Visual representation of table relationships

---

## Table Ownership Summary

| Schema.Table | Owner | Write | Read |
|--------------|-------|-------|------|
| `outreach.people` | People Intelligence | YES | YES |
| `outreach.slot_assignments` | People Intelligence | YES | YES |
| `outreach.email_verification` | People Intelligence | YES | YES |
| `people.movement_history` | People Intelligence | YES | YES |
| `people.enrichment_state` | People Intelligence | YES | YES |
| `marketing.people_master` | Legacy (to outreach) | YES | YES |
| `outreach.company_target` | Company Target | NO | YES |
| `cl.company_identity` | CL Parent | NO | YES |

---

## Slot Split Doctrine

| Aspect | Owner | Table |
|--------|-------|-------|
| WHAT roles needed | Company Target | slot_requirements |
| WHO fills roles | People Intelligence | slot_assignments |

> Company Hub defines **WHAT** roles are needed.
> People Hub defines **WHO** fills those roles.

---

## Consequences

### Enables

- Clear ownership boundaries
- Prevents unauthorized table writes
- Documents migration path for legacy tables
- Clarifies slot split doctrine

### Prevents

- Scope creep into Company Target tables
- Confusion about write authority
- Undocumented table dependencies

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |

---

**Last Updated**: 2026-01-02
**ADR Count**: 2 (ADR-PI-001, ADR-PI-002)
