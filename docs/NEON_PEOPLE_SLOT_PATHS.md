# Neon Database — People Slot Data Paths

**Version:** 1.0.0  
**Date:** 2026-01-09  
**Status:** PRODUCTION  

---

## Overview

This document defines the canonical data paths in Neon for People Intelligence slot operations.

---

## The Sovereign Bridge Path

The **only valid path** from `outreach_id` to a FK-compliant `company_unique_id`:

```
┌─────────────────────────────────────┐
│  outreach.outreach                  │
│  ├── outreach_id (UUID) ←── ANCHOR  │
│  └── sovereign_id (UUID) ────────┐  │
└─────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────┐
│  cl.company_identity_bridge                     │
│  ├── company_sov_id (UUID) ←─── JOIN KEY        │
│  └── source_company_id (04.04.01.xx) ───────┐   │
└─────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────┐
│  company.company_master                         │
│  └── company_unique_id (04.04.01.xx) ← FK TARGET│
└─────────────────────────────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────┐
│  people.company_slot                            │
│  ├── company_unique_id (FK to company_master)   │
│  ├── outreach_id (UUID)                         │
│  └── slot_type (CEO/CFO/HR)                     │
└─────────────────────────────────────────────────┘
```

---

## Table Details

### outreach.outreach (Spine)

| Column | Type | Description |
|--------|------|-------------|
| `outreach_id` | UUID | Primary key, anchor for all downstream |
| `sovereign_id` | UUID | Links to company identity |
| `domain` | VARCHAR | Company domain |
| `created_at` | TIMESTAMPTZ | Created timestamp |

**Count:** 63,911 rows

### cl.company_identity_bridge

| Column | Type | Description |
|--------|------|-------------|
| `bridge_id` | UUID | Primary key |
| `source_company_id` | TEXT | `04.04.01.xx.xxxxx.xxx` format |
| `company_sov_id` | UUID | Links to `outreach.sovereign_id` |
| `source_system` | TEXT | Origin (e.g., 'clay') |
| `minted_at` | TIMESTAMPTZ | When identity was minted |

**Count:** 71,820 rows

### company.company_master

| Column | Type | Description |
|--------|------|-------------|
| `company_unique_id` | TEXT | Primary key, `04.04.01.xx` format |
| `company_name` | TEXT | Company name |
| `website_url` | TEXT | Company website |
| `industry` | TEXT | Industry classification |
| `employee_count` | INTEGER | Employee count |

**Count:** 71,826 rows

### people.company_slot

| Column | Type | Description |
|--------|------|-------------|
| `company_slot_unique_id` | TEXT | Primary key |
| `company_unique_id` | TEXT | FK to `company_master` |
| `outreach_id` | UUID | Links to outreach spine |
| `slot_type` | TEXT | CEO, CFO, HR |
| `slot_status` | TEXT | open, filled, vacated, quarantined |
| `person_unique_id` | TEXT | FK to `people_master` (nullable) |
| `canonical_flag` | BOOLEAN | TRUE for canonical slots |
| `creation_reason` | TEXT | How slot was created |

**Count:** 190,755 rows (as of 2026-01-09)

---

## Constraints on people.company_slot

| Constraint | Type | Columns |
|------------|------|---------|
| `company_slot_pkey` | PRIMARY KEY | `company_slot_unique_id` |
| `unique_company_slot` | UNIQUE | `(company_unique_id, slot_type)` |
| `uq_company_slot_outreach_slot_type` | UNIQUE | `(outreach_id, slot_type)` |
| `fk_company` | FOREIGN KEY | `company_unique_id` → `company_master` |
| `fk_person` | FOREIGN KEY | `person_unique_id` → `people_master` |
| `company_slot_slot_type_check` | CHECK | `slot_type IN ('CEO','CFO','HR')` |
| `company_slot_slot_status_check` | CHECK | `slot_status IN ('open','filled','vacated','quarantined')` |

---

## Common Queries

### Get all slots for an outreach_id

```sql
SELECT * FROM people.company_slot 
WHERE outreach_id = :outreach_id;
```

### Find open slots needing candidates

```sql
SELECT * FROM people.v_open_slots
WHERE slot_type = 'CEO'
ORDER BY days_open DESC;
```

### Check slot fill rates

```sql
SELECT * FROM people.v_slot_fill_rate;
```

### Validate FK path before insert

```sql
SELECT COUNT(DISTINCT o.outreach_id)
FROM outreach.outreach o
JOIN cl.company_identity_bridge b ON b.company_sov_id = o.sovereign_id
JOIN company.company_master cm ON cm.company_unique_id = b.source_company_id;
-- Should equal total outreach_ids (63,911)
```

---

## Anti-Patterns (DO NOT USE)

| Approach | Why It Fails |
|----------|--------------|
| `outreach.company_target.company_unique_id` | UUID format, not FK-compliant |
| `outreach.outreach.domain` → `company_master.website_url` | ILIKE is slow, partial matches |
| Generate `04.04.01.xx` format manually | No FK guarantee |
| Use template `company_unique_id` for all | Violates UNIQUE constraint |

---

## References

- ADR: [ADR-PI-001](../adr/ADR-PI-001_Slot_Seeding_Sovereign_Bridge.md)
- Migration: `src/data/migrations/2026-01-08-people-slot-structure.sql`
- Script: `ops/scripts/people_slot_bulk_seed_v2.py`
