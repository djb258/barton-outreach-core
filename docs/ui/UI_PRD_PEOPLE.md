# UI PRD — People Intelligence

**Status**: DERIVED
**Authority**: SUBORDINATE TO PRD_PEOPLE_SUBHUB.md
**Generated**: 2026-01-29

---

## UI Identity

| Field | Value |
|-------|-------|
| **UI Name** | People Intelligence Dashboard |
| **Owning Hub** | HUB-PPL-04.04.02 |
| **Canonical PRD** | docs/prd/PRD_PEOPLE_SUBHUB.md |
| **Type** | Read-only + Event-emitting |

---

## Explicit Exclusions

This UI does NOT:

- Create people records
- Assign slots
- Generate emails
- Verify emails
- Compute slot fill rates

---

## Screens / Views

| Screen | Type | Description |
|--------|------|-------------|
| Slot Overview | Read-only | CEO/CFO/HR slot fill status by company |
| People List | Read-only | Paginated list of people with filters |
| Person Detail | Read-only | Single person with slot assignment |
| Staging Queue | Read-only | people_staging status view |

---

## Canonical Outputs Consumed

| Output | Source | Read Pattern |
|--------|--------|--------------|
| Slot status | people.company_slot | SELECT with aggregation |
| People list | people.people_master | SELECT with pagination |
| Staging queue | people.people_staging | SELECT with status filter |
| Slot fill rates | Computed view | SELECT |

---

## Events Emitted

| Event | Trigger | Destination |
|-------|---------|-------------|
| `refresh_slots` | User clicks refresh | Backend API |
| `filter_people` | User changes filters | Local state + API |
| `trigger_extraction` | User requests extraction | Backend API (event only) |

---

## Failure States

| Failure | Display |
|---------|---------|
| Person not found | "Person not found" message |
| Slot not filled | "Slot empty" indicator |
| Email unverified | "Email pending verification" badge |

---

## Forbidden Behaviors

- Creating people records
- Modifying slot assignments
- Triggering email verification directly
- Computing email patterns
