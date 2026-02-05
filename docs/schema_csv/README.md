# Schema Export - CSV Documentation

**Generated**: 2026-02-05
**Script**: `scripts/export_schema_to_csv.py`
**Purpose**: Export table schemas for mapping purposes

## Overview

This directory contains CSV exports of table schemas from the Neon PostgreSQL database. Each CSV includes column metadata extracted from `information_schema.columns` with PostgreSQL descriptions.

## Files Generated

| File | Table | Schema | Columns |
|------|-------|--------|---------|
| `01_outreach_outreach.csv` | outreach.outreach | outreach | 7 |
| `02_outreach_company_target.csv` | outreach.company_target | outreach | 18 |
| `03_outreach_dol.csv` | outreach.dol | outreach | 9 |
| `04_outreach_blog.csv` | outreach.blog | outreach | 12 |
| `05_outreach_people.csv` | outreach.people | outreach | 20 |
| `06_people_company_slot.csv` | people.company_slot | people | 11 |
| `07_people_people_master.csv` | people.people_master | people | 32 |
| `08_enrichment_hunter_company.csv` | enrichment.hunter_company | enrichment | 26 |
| `09_enrichment_hunter_contact.csv` | enrichment.hunter_contact | enrichment | 59 |
| `all_tables_schema.csv` | ALL TABLES COMBINED | multiple | 194 |

**Total Columns Exported**: 194

## CSV Schema

Each CSV contains the following columns:

| Column | Description |
|--------|-------------|
| `schema_name` | PostgreSQL schema name (e.g., outreach, people, enrichment) |
| `table_name` | Table name |
| `column_name` | Column name |
| `data_type` | PostgreSQL data type (e.g., uuid, character varying, integer) |
| `is_nullable` | YES or NO - whether column accepts NULL values |
| `column_default` | Default value expression for the column |
| `description` | Column description from pg_description (if available) |

## Key Tables

### Outreach Spine (7 columns)
**Table**: `outreach.outreach`
**Purpose**: Operational spine - all sub-hubs FK to `outreach_id`

Key columns:
- `outreach_id` (PK) - Minted by Outreach hub
- `sovereign_id` (FK) - Receipt to `cl.company_identity.company_unique_id`
- `domain` - Denormalized from CL for query performance
- `ein` - Tax ID for DOL matching
- `has_appointment` - Historical appointment flag

### Company Target (18 columns)
**Table**: `outreach.company_target`
**Purpose**: Company intelligence and email pattern discovery (Hub 04.04.01)

Key columns:
- `target_id` (PK)
- `outreach_id` (FK) - Links to spine
- `email_method` - Email pattern for generation
- `domain_verified` - Domain resolution status
- `bit_score` - Buyer Intent score (0-100)

### People Intelligence (20 columns)
**Table**: `outreach.people`
**Purpose**: Executive contacts with slot assignments (Hub 04.04.02)

Key columns:
- `person_id` (PK)
- `outreach_id` (FK) - Links to spine
- `slot_type` - Executive role (CEO, CFO, HR, etc.)
- `email` - Validated email address
- `email_verified` - Verification status
- `lifecycle_state` - Lifecycle stage (suspect → prospect → MQL → SQL)
- `funnel_membership` - Funnel position

### Hunter Company (26 columns)
**Table**: `enrichment.hunter_company`
**Purpose**: SOURCE data from Hunter.io (company enrichment)

Key columns:
- `domain` - Company domain (primary identifier)
- `organization` - Company name
- `email_pattern` - Email generation pattern
- `headcount_min` / `headcount_max` - Employee count range
- `industry_normalized` - Standardized industry
- `outreach_id` (FK) - Links to Outreach spine

### Hunter Contact (59 columns)
**Table**: `enrichment.hunter_contact`
**Purpose**: SOURCE data from Hunter.io (executive contacts)

Key columns:
- `email` - Contact email address
- `first_name` / `last_name` - Contact name
- `position` - Job title/role
- `seniority` - Executive level
- `department` - Functional area
- `domain` (FK) - Links to hunter_company
- `outreach_id` (FK) - Links to Outreach spine

## Usage

### Load Schema in Python

```python
import pandas as pd

# Load specific table schema
df = pd.read_csv('01_outreach_outreach.csv')

# Load all schemas
all_schemas = pd.read_csv('all_tables_schema.csv')

# Filter by schema
outreach_tables = all_schemas[all_schemas['schema_name'] == 'outreach']
```

### Query Patterns

```python
# Find all UUIDs in outreach schema
uuid_cols = all_schemas[
    (all_schemas['schema_name'] == 'outreach') &
    (all_schemas['data_type'] == 'uuid')
]

# Find all foreign keys (columns ending in _id)
fk_cols = all_schemas[all_schemas['column_name'].str.endswith('_id')]

# Find all nullable columns
nullable = all_schemas[all_schemas['is_nullable'] == 'YES']
```

## Regenerating Exports

To regenerate these CSV files:

```bash
doppler run -- python scripts/export_schema_to_csv.py
```

The script will:
1. Connect to Neon PostgreSQL via `DATABASE_URL`
2. Query `information_schema.columns` for each table
3. Left join with `pg_catalog.pg_description` for column descriptions
4. Export individual CSV files (numbered by waterfall order)
5. Create combined `all_tables_schema.csv`

## Notes

- All CSVs use UTF-8 encoding
- Column descriptions are pulled from PostgreSQL COMMENT ON COLUMN statements
- Empty descriptions appear as empty strings
- Columns are ordered by `ordinal_position` (table definition order)
- File names are prefixed with numbers indicating waterfall execution order

## Related Documentation

- `docs/schema_map.json` - JSON schema reference
- `doctrine/schemas/` - IMO Canonical schemas
- `neon/migrations/` - Database migration files
- `CLAUDE.md` - Architecture overview

---

**Last Generated**: 2026-02-05
**Database**: Neon PostgreSQL (Marketing DB)
**Connection**: ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech
