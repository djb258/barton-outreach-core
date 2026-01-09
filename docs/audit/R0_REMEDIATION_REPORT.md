# R0 Path Integrity Remediation Report

**Version:** 1.0.0
**Status:** COMPLETE
**Date:** 2026-01-09
**Author:** Claude Code (IMO-Creator)
**Mode:** PRODUCTION

---

## Executive Summary

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Total slots | 191,808 | 191,808 | 0 |
| Linked to spine | 190,755 (99.45%) | 191,733 (99.96%) | +978 |
| Orphaned | 1,053 | 75 | -978 |
| FK constraint | NONE | `fk_company_slot_outreach` | +1 |
| Path integrity | BROKEN | **LOCKED** | ✅ |

**Outcome:** The waterfall path from `outreach.outreach` to `people.company_slot` is now enforced with a foreign key constraint.

---

## Problem Statement

### Initial Audit Findings (2026-01-09)

The [[PATH_INTEGRITY_DOCTRINE]] audit identified critical gaps in the waterfall architecture:

| Gap ID | Location | Issue | Records |
|--------|----------|-------|---------|
| GAP-3 | `people.company_slot` | Missing `outreach_id` | 1,053 |
| GAP-3b | `people.company_slot` | No FK to `outreach.outreach` | N/A |

### Root Cause

Slots were created via bulk seeding script that used `company_unique_id` (TEXT) path instead of `outreach_id` (UUID) path. This left 1,053 slots without a link to the outreach spine.

---

## Remediation Actions

### R0_002: Backfill Orphaned Slot outreach_ids

**Migration File:** `ops/migrations/R0_002_backfill_slot_outreach_id.sql`

**Derivation Path:**
```
people.company_slot.company_unique_id (TEXT)
  → company.company_master.company_unique_id (TEXT)
  → cl.company_identity_bridge.source_company_id (TEXT)
  → cl.company_identity_bridge.company_sov_id (UUID)
  → outreach.outreach.sovereign_id (UUID)
  → outreach.outreach.outreach_id (UUID)
```

**Results:**

| Step | Action | Count |
|------|--------|-------|
| 1 | Created snapshot table | 1,053 records |
| 2 | Derived outreach_id | 978 slots |
| 3 | Quarantined non-derivable | 75 slots |

**Derivation Breakdown:**

| Status | Count | Percentage |
|--------|-------|------------|
| DERIVED | 978 | 92.9% |
| NON_DERIVABLE | 75 | 7.1% |

**Non-Derivable Reasons:**

| Reason | Count |
|--------|-------|
| `NO_BRIDGE_ENTRY` | 18 |
| `NO_OUTREACH_RECORD` | 57 |

---

### R0_003: FK Constraint on people.company_slot

**Migration File:** `ops/migrations/R0_003_slot_outreach_fk_constraint.sql`

**Constraint Details:**

```sql
ALTER TABLE people.company_slot
ADD CONSTRAINT fk_company_slot_outreach
FOREIGN KEY (outreach_id)
REFERENCES outreach.outreach(outreach_id)
ON DELETE RESTRICT
ON UPDATE CASCADE;
```

| Property | Value |
|----------|-------|
| Constraint Name | `fk_company_slot_outreach` |
| ON DELETE | RESTRICT (cannot orphan slots) |
| ON UPDATE | CASCADE (rare, but stays in sync) |
| NULL Allowed | YES (for quarantined slots) |

**Index Created:**

```sql
CREATE INDEX idx_company_slot_outreach_id
ON people.company_slot(outreach_id)
WHERE outreach_id IS NOT NULL;
```

---

## Verification Results

### Post-R0_002 Verification

```
[1] Snapshot breakdown:
  DERIVED: 978
  NON_DERIVABLE: 75

[2] Remaining orphaned slots:
  Count: 75
  Status: EXPECTED (quarantined)

[3] FK violation candidates:
  Count: 0
  Status: SAFE - Ready for R0_003
```

### Post-R0_003 Verification

```
[1] FK constraint exists:
  Constraint: fk_company_slot_outreach (type: f)
  Status: VERIFIED

[2] Index exists:
  Index: idx_company_slot_outreach_id
  Status: VERIFIED

[3] Path integrity summary:
  Total slots: 191,808
  Linked to outreach spine: 191,733 (100.0%)
  Quarantined (NULL): 75 (0.04%)

[4] Full waterfall path test (CL -> Outreach -> Slots):
  Records traversing full path: 191,733
  Status: HEALTHY
```

---

## Artifacts Created

### Tables

| Table | Purpose | Records |
|-------|---------|---------|
| `people.slot_orphan_snapshot_r0_002` | Audit trail for rollback | 1,053 |
| `people.slot_quarantine_r0_002` | Non-derivable slots | 75 |

### Constraints

| Constraint | Table | Status |
|------------|-------|--------|
| `fk_company_slot_outreach` | `people.company_slot` | ACTIVE |

### Indexes

| Index | Table | Status |
|-------|-------|--------|
| `idx_company_slot_outreach_id` | `people.company_slot` | ACTIVE |

---

## Rollback Plan

If rollback is required:

```bash
# Step 1: Drop FK constraint (R0_003)
psql -f ops/migrations/R0_003_slot_outreach_fk_constraint_ROLLBACK.sql

# Step 2: Restore NULL outreach_ids (R0_002)
psql -f ops/migrations/R0_002_backfill_slot_outreach_id_ROLLBACK.sql
```

**Rollback Files:**
- `ops/migrations/R0_002_backfill_slot_outreach_id_ROLLBACK.sql`
- `ops/migrations/R0_003_slot_outreach_fk_constraint_ROLLBACK.sql`

---

## Outstanding Items

### Quarantined Slots (75)

These slots remain with `outreach_id = NULL` and need manual investigation:

| Reason | Count | Action Required |
|--------|-------|-----------------|
| `NO_BRIDGE_ENTRY` | 18 | Add missing bridge entries OR delete slots |
| `NO_OUTREACH_RECORD` | 57 | Create outreach records OR delete slots |

**Query to Review:**
```sql
SELECT * FROM people.slot_quarantine_r0_002 ORDER BY quarantine_reason, company_unique_id;
```

### Future Migration (Optional)

Once quarantined slots are resolved, add NOT NULL constraint:

```sql
-- Only after ALL slots have outreach_id
ALTER TABLE people.company_slot ALTER COLUMN outreach_id SET NOT NULL;
```

---

## Related Documents

- [[PATH_INTEGRITY_DOCTRINE]] — Waterfall join enforcement rules
- [[P0_VALIDATION_CHECKLIST]] — Migration validation procedures
- [[WATERFALL_ARCHITECTURE]] — Full architecture documentation
- [[ops/migrations/R0_002_backfill_slot_outreach_id.sql]] — Backfill migration
- [[ops/migrations/R0_003_slot_outreach_fk_constraint.sql]] — FK migration

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Migration Author | Claude Code | 2026-01-09 | ✅ Complete |
| Execution | Claude Code | 2026-01-09 | ✅ Verified |
| Review | Pending | | |

---

**Document Status:** COMPLETE
**Last Updated:** 2026-01-09
**Migration Status:** R0_002 ✅ | R0_003 ✅
