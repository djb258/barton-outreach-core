# CTB Structural Reorganization Plan

**Date**: 2026-02-06
**Type**: READ-WRITE MIGRATION PLAN
**Status**: PENDING APPROVAL

---

## Objective

Reorganize existing tables to conform to the CTB Joint Path diagram:
- Preserve all data (no deletions)
- Prepare for later column-level cleanup
- Lock leaf schemas after completion

---

## Action Summary

| Action | Count | Description |
|--------|-------|-------------|
| ARCHIVE | 20 | Move to archive schema unchanged |
| MERGE | 22 | Combine into target table |
| MOVE | 7 | Relocate to correct schema |
| KEEP_AS_MV | 5 | Reclassify as materialized view |
| MERGE_JSONB | 3 | Add JSONB column to canonical |
| MERGE_COLS | 2 | Add columns to canonical |
| ADD_PK | 2 | Add missing primary key |
| PENDING | 3 | Awaiting human decision |
| **TOTAL** | **64** | |

---

## Phase 1A: Duplicate Truth Tables → ARCHIVE

These tables bypass the canonical CTB path. Archive for reference, deprecate reads.

| Table | Rows | Archive Target |
|-------|------|----------------|
| `company.company_master` | 74,641 | `archive.company_company_master_ctb` |
| `marketing.company_master` | 512 | `archive.marketing_company_master_ctb` |
| `marketing.people_master` | 149 | `archive.marketing_people_master_ctb` |
| `company.company_slots` | 1,359 | `archive.company_company_slots_ctb` |

**Post-Archive**: Update any code reading these tables to use canonical sources.

---

## Phase 1B: Orphaned Error Tables → MERGE

Merge into CTB-aligned error tables with `error_type` discriminator.

| Source | Rows | Target |
|--------|------|--------|
| `marketing.failed_company_match` | 32 | `outreach.company_target_errors` |
| `marketing.failed_email_verification` | 310 | `people.people_errors` |
| `marketing.failed_low_confidence` | 5 | `cl.cl_err_existence` |
| `marketing.failed_no_pattern` | 6 | `outreach.company_target_errors` |
| `marketing.failed_slot_assignment` | 222 | `people.people_errors` |

**Pre-Merge**: Add `error_type` column to target tables if not exists.

---

## Phase 1C: Wrong Schema Tables → MOVE

| Source | Target | Reason |
|--------|--------|--------|
| `company.url_discovery_failures` | `outreach.url_discovery_failures` | CT errors belong in outreach |
| `company.url_discovery_failures_archive` | `outreach.url_discovery_failures_archive` | Follow parent |
| `outreach.people` | `people.people_outreach_link` | Clarify as link table |
| `outreach.people_archive` | `people.people_outreach_link_archive` | Follow parent |
| `outreach.people_errors` | MERGE → `people.people_errors` | Consolidate |

---

## Phase 1D: Audit Table Centralization → MERGE

All audit logs merge into `outreach.pipeline_audit_log` with `source_hub` discriminator.

| Source Table | source_hub Value |
|--------------|------------------|
| `outreach.dol_audit_log` | `dol` |
| `outreach.blog_source_history` | `blog` |
| `outreach.bit_input_history` | `bit` |
| `bit.authorization_log` | `bit_auth` |
| `people.people_promotion_audit` | `people_promo` |
| `people.people_resolution_history` | `people_resolution` |
| `people.company_resolution_log` | `company_resolution` |
| `people.person_movement_history` | `person_movement` |
| `people.slot_assignment_history` | `slot_assignment` |
| `outreach.send_log` | `execution_send` |

**Pre-Merge**: Add `source_hub VARCHAR(50)` to `outreach.pipeline_audit_log`.

---

## Phase 1E: Queue Table Centralization → MERGE

All queues merge into `outreach.entity_resolution_queue` with `queue_type` discriminator.

| Source Table | queue_type Value |
|--------------|------------------|
| `people.people_resolution_queue` | `people_resolution` |
| `people.paid_enrichment_queue` | `paid_enrichment` |

**Pre-Merge**: Add `queue_type VARCHAR(50)` to `outreach.entity_resolution_queue`.

---

## Phase 1F: Signals Centralization → MERGE to BIT

All `pressure_signals` merge into `outreach.bit_signals` with `signal_source` discriminator.

| Source Table | signal_source Value |
|--------------|---------------------|
| `dol.pressure_signals` | `dol` |
| `blog.pressure_signals` | `blog` |
| `people.pressure_signals` | `people` |

**Pre-Merge**: Add `signal_source VARCHAR(50)` to `outreach.bit_signals`.

---

## Phase 1G: Non-Conforming Leaf Tables

### Reclassify as MV (No Data Change)

| Table | New Classification |
|-------|-------------------|
| `outreach.company_hub_status` | MATERIALIZED_VIEW |
| `bit.movement_events` | MATERIALIZED_VIEW |
| `outreach.engagement_events` | MATERIALIZED_VIEW |
| `outreach.bit_signals` | MATERIALIZED_VIEW |

### Move to Correct Schema

| Table | Target |
|-------|--------|
| `people.people_staging` | `intake.people_staging` |
| `people.people_candidate` | `intake.people_candidate` |

### Merge into Canonical

| Source | Target | Method |
|--------|--------|--------|
| `people.people_invalid` | `people.people_errors` | MERGE rows |
| `people.people_sidecar` | `people.people_master` | Add JSONB column |
| `people.person_scores` | `people.people_master` | Add score columns |
| `outreach.dol_url_enrichment` | `outreach.dol` | Add JSONB column |
| `bit.phase_state` | `outreach.bit_scores` | Add state columns |
| `bit.proof_lines` | `outreach.bit_scores` | Add JSONB column |

---

## Phase 1H: Temp Tables → ARCHIVE

| Table | Archive Target |
|-------|----------------|
| `people.slot_orphan_snapshot_r0_002` | `archive.people_slot_orphan_snapshot_ctb` |
| `people.slot_quarantine_r0_002` | `archive.people_slot_quarantine_ctb` |

---

## Phase 1I: Out of Scope Tables → ARCHIVE

### Sales Namespace (Future Sales Hub)

| Table | Archive Target |
|-------|----------------|
| `public.sn_meeting` | `archive.public_sn_meeting_ctb` |
| `public.sn_meeting_outcome` | `archive.public_sn_meeting_outcome_ctb` |
| `public.sn_prospect` | `archive.public_sn_prospect_ctb` |
| `public.sn_sales_process` | `archive.public_sn_sales_process_ctb` |

### Isolated Lanes

| Table | Archive Target |
|-------|----------------|
| `talent_flow.movement_history` | `archive.talent_flow_movement_history_ctb` |
| `talent_flow.movements` | `archive.talent_flow_movements_ctb` |

---

## Phase 1J: Duplicate Archives → MERGE

| Source | Target |
|--------|--------|
| `outreach.outreach_orphan_archive` | `outreach.outreach_archive` |
| `outreach.company_target_orphaned_archive` | `outreach.company_target_archive` |

---

## Phase 1K: Structural Fixes

### Add Missing Primary Keys

| Table | New PK |
|-------|--------|
| `dol.form_5500_icp_filtered` | `filter_id SERIAL PRIMARY KEY` |
| `people.people_master_archive` | `archive_id SERIAL PRIMARY KEY` |

---

## Phase 1L: Pending Human Decision

| Table | Rows | Question |
|-------|------|----------|
| `company.company_source_urls` | 104,012 | Which sub-hub owns URL discovery? |
| `company.pipeline_events` | 2,185 | Which pipeline do these events track? |
| `marketing.review_queue` | 516 | What is being reviewed and by which sub-hub? |

---

## Phase 2C: Data Quality Issues (2026-02-07)

### Audit Results

Full audit run via `scripts/full_numbers_audit.py`:

| Issue | Count | Status |
|-------|-------|--------|
| NULL domains on spine | 0 | CLEAN |
| Duplicate domains on spine | 488 | LOGGED for manual merge |
| Orphan slots (no spine match) | 0 | CLEAN |
| Duplicate emails in people_master | 42,928 | LOGGED for dedup |
| Orphan people (no slot) | N/A | Schema check needed |

### Cleanup Script

`hubs/dol-filings/imo/middle/importers/audit_cleanup.py` addresses:
1. NULL domains → backfill from CL
2. Duplicate domains → export for manual merge
3. Orphan people → email domain match
4. Duplicate emails → dedupe + slot reassign
5. Orphan slots → archive and remove

### Post-Cleanup Counts (2026-02-07 VERIFIED)

| Table | Count |
|-------|-------|
| cl.company_identity | 102,426 |
| cl.company_identity (with outreach_id) | 95,004 |
| cl.company_identity_excluded | 5,327 |
| outreach.outreach (spine) | 95,004 |
| outreach.company_target | 95,004 |
| outreach.dol | 70,150 |
| outreach.blog | 95,004 |
| outreach.bit_scores | 13,226 |
| people.company_slot | 285,012 |
| people.people_master | 182,661 |

**Alignment Check:** CL claimed (95,004) = Spine (95,004) **ALIGNED**

---

## Phase 2: Leaf Lock

After Phase 1 completion, each sub-hub should have:

| Sub-Hub | CANONICAL | ERRORS | MV | REGISTRY |
|---------|-----------|--------|----|---------|
| company_target | company_target | company_target_errors | company_hub_status | - |
| dol | dol | dol_errors | form_5500_icp_filtered | column_metadata |
| blog | blog | blog_errors | - | blog_ingress_control |
| people | people_master, company_slot | people_errors | - | slot_ingress_control, title_slot_mapping |
| bit | bit_scores | bit_errors | bit_signals, movement_events | - |
| execution | appointments, campaigns, sequences | - | engagement_events | - |

**After Leaf Lock**: No new tables allowed without CTB path assignment.

---

## Execution Order

1. **Pre-flight**: Add discriminator columns to target tables
2. **Archives**: Execute all ARCHIVE operations
3. **Merges**: Execute all MERGE operations
4. **Moves**: Execute all MOVE operations
5. **PKs**: Add missing primary keys
6. **Reclassify**: Update metadata for MV tables
7. **Verify**: Run CTB audit to confirm compliance
8. **Freeze**: Enable Leaf Lock enforcement

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | MIGRATION PLAN |
| Status | PENDING APPROVAL |
| Execution | BLOCKED until approved |
