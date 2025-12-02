# PLE Hub + Spoke Schema Architecture

> Migrated: 2024-11-27
> Status: COMPLETE - Marketing schema is now EMPTY

## Architecture Overview

```
                                    ┌─────────────────────────────────────┐
                                    │          COMPANY (HUB)              │
                                    │     The Company Record              │
                                    │   All enrichment lands here         │
                                    ├─────────────────────────────────────┤
                                    │ company_master (453 rows)           │
                                    │ company_slots (1,359 rows)          │
                                    │ company_events (0 rows)             │
                                    │ company_sidecar (0 rows)            │
                                    │ pipeline_events (2,185 rows)        │
                                    │ pipeline_errors (0 rows)            │
                                    │ contact_enrichment (0 rows)         │
                                    │ email_verification (0 rows)         │
                                    │ message_key_reference (8 rows)      │
                                    │ validation_failures_log (2 rows)    │
                                    └────────────────┬────────────────────┘
                                                     │
                     ┌───────────────────────────────┼───────────────────────────────┐
                     │                               │                               │
    ┌────────────────▼────────────────┐ ┌───────────▼───────────┐ ┌────────────────▼────────────────┐
    │          DOL (SPOKE)            │ │   PEOPLE (SPOKE)      │ │          CLAY (SPOKE)           │
    │   DOL Federal Data              │ │  People as Sensors    │ │   Clay.com Enrichment           │
    ├─────────────────────────────────┤ ├───────────────────────┤ ├─────────────────────────────────┤
    │ form_5500 (230,009 rows)        │ │ company_slot (1,359)  │ │ company_raw (0 rows)            │
    │ form_5500_sf (759,569 rows)     │ │ people_master (170)   │ │ people_raw (0 rows)             │
    │ schedule_a (336,817 rows)       │ │ people_invalid (21)   │ └─────────────────────────────────┘
    │ violations (0 rows)             │ │ people_resolution_q   │
    │ form_5500_staging (0 rows)      │ │   (1,206 rows)        │
    │ form_5500_sf_staging (759,569)  │ │ people_sidecar (0)    │
    │ schedule_a_staging (336,817)    │ │ person_movement_hist  │
    └─────────────────────────────────┘ │   (0 rows)            │
                                        │ person_scores (0)     │
                                        └───────────────────────┘
                                                     │
                                    ┌────────────────▼────────────────────┐
                                    │       INTAKE (QUARANTINE)           │
                                    │    Invalid Records Pending Review   │
                                    ├─────────────────────────────────────┤
                                    │ quarantine (114 rows)               │
                                    │ company_raw_intake (563 rows)       │
                                    │ company_raw_wv (10 rows)            │
                                    │ people_raw_intake (0 rows)          │
                                    │ people_raw_wv (10 rows)             │
                                    └─────────────────────────────────────┘
```

## Schema Descriptions

### COMPANY Schema (HUB)
**Purpose**: The company record - all enrichment lands here

| Table | Rows | Description |
|-------|------|-------------|
| `company_master` | 453 | Core company records |
| `company_slots` | 1,359 | Executive position tracking |
| `company_events` | 0 | Company-level events |
| `company_sidecar` | 0 | Extended company attributes |
| `pipeline_events` | 2,185 | Pipeline activity log |
| `pipeline_errors` | 0 | Pipeline error tracking |
| `contact_enrichment` | 0 | Contact enrichment results |
| `email_verification` | 0 | Email verification status |
| `message_key_reference` | 8 | Message key lookup |
| `validation_failures_log` | 2 | Validation failures |

### DOL Schema (SPOKE)
**Purpose**: DOL federal data - Form 5500, Schedule A, violations

| Table | Rows | Description |
|-------|------|-------------|
| `form_5500` | 230,009 | Large plan filings |
| `form_5500_sf` | 759,569 | Small plan filings |
| `schedule_a` | 336,817 | Insurance contract details |
| `violations` | 0 | DOL violations (renamed from dol_violations) |
| `form_5500_staging` | 0 | Form 5500 staging |
| `form_5500_sf_staging` | 759,569 | Form 5500-SF staging |
| `schedule_a_staging` | 336,817 | Schedule A staging |

**Total DOL Records**: 1,326,395+

### PEOPLE Schema (SPOKE)
**Purpose**: People as sensors - slots, occupants, movement tracking

| Table | Rows | Description |
|-------|------|-------------|
| `company_slot` | 1,359 | Executive position slots |
| `people_master` | 170 | Core person records |
| `people_invalid` | 21 | Invalid person records |
| `people_resolution_queue` | 1,206 | Duplicate resolution queue |
| `people_sidecar` | 0 | Extended person attributes |
| `person_movement_history` | 0 | Job change tracking |
| `person_scores` | 0 | Person scoring data |

### CLAY Schema (SPOKE)
**Purpose**: Clay.com enrichment engine - raw data intake

| Table | Rows | Description |
|-------|------|-------------|
| `company_raw` | 0 | Raw company data from Clay |
| `people_raw` | 0 | Raw people data from Clay |

### INTAKE Schema (QUARANTINE)
**Purpose**: Invalid records pending review

| Table | Rows | Description |
|-------|------|-------------|
| `quarantine` | 114 | Invalid company records (renamed from company_invalid) |
| `company_raw_intake` | 563 | Raw company intake staging |
| `company_raw_wv` | 10 | West Virginia company raw data |
| `people_raw_intake` | 0 | Raw people intake staging |
| `people_raw_wv` | 10 | West Virginia people raw data |

## Key Relationships

### Primary Key: `company_unique_id`
- Links company.company_master to all other company-related tables
- Format: Barton ID `04.04.02.04.30000.###`

### Cross-Schema Joins

```sql
-- Company to DOL data (via EIN)
SELECT c.company_name, f.plan_name, f.tot_partcp_eoy_cnt
FROM company.company_master c
JOIN dol.form_5500 f ON c.ein = f.sponsor_dfe_ein;

-- Company to People
SELECT c.company_name, p.full_name, s.slot_type
FROM company.company_master c
JOIN people.company_slot s ON c.company_unique_id = s.company_unique_id
JOIN people.people_master p ON s.person_unique_id = p.unique_id;

-- DOL Form to Schedule A
SELECT f.sponsor_dfe_name, a.insurance_company_name, a.covered_lives
FROM dol.form_5500 f
JOIN dol.schedule_a a ON f.ack_id = a.ack_id;
```

## Migration Log

All migration steps are logged in `public.migration_log`:

```sql
SELECT * FROM public.migration_log
WHERE migration_name LIKE 'hub_spoke%'
ORDER BY executed_at;
```

## Scripts

| Script | Purpose |
|--------|---------|
| `ctb/sys/enrichment/hub_spoke_migration.js` | Phase 1: Create schemas, move primary tables |
| `ctb/sys/enrichment/hub_spoke_migration_phase2.js` | Phase 2: Move remaining tables, clean up marketing |

## Post-Migration Notes

1. **Marketing schema is now EMPTY** - All tables have been migrated
2. **Staging tables remain in DOL schema** - For ongoing data imports
3. **Quarantine table renamed** - `company_invalid` -> `intake.quarantine`
4. **Violations renamed** - `dol_violations` -> `dol.violations`
5. **Clay tables renamed** - `company_raw_from_clay` -> `clay.company_raw`, etc.

## Total Row Counts

| Schema | Tables | Total Rows |
|--------|--------|------------|
| company | 10 | 4,007 |
| dol | 7 | 2,423,211 |
| people | 7 | 2,756 |
| clay | 2 | 0 |
| intake | 5 | 697 |
| **TOTAL** | **31** | **2,430,671** |

---

## Data Catalog (catalog schema)

A searchable metadata layer for AI and human discovery of database fields.

### Catalog Summary

| Schema | Tables | Columns |
|--------|--------|---------|
| company | 10 | 129 |
| dol | 7 | 282 |
| people | 7 | 121 |
| clay | 2 | 65 |
| intake | 5 | 128 |
| **TOTAL** | **31** | **725** |

### Search Functions

```sql
-- Full-text search for columns by keyword
SELECT * FROM catalog.search_columns('ein federal tax');
SELECT * FROM catalog.search_columns('renewal date');
SELECT * FROM catalog.search_columns('linkedin');

-- Search columns by tag
SELECT * FROM catalog.search_by_tag('dol');
SELECT * FROM catalog.search_by_tag('bit');
SELECT * FROM catalog.search_by_tag('renewal');

-- Get all columns for a specific table
SELECT * FROM catalog.get_table_details('company.company_master');
SELECT * FROM catalog.get_table_details('dol.schedule_a');

-- Get AI-friendly context dump for a schema
SELECT catalog.get_ai_context('company');
SELECT catalog.get_ai_context();  -- All schemas
```

### Views

- `catalog.v_searchable_columns` - Flat view of all columns with metadata
- `catalog.v_ai_reference` - Quick reference view for AI/LLM
- `catalog.v_schema_summary` - Summary statistics per schema

### Column ID Format

Every column has a unique identifier: `{schema}.{table}.{column}`

Examples:
- `company.company_master.ein`
- `dol.schedule_a.insurance_company_name`
- `people.company_slot.slot_type`

### Common Tags

| Tag | Description |
|-----|-------------|
| `dol` | DOL federal data fields |
| `bit` | Used in BIT scoring |
| `renewal` | Related to renewal timing |
| `ein` | Federal tax ID fields |
| `linkedin` | LinkedIn profile URLs |
| `talent-flow` | Movement detection fields |
| `icp` | ICP criteria fields |

### Scripts

| Script | Purpose |
|--------|---------|
| `ctb/sys/enrichment/create_data_catalog.js` | Create and populate catalog |
| `ctb/sys/enrichment/fix_catalog_functions.js` | Fix search function types |
| `ctb/sys/enrichment/test_data_catalog.js` | Test search functionality |
