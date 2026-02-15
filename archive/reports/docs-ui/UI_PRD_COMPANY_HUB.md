# UI PRD — Company Hub

**Status**: DERIVED
**Authority**: SUBORDINATE TO PRD_COMPANY_HUB.md
**Generated**: 2026-01-29

---

## UI Identity

| Field | Value |
|-------|-------|
| **UI Name** | Company Hub Dashboard |
| **Owning Hub** | HUB-OUTREACH-001 |
| **Canonical PRD** | docs/prd/PRD_COMPANY_HUB.md |
| **Type** | Read-only + Event-emitting |

---

## Explicit Exclusions

This UI does NOT:

- Create companies
- Mint outreach_id
- Write to CL
- Compute BIT scores
- Execute business logic
- Modify eligibility status

---

## Screens / Views

| Screen | Type | Description |
|--------|------|-------------|
| Company List | Read-only | Paginated list of companies with filters |
| Company Detail | Read-only | Single company with all sub-hub data |
| Marketing Eligibility | Read-only | vw_marketing_eligibility_with_overrides |
| Sovereign Completion | Read-only | vw_sovereign_completion |

---

## Canonical Outputs Consumed

| Output | Source | Read Pattern |
|--------|--------|--------------|
| Company list | outreach.company_target | SELECT with pagination |
| Company detail | Multiple tables via outreach_id | JOIN on outreach_id |
| Eligibility status | vw_marketing_eligibility_with_overrides | SELECT |
| BIT score | outreach.bit_scores | SELECT |
| Sub-hub status | Hub status views | SELECT |

---

## Events Emitted

| Event | Trigger | Destination |
|-------|---------|-------------|
| `refresh_company` | User clicks refresh | Backend API |
| `filter_companies` | User changes filters | Local state + API |
| `export_companies` | User requests export | Backend API |

---

## Failure States

| Failure | Display |
|---------|---------|
| Company not found | "Company not found" message |
| API timeout | "Request timed out. Please retry." |
| Authorization failure | "Access denied" |

---

## Forbidden Behaviors

- Writing to any table
- Computing derived values
- Caching business logic results
- Making decisions based on data
