# ADR: DOL EIN Matching — Exact Only

## ADR Identity

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-DOL-001 |
| **Status** | [x] Accepted |
| **Date** | 2026-01-01 |

---

## Owning Hub

| Field | Value |
|-------|-------|
| **Hub Name** | DOL Filings |
| **Hub ID** | HUB-DOL-001 |

---

## Context

DOL filings contain EINs that should match company_master records.
Fuzzy matching introduces false positives and compliance risk.

---

## Decision

DOL Filings uses **exact EIN matching only**:
- No fuzzy matching
- No retries on mismatch
- Fail closed — unmatched filings are not attached

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Fuzzy EIN matching | False positive risk too high |
| Multiple match attempts | Compliance concern |
| Do Nothing | Would allow bad matches |

---

## Consequences

### Enables

- High confidence in filing attachments
- Clean audit trail
- Compliance-safe matching

### Prevents

- False positive attachments
- Bad data propagation

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | | |
| Reviewer | | |
