# CTB Phase 2 Column Hygiene Plan

**Date**: 2026-02-06
**Mode**: READ-ONLY AUDIT COMPLETE
**Status**: PENDING APPROVAL

---

## Audit Summary

| Metric | Count |
|--------|-------|
| Total Columns Inventoried | 3,173 |
| Schemas Audited | 17 |
| Tables Audited | 214 |
| Gaps Identified | 12 |

### Column Classification Summary

| Classification | Count | Description |
|----------------|-------|-------------|
| DATA | 2,366 | Business data columns |
| AUDIT | 234 | Timestamps (created_at, updated_at, etc.) |
| OPERATIONAL | 204 | Status/state columns |
| PK | 153 | Primary key columns |
| CTB_PATH | 118 | Identity columns (sovereign_id, outreach_id, etc.) |
| FK | 48 | Foreign key columns |
| DISCRIMINATOR | 48 | Type discriminators (error_type, source_hub, etc.) |

---

## Phase 2 Remediation Actions

### Priority 1: Error Table Standardization

Error tables missing `error_type` discriminator need standardization.

| Table | Rows | Action |
|-------|------|--------|
| `outreach.dol_errors` | 29,740 | ADD error_type column |
| `cl.cl_errors_archive` | 16,103 | ADD error_type column (archive) |
| `marketing.failed_email_verification` | 310 | MERGE to people.people_errors |
| `marketing.failed_slot_assignment` | 222 | MERGE to people.people_errors |
| `marketing.failed_company_match` | 32 | MERGE to outreach.company_target_errors |
| `marketing.failed_no_pattern` | 6 | MERGE to outreach.company_target_errors |
| `marketing.failed_low_confidence` | 5 | MERGE to cl.cl_err_existence |
| `outreach.blog_errors` | 2 | ADD error_type column |

**SQL Template**:
```sql
ALTER TABLE {table} ADD COLUMN IF NOT EXISTS error_type VARCHAR(100);
UPDATE {table} SET error_type = '{default_type}' WHERE error_type IS NULL;
```

### Priority 2: Orphan Column Review

Columns with deprecated naming patterns require review.

| Table | Column | Recommendation |
|-------|--------|----------------|
| `company.message_key_reference` | `vibeos_template_id` | Review for deprecation |
| `dol.schedule_a` | `wlfr_bnft_temp_disab_ind` | Keep (DOL standard field) |
| `outreach.sequences` | `body_template` | Keep (active template field) |
| `outreach.sequences` | `subject_template` | Keep (active template field) |

### Priority 3: Canonical Hygiene

All canonical tables have required columns. No action needed.

### Priority 4: MV Conversion

Tables reclassified as MV in Phase 1 should be converted to actual materialized views:

| Table | Rows | Action |
|-------|------|--------|
| `outreach.company_hub_status` | 68,908 | Convert to actual MV |
| `dol.form_5500_icp_filtered` | 24,892 | Convert to actual MV |
| `outreach.bit_signals` | 0 | Keep as table (signals table) |
| `outreach.engagement_events` | 0 | Keep as table (events table) |
| `bit.movement_events` | 0 | Keep as table (events table) |

---

## Phase 2 Execution Checklist

- [ ] STEP 2A: Add error_type to dol_errors (29,740 rows)
- [ ] STEP 2B: Add error_type to blog_errors (2 rows)
- [ ] STEP 2C: Merge remaining marketing.failed_* tables
- [ ] STEP 2D: Review orphan column candidates
- [ ] STEP 2E: Convert company_hub_status to MV
- [ ] STEP 2F: Convert form_5500_icp_filtered to MV
- [ ] STEP 2G: Final verification audit

---

## Files Generated

| File | Purpose |
|------|---------|
| `docs/audit/CTB_COLUMN_INVENTORY.csv` | All columns with metadata |
| `docs/audit/CTB_COLUMN_CLASSIFICATION.csv` | Column type classification |
| `docs/audit/CTB_CANONICAL_HYGIENE.csv` | Canonical table health check |
| `docs/audit/CTB_ERROR_TABLE_SANITY.csv` | Error table standardization |
| `docs/audit/CTB_MV_JUSTIFICATION.csv` | MV identification |
| `docs/audit/CTB_REGISTRY_VALIDATION.csv` | Registry table validation |
| `docs/audit/CTB_PHASE2_GAP_REPORT.csv` | Gap analysis |
| `docs/contracts/CTB_COLUMN_CONTRACTS.csv` | Column contracts validation |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | READ-ONLY AUDIT |
| Status | AWAITING EXECUTION APPROVAL |
| Phase 1 Tag | CTB_PHASE1_LOCK |
