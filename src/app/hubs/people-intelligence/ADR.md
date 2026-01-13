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

# ADR: Schema Evolution and FULL PASS Certification

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-PI-003 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-08 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | People Intelligence |
| **Hub ID** | HUB-PI-001 |

---

## Context

The People Intelligence sub-hub required schema evolution to add doctrine-required columns
to `people.company_slot`. The migration was needed to achieve FULL PASS certification and
enable full traceability between slots and outreach contexts.

---

## Decision

Apply schema evolution migration `004_people_slot_schema_evolution.sql` with:

1. **4 New Columns** added to `people.company_slot`:
   - `outreach_id` (UUID NULL) - Links slot to outreach context
   - `canonical_flag` (BOOLEAN) - TRUE for CEO/CFO/HR slots
   - `creation_reason` (TEXT) - Why slot was created
   - `slot_status` (TEXT) - Current slot lifecycle state

2. **Backfill Strategy**:
   - `outreach_id`: Via `dol.ein_linkage` (22.5% coverage)
   - `canonical_flag`: TRUE for CEO/CFO/HR slot types
   - `creation_reason`: 'canonical' for all existing slots
   - `slot_status`: Copied from existing `status` column

3. **Error Handling**:
   - Unresolvable slots logged to `people.people_errors`
   - Error code: `PI-E901` (schema_evolution)
   - Retry strategy: `manual_fix`

---

## Migration Details

| Field | Value |
|-------|-------|
| **Migration Hash** | `678a8d99` |
| **Applied** | 2026-01-08T09:04:20 |
| **Total Slots** | 1,359 |
| **Outreach ID Coverage** | 306 (22.5%) |
| **Errors Logged** | 1,053 |

---

## Indexes Created

- `idx_company_slot_outreach_id`
- `idx_company_slot_slot_status`
- `idx_company_slot_canonical_flag`

---

## Consequences

### Enables

- Full traceability: slot → outreach_id → company
- Doctrine compliance for slot lifecycle
- Error audit for unresolved linkages
- FULL PASS certification

### Prevents

- Orphan slots without outreach context
- Implicit slot status (now explicit)
- Data loss (unresolvable slots logged, not dropped)

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | 2026-01-08 |
| Reviewer | Claude Code | 2026-01-08 |

---

**Last Updated**: 2026-01-08
**ADR Count**: 3 (ADR-PI-001, ADR-PI-002, ADR-PI-003)
