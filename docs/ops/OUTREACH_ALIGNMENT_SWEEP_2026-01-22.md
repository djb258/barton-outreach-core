# Outreach Sub-Hub Alignment Sweep

**Date**: 2026-01-22
**Objective**: Hard-align all Outreach tables to CL Authority count
**Status**: COMPLETE

---

## Authority Source

| Metric | Count |
|--------|-------|
| CL Total | 51,910 |
| CL PASS (Authority) | **51,148** |
| CL FAIL | 762 |

**Alignment Target**: 51,148 (CL PASS only)

---

## Pre-Cleanup Audit

| Table | Pre-Cleanup Count | Orphans Found |
|-------|-------------------|---------------|
| outreach.outreach | 51,148 | 0 |
| outreach.company_target | 51,148 | 0 |
| outreach.company_target_errors | 5,539 | 0 |
| outreach.dol | 13,829 | 0 |
| outreach.dol_errors | 37,319 | 0 |
| outreach.people | 426 | 0 |
| outreach.people_errors | 0 | 0 |
| outreach.blog | 51,148 | 0 |
| outreach.blog_errors | 2 | 0 |
| outreach.bit_scores | 17,227 | 0 |
| outreach.bit_signals | 0 | 0 |
| outreach.bit_input_history | 0 | 0 |
| outreach.blog_source_history | 0 | 0 |
| people.company_slot | 285,012 | 0 |
| **people.people_master** | **30,808** | **5,675** |
| outreach.company_hub_status | 68,908 | 0 |

---

## Cleanup Actions

### people.people_master Orphan Cleanup

**Issue**: 5,675 records in `people.people_master` had no valid linkage to the outreach spine via `people.company_slot.person_unique_id`.

**Root Cause**: Legacy Barton ID format (`04.04.01.xx.xxxxx.xxx`) records that were not migrated to the current UUID-based system.

**Action Taken**:
1. Archived 5,675 orphaned records to `people.people_master_archive`
2. Deleted orphaned records from `people.people_master`
3. Archive reason: `orphan_cleanup_2026-01-22: no_slot_linkage`

**Script**: `scripts/people_master_orphan_cleanup.py`

---

## Post-Cleanup Verification

| Table | Post-Cleanup Count | Orphans | Status |
|-------|-------------------|---------|--------|
| outreach.outreach | 51,148 | 0 | OK |
| outreach.company_target | 51,148 | 0 | OK |
| outreach.company_target_errors | 5,539 | 0 | OK |
| outreach.dol | 13,829 | 0 | OK |
| outreach.dol_errors | 37,319 | 0 | OK |
| outreach.people | 426 | 0 | OK |
| outreach.people_errors | 0 | 0 | OK |
| outreach.blog | 51,148 | 0 | OK |
| outreach.blog_errors | 2 | 0 | OK |
| outreach.bit_scores | 17,227 | 0 | OK |
| outreach.bit_signals | 0 | 0 | OK |
| outreach.bit_input_history | 0 | 0 | OK |
| outreach.blog_source_history | 0 | 0 | OK |
| people.company_slot | 285,012 | 0 | OK |
| **people.people_master** | **25,133** | **0** | **OK** |
| outreach.company_hub_status | 68,908 | 0 | OK |

---

## Archive Table Counts

| Archive Table | Count |
|---------------|-------|
| outreach.outreach_archive | 23,025 |
| outreach.company_target_archive | 23,025 |
| outreach.people_archive | 120 |
| people.company_slot_archive | 69,075 |
| people.people_master_archive | 5,675 |

---

## Final Alignment Summary

| Metric | Value |
|--------|-------|
| CL Authority (PASS) | 51,148 |
| Outreach Spine | 51,148 |
| Spine Delta | +0 |
| Total Orphans Remaining | 0 |
| Total Active Rows | 424,123 |

---

## Certification

```
============================================================
STATUS: FULLY ALIGNED
Safe for paid enrichment: YES
============================================================
```

**Verified**: 2026-01-22T08:07:23 UTC

---

## Artifacts

- `scripts/outreach_alignment_audit.py` - Initial audit script
- `scripts/outreach_alignment_audit_v2.py` - Fixed audit script with type handling
- `scripts/people_master_orphan_cleanup.py` - Cleanup migration script

---

**Sweep Completed By**: Claude Code
**Doctrine**: CL Authority Registry + Outreach Operational Spine (ADR-011)
