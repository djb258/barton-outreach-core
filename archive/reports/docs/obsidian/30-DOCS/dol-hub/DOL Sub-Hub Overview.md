---
title: DOL Sub-Hub Overview
hub: DOL Filings
doctrine_id: "04.04.03"
cc_layer: CC-02
status: hardened
created: 2026-01-15
updated: 2026-01-15
tags:
  - hub/dol
  - hardened
  - schema
---

# DOL Sub-Hub Overview

## Quick Stats

| Metric | Value |
|--------|-------|
| **Doctrine ID** | 04.04.03 |
| **CC Layer** | CC-02 |
| **Status** | Hardened |
| **Data Year** | 2023 |
| **Total Rows** | 1,328,797 |
| **Total Columns** | 441 |

## Purpose

The DOL Sub-Hub processes U.S. Department of Labor EFAST2 data to enrich company records with regulatory filings and insurance information.

## Data Tables

### dol.form_5500
- **Rows**: 230,482
- **Columns**: 147
- **Description**: Large plan filings (>=100 participants)
- **Key Fields**: EIN, sponsor name, plan year, total assets
- **Status**: Read-Only

### dol.form_5500_sf
- **Rows**: 760,839
- **Columns**: 196
- **Description**: Small plan filings (<100 participants)
- **Key Fields**: EIN, sponsor name, plan year
- **Status**: Read-Only

### dol.schedule_a
- **Rows**: 337,476
- **Columns**: 98
- **Description**: Insurance broker/carrier data
- **Key Fields**: Carrier name, broker commissions, welfare benefits
- **Status**: Read-Only
- **Links to**: form_5500 via ACK_ID

### dol.column_metadata
- **Rows**: 441
- **Columns**: 12
- **Description**: AI-ready column documentation
- **Status**: Writable

## Related Documents

- [[PRD_DOL_SUBHUB|PRD v3.0]]
- [[ADR-004|ADR-004: Data Import & Lock]]
- [[DOL_HUB_COMPLIANCE|Compliance Checklist]]
- [[DOL Schema ERD]]
- [[Column Metadata Guide]]

## Key Queries

```sql
-- Search columns by keyword
SELECT * FROM dol.search_columns('broker');

-- Get table schema
SELECT * FROM dol.get_table_schema('schedule_a');

-- Find companies with broker data in Texas
SELECT sponsor_name, ins_carrier_name, ins_broker_comm_tot_amt
FROM dol.schedule_a
WHERE sponsor_state = 'TX' AND ins_broker_comm_tot_amt > 0;
```

## Read-Only Protection

All DOL data tables are protected by PostgreSQL triggers:

```sql
-- Normal access: blocked
INSERT → DOL_READONLY_VIOLATION
UPDATE → DOL_READONLY_VIOLATION
DELETE → DOL_READONLY_VIOLATION

-- Import bypass
SET session dol.import_mode = 'active';
```

## Signals Emitted

| Signal | Impact | When |
|--------|--------|------|
| FORM_5500_FILED | +5.0 | Filing matched to company |
| LARGE_PLAN | +8.0 | >=500 participants |
| BROKER_CHANGE | +7.0 | Broker changed YoY |

## Tags

#hub/dol #hardened #schema #data/2023
