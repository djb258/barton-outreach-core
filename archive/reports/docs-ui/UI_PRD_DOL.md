# UI PRD — DOL Filings

**Status**: DERIVED
**Authority**: SUBORDINATE TO PRD_DOL_SUBHUB.md
**Generated**: 2026-02-10

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
| Filing Overview | Read-only | Companies with DOL match status (multi-year) |
| Form 5500 Detail | Read-only | Individual filing details (2023/2024/2025) |
| Form 5500-SF Detail | Read-only | Short form filing details |
| Schedule A View | Read-only | Insurance contracts & broker commissions |
| Schedule C View | Read-only | Service provider compensation (9 sub-tables) |
| Schedule D View | Read-only | DFE participation (4 sub-tables) |
| Schedule G View | Read-only | Financial transactions (4 sub-tables) |
| Schedule H View | Read-only | Large plan financial information |
| Schedule I View | Read-only | Small plan financial information |
| Renewal Calendar | Read-only | Upcoming renewal dates |
| Cross-Year Compare | Read-only | Year-over-year filing comparison |

---

## Canonical Outputs Consumed

| Output | Source | Read Pattern |
|--------|--------|--------------|
| DOL match status | outreach.dol | SELECT |
| Form 5500 data | dol.form_5500 | SELECT (filter by form_year) |
| Form 5500-SF data | dol.form_5500_sf | SELECT (filter by form_year) |
| Schedule A data | dol.schedule_a | SELECT (join via ack_id) |
| Schedule C data | dol.schedule_c + 8 sub-tables | SELECT (join via ack_id) |
| Schedule D data | dol.schedule_d + 3 sub-tables | SELECT (join via ack_id) |
| Schedule G data | dol.schedule_g + 3 sub-tables | SELECT (join via ack_id) |
| Schedule H data | dol.schedule_h + 1 sub-table | SELECT (join via ack_id) |
| Schedule I data | dol.schedule_i + 1 sub-table | SELECT (join via ack_id) |
| Renewal dates | dol.renewal_calendar | SELECT |
| Column metadata | dol.column_metadata | SELECT (1,081 entries) |

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
