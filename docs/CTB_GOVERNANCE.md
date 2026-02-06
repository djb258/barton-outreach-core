# CTB Governance Document

**Version**: 1.0.0
**Created**: 2026-02-06
**Status**: PHASE 3 COMPLETE - ENFORCEMENT LOCKED
**Tags**: `CTB_PHASE1_LOCK`, `CTB_PHASE2_COLUMN_HYGIENE`, `CTB_PHASE3_ENFORCEMENT_LOCK`

---

## 1. Overview

### 1.1 What is CTB?

**CTB (Christmas Tree Backbone)** is the hierarchical data model with ID-based paths that organizes all tables in the Neon PostgreSQL database. It provides:

- **Table Classification**: Every table has a designated leaf type
- **Governance Enforcement**: Frozen tables cannot be modified without formal change request
- **Drift Detection**: Automated identification of schema inconsistencies
- **Audit Trail**: Complete history of table modifications and violations

### 1.2 CTB Registry Location

```
Schema: ctb
Tables:
  - ctb.table_registry (246 rows) - Master table classification
  - ctb.violation_log (audit trail) - Schema violation tracking
```

### 1.3 Quick Reference

| Metric | Value |
|--------|-------|
| Total Tables Registered | 246 |
| Frozen Core Tables | 9 |
| Current Violations | 0 |
| **Sovereign Eligible** | 95,004 (101,503 - 6,499 excluded) |
| **Outreach Claimed** | 95,004 = 95,004 ✓ ALIGNED |

---

## 2. Leaf Type Classification

Every table in the database is assigned exactly one leaf type:

| Leaf Type | Count | Description | Modification Rules |
|-----------|-------|-------------|-------------------|
| **CANONICAL** | 50 | Primary data tables | Normal write access |
| **ARCHIVE** | 112 | CTB archive tables | Append-only |
| **SYSTEM** | 23 | System/metadata tables | Admin only |
| **DEPRECATED** | 21 | Legacy tables | Read-only |
| **ERROR** | 14 | Error tracking tables | Append-only |
| **STAGING** | 12 | Intake/staging tables | Temporary data |
| **MV** | 8 | Materialized view candidates | Refresh-only |
| **REGISTRY** | 6 | Lookup/reference tables | Admin only |

### 2.1 Leaf Type Query

```sql
-- Get leaf type for any table
SELECT table_schema, table_name, leaf_type, is_frozen, notes
FROM ctb.table_registry
WHERE table_name = 'your_table_name';

-- Count by leaf type
SELECT leaf_type, COUNT(*) as table_count
FROM ctb.table_registry
GROUP BY leaf_type
ORDER BY table_count DESC;
```

---

## 3. Frozen Core Tables

The following 9 tables are **FROZEN** and require formal change request before modification:

| Schema | Table | Purpose |
|--------|-------|---------|
| `cl` | `company_identity` | Authority registry (identity pointers) |
| `outreach` | `outreach` | Operational spine |
| `outreach` | `company_target` | Company targeting data |
| `outreach` | `dol` | DOL filing references |
| `outreach` | `blog` | Blog/content signals |
| `outreach` | `people` | People references |
| `outreach` | `bit_scores` | BIT scoring data |
| `people` | `people_master` | Contact master records |
| `people` | `company_slot` | Executive slot assignments |

### 3.1 Frozen Table Query

```sql
-- List all frozen tables
SELECT table_schema, table_name, notes
FROM ctb.table_registry
WHERE is_frozen = TRUE
ORDER BY table_schema, table_name;
```

### 3.2 Change Request Process

To modify a frozen table:

1. Create ADR documenting the change rationale
2. Update `doctrine/DO_NOT_MODIFY_REGISTRY.md`
3. Get approval from system owner
4. Execute change with audit trail
5. Update CTB registry if needed

---

## 4. Column Contracts

### 4.1 NOT NULL Constraints

Error tables have mandatory discriminator columns:

| Table | Column | Constraint |
|-------|--------|------------|
| `outreach.dol_errors` | `error_type` | NOT NULL |
| `outreach.blog_errors` | `error_type` | NOT NULL |
| `cl.cl_errors_archive` | `error_type` | NOT NULL |
| `people.people_errors` | `error_type` | NOT NULL |

### 4.2 CTB_CONTRACT Comments

Key columns should have `CTB_CONTRACT` comments documenting their purpose:

```sql
COMMENT ON COLUMN outreach.outreach.outreach_id IS
  'CTB_CONTRACT: Primary key, minted by Outreach hub, registered in CL once';
```

---

## 5. Drift Detection

### 5.1 Drift Types

| Type | Description | Action |
|------|-------------|--------|
| `DEPRECATED_WITH_DATA` | Legacy tables with data | Archive or delete |
| `MISSING_CONTRACT` | Key columns without documentation | Add CTB_CONTRACT comment |
| `UNREGISTERED_TABLE` | Tables not in CTB registry | Register or drop |

### 5.2 Current Drift Status

| Type | Count | Notes |
|------|-------|-------|
| DEPRECATED_WITH_DATA | 13 | Legacy tables retained for reference |
| MISSING_CONTRACT | 10 | Key columns need CTB_CONTRACT comment |
| UNREGISTERED_TABLE | 0 | All tables registered |

### 5.3 Deprecated Tables With Data

These tables are marked DEPRECATED but retain data:

| Table | Rows | Notes |
|-------|------|-------|
| `company.company_source_urls` | 104,012 | Legacy URL data |
| `company.company_master` | 74,641 | Archived in Phase 1 |
| `company.pipeline_events` | 2,185 | Pipeline audit data |
| `company.company_slots` | 1,359 | Archived in Phase 1 |
| `marketing.review_queue` | 516 | Legacy review queue |
| `marketing.company_master` | 512 | Archived in Phase 1 |
| `marketing.failed_email_verification` | 310 | Archived in Phase 1 |
| `marketing.failed_slot_assignment` | 222 | Archived in Phase 1 |
| `marketing.people_master` | 149 | Archived in Phase 1 |
| `marketing.failed_company_match` | 32 | Archived in Phase 1 |
| `company.message_key_reference` | 8 | Legacy mapping |
| `marketing.failed_no_pattern` | 6 | Archived in Phase 1 |
| `marketing.failed_low_confidence` | 5 | Archived in Phase 1 |

---

## 6. CTB Phase History

### 6.1 Phase 1: Initial Lock (CTB_PHASE1_LOCK)

- Created CTB registry schema
- Registered all 246 tables
- Established leaf type classification

### 6.2 Phase 2: Column Hygiene (CTB_PHASE2_COLUMN_HYGIENE)

- Normalized error tables
- Added NOT NULL constraints
- Documented column contracts

### 6.3 Phase 3: Enforcement Lock (CTB_PHASE3_ENFORCEMENT_LOCK)

- Froze 9 core tables
- Enabled drift detection
- Created violation logging
- Verified join key integrity

---

## 7. Governance Rules

### 7.1 Table Creation

New tables must be registered in CTB before use:

```sql
INSERT INTO ctb.table_registry (table_schema, table_name, leaf_type, notes)
VALUES ('your_schema', 'your_table', 'CANONICAL', 'Purpose description');
```

### 7.2 Table Modification

- **CANONICAL**: Normal DDL allowed
- **FROZEN**: Requires formal change request
- **DEPRECATED**: Read-only, no modifications
- **ARCHIVE**: Append-only, no updates/deletes

### 7.3 Table Deletion

Tables should be marked DEPRECATED before deletion:

```sql
UPDATE ctb.table_registry
SET leaf_type = 'DEPRECATED', notes = 'Scheduled for removal: YYYY-MM-DD'
WHERE table_schema = 'schema' AND table_name = 'table';
```

---

## 8. Useful Queries

### 8.1 Registry Overview

```sql
-- Full registry with counts
SELECT
    leaf_type,
    COUNT(*) as tables,
    SUM(CASE WHEN is_frozen THEN 1 ELSE 0 END) as frozen
FROM ctb.table_registry
GROUP BY leaf_type
ORDER BY tables DESC;
```

### 8.2 Schema Summary

```sql
-- Tables by schema
SELECT
    table_schema,
    COUNT(*) as tables,
    string_agg(DISTINCT leaf_type, ', ') as leaf_types
FROM ctb.table_registry
GROUP BY table_schema
ORDER BY tables DESC;
```

### 8.3 Violation Check

```sql
-- Recent violations
SELECT *
FROM ctb.violation_log
ORDER BY created_at DESC
LIMIT 20;
```

### 8.4 Frozen Table Check

```sql
-- Check if a table is frozen before modifying
SELECT is_frozen, notes
FROM ctb.table_registry
WHERE table_schema = 'your_schema'
  AND table_name = 'your_table';
```

---

## 9. Related Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Phase 3 Summary | `docs/audit/CTB_PHASE3_ENFORCEMENT_SUMMARY.md` | Enforcement details |
| Drift Report | `docs/audit/CTB_DRIFT_REPORT.md` | Current drift status |
| Guardrail Status | `docs/audit/CTB_GUARDRAIL_STATUS.md` | Constraint status |
| Guardrail Matrix | `docs/audit/CTB_GUARDRAIL_MATRIX.csv` | Full table registry |
| DO NOT MODIFY | `doctrine/DO_NOT_MODIFY_REGISTRY.md` | Frozen components |
| MASTER ERD | `docs/MASTER_ERD.md` | Database architecture |
| OSAM | `docs/OSAM.md` | Semantic access map |

---

## 10. Event Trigger (Optional)

To enforce table registration at creation time:

```sql
CREATE EVENT TRIGGER ctb_table_creation_check
    ON ddl_command_end
    WHEN TAG IN ('CREATE TABLE')
    EXECUTE FUNCTION ctb.check_table_creation();
```

**Note**: Event trigger is available but not enabled by default.

---

## Document Control

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Created | 2026-02-06 |
| Author | System |
| Status | ACTIVE |
| Review Cycle | Quarterly |

---

**CTB Tags**: `CTB_PHASE1_LOCK` | `CTB_PHASE2_COLUMN_HYGIENE` | `CTB_PHASE3_ENFORCEMENT_LOCK`
