# CTB Violations Report — Strict Leaf Conformance

**Date**: 2026-02-06
**Type**: READ-ONLY AUDIT
**Audit Rule**: Only 4 table types allowed at sub-hub leaves:
- `CANONICAL` — The main entity table
- `ERRORS` — Error logging for that entity
- `MATERIALIZED_VIEW` — Precomputed views
- `REGISTRY` — Lookup/config tables

---

## Executive Summary

| Sub-Hub | Total Tables | Violations | Status |
|---------|--------------|------------|--------|
| Company Target | 8 | 3 | ⚠ NEEDS WORK |
| DOL | 14 | 3 | ⚠ NEEDS WORK |
| Blog | 6 | 2 | ⚠ NEEDS WORK |
| People | 26 | 15 | ❌ CRITICAL BLOAT |
| BIT | 9 | 6 | ❌ NEEDS RESTRUCTURE |
| Execution | 5 | 2 | ⚠ NEEDS WORK |
| OUT_OF_TREE | 17 | 17 | ❌ ORPHANED |
| **TOTAL** | **85** | **48** | ❌ **FAIL** |

---

## Part 1: Leaf Type Violations (Non-Allowed Table Types)

### Company Target Sub-Hub

| Table | Current Type | Violation | Resolution |
|-------|--------------|-----------|------------|
| `outreach.company_hub_status` | STATUS | Not in allowed types | Convert to MV or merge into CT canonical |
| `company.url_discovery_failures` | ERRORS | Wrong schema | Move to `outreach.company_target_errors` |
| `company.url_discovery_failures_archive` | ARCHIVE | Wrong schema | Move to `outreach` schema |

---

### DOL Sub-Hub

| Table | Current Type | Violation | Resolution |
|-------|--------------|-----------|------------|
| `outreach.dol_audit_log` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `outreach.dol_url_enrichment` | ENRICHMENT | Not in allowed types | Merge into `outreach.dol` as columns or MV |
| `dol.pressure_signals` | SIGNALS | Not in allowed types | Move to BIT sub-hub or merge into dol_errors |

---

### Blog Sub-Hub

| Table | Current Type | Violation | Resolution |
|-------|--------------|-----------|------------|
| `outreach.blog_source_history` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `blog.pressure_signals` | SIGNALS | Not in allowed types | Move to BIT sub-hub |

---

### People Sub-Hub (CRITICAL — 15 Violations)

| Table | Current Type | Violation | Resolution |
|-------|--------------|-----------|------------|
| `people.people_staging` | STAGING | Not in allowed types | Move to `intake` schema |
| `people.people_candidate` | STAGING | Not in allowed types | Move to `intake` schema |
| `people.people_promotion_audit` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `people.people_resolution_history` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `people.people_resolution_queue` | QUEUE | Not in allowed types | Move to `outreach.entity_resolution_queue` |
| `people.people_sidecar` | SIDECAR | Not in allowed types | Merge into `people.people_master` as JSONB |
| `people.company_resolution_log` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `people.paid_enrichment_queue` | QUEUE | Not in allowed types | Move to `outreach.entity_resolution_queue` |
| `people.person_movement_history` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `people.person_scores` | SCORING | Not in allowed types | Merge into `people.people_master` as columns |
| `people.pressure_signals` | SIGNALS | Not in allowed types | Move to BIT sub-hub |
| `people.slot_assignment_history` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `people.slot_orphan_snapshot_r0_002` | SNAPSHOT | Temp table | DROP after migration |
| `people.slot_quarantine_r0_002` | QUARANTINE | Temp table | DROP after migration |
| `people.people_invalid` | ERRORS | Duplicate | Merge into `people.people_errors` |

**Note**: `outreach.people*` tables are in wrong schema — should be in `people` schema.

---

### BIT Sub-Hub (6 Violations)

| Table | Current Type | Violation | Resolution |
|-------|--------------|-----------|------------|
| `outreach.bit_signals` | SIGNALS | Not in allowed types | Convert to MV or merge into canonical |
| `outreach.bit_input_history` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `bit.authorization_log` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `bit.movement_events` | EVENTS | Not in allowed types | Convert to MV or merge into canonical |
| `bit.phase_state` | STATE | Not in allowed types | Merge into `outreach.bit_scores` as columns |
| `bit.proof_lines` | PROOF | Not in allowed types | Merge into `outreach.bit_scores` as JSONB |

---

### Execution Sub-Hub

| Table | Current Type | Violation | Resolution |
|-------|--------------|-----------|------------|
| `outreach.send_log` | AUDIT | Not in allowed types | Merge into `outreach.pipeline_audit_log` |
| `outreach.engagement_events` | EVENTS | Not in allowed types | Convert to MV or merge into canonical |

---

## Part 2: OUT_OF_TREE Violations (Not in CTB Path)

These tables exist outside the CTB and violate the single-source-of-truth principle.

### Duplicate Truth Tables (CRITICAL)

| Table | Rows | Violation | Resolution |
|-------|------|-----------|------------|
| `company.company_master` | 74,641 | Bypasses CL | DROP — use `cl.company_identity` |
| `marketing.company_master` | 512 | Bypasses CL | DROP — use `cl.company_identity` |
| `marketing.people_master` | 149 | Bypasses `people.people_master` | DROP — use canonical |
| `company.company_slots` | 1,359 | Bypasses `people.company_slot` | DROP — use canonical |

### Orphaned Error Tables

| Table | Rows | Violation | Resolution |
|-------|------|-----------|------------|
| `marketing.failed_company_match` | 32 | No CTB path | Merge into `outreach.company_target_errors` |
| `marketing.failed_email_verification` | 310 | No CTB path | Merge into `people.people_errors` |
| `marketing.failed_low_confidence` | 5 | No CTB path | Merge into `cl.cl_err_existence` |
| `marketing.failed_no_pattern` | 6 | No CTB path | Merge into `outreach.company_target_errors` |
| `marketing.failed_slot_assignment` | 222 | No CTB path | Merge into `people.people_errors` |
| `company.message_key_reference` | 8 | No CTB path | DROP or move to REGISTRY |

### Sales Namespace (OUT OF SCOPE)

| Table | Rows | Violation | Resolution |
|-------|------|-----------|------------|
| `public.sn_meeting` | 0 | Sales namespace | Move to Sales hub (separate repo) |
| `public.sn_meeting_outcome` | 0 | Sales namespace | Move to Sales hub |
| `public.sn_prospect` | 0 | Sales namespace | Move to Sales hub |
| `public.sn_sales_process` | 0 | Sales namespace | Move to Sales hub |

### Isolated Lanes

| Table | Rows | Violation | Resolution |
|-------|------|-----------|------------|
| `talent_flow.movement_history` | 0 | Isolated lane | Integrate into People or DROP |
| `talent_flow.movements` | 0 | Isolated lane | Integrate into People or DROP |

---

## Part 3: Structural Violations

### Missing Primary Keys

| Table | Issue | Resolution |
|-------|-------|------------|
| `dol.form_5500_icp_filtered` | No PK defined | Add `filter_id` PK |
| `people.people_master_archive` | No PK defined | Add archive PK |

### Wrong Schema Placement

| Table | Current Schema | Correct Schema | Resolution |
|-------|----------------|----------------|------------|
| `outreach.people` | outreach | people | Move to `people.people_link` |
| `outreach.people_archive` | outreach | people | Move to `people` schema |
| `outreach.people_errors` | outreach | people | Merge with `people.people_errors` |
| `company.url_discovery_failures` | company | outreach | Move to `outreach.company_target_errors` |

---

## Part 4: Bloat Analysis

### Tables That Should Merge

| Source Table | Target Table | Reason |
|--------------|--------------|--------|
| `outreach.outreach_orphan_archive` | `outreach.outreach_archive` | Duplicate archive |
| `outreach.company_target_orphaned_archive` | `outreach.company_target_archive` | Duplicate archive |
| `people.people_invalid` | `people.people_errors` | Error variant |
| All `*_audit_log` tables | `outreach.pipeline_audit_log` | Centralize audit |
| All `*_queue` tables | `outreach.entity_resolution_queue` | Centralize queues |
| All `pressure_signals` tables | `outreach.bit_signals` | Centralize signals |

---

## Remediation Priority

### Priority 1: Critical (Data Integrity)

1. DROP `company.company_master` (duplicate truth)
2. DROP `marketing.company_master` (duplicate truth)
3. DROP `marketing.people_master` (duplicate truth)
4. DROP `company.company_slots` (duplicate truth)
5. Merge `marketing.failed_*` tables into CTB error tables

### Priority 2: High (Structural)

1. Move `company.url_discovery_failures` to `outreach` schema
2. Move `outreach.people*` to `people` schema
3. Add PKs to tables missing them
4. Merge duplicate archive tables

### Priority 3: Medium (Bloat Reduction)

1. Merge all `*_audit_log` into `outreach.pipeline_audit_log`
2. Merge all `*_queue` into `outreach.entity_resolution_queue`
3. Consolidate `pressure_signals` tables
4. DROP temp tables (`slot_orphan_snapshot_r0_002`, `slot_quarantine_r0_002`)

### Priority 4: Low (Cleanup)

1. Move Sales namespace tables to Sales hub
2. Resolve or DROP `talent_flow` schema
3. Archive empty tables with unclear purpose

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-02-06 |
| Type | READ-ONLY AUDIT |
| Status | **48 VIOLATIONS FOUND** |
| Action | NONE (audit only) |
