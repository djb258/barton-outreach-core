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
