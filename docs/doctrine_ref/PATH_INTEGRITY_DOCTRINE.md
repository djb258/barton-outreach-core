# Path Integrity Doctrine — Waterfall Join Enforcement

**Version:** 1.0.0
**Status:** ACTIVE
**Date:** 2026-01-09
**Author:** Claude Code (IMO-Creator)
**Barton ID:** `04.04.00.04.50000.001`

---

## Purpose

This doctrine defines the **path integrity requirements** for the Outreach waterfall architecture. All sub-hubs MUST maintain valid join paths to the [[outreach.outreach]] spine table via `outreach_id`.

**Golden Rule:**
```
IF outreach_id IS NULL OR NOT EXISTS IN outreach.outreach:
    RECORD IS ORPHANED → QUARANTINE
```

---

## Waterfall Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CL.COMPANY_IDENTITY                                  │
│                        (Sovereign Identity Hub)                              │
│                                                                              │
│  company_unique_id (UUID) ────► 63,911 PASS | 7,912 FAIL                    │
│                                                                              │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
                                        │ sovereign_id [FK]
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OUTREACH.OUTREACH                                    │
│                          (Program Spine)                                     │
│                                                                              │
│  outreach_id (UUID) ────► Minted for each CL PASS record                    │
│  sovereign_id (UUID) ────► FK to cl.company_identity                        │
│                                                                              │
│  STATUS: HEALTHY (63,911 records, 100% linked to CL)                        │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
            ┌───────────────────────────┼───────────────────────────┐
            │                           │                           │
            ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│  COMPANY TARGET     │   │       DOL           │   │       BLOG          │
│  ─────────────────  │   │  ─────────────────  │   │  ─────────────────  │
│  outreach_id [FK]   │   │  outreach_id [FK]   │   │  outreach_id [FK]   │
│  STATUS: HEALTHY    │   │  STATUS: EMPTY      │   │  STATUS: HEALTHY    │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PEOPLE.COMPANY_SLOT                                  │
│                          (Slot Assignment)                                   │
│                                                                              │
│  outreach_id (UUID) ────► FK to outreach.outreach [R0_003]                  │
│  company_unique_id (TEXT) ────► FK to company.company_master                │
│                                                                              │
│  STATUS: 99.96% LINKED (191,733 linked, 75 quarantined)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Path Integrity Rules

### Rule 1: All Sub-Hubs FK to Outreach Spine

| Sub-Hub | Table | FK Column | FK Target | Status |
|---------|-------|-----------|-----------|--------|
| Company Target | `outreach.company_target` | `outreach_id` | `outreach.outreach` | ✅ ENFORCED |
| DOL | `outreach.dol` | `outreach_id` | `outreach.outreach` | ✅ ENFORCED |
| Blog | `outreach.blog` | `outreach_id` | `outreach.outreach` | ✅ ENFORCED |
| People | `people.company_slot` | `outreach_id` | `outreach.outreach` | ✅ ENFORCED (R0_003) |

### Rule 2: No Orphaned Records

```sql
-- This query MUST return 0 for all sub-hub tables
SELECT COUNT(*) FROM [sub_hub_table] t
WHERE t.outreach_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = t.outreach_id);
```

### Rule 3: NULL outreach_id = Quarantined

Records with `NULL` outreach_id are explicitly quarantined and MUST be tracked in a quarantine table for investigation.

---

## Bridge Tables

### CL → Company Master Bridge

The `cl.company_identity_bridge` table resolves the UUID ↔ TEXT datatype mismatch between CL (UUID) and downstream schemas (TEXT).

| Column | Type | Purpose |
|--------|------|---------|
| `company_sov_id` | UUID | Links to `cl.company_identity.company_unique_id` |
| `source_company_id` | TEXT | Links to `company.company_master.company_unique_id` |

**Usage:**
```sql
-- Derive outreach_id from company_unique_id (TEXT)
SELECT o.outreach_id
FROM company.company_master cm
JOIN cl.company_identity_bridge cib ON cm.company_unique_id = cib.source_company_id
JOIN outreach.outreach o ON cib.company_sov_id = o.sovereign_id
WHERE cm.company_unique_id = 'some-text-id';
```

---

## Conformance Checks

### Daily Audit Query

```sql
-- Run daily to detect path integrity drift
SELECT
    'outreach.company_target' AS table_name,
    COUNT(*) FILTER (WHERE outreach_id IS NULL) AS null_count,
    COUNT(*) FILTER (WHERE outreach_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = company_target.outreach_id
    )) AS orphan_count
FROM outreach.company_target

UNION ALL

SELECT
    'people.company_slot',
    COUNT(*) FILTER (WHERE outreach_id IS NULL),
    COUNT(*) FILTER (WHERE outreach_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = company_slot.outreach_id
    ))
FROM people.company_slot;
```

**Expected Results:**
- `null_count`: Should match quarantine table count
- `orphan_count`: MUST be 0

---

## Remediation History

| Migration | Date | Action | Records Affected |
|-----------|------|--------|------------------|
| [[R0_002]] | 2026-01-09 | Backfill orphaned slot outreach_ids | 978 derived, 75 quarantined |
| [[R0_003]] | 2026-01-09 | Add FK constraint on people.company_slot | Path locked |

---

## Related Documents

- [[WATERFALL_ARCHITECTURE]] — Full waterfall flow documentation
- [[P0_VALIDATION_CHECKLIST]] — Migration validation procedures
- [[R0_REMEDIATION_REPORT]] — Detailed remediation report
- [[CLAUDE.md]] — Bootstrap guide with architecture overview

---

## Quarantine Protocol

When records cannot be linked to the outreach spine:

1. **Do NOT delete** — Records may be valid, just missing linkage
2. **Insert into quarantine table** — Track for investigation
3. **Log the reason** — `NO_BRIDGE_ENTRY`, `NO_OUTREACH_RECORD`, etc.
4. **Review weekly** — Determine if records need manual resolution

**Current Quarantine Tables:**
- `people.slot_quarantine_r0_002` — 75 slots pending investigation

---

**Document Status:** ACTIVE
**Last Updated:** 2026-01-09
**Owner:** Schema Remediation Engineer
