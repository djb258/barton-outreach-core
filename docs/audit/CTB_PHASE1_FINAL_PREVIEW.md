# CTB Phase 1 Final Preview — Pending Operations

**Date**: 2026-02-06
**Mode**: READ-ONLY (EXECUTE_WRITES=FALSE)
**Status**: AWAITING APPROVAL

---

## Summary of Pending Operations

| Phase | Operation | Rows Affected |
|-------|-----------|---------------|
| STEP 1 | Fix CL→Outreach joint (Option B) | 1,343 |
| 1C | Move url_discovery_failures to outreach | 42,348 |
| 1D | Merge audit tables → pipeline_audit_log | 1,534 |
| 1E | Merge queue tables → entity_resolution_queue | 33,217 |
| 1F | Merge pressure_signals → bit_signals | 0 |
| 1G.1 | Move staging tables to intake | 139,861 |
| 1G.2 | Merge people_invalid → people_errors | 21 |
| 1G.3 | Merge sidecar/scores as JSONB | 16 |
| 1G.4 | Reclassify MV tables (metadata only) | 0 |
| 1G.5 | Merge duplicate archives | 55,521 |
| **TOTAL** | | **273,861** |

---

## STEP 1: Fix CL→Outreach Joint (RECOMMENDED: Option B)

### Problem
- 1,343 CL records have `outreach_id` pointing to non-existent outreach rows
- All created at same timestamp (2026-02-04) - bulk operation that didn't complete
- Zero have data in any sub-hub

### SQL Preview
```sql
-- Step 1a: Log orphan outreach_ids to error table
INSERT INTO cl.cl_err_existence (error_type, error_message, created_at)
SELECT
    'orphan_outreach_id',
    json_build_object(
        'company_unique_id', ci.company_unique_id,
        'orphan_outreach_id', ci.outreach_id,
        'original_created_at', ci.created_at
    )::text,
    NOW()
FROM cl.company_identity ci
WHERE ci.outreach_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = ci.outreach_id);

-- Step 1b: NULL the orphan pointers
UPDATE cl.company_identity
SET outreach_id = NULL, updated_at = NOW()
WHERE outreach_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = company_identity.outreach_id);
```

### Expected Result
- CL with outreach_id: 96,347 → 95,004
- Outreach.outreach: 95,004
- **Parity restored: 95,004 = 95,004**

---

## PHASE 1C: Move Wrong Schema Tables

### company.url_discovery_failures → outreach
```sql
-- Archive first
CREATE TABLE IF NOT EXISTS archive.company_url_discovery_failures_ctb AS
SELECT *, NOW() as archived_at FROM company.url_discovery_failures;

-- Move table
ALTER TABLE company.url_discovery_failures SET SCHEMA outreach;
ALTER TABLE company.url_discovery_failures_archive SET SCHEMA outreach;
```
**Rows**: 42,348

---

## PHASE 1D: Audit Table Centralization

All audit tables merge into `outreach.pipeline_audit_log` with `source_hub` discriminator.

| Source Table | Rows | source_hub |
|--------------|------|------------|
| outreach.dol_audit_log | 0 | dol |
| outreach.blog_source_history | 0 | blog |
| outreach.bit_input_history | 0 | bit |
| bit.authorization_log | 0 | bit_auth |
| people.people_promotion_audit | 9 | people_promo |
| people.people_resolution_history | 0 | people_resolution |
| people.company_resolution_log | 155 | company_resolution |
| people.person_movement_history | 0 | person_movement |
| people.slot_assignment_history | 1,370 | slot_assignment |
| outreach.send_log | 0 | execution_send |
| **TOTAL** | **1,534** | |

### SQL Template
```sql
-- Ensure target has required columns
ALTER TABLE outreach.pipeline_audit_log ADD COLUMN IF NOT EXISTS log_data JSONB;

-- For each audit table:
INSERT INTO outreach.pipeline_audit_log (source_hub, log_data, created_at)
SELECT
    '{source_hub}',
    to_jsonb(src),
    COALESCE(src.created_at, NOW())
FROM {source_table} src;

-- Archive source
CREATE TABLE IF NOT EXISTS archive.{source_name}_ctb AS
SELECT *, NOW() as archived_at FROM {source_table};
```

---

## PHASE 1E: Queue Table Centralization

All queue tables merge into `outreach.entity_resolution_queue` with `queue_type` discriminator.

| Source Table | Rows | queue_type |
|--------------|------|------------|
| people.people_resolution_queue | 1,206 | people_resolution |
| people.paid_enrichment_queue | 32,011 | paid_enrichment |
| **TOTAL** | **33,217** | |

### SQL Template
```sql
-- Ensure target has required columns
ALTER TABLE outreach.entity_resolution_queue ADD COLUMN IF NOT EXISTS queue_data JSONB;

-- For each queue table:
INSERT INTO outreach.entity_resolution_queue (queue_type, queue_data, created_at)
SELECT
    '{queue_type}',
    to_jsonb(src),
    COALESCE(src.created_at, NOW())
FROM {source_table} src;

-- Archive source
CREATE TABLE IF NOT EXISTS archive.{source_name}_ctb AS
SELECT *, NOW() as archived_at FROM {source_table};
```

---

## PHASE 1F: Signals Centralization

All pressure_signals merge into `outreach.bit_signals` with `signal_source` discriminator.

| Source Table | Rows | signal_source |
|--------------|------|---------------|
| dol.pressure_signals | 0 | dol |
| blog.pressure_signals | 0 | blog |
| people.pressure_signals | 0 | people |
| **TOTAL** | **0** | |

**Note**: All empty - archive only, no merge needed.

---

## PHASE 1G: Non-Conforming Leaf Tables

### 1G.1 Staging Tables → intake schema
```sql
-- Move to intake schema
ALTER TABLE people.people_staging SET SCHEMA intake;
ALTER TABLE people.people_candidate SET SCHEMA intake;
```
**Rows**: 139,861

### 1G.2 Error Variants → Merge
```sql
-- Merge people_invalid into people_errors
INSERT INTO people.people_errors (error_type, error_message, created_at)
SELECT 'invalid_record', to_jsonb(src)::text, COALESCE(src.created_at, NOW())
FROM people.people_invalid src;

-- Archive source
CREATE TABLE IF NOT EXISTS archive.people_people_invalid_ctb AS
SELECT *, NOW() as archived_at FROM people.people_invalid;
```
**Rows**: 21

### 1G.3 Sidecar/Scores → Merge as JSONB
```sql
-- outreach.dol_url_enrichment → outreach.dol (16 rows)
ALTER TABLE outreach.dol ADD COLUMN IF NOT EXISTS url_enrichment_data JSONB;

UPDATE outreach.dol d
SET url_enrichment_data = (
    SELECT to_jsonb(e) FROM outreach.dol_url_enrichment e
    WHERE e.dol_id = d.dol_id  -- assuming FK
)
WHERE EXISTS (SELECT 1 FROM outreach.dol_url_enrichment e WHERE e.dol_id = d.dol_id);

-- Archive source
CREATE TABLE IF NOT EXISTS archive.outreach_dol_url_enrichment_ctb AS
SELECT *, NOW() as archived_at FROM outreach.dol_url_enrichment;
```
**Rows**: 16

### 1G.4 Reclassify as MV (Metadata Only)
Tables reclassified as MATERIALIZED_VIEW in CTB conformance map:
- `outreach.company_hub_status` (68,908 rows)
- `bit.movement_events` (0 rows)
- `outreach.engagement_events` (0 rows)
- `outreach.bit_signals` (0 rows)

**No SQL needed** - documentation/metadata update only.

### 1G.5 Duplicate Archives → Merge
```sql
-- Merge outreach_orphan_archive into outreach_archive
INSERT INTO outreach.outreach_archive
SELECT * FROM outreach.outreach_orphan_archive
ON CONFLICT (outreach_id) DO NOTHING;

-- Merge company_target_orphaned_archive into company_target_archive
INSERT INTO outreach.company_target_archive
SELECT * FROM outreach.company_target_orphaned_archive
ON CONFLICT (target_id) DO NOTHING;
```
**Rows**: 55,521

---

## Execution Checklist

- [ ] STEP 1: Fix CL→Outreach joint (1,343 records)
- [ ] PHASE 1C: Move url_discovery tables (42,348 rows)
- [ ] PHASE 1D: Merge audit tables (1,534 rows)
- [ ] PHASE 1E: Merge queue tables (33,217 rows)
- [ ] PHASE 1F: Archive signal tables (0 rows)
- [ ] PHASE 1G.1: Move staging tables (139,861 rows)
- [ ] PHASE 1G.2: Merge error variants (21 rows)
- [ ] PHASE 1G.3: Merge sidecar/scores (16 rows)
- [ ] PHASE 1G.4: Reclassify MVs (metadata only)
- [ ] PHASE 1G.5: Merge duplicate archives (55,521 rows)

---

## To Execute

Set `EXECUTE_WRITES=TRUE` to proceed with execution.

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | EXECUTION PREVIEW |
| Status | AWAITING EXECUTE_WRITES=TRUE |
