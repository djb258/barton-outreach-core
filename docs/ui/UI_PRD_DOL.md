# UI PRD — DOL Filings

**Status**: DERIVED
**Authority**: SUBORDINATE TO PRD_DOL_SUBHUB.md
**Generated**: 2026-01-29

---

## UI Identity

| Field | Value |
|-------|-------|
| **UI Name** | DOL Filings Dashboard |
| **Owning Hub** | HUB-DOL-04.04.03 |
| **Canonical PRD** | docs/prd/PRD_DOL_SUBHUB.md |
| **Type** | Read-only |

---

## Explicit Exclusions

This UI does NOT:

- Import Form 5500 data
- Match EINs
- Parse filings
- Compute renewal calendars
- Write to DOL tables

---

## Screens / Views

| Screen | Type | Description |
|--------|------|-------------|
| Filing Overview | Read-only | Companies with DOL match status |
| Form 5500 Detail | Read-only | Individual filing details |
| Schedule A View | Read-only | Schedule A data for a filing |
| Renewal Calendar | Read-only | Upcoming renewal dates |

---

## Canonical Outputs Consumed

| Output | Source | Read Pattern |
|--------|--------|--------------|
| DOL match status | outreach.dol | SELECT |
| Form 5500 data | dol.form_5500 | SELECT |
| Schedule A data | dol.schedule_a | SELECT |
| Renewal dates | dol.renewal_calendar | SELECT |

---

## Events Emitted

| Event | Trigger | Destination |
|-------|---------|-------------|
| `refresh_dol` | User clicks refresh | Backend API |
| `filter_filings` | User changes filters | Local state + API |

---

## Failure States

| Failure | Display |
|---------|---------|
| No DOL match | "No DOL filing found" indicator |
| EIN mismatch | "EIN resolution pending" badge |
| Filing not found | "Filing not found" message |

---

## Forbidden Behaviors

- Importing DOL data
- Matching EINs
- Modifying filing records
- Computing derived metrics
