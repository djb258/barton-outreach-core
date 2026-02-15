---
title: Column Metadata Guide
hub: DOL Filings
type: reference
created: 2026-01-15
updated: 2026-01-15
tags:
  - hub/dol
  - metadata
  - ai-ready
---

# DOL Column Metadata Guide

## Overview

All 441 columns across DOL tables are documented with AI-ready metadata including:
- Unique column IDs
- Human-readable descriptions
- Data format patterns
- Search keywords
- Example values

## Column ID Convention

| Table | Prefix | Example |
|-------|--------|---------|
| form_5500 | `DOL_F5500_` | `DOL_F5500_SPONSOR_DFE_NAME` |
| form_5500_sf | `DOL_F5500SF_` | `DOL_F5500SF_SF_SPONSOR_NAME` |
| schedule_a | `DOL_SCHA_` | `DOL_SCHA_INS_BROKER_COMM_TOT_AMT` |

## Categories

| Category | Columns | Description |
|----------|---------|-------------|
| Form | 136 | Filing and form metadata |
| Sponsor | 68 | Plan sponsor information |
| General | 57 | General purpose fields |
| Administrator | 45 | Plan administrator data |
| Welfare | 40 | Welfare benefit indicators |
| Pension | 23 | Pension financial data |
| Preparer | 15 | Form preparer information |
| Filing | 12 | Filing identifiers and dates |
| Insurance | 11 | Insurance carrier/broker data |
| Contract | 9 | Contract type indicators |

## Data Formats

| Format | Pattern | Suffix |
|--------|---------|--------|
| CURRENCY | Decimal dollars (12345.67) | `*_amt` |
| DATE | YYYY-MM-DD | `*_date` |
| FLAG | Y/N/X or 1/0 | `*_ind` |
| EIN | 9 digits (XX-XXXXXXX) | `*_ein` |
| INTEGER | Whole number | `*_cnt` |
| TEXT | Variable length | name, address |

## Search Functions

### Search by Keyword
```sql
SELECT * FROM dol.search_columns('broker');
SELECT * FROM dol.search_columns('health benefits');
SELECT * FROM dol.search_columns('ein');
SELECT * FROM dol.search_columns('renewal');
```

### Get Table Schema
```sql
SELECT * FROM dol.get_table_schema('schedule_a');
SELECT * FROM dol.get_table_schema('form_5500');
SELECT * FROM dol.get_table_schema('form_5500_sf');
```

### Browse by Category
```sql
SELECT column_id, description, format_pattern
FROM dol.column_metadata
WHERE category = 'Insurance';
```

## Common Searches

### Broker-Related Columns
```sql
SELECT column_id, description
FROM dol.column_metadata
WHERE 'broker' = ANY(search_keywords);
```

**Results:**
- `DOL_SCHA_INS_BROKER_COMM_TOT_AMT` - Total broker commissions paid
- `DOL_SCHA_INS_BROKER_FEES_TOT_AMT` - Total broker fees paid
- `DOL_F5500SF_SF_BROKER_FEES_PAID_AMT` - Short Form broker fees

### Welfare Benefit Columns
```sql
SELECT column_id, description
FROM dol.column_metadata
WHERE category = 'Welfare';
```

**Key Columns:**
- `DOL_SCHA_WLFR_BNFT_HEALTH_IND` - Health benefits flag
- `DOL_SCHA_WLFR_BNFT_DENTAL_IND` - Dental benefits flag
- `DOL_SCHA_WLFR_BNFT_VISION_IND` - Vision benefits flag
- `DOL_SCHA_WLFR_BNFT_LIFE_INSUR_IND` - Life insurance flag

### Renewal Date Columns
```sql
SELECT column_id, description
FROM dol.column_metadata
WHERE column_name LIKE '%plan_year%';
```

**Results:**
- `DOL_F5500_FORM_PLAN_YEAR_BEGIN_DATE` - Form 5500 plan year start
- `DOL_F5500SF_SF_PLAN_YEAR_BEGIN_DATE` - Form 5500-SF plan year start
- `DOL_SCHA_SCH_A_PLAN_YEAR_BEGIN_DATE` - Schedule A plan year start

## Metadata Schema

```sql
CREATE TABLE dol.column_metadata (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50),
    column_name VARCHAR(100),
    column_id VARCHAR(100) UNIQUE,
    description TEXT,
    category VARCHAR(50),
    data_type VARCHAR(50),
    format_pattern VARCHAR(100),
    max_length INTEGER,
    search_keywords TEXT[],
    is_pii BOOLEAN,
    is_searchable BOOLEAN,
    example_values TEXT[]
);
```

## Related

- [[DOL Sub-Hub Overview]]
- [[DOL Schema ERD]]

#hub/dol #metadata #ai-ready
