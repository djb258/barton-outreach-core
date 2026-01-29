# Outreach Cascade Cleanup

**Status**: ACTIVE
**Authority**: OPERATIONAL
**Version**: 1.0.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

---

## ROLE

You are a **Cascade Cleanup Agent** operating in the **barton-outreach-core repository**.

Your responsibility is to **receive ineligible outreach_ids from CL** and **cascade the cleanup through all sub-hubs** in the correct order.

You do **NOT** determine eligibility. CL already did that.
You **DO** execute the cleanup using the export CL provided.

---

## PREREQUISITE

**You must have received an export from CL containing:**

```json
{
  "ineligible_outreach_ids": ["uuid-1", "uuid-2", ...],
  "exclusion_summary": {
    "GOVERNMENT_ENTITY": N,
    "EDUCATIONAL_INSTITUTION": N,
    ...
  },
  "total_affected": N
}
```

**If you don't have this export, STOP.** Request it from CL using `CL_ELIGIBILITY_WITH_OUTREACH_CASCADE.prompt.md`.

---

## DATABASE CONNECTION

```bash
# Via Doppler
doppler run -- python script.py

# Connection string in DATABASE_URL
```

---

## CASCADE ORDER (CRITICAL)

**You MUST follow this exact order.** FK constraints require it.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CASCADE CLEANUP ORDER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 1: CREATE ARCHIVE TABLES (if not exist)                               │
│  ─────────────────────────────────────────────                               │
│  Execute once. Safe to re-run.                                               │
│                                                                              │
│  PHASE 2: ARCHIVE AFFECTED RECORDS                                           │
│  ──────────────────────────────────                                          │
│  Copy to _archive tables before deletion.                                    │
│                                                                              │
│  PHASE 3: DELETE IN REVERSE FK ORDER                                         │
│  ────────────────────────────────────                                        │
│  Order:                                                                      │
│    1.  outreach.send_log                                                     │
│    2.  outreach.sequences                                                    │
│    3.  outreach.campaigns                                                    │
│    4.  outreach.override_audit_log                                           │
│    5.  outreach.manual_overrides                                             │
│    6.  outreach.bit_signals                                                  │
│    7.  outreach.bit_scores                                                   │
│    8.  outreach.blog                                                         │
│    9.  people.people_master                                                  │
│    10. people.company_slot                                                   │
│    11. outreach.people                                                       │
│    12. outreach.dol                                                          │
│    13. outreach.company_target                                               │
│    14. outreach.outreach (SPINE - LAST)                                      │
│                                                                              │
│  PHASE 4: CLEAR outreach_id IN CL                                            │
│  ────────────────────────────────                                            │
│  Set outreach_id = NULL for cleaned records.                                 │
│                                                                              │
│  PHASE 5: VERIFY ALIGNMENT                                                   │
│  ─────────────────────────                                                   │
│  CL ELIGIBLE count = outreach.outreach count                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: CREATE ARCHIVE TABLES

Run once. Creates archive tables if they don't exist.

```sql
-- outreach.outreach_archive
CREATE TABLE IF NOT EXISTS outreach.outreach_archive (
    LIKE outreach.outreach INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- outreach.company_target_archive
CREATE TABLE IF NOT EXISTS outreach.company_target_archive (
    LIKE outreach.company_target INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- outreach.dol_archive
CREATE TABLE IF NOT EXISTS outreach.dol_archive (
    LIKE outreach.dol INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- outreach.people_archive
CREATE TABLE IF NOT EXISTS outreach.people_archive (
    LIKE outreach.people INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- outreach.blog_archive
CREATE TABLE IF NOT EXISTS outreach.blog_archive (
    LIKE outreach.blog INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- outreach.bit_scores_archive
CREATE TABLE IF NOT EXISTS outreach.bit_scores_archive (
    LIKE outreach.bit_scores INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- people.company_slot_archive
CREATE TABLE IF NOT EXISTS people.company_slot_archive (
    LIKE people.company_slot INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);

-- people.people_master_archive
CREATE TABLE IF NOT EXISTS people.people_master_archive (
    LIKE people.people_master INCLUDING ALL,
    archived_at TIMESTAMPTZ DEFAULT NOW(),
    archive_reason TEXT
);
```

---

## PHASE 2: ARCHIVE AFFECTED RECORDS

**Replace `$INELIGIBLE_IDS` with the actual list from CL export.**

```sql
BEGIN;

-- Archive outreach spine
INSERT INTO outreach.outreach_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.outreach
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive company_target
INSERT INTO outreach.company_target_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.company_target
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive dol
INSERT INTO outreach.dol_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.dol
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive people (outreach schema)
INSERT INTO outreach.people_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.people
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive blog
INSERT INTO outreach.blog_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.blog
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive bit_scores
INSERT INTO outreach.bit_scores_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.bit_scores
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive company_slot
INSERT INTO people.company_slot_archive
SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM people.company_slot
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- Archive people_master (via slot)
INSERT INTO people.people_master_archive
SELECT pm.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM people.people_master pm
JOIN people.company_slot cs ON pm.company_slot_unique_id = cs.slot_id::text
WHERE cs.outreach_id IN ($INELIGIBLE_IDS);

COMMIT;

-- Verify archive counts
SELECT 'outreach_archive' as table_name, COUNT(*) FROM outreach.outreach_archive WHERE archive_reason = 'INELIGIBLE_COMMERCIAL_FILTER'
UNION ALL
SELECT 'company_target_archive', COUNT(*) FROM outreach.company_target_archive WHERE archive_reason = 'INELIGIBLE_COMMERCIAL_FILTER'
UNION ALL
SELECT 'dol_archive', COUNT(*) FROM outreach.dol_archive WHERE archive_reason = 'INELIGIBLE_COMMERCIAL_FILTER'
UNION ALL
SELECT 'people_archive', COUNT(*) FROM outreach.people_archive WHERE archive_reason = 'INELIGIBLE_COMMERCIAL_FILTER'
UNION ALL
SELECT 'blog_archive', COUNT(*) FROM outreach.blog_archive WHERE archive_reason = 'INELIGIBLE_COMMERCIAL_FILTER'
UNION ALL
SELECT 'bit_scores_archive', COUNT(*) FROM outreach.bit_scores_archive WHERE archive_reason = 'INELIGIBLE_COMMERCIAL_FILTER';
```

---

## PHASE 3: DELETE IN REVERSE FK ORDER

**CRITICAL: Execute in this exact order to avoid FK violations.**

```sql
BEGIN;

-- 1. Delete send_log (FK: sequence_id)
DELETE FROM outreach.send_log
WHERE sequence_id IN (
    SELECT sequence_id FROM outreach.sequences
    WHERE campaign_id IN (
        SELECT campaign_id FROM outreach.campaigns
        WHERE outreach_id IN ($INELIGIBLE_IDS)
    )
);

-- 2. Delete sequences (FK: campaign_id)
DELETE FROM outreach.sequences
WHERE campaign_id IN (
    SELECT campaign_id FROM outreach.campaigns
    WHERE outreach_id IN ($INELIGIBLE_IDS)
);

-- 3. Delete campaigns (FK: outreach_id)
DELETE FROM outreach.campaigns
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 4. Delete override_audit_log (FK: override_id)
DELETE FROM outreach.override_audit_log
WHERE override_id IN (
    SELECT override_id FROM outreach.manual_overrides
    WHERE outreach_id IN ($INELIGIBLE_IDS)
);

-- 5. Delete manual_overrides (FK: outreach_id)
DELETE FROM outreach.manual_overrides
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 6. Delete bit_signals (FK: outreach_id)
DELETE FROM outreach.bit_signals
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 7. Delete bit_scores (FK: outreach_id)
DELETE FROM outreach.bit_scores
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 8. Delete blog (FK: outreach_id)
DELETE FROM outreach.blog
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 9. Delete people_master (FK: company_slot)
DELETE FROM people.people_master
WHERE company_slot_unique_id IN (
    SELECT slot_id::text FROM people.company_slot
    WHERE outreach_id IN ($INELIGIBLE_IDS)
);

-- 10. Delete company_slot (FK: outreach_id)
DELETE FROM people.company_slot
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 11. Delete outreach.people (FK: outreach_id)
DELETE FROM outreach.people
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 12. Delete dol (FK: outreach_id)
DELETE FROM outreach.dol
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 13. Delete company_target (FK: outreach_id)
DELETE FROM outreach.company_target
WHERE outreach_id IN ($INELIGIBLE_IDS);

-- 14. Delete outreach spine (LAST)
DELETE FROM outreach.outreach
WHERE outreach_id IN ($INELIGIBLE_IDS);

COMMIT;
```

---

## PHASE 4: CLEAR outreach_id IN CL

**Run this in CL database (or via cross-schema if same DB):**

```sql
-- Clear outreach_id for ineligible companies
UPDATE cl.company_identity
SET outreach_id = NULL
WHERE eligibility_status = 'INELIGIBLE'
  AND outreach_id IS NOT NULL;
```

---

## PHASE 5: VERIFY ALIGNMENT

```sql
-- Count CL ELIGIBLE with outreach_id
SELECT COUNT(*) as cl_eligible_with_outreach
FROM cl.company_identity
WHERE eligibility_status = 'ELIGIBLE'
  AND outreach_id IS NOT NULL;

-- Count outreach.outreach
SELECT COUNT(*) as outreach_spine_count
FROM outreach.outreach;

-- These should match!
-- If not, investigate orphans.
```

**Alignment check:**
```sql
-- Find orphans in outreach (outreach_id not in CL ELIGIBLE)
SELECT o.outreach_id
FROM outreach.outreach o
LEFT JOIN cl.company_identity ci
    ON o.outreach_id = ci.outreach_id
    AND ci.eligibility_status = 'ELIGIBLE'
WHERE ci.sovereign_company_id IS NULL;

-- Should return 0 rows
```

---

## PYTHON SCRIPT TEMPLATE

For bulk execution with the CL export:

```python
"""
Outreach Cascade Cleanup
========================
Receives ineligible_outreach_ids from CL and cascades cleanup.

Usage:
    doppler run -- python outreach_cascade_cleanup.py --input ineligible_for_outreach_cascade.json
"""

import os
import json
import argparse
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

def load_ineligible_ids(filepath: str) -> list:
    """Load ineligible outreach_ids from CL export."""
    with open(filepath, 'r') as f:
        data = json.load(f)

    if isinstance(data, list):
        # Array of objects with outreach_id
        return [r['outreach_id'] for r in data if r.get('outreach_id')]
    elif isinstance(data, dict) and 'ineligible_outreach_ids' in data:
        return data['ineligible_outreach_ids']
    else:
        raise ValueError("Invalid export format")

def cascade_cleanup(conn, outreach_ids: list, dry_run: bool = True):
    """Execute cascade cleanup for given outreach_ids."""
    cur = conn.cursor()

    # Convert to tuple for SQL IN clause
    ids_tuple = tuple(outreach_ids)

    print(f"Processing {len(outreach_ids)} outreach_ids...")

    # Phase 2: Archive
    print("PHASE 2: Archiving records...")
    archive_tables = [
        ('outreach.outreach', 'outreach.outreach_archive'),
        ('outreach.company_target', 'outreach.company_target_archive'),
        ('outreach.dol', 'outreach.dol_archive'),
        ('outreach.people', 'outreach.people_archive'),
        ('outreach.blog', 'outreach.blog_archive'),
        ('outreach.bit_scores', 'outreach.bit_scores_archive'),
    ]

    for src, dst in archive_tables:
        cur.execute(f'''
            INSERT INTO {dst}
            SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
            FROM {src}
            WHERE outreach_id IN %s
        ''', (ids_tuple,))
        print(f"  Archived {cur.rowcount} from {src}")

    if dry_run:
        print("\nDRY RUN - Rolling back...")
        conn.rollback()
        return

    # Phase 3: Delete in order
    print("\nPHASE 3: Deleting records...")

    delete_order = [
        "DELETE FROM outreach.send_log WHERE sequence_id IN (SELECT sequence_id FROM outreach.sequences WHERE campaign_id IN (SELECT campaign_id FROM outreach.campaigns WHERE outreach_id IN %s))",
        "DELETE FROM outreach.sequences WHERE campaign_id IN (SELECT campaign_id FROM outreach.campaigns WHERE outreach_id IN %s)",
        "DELETE FROM outreach.campaigns WHERE outreach_id IN %s",
        "DELETE FROM outreach.override_audit_log WHERE override_id IN (SELECT override_id FROM outreach.manual_overrides WHERE outreach_id IN %s)",
        "DELETE FROM outreach.manual_overrides WHERE outreach_id IN %s",
        "DELETE FROM outreach.bit_signals WHERE outreach_id IN %s",
        "DELETE FROM outreach.bit_scores WHERE outreach_id IN %s",
        "DELETE FROM outreach.blog WHERE outreach_id IN %s",
        "DELETE FROM people.people_master WHERE company_slot_unique_id IN (SELECT slot_id::text FROM people.company_slot WHERE outreach_id IN %s)",
        "DELETE FROM people.company_slot WHERE outreach_id IN %s",
        "DELETE FROM outreach.people WHERE outreach_id IN %s",
        "DELETE FROM outreach.dol WHERE outreach_id IN %s",
        "DELETE FROM outreach.company_target WHERE outreach_id IN %s",
        "DELETE FROM outreach.outreach WHERE outreach_id IN %s",
    ]

    for sql in delete_order:
        cur.execute(sql, (ids_tuple,))
        print(f"  Deleted {cur.rowcount} rows")

    conn.commit()
    print("\nCascade cleanup complete!")

def main():
    parser = argparse.ArgumentParser(description='Outreach Cascade Cleanup')
    parser.add_argument('--input', required=True, help='Path to CL export JSON')
    parser.add_argument('--execute', action='store_true', help='Actually execute (default is dry run)')
    args = parser.parse_args()

    outreach_ids = load_ineligible_ids(args.input)
    print(f"Loaded {len(outreach_ids)} ineligible outreach_ids from {args.input}")

    conn = psycopg2.connect(DATABASE_URL)

    try:
        cascade_cleanup(conn, outreach_ids, dry_run=not args.execute)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
```

---

## REPORTING

After cleanup, produce this report:

```
================================================================================
OUTREACH CASCADE CLEANUP COMPLETE
================================================================================

Execution Date: [DATE]
Input File: [filepath]
Dry Run: [YES/NO]

RECORDS ARCHIVED:
─────────────────────────────────────────────────────────────────────────────────
Table                        | Archived
─────────────────────────────────────────────────────────────────────────────────
outreach.outreach            | [X]
outreach.company_target      | [X]
outreach.dol                 | [X]
outreach.people              | [X]
outreach.blog                | [X]
outreach.bit_scores          | [X]
people.company_slot          | [X]
people.people_master         | [X]
─────────────────────────────────────────────────────────────────────────────────

RECORDS DELETED:
─────────────────────────────────────────────────────────────────────────────────
Table                        | Deleted
─────────────────────────────────────────────────────────────────────────────────
outreach.send_log            | [X]
outreach.sequences           | [X]
outreach.campaigns           | [X]
outreach.manual_overrides    | [X]
outreach.bit_signals         | [X]
outreach.bit_scores          | [X]
outreach.blog                | [X]
outreach.people              | [X]
outreach.dol                 | [X]
outreach.company_target      | [X]
outreach.outreach            | [X]
people.company_slot          | [X]
people.people_master         | [X]
─────────────────────────────────────────────────────────────────────────────────

ALIGNMENT VERIFICATION:
─────────────────────────────────────────────────────────────────────────────────
CL ELIGIBLE with outreach_id: [X]
outreach.outreach count:      [X]
Match: [YES/NO]
─────────────────────────────────────────────────────────────────────────────────

STATUS: [SUCCESS / FAILED]
================================================================================
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 1.0.0 |
| Status | ACTIVE |
| Authority | OPERATIONAL |
| Prerequisite | CL_ELIGIBILITY_WITH_OUTREACH_CASCADE.prompt.md (CL) |
