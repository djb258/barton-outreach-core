# CTB Phase 2 Verification Report

**Date**: 2026-02-06
**Status**: PASSED
**Tag**: CTB_PHASE2_COLUMN_HYGIENE

---

## Execution Summary

| Step | Description | Status |
|------|-------------|--------|
| STEP 1 | Error Table Normalization | COMPLETE |
| STEP 2 | Marketing.failed_* Deprecation | COMPLETE |
| STEP 3 | MV Documentation | COMPLETE |
| STEP 4 | Canonical Column Hygiene | COMPLETE |
| STEP 5 | Column Contract Enforcement | COMPLETE |
| STEP 6 | Verification | PASSED |

---

## STEP 1: Error Table Normalization

Added `error_type` column to 9 error tables:

| Table | Rows | Action |
|-------|------|--------|
| outreach.dol_errors | 29,740 | Added + backfilled |
| cl.cl_errors_archive | 16,103 | Added + backfilled |
| outreach.blog_errors | 2 | Added + backfilled |
| outreach.outreach_errors | 0 | Added |
| outreach.people_errors | 0 | Added |
| outreach.bit_errors | 0 | Added |
| outreach.company_target_errors_archive | 0 | Added |
| outreach.dol_errors_archive | 0 | Added |
| company.pipeline_errors | 0 | Added |

**Total backfilled**: 45,845 rows

---

## STEP 2: Marketing.failed_* Deprecation

Marked 5 tables as DEPRECATED (schema incompatible for direct merge):

| Table | Rows | Status |
|-------|------|--------|
| marketing.failed_company_match | 32 | DEPRECATED (archived) |
| marketing.failed_no_pattern | 6 | DEPRECATED (archived) |
| marketing.failed_email_verification | 310 | DEPRECATED (archived) |
| marketing.failed_slot_assignment | 222 | DEPRECATED (archived) |
| marketing.failed_low_confidence | 5 | DEPRECATED (archived) |

**Note**: Data preserved in `archive.*_ctb` tables from Phase 1.

---

## STEP 3: MV Documentation

| Table | Rows | Status |
|-------|------|--------|
| outreach.company_hub_status | 68,908 | MV_CANDIDATE (conversion deferred) |
| dol.form_5500_icp_filtered | 24,892 | MV_CANDIDATE (conversion deferred) |
| bit.movement_events | 0 | MV_PLACEHOLDER |
| outreach.engagement_events | 0 | MV_PLACEHOLDER |
| outreach.bit_signals | 0 | MV_PLACEHOLDER |

**Note**: Actual MV conversion requires documented derivation queries.

---

## STEP 4: Canonical Column Hygiene

Added missing audit columns:

| Table | Column | Type |
|-------|--------|------|
| cl.company_identity | updated_at | TIMESTAMPTZ |
| outreach.blog | updated_at | TIMESTAMPTZ |

---

## STEP 5: Column Contract Enforcement

Added 20 column contract comments to CTB path tables:
- CL Authority Registry: 4 columns
- Outreach Spine: 4 columns
- Company Target: 3 columns
- DOL: 2 columns
- Blog: 2 columns
- People: 4 columns
- BIT: 1 column

---

## STEP 6: Verification Results

### Join Key Integrity
| Check | Result |
|-------|--------|
| CL -> Outreach | 95,004 = 95,004 ✓ |
| Outreach -> CT | 95,004 = 95,004 ✓ |

### Canonical Audit Columns
| Table | Status |
|-------|--------|
| cl.company_identity | OK |
| outreach.outreach | OK |
| outreach.company_target | OK |
| outreach.blog | OK |
| outreach.dol | OK |
| people.company_slot | OK |

### Error Table Normalization
- 15/17 error tables have `error_type` column
- 2 false positives (control tables, not error tables):
  - outreach.manual_overrides
  - outreach.override_audit_log

### NULL Ratios
| Column | NULL Count | Percentage |
|--------|------------|------------|
| cl.company_identity.outreach_id | 6,499 | 6.4% |
| outreach.company_target.outreach_id | 0 | 0.0% |
| outreach.dol.outreach_id | 0 | 0.0% |
| outreach.blog.outreach_id | 0 | 0.0% |
| people.company_slot.outreach_id | 0 | 0.0% |

---

## Migration Log Entries

| Migration | Step | Status |
|-----------|------|--------|
| ctb-phase2-column-hygiene | step1-error-normalization | success |
| ctb-phase2-column-hygiene | step2-marketing-deprecation | success |
| ctb-phase2-column-hygiene | step3-mv-documentation | success |
| ctb-phase2-column-hygiene | step4-canonical-hygiene | success |
| ctb-phase2-column-hygiene | step5-contract-enforcement | success |

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Phase | CTB Phase 2 |
| Type | VERIFICATION REPORT |
| Status | PASSED |
| Tag | CTB_PHASE2_COLUMN_HYGIENE |
