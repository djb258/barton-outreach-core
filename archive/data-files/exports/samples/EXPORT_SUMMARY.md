# DOL Schema Sample Export Summary

**Export Date**: 2026-02-06
**Export Location**: `C:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\exports\samples`

## Overview

Successfully exported 10 sample rows from each of 31 tables in the `dol` schema to CSV files.

## Export Statistics

- **Total Tables**: 31
- **Tables with Data**: 29
- **Empty Tables**: 2 (pressure_signals, renewal_calendar)
- **Total CSV Files Created**: 31

## Table Breakdown

### Core Form Tables

| Table | Total Rows | Sample Rows | Columns | Description |
|-------|------------|-------------|---------|-------------|
| form_5500 | 432,582 | 10 | 147 | Main Form 5500 filings (large plans) |
| form_5500_sf | 1,535,999 | 10 | 196 | Form 5500-SF (small plans) |
| form_5500_sf_part7 | 10,613 | 10 | 8 | Form 5500-SF Part VII |
| form_5500_icp_filtered | 24,892 | 10 | 7 | ICP filtered subset |

### Schedule A (Insurance Information)

| Table | Total Rows | Sample Rows | Columns |
|-------|------------|-------------|---------|
| schedule_a | 625,520 | 10 | 98 |
| schedule_a_part1 | 380,509 | 10 | 22 |

### Schedule C (Service Provider Information)

| Table | Total Rows | Sample Rows | Columns |
|-------|------------|-------------|---------|
| schedule_c | 241,556 | 10 | 5 |
| schedule_c_part1_item1 | 396,838 | 10 | 18 |
| schedule_c_part1_item2 | 754,802 | 10 | 25 |
| schedule_c_part1_item2_codes | 1,848,202 | 10 | 7 |
| schedule_c_part1_item3 | 383,338 | 10 | 22 |
| schedule_c_part1_item3_codes | 707,007 | 10 | 7 |
| schedule_c_part2 | 4,593 | 10 | 20 |
| schedule_c_part2_codes | 2,352 | 10 | 7 |
| schedule_c_part3 | 15,514 | 10 | 22 |

### Schedule D (Financial Information)

| Table | Total Rows | Sample Rows | Columns |
|-------|------------|-------------|---------|
| schedule_d | 121,813 | 10 | 8 |
| schedule_d_part1 | 808,051 | 10 | 11 |
| schedule_d_part2 | 2,392,112 | 10 | 9 |

### Schedule G (Financial Transaction Schedules)

| Table | Total Rows | Sample Rows | Columns |
|-------|------------|-------------|---------|
| schedule_g | 568 | 10 | 8 |
| schedule_g_part1 | 784 | 10 | 25 |
| schedule_g_part2 | 97 | 10 | 15 |
| schedule_g_part3 | 469 | 10 | 15 |

### Schedule H (Financial Information - Large Plans)

| Table | Total Rows | Sample Rows | Columns |
|-------|------------|-------------|---------|
| schedule_h | 169,276 | 10 | 169 |
| schedule_h_part1 | 20,359 | 10 | 8 |

### Schedule I (Financial Information - Small Plans)

| Table | Total Rows | Sample Rows | Columns |
|-------|------------|-------------|---------|
| schedule_i | 116,493 | 10 | 80 |
| schedule_i_part1 | 944 | 10 | 8 |

### Other Tables

| Table | Total Rows | Sample Rows | Columns | Description |
|-------|------------|-------------|---------|-------------|
| schedule_dcg | 235 | 10 | 121 | Schedule of DFE/Participating Plans |
| ein_urls | 127,909 | 10 | 9 | EIN lookup URLs |
| column_metadata | 1,081 | 10 | 14 | Column metadata reference |
| pressure_signals | 0 | 0 | 12 | Empty - pressure signals |
| renewal_calendar | 0 | 0 | 13 | Empty - renewal calendar |

## Key Observations

### Data Volume
- **Largest table**: schedule_d_part2 (2,392,112 rows)
- **Second largest**: schedule_c_part1_item2_codes (1,848,202 rows)
- **Third largest**: form_5500_sf (1,535,999 rows)

### Data Coverage
- **Form 5500**: 432,582 plans (large)
- **Form 5500-SF**: 1,535,999 plans (small)
- **Schedule A**: 625,520 insurance contracts
- **Schedule C**: 241,556 service provider relationships
- **Schedule D**: 121,813 financial schedules

### Empty Tables
- `pressure_signals` - Intended for future DOL pressure signal tracking
- `renewal_calendar` - Intended for future renewal tracking

## File Naming Convention

All files follow the pattern: `sample_<table_name>.csv`

Examples:
- `sample_form_5500.csv`
- `sample_schedule_a.csv`
- `sample_ein_urls.csv`

## Usage Notes

1. All CSV files are UTF-8 encoded
2. Each file contains column headers in the first row
3. Sample size is 10 rows or fewer (if table has less than 10 rows)
4. Empty tables (0 rows) have only header rows in their CSV files

## Next Steps

These sample files can be used for:
- Schema exploration and understanding
- Data quality assessment
- ETL pipeline development
- Integration testing
- Documentation generation

## Database Connection

**Schema**: dol
**Database**: Marketing DB (Neon PostgreSQL)
**SSL Mode**: require
