# 🚀 PRE-FLIGHT VALIDATION REPORT
**Barton Outreach Core - Production Readiness Check**

**Generated**: 2025-10-22
**Status**: Manual validation required

---

## ✅ Check 1: Table/View Existence

Verifying that all required tables and views exist in the Neon marketing schema.

| Object | Type | Doctrine | Status | Notes |
|--------|------|----------|--------|-------|
| marketing.company_master | table | 04.04.01 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_slot | table | 04.04.05 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_intelligence | table | 04.04.03 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_master | table | 04.04.02 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_intelligence | table | 04.04.04 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.actor_usage_log | table | 04.04.07 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.linkedin_refresh_jobs | table | 04.04.06 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_audit_log | table | 04.04.01 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_audit_log | table | 04.04.02 | ⏳ PENDING | Requires manual MCP query execution |
| marketing.validation_log | table | 04.04 | ⏳ PENDING | Requires manual MCP query execution |

### SQL Query for Check 1

```sql
SELECT
  table_schema || '.' || table_name as full_name,
  table_type
FROM information_schema.tables
WHERE table_schema = 'marketing'
  AND table_name IN (
    'company_master', 'company_slot', 'company_intelligence',
    'people_master', 'people_intelligence', 'actor_usage_log',
    'linkedin_refresh_jobs', 'company_audit_log', 'people_audit_log',
    'validation_log'
  )
ORDER BY table_name;
```

---

## 🔢 Check 2: Row Count Thresholds

Validating that tables meet minimum data sufficiency requirements.

| Table | Threshold | Actual | Status | Notes |
|-------|-----------|--------|--------|-------|
| marketing.company_master | ≥ 400 | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_slot | = 3× company_master | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_master | ≥ 0 | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_audit_log | > 0 (not empty) | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_audit_log | > 0 (not empty) | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.validation_log | > 0 (not empty) | TBD | ⏳ PENDING | Requires manual MCP query execution |

### SQL Queries for Check 2

```sql
-- Query 1: Count all tables
SELECT 'company_master' as table_name, COUNT(*) as row_count
FROM marketing.company_master
UNION ALL
SELECT 'company_slot', COUNT(*)
FROM marketing.company_slot
UNION ALL
SELECT 'people_master', COUNT(*)
FROM marketing.people_master
UNION ALL
SELECT 'company_audit_log', COUNT(*)
FROM marketing.company_audit_log
UNION ALL
SELECT 'people_audit_log', COUNT(*)
FROM marketing.people_audit_log
UNION ALL
SELECT 'validation_log', COUNT(*)
FROM marketing.validation_log;

-- Query 2: Validate company_slot ratio (must equal 3× company_master)
SELECT
  (SELECT COUNT(*) FROM marketing.company_master) as company_master_count,
  (SELECT COUNT(*) FROM marketing.company_slot) as company_slot_count,
  CASE
    WHEN (SELECT COUNT(*) FROM marketing.company_slot) =
         (SELECT COUNT(*) FROM marketing.company_master) * 3
    THEN 'VALID'
    ELSE 'INVALID'
  END as slot_ratio_status;
```

---

## 🔖 Check 3: Barton ID Pattern Compliance

Validating that all Barton IDs follow the 6-segment format: `04.04.0x.xx.xxxxx.xxx`

| Table | Column | Pattern | Valid | Invalid | Status | Notes |
|-------|--------|---------|-------|---------|--------|-------|
| marketing.company_master | company_barton_id | `^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | TBD | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_master | people_barton_id | `^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | TBD | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_intelligence | intel_barton_id | `^04\.04\.03\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | TBD | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.people_intelligence | intel_barton_id | `^04\.04\.04\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | TBD | TBD | ⏳ PENDING | Requires manual MCP query execution |
| marketing.company_slot | slot_barton_id | `^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$` | TBD | TBD | ⏳ PENDING | Requires manual MCP query execution |

### SQL Queries for Check 3

```sql
-- Query 1: Validate company_master Barton IDs
SELECT
  'company_master' as table_name,
  'company_barton_id' as id_column,
  COUNT(*) as total_rows,
  COUNT(*) FILTER (
    WHERE company_barton_id ~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as valid_ids,
  COUNT(*) FILTER (
    WHERE company_barton_id !~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_ids,
  ARRAY_AGG(company_barton_id) FILTER (
    WHERE company_barton_id !~ '^04\.04\.01\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_examples
FROM marketing.company_master;

-- Query 2: Validate people_master Barton IDs
SELECT
  'people_master' as table_name,
  'people_barton_id' as id_column,
  COUNT(*) as total_rows,
  COUNT(*) FILTER (
    WHERE people_barton_id ~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as valid_ids,
  COUNT(*) FILTER (
    WHERE people_barton_id !~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_ids,
  ARRAY_AGG(people_barton_id) FILTER (
    WHERE people_barton_id !~ '^04\.04\.02\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_examples
FROM marketing.people_master;

-- Query 3: Validate company_intelligence Barton IDs
SELECT
  'company_intelligence' as table_name,
  'intel_barton_id' as id_column,
  COUNT(*) as total_rows,
  COUNT(*) FILTER (
    WHERE intel_barton_id ~ '^04\.04\.03\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as valid_ids,
  COUNT(*) FILTER (
    WHERE intel_barton_id !~ '^04\.04\.03\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_ids,
  ARRAY_AGG(intel_barton_id) FILTER (
    WHERE intel_barton_id !~ '^04\.04\.03\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_examples
FROM marketing.company_intelligence;

-- Query 4: Validate people_intelligence Barton IDs
SELECT
  'people_intelligence' as table_name,
  'intel_barton_id' as id_column,
  COUNT(*) as total_rows,
  COUNT(*) FILTER (
    WHERE intel_barton_id ~ '^04\.04\.04\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as valid_ids,
  COUNT(*) FILTER (
    WHERE intel_barton_id !~ '^04\.04\.04\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_ids,
  ARRAY_AGG(intel_barton_id) FILTER (
    WHERE intel_barton_id !~ '^04\.04\.04\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_examples
FROM marketing.people_intelligence;

-- Query 5: Validate company_slot Barton IDs
SELECT
  'company_slot' as table_name,
  'slot_barton_id' as id_column,
  COUNT(*) as total_rows,
  COUNT(*) FILTER (
    WHERE slot_barton_id ~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as valid_ids,
  COUNT(*) FILTER (
    WHERE slot_barton_id !~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_ids,
  ARRAY_AGG(slot_barton_id) FILTER (
    WHERE slot_barton_id !~ '^04\.04\.05\.[0-9]{2}\.[0-9]{5}\.[0-9]{3}$'
  ) as invalid_examples
FROM marketing.company_slot;
```

---

## 🔗 Check 4: Foreign Key Integrity

Validating referential integrity between parent and child tables.

| Relationship | Parent Table | Child Table | Orphaned | Status | Notes |
|--------------|--------------|-------------|----------|--------|-------|
| company_master → company_slot | marketing.company_master | marketing.company_slot | TBD | ⏳ PENDING | Requires manual MCP query execution |
| company_master → company_intelligence | marketing.company_master | marketing.company_intelligence | TBD | ⏳ PENDING | Requires manual MCP query execution |
| people_master → people_intelligence | marketing.people_master | marketing.people_intelligence | TBD | ⏳ PENDING | Requires manual MCP query execution |
| company_master → people_intelligence (via company_barton_id) | marketing.company_master | marketing.people_intelligence | TBD | ⏳ PENDING | Requires manual MCP query execution |

### SQL Queries for Check 4

```sql
-- Query 1: Check for orphaned company_slot records
SELECT
  'company_master → company_slot' as relationship,
  'company_slot' as child_table,
  COUNT(*) as orphaned_records
FROM marketing.company_slot child
WHERE NOT EXISTS (
  SELECT 1 FROM marketing.company_master parent
  WHERE parent.company_barton_id = child.company_barton_id
);

-- Query 2: Check for orphaned company_intelligence records
SELECT
  'company_master → company_intelligence' as relationship,
  'company_intelligence' as child_table,
  COUNT(*) as orphaned_records
FROM marketing.company_intelligence child
WHERE NOT EXISTS (
  SELECT 1 FROM marketing.company_master parent
  WHERE parent.company_barton_id = child.company_barton_id
);

-- Query 3: Check for orphaned people_intelligence records (people_barton_id)
SELECT
  'people_master → people_intelligence' as relationship,
  'people_intelligence' as child_table,
  COUNT(*) as orphaned_records
FROM marketing.people_intelligence child
WHERE NOT EXISTS (
  SELECT 1 FROM marketing.people_master parent
  WHERE parent.people_barton_id = child.people_barton_id
);

-- Query 4: Check for orphaned people_intelligence records (company_barton_id)
SELECT
  'company_master → people_intelligence' as relationship,
  'people_intelligence' as child_table,
  COUNT(*) as orphaned_records
FROM marketing.people_intelligence child
WHERE child.company_barton_id IS NOT NULL
  AND NOT EXISTS (
    SELECT 1 FROM marketing.company_master parent
    WHERE parent.company_barton_id = child.company_barton_id
  );

-- Query 5: List all foreign key constraints in marketing schema
SELECT
  tc.table_schema || '.' || tc.table_name as child_table,
  kcu.column_name as child_column,
  ccu.table_schema || '.' || ccu.table_name as parent_table,
  ccu.column_name as parent_column,
  tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'marketing'
ORDER BY tc.table_name;
```

---

## 📊 Validation Summary

| Metric | Count |
|--------|-------|
| Total Checks | 25 |
| ✅ Passed | 0 |
| ⚠️  Warnings | 0 |
| ❌ Failed | 0 |
| ⏳ Pending | 25 |

**Status**: All checks require manual execution via Composio MCP

---

## 🎯 Next Steps

1. Execute all SQL queries via Composio MCP `neon_execute_sql` tool
2. Update this report with actual results from database
3. Resolve any ❌ FAIL or ⚠️  WARN statuses before production deployment
4. Re-run validation after fixes to confirm ✅ OK status
5. Archive this report for audit trail

---

## 🛠️  SQL Execution Instructions

All queries must be executed via Composio MCP using the following pattern:

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "<YOUR_SQL_QUERY_HERE>"
    },
    "unique_id": "HEIR-2025-10-PREFLIGHT-01",
    "process_id": "PRC-VALIDATION-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

### Example: Check Table Existence

```bash
curl -X POST http://localhost:3001/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "neon_execute_sql",
    "data": {
      "sql_query": "SELECT table_schema || '\''.'\'' || table_name as full_name, table_type FROM information_schema.tables WHERE table_schema = '\''marketing'\'' AND table_name IN ('\''company_master'\'', '\''company_slot'\'', '\''company_intelligence'\'', '\''people_master'\'', '\''people_intelligence'\'', '\''actor_usage_log'\'', '\''linkedin_refresh_jobs'\'', '\''company_audit_log'\'', '\''people_audit_log'\'', '\''validation_log'\'') ORDER BY table_name;"
    },
    "unique_id": "HEIR-2025-10-PREFLIGHT-01",
    "process_id": "PRC-VALIDATION-001",
    "orbt_layer": 2,
    "blueprint_version": "1.0"
  }'
```

---

## 📝 Validation Checklist

Use this checklist to track manual validation progress:

- [ ] **Check 1**: Table/View Existence - Execute query and verify all 10 objects exist
- [ ] **Check 2**: Row Count Thresholds - Execute queries and verify all thresholds met
- [ ] **Check 3**: Barton ID Pattern Compliance - Execute queries and verify 0 invalid IDs
- [ ] **Check 4**: Foreign Key Integrity - Execute queries and verify 0 orphaned records
- [ ] **Final Review**: All checks passed with ✅ OK status

---

## 🔒 Production Deployment Criteria

The system is **APPROVED FOR PRODUCTION** when:

1. ✅ All 10 required tables/views exist in Neon
2. ✅ All row count thresholds are met or exceeded
3. ✅ All Barton IDs conform to the 6-segment pattern (0 invalid IDs)
4. ✅ All foreign key relationships have 0 orphaned records
5. ✅ No ❌ FAIL or ⚠️  WARN statuses in final report

**Current Status**: ⏳ PENDING - Awaiting manual validation

---

**Doctrine Reference**: 04.04 - Outreach Core Data Integrity
**Validation Script**: `analysis/pre_flight_validation.js`
**Report File**: `analysis/PRE_FLIGHT_VALIDATION_REPORT.md`
**Generated**: 2025-10-22
**Report Version**: 1.0
