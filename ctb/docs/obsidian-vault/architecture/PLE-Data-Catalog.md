---
title: PLE Data Catalog
tags: [architecture, neon, postgresql, catalog, metadata, ai-searchable]
created: 2025-11-27
status: active
doctrine_id: 04.04.02.05
---

# PLE Data Catalog: AI & Human Searchable Metadata Layer

## Overview

The Data Catalog is a searchable metadata layer that enables both AI agents (Claude/LLMs) and human analysts to discover and understand database fields by business meaning, not just technical names.

**Created**: 2025-11-27
**Schema**: `catalog`
**Location**: PostgreSQL `catalog.*` tables and functions

---

## Why This Matters

### For AI Agents (Claude)
- Query metadata to understand which columns contain business data
- Find EIN, LinkedIn URLs, renewal dates without memorizing column names
- Understand data relationships and constraints

### For Human Analysts
- Search by business terms ("renewal date", "federal tax ID")
- Find columns across all schemas by meaning
- Discover data you didn't know existed

---

## Catalog Summary

| Schema | Tables | Columns |
|--------|--------|---------|
| company | 10 | 129 |
| dol | 7 | 282 |
| people | 7 | 121 |
| clay | 2 | 65 |
| intake | 5 | 128 |
| **TOTAL** | **31** | **725** |

---

## Search Functions

### Full-Text Search by Keyword

Search columns by any keyword in their name, description, or business context:

```sql
-- Search for EIN-related columns
SELECT * FROM catalog.search_columns('ein federal tax');

-- Search for renewal dates
SELECT * FROM catalog.search_columns('renewal date');

-- Search for LinkedIn fields
SELECT * FROM catalog.search_columns('linkedin');
```

**Returns**: column_id, table_id, column_name, description, business_name, data_type, relevance

### Search by Tag

Find all columns tagged with a specific category:

```sql
-- All DOL-related columns
SELECT * FROM catalog.search_by_tag('dol');

-- BIT scoring fields
SELECT * FROM catalog.search_by_tag('bit');

-- Renewal-related fields
SELECT * FROM catalog.search_by_tag('renewal');
```

**Returns**: column_id, table_id, column_name, description, tags

### Get Table Details

View all columns for a specific table with full metadata:

```sql
-- Company master columns
SELECT * FROM catalog.get_table_details('company.company_master');

-- Schedule A details
SELECT * FROM catalog.get_table_details('dol.schedule_a');
```

**Returns**: column_id, column_name, business_name, data_type, description, format_example, is_nullable, is_primary_key, is_foreign_key

### Get AI Context

Get a full text dump optimized for AI consumption:

```sql
-- Get context for company schema
SELECT catalog.get_ai_context('company');

-- Get context for ALL schemas
SELECT catalog.get_ai_context();
```

---

## Views

### v_searchable_columns

Flat view of all columns with full metadata. Good for bulk queries.

```sql
SELECT * FROM catalog.v_searchable_columns
WHERE schema_name = 'dol'
LIMIT 20;
```

### v_ai_reference

Quick reference view optimized for AI/LLM context windows.

```sql
SELECT * FROM catalog.v_ai_reference
WHERE table_id LIKE 'company.%';
```

### v_schema_summary

Summary statistics per schema.

```sql
SELECT * FROM catalog.v_schema_summary;
```

---

## Column ID Format

Every column has a unique identifier: `{schema}.{table}.{column}`

**Examples**:
- `company.company_master.ein`
- `dol.schedule_a.insurance_company_name`
- `people.company_slot.slot_type`

This format allows precise references across all documentation and queries.

---

## Common Tags

| Tag | Description |
|-----|-------------|
| `dol` | DOL federal data fields |
| `bit` | Used in BIT scoring |
| `renewal` | Related to renewal timing |
| `ein` | Federal tax ID fields |
| `linkedin` | LinkedIn profile URLs |
| `talent-flow` | Movement detection fields |
| `icp` | ICP criteria fields |

---

## Usage Examples

### AI Agent: Find EIN columns

```sql
-- Claude can search for EIN across all tables
SELECT column_id, table_id, description
FROM catalog.search_columns('ein federal employer')
ORDER BY relevance DESC
LIMIT 10;
```

**Result**:
- `dol.form_5500.sponsor_dfe_ein` - "Employer Identification Number of the plan sponsor"
- `company.company_master.ein` - "Federal Employer Identification Number"
- `dol.form_5500_sf.sponsor_dfe_ein` - "EIN for small plan sponsors"

### Analyst: Find all LinkedIn fields

```sql
SELECT column_id, business_name, format_example
FROM catalog.search_columns('linkedin url profile');
```

### Developer: Get schema for API

```sql
SELECT * FROM catalog.get_table_details('company.company_master')
WHERE is_nullable = false;
```

---

## Catalog Tables

### catalog.schemas

Registry of all PLE schemas:
- `schema_id` (PK) - Schema name
- `description` - Business purpose
- `schema_type` - hub, spoke, quarantine
- `owner` - Team responsible

### catalog.tables

Registry of all tables:
- `table_id` (PK) - `{schema}.{table}`
- `schema_id` (FK) - Parent schema
- `description` - Business purpose
- `row_count` - Estimated rows
- `primary_key` - PK column(s)

### catalog.columns

Registry of all columns (725+ entries):
- `column_id` (PK) - `{schema}.{table}.{column}`
- `table_id` (FK) - Parent table
- `column_name` - Technical name
- `business_name` - Human-readable name
- `description` - What this column stores
- `data_type` - PostgreSQL type
- `format_example` - Sample data format
- `synonyms` - Array of alternative names
- `tags` - Array of category tags
- `is_nullable`, `is_primary_key`, `is_foreign_key`

### catalog.relationships

Foreign key relationships:
- `from_column_id` - Source column
- `to_column_id` - Target column
- `relationship_type` - foreign_key, logical
- `description` - Relationship meaning

---

## Scripts

| Script | Purpose |
|--------|---------|
| `ctb/sys/enrichment/create_data_catalog.js` | Create and populate catalog |
| `ctb/sys/enrichment/fix_catalog_functions.js` | Fix search function types |
| `ctb/sys/enrichment/test_data_catalog.js` | Test search functionality |

---

## Maintenance

### Refresh Catalog After Schema Changes

```bash
node ctb/sys/enrichment/create_data_catalog.js
```

### Test Search Functions

```bash
node ctb/sys/enrichment/test_data_catalog.js
```

### Add Business Metadata

Update business names and descriptions for new columns:

```sql
UPDATE catalog.columns
SET business_name = 'Employee Count',
    description = 'Total number of active employees',
    tags = ARRAY['icp', 'company-size']
WHERE column_id = 'company.company_master.employee_count';
```

---

## Related Documentation

- [[Hub-Spoke-Schema-Architecture]] - Schema organization
- [[Schema-Export-System]] - Automated schema export
- [[Neon-Database-Architecture]] - Overall database setup

---

## Technical Notes

1. **Full-text search** uses PostgreSQL `ts_rank` and `plainto_tsquery`
2. **GIN indexes** on tags and synonyms arrays for fast lookup
3. **Type casting** in functions ensures consistent return types
4. **Auto-discovery** populates columns from `information_schema`
5. **Business metadata** added via UPDATE statements post-creation

---

**Status**: Production Ready
**Created**: 2025-11-27
**CTB Location**: `ctb/sys/enrichment/create_data_catalog.js`
