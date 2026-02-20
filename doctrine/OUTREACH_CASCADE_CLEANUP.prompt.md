# Outreach Cascade Cleanup (CL Direct Query)

**Status**: ACTIVE
**Authority**: OPERATIONAL
**Version**: 2.0.0
**Change Protocol**: ADR + HUMAN APPROVAL REQUIRED

---

## ROLE

You are a **Cascade Cleanup Agent** operating in the **barton-outreach-core repository**.

Your responsibility is to **query CL for ineligible outreach_ids** and **cascade the cleanup through all sub-hubs** in the correct order.

You do **NOT** determine eligibility. CL already did that.
You **DO** query CL and execute the cleanup autonomously.

---

## PREREQUISITE

**CL must have already marked non-commercial entities as INELIGIBLE.**

Verify by running:

```sql
-- Check if CL has INELIGIBLE records with outreach_ids
SELECT COUNT(*) as pending_cleanup
FROM cl.company_identity
WHERE eligibility_status = 'INELIGIBLE'
  AND outreach_id IS NOT NULL;
```

**If this returns 0, STOP.** CL hasn't run its eligibility filter yet.

---

## DATABASE CONNECTION

```bash
# Via Doppler
doppler run -- python script.py

# Connection string in DATABASE_URL
```

---

## STEP 0: DISCOVERY — Query CL for Ineligible Outreach IDs

**This is your source of truth.** Query CL directly.

```sql
-- Get all outreach_ids that need cleanup
SELECT
    ci.outreach_id,
    ci.sovereign_company_id,
    ci.exclusion_reason,
    ci.company_name,
    ci.company_domain
FROM cl.company_identity ci
WHERE ci.eligibility_status = 'INELIGIBLE'
  AND ci.outreach_id IS NOT NULL
ORDER BY ci.exclusion_reason;
```

**Count by category:**

```sql
SELECT
    exclusion_reason,
    COUNT(*) as count
FROM cl.company_identity
WHERE eligibility_status = 'INELIGIBLE'
  AND outreach_id IS NOT NULL
GROUP BY exclusion_reason
ORDER BY count DESC;
```

**Expected output:**
```
exclusion_reason           | count
---------------------------+-------
EDUCATIONAL_INSTITUTION    | ~1080
GOVERNMENT_ENTITY          | ~150
HEALTHCARE_FACILITY        | ~150
RELIGIOUS_ORGANIZATION     | ~70
INSURANCE_CARRIER          | ~15
```

---

## CASCADE ORDER (CRITICAL)

**You MUST follow this exact order.** FK constraints require it.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CASCADE CLEANUP ORDER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  PHASE 0: QUERY CL (done above)                                              │
│  ────────────────────────────                                                │
│  Get ineligible outreach_ids directly from cl.company_identity              │
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

**Uses subquery to CL — no import file needed.**

```sql
BEGIN;

-- Archive outreach spine
INSERT INTO outreach.outreach_archive
SELECT o.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.outreach o
WHERE o.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive company_target
INSERT INTO outreach.company_target_archive
SELECT ct.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.company_target ct
WHERE ct.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive dol
INSERT INTO outreach.dol_archive
SELECT d.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.dol d
WHERE d.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive people (outreach schema)
INSERT INTO outreach.people_archive
SELECT p.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.people p
WHERE p.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive blog
INSERT INTO outreach.blog_archive
SELECT b.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.blog b
WHERE b.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive bit_scores
INSERT INTO outreach.bit_scores_archive
SELECT bs.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM outreach.bit_scores bs
WHERE bs.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive company_slot
INSERT INTO people.company_slot_archive
SELECT cs.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM people.company_slot cs
WHERE cs.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- Archive people_master (via slot)
INSERT INTO people.people_master_archive
SELECT pm.*, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
FROM people.people_master pm
JOIN people.company_slot cs ON pm.company_slot_unique_id = cs.slot_id::text
WHERE cs.outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

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

**Uses CTE for cleaner subquery reference.**

```sql
BEGIN;

-- Define ineligible IDs once
WITH ineligible AS (
    SELECT outreach_id
    FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
)

-- 1. Delete send_log (FK: sequence_id)
DELETE FROM outreach.send_log
WHERE sequence_id IN (
    SELECT sequence_id FROM outreach.sequences
    WHERE campaign_id IN (
        SELECT campaign_id FROM outreach.campaigns
        WHERE outreach_id IN (SELECT outreach_id FROM ineligible)
    )
);

-- 2. Delete sequences (FK: campaign_id)
DELETE FROM outreach.sequences
WHERE campaign_id IN (
    SELECT campaign_id FROM outreach.campaigns
    WHERE outreach_id IN (
        SELECT outreach_id FROM cl.company_identity
        WHERE eligibility_status = 'INELIGIBLE'
          AND outreach_id IS NOT NULL
    )
);

-- 3. Delete campaigns (FK: outreach_id)
DELETE FROM outreach.campaigns
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 4. Delete override_audit_log (FK: override_id)
DELETE FROM outreach.override_audit_log
WHERE override_id IN (
    SELECT override_id FROM outreach.manual_overrides
    WHERE outreach_id IN (
        SELECT outreach_id FROM cl.company_identity
        WHERE eligibility_status = 'INELIGIBLE'
          AND outreach_id IS NOT NULL
    )
);

-- 5. Delete manual_overrides (FK: outreach_id)
DELETE FROM outreach.manual_overrides
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 6. Delete bit_signals (FK: outreach_id)
DELETE FROM outreach.bit_signals
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 7. Delete bit_scores (FK: outreach_id)
DELETE FROM outreach.bit_scores
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 8. Delete blog (FK: outreach_id)
DELETE FROM outreach.blog
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 9. Delete people_master (FK: company_slot)
DELETE FROM people.people_master
WHERE company_slot_unique_id IN (
    SELECT slot_id::text FROM people.company_slot
    WHERE outreach_id IN (
        SELECT outreach_id FROM cl.company_identity
        WHERE eligibility_status = 'INELIGIBLE'
          AND outreach_id IS NOT NULL
    )
);

-- 10. Delete company_slot (FK: outreach_id)
DELETE FROM people.company_slot
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 11. Delete outreach.people (FK: outreach_id)
DELETE FROM outreach.people
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 12. Delete dol (FK: outreach_id)
DELETE FROM outreach.dol
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 13. Delete company_target (FK: outreach_id)
DELETE FROM outreach.company_target
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

-- 14. Delete outreach spine (LAST)
DELETE FROM outreach.outreach
WHERE outreach_id IN (
    SELECT outreach_id FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
);

COMMIT;
```

---

## PHASE 4: CLEAR outreach_id IN CL

**After Outreach cleanup is done, clear the now-orphaned outreach_ids in CL.**

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

For automated execution (queries CL directly, no import file):

```python
"""
Outreach Cascade Cleanup (CL Direct Query)
==========================================
Queries CL for ineligible outreach_ids and cascades cleanup.

Usage:
    doppler run -- python outreach_cascade_cleanup.py --dry-run
    doppler run -- python outreach_cascade_cleanup.py --execute
"""

import os
import argparse
import psycopg2
from datetime import datetime

DATABASE_URL = os.environ.get('DATABASE_URL')

# CL query for ineligible outreach_ids
INELIGIBLE_QUERY = """
    SELECT outreach_id
    FROM cl.company_identity
    WHERE eligibility_status = 'INELIGIBLE'
      AND outreach_id IS NOT NULL
"""

def get_ineligible_ids(conn) -> list:
    """Query CL directly for ineligible outreach_ids."""
    cur = conn.cursor()
    cur.execute(INELIGIBLE_QUERY)
    return [row[0] for row in cur.fetchall()]

def cascade_cleanup(conn, outreach_ids: list, dry_run: bool = True):
    """Execute cascade cleanup for given outreach_ids."""
    cur = conn.cursor()

    # Convert to tuple for SQL IN clause
    ids_tuple = tuple(outreach_ids)

    if not ids_tuple:
        print("No ineligible outreach_ids found. Nothing to clean.")
        return

    print(f"Processing {len(outreach_ids)} outreach_ids...")

    # Phase 2: Archive
    print("\nPHASE 2: Archiving records...")
    archive_queries = [
        ('outreach.outreach', 'outreach.outreach_archive'),
        ('outreach.company_target', 'outreach.company_target_archive'),
        ('outreach.dol', 'outreach.dol_archive'),
        ('outreach.people', 'outreach.people_archive'),
        ('outreach.blog', 'outreach.blog_archive'),
        ('outreach.bit_scores', 'outreach.bit_scores_archive'),
        ('people.company_slot', 'people.company_slot_archive'),
    ]

    for src, dst in archive_queries:
        cur.execute(f'''
            INSERT INTO {dst}
            SELECT *, NOW(), 'INELIGIBLE_COMMERCIAL_FILTER'
            FROM {src}
            WHERE outreach_id IN %s
        ''', (ids_tuple,))
        print(f"  Archived {cur.rowcount} from {src}")

    # Phase 3: Delete in order
    print("\nPHASE 3: Deleting records...")

    delete_queries = [
        ("outreach.send_log", """
            DELETE FROM outreach.send_log
            WHERE sequence_id IN (
                SELECT sequence_id FROM outreach.sequences
                WHERE campaign_id IN (
                    SELECT campaign_id FROM outreach.campaigns
                    WHERE outreach_id IN %s
                )
            )
        """),
        ("outreach.sequences", """
            DELETE FROM outreach.sequences
            WHERE campaign_id IN (
                SELECT campaign_id FROM outreach.campaigns
                WHERE outreach_id IN %s
            )
        """),
        ("outreach.campaigns", "DELETE FROM outreach.campaigns WHERE outreach_id IN %s"),
        ("outreach.override_audit_log", """
            DELETE FROM outreach.override_audit_log
            WHERE override_id IN (
                SELECT override_id FROM outreach.manual_overrides
                WHERE outreach_id IN %s
            )
        """),
        ("outreach.manual_overrides", "DELETE FROM outreach.manual_overrides WHERE outreach_id IN %s"),
        ("outreach.bit_signals", "DELETE FROM outreach.bit_signals WHERE outreach_id IN %s"),
        ("outreach.bit_scores", "DELETE FROM outreach.bit_scores WHERE outreach_id IN %s"),
        ("outreach.blog", "DELETE FROM outreach.blog WHERE outreach_id IN %s"),
        ("people.people_master", """
            DELETE FROM people.people_master
            WHERE company_slot_unique_id IN (
                SELECT slot_id::text FROM people.company_slot
                WHERE outreach_id IN %s
            )
        """),
        ("people.company_slot", "DELETE FROM people.company_slot WHERE outreach_id IN %s"),
        ("outreach.people", "DELETE FROM outreach.people WHERE outreach_id IN %s"),
        ("outreach.dol", "DELETE FROM outreach.dol WHERE outreach_id IN %s"),
        ("outreach.company_target", "DELETE FROM outreach.company_target WHERE outreach_id IN %s"),
        ("outreach.outreach", "DELETE FROM outreach.outreach WHERE outreach_id IN %s"),
    ]

    for table, sql in delete_queries:
        cur.execute(sql, (ids_tuple,))
        print(f"  {table}: deleted {cur.rowcount}")

    # Phase 4: Clear outreach_id in CL
    print("\nPHASE 4: Clearing outreach_id in CL...")
    cur.execute("""
        UPDATE cl.company_identity
        SET outreach_id = NULL
        WHERE eligibility_status = 'INELIGIBLE'
          AND outreach_id IS NOT NULL
    """)
    print(f"  Cleared {cur.rowcount} outreach_ids in CL")

    if dry_run:
        print("\n*** DRY RUN - Rolling back all changes ***")
        conn.rollback()
        return

    conn.commit()
    print("\nCascade cleanup committed!")

    # Phase 5: Verify
    print("\nPHASE 5: Verifying alignment...")
    cur.execute("""
        SELECT COUNT(*) FROM cl.company_identity
        WHERE eligibility_status = 'ELIGIBLE'
          AND outreach_id IS NOT NULL
    """)
    cl_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    outreach_count = cur.fetchone()[0]

    print(f"  CL ELIGIBLE with outreach_id: {cl_count}")
    print(f"  outreach.outreach count:      {outreach_count}")

    if cl_count == outreach_count:
        print("  ✓ ALIGNED")
    else:
        print(f"  ✗ MISMATCH (diff: {abs(cl_count - outreach_count)})")

def main():
    parser = argparse.ArgumentParser(description='Outreach Cascade Cleanup')
    parser.add_argument('--execute', action='store_true',
                        help='Actually execute (default is dry run)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Dry run only (default)')
    args = parser.parse_args()

    conn = psycopg2.connect(DATABASE_URL)

    try:
        # Query CL for ineligible IDs
        print("Querying CL for ineligible outreach_ids...")
        outreach_ids = get_ineligible_ids(conn)
        print(f"Found {len(outreach_ids)} ineligible outreach_ids in CL")

        if not outreach_ids:
            print("Nothing to clean up.")
            return

        # Execute cleanup
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
Source: CL Direct Query (cl.company_identity WHERE eligibility_status = 'INELIGIBLE')
Mode: [DRY RUN / EXECUTED]

INELIGIBLE BREAKDOWN (from CL):
─────────────────────────────────────────────────────────────────────────────────
Exclusion Reason             | Count
─────────────────────────────────────────────────────────────────────────────────
EDUCATIONAL_INSTITUTION      | [X]
GOVERNMENT_ENTITY            | [X]
HEALTHCARE_FACILITY          | [X]
RELIGIOUS_ORGANIZATION       | [X]
INSURANCE_CARRIER            | [X]
─────────────────────────────────────────────────────────────────────────────────
TOTAL                        | [X]
─────────────────────────────────────────────────────────────────────────────────

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

## SIMPLIFIED WORKFLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SIMPLIFIED WORKFLOW                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   1. CL marks non-commercial as INELIGIBLE (separate operation)              │
│                                                                              │
│   2. Run this prompt in barton-outreach-core:                                │
│      - Queries CL for ineligible outreach_ids                                │
│      - Archives affected records                                             │
│      - Deletes in FK order                                                   │
│      - Clears outreach_id in CL                                              │
│      - Verifies alignment                                                    │
│                                                                              │
│   No export file. No handoff. Outreach handles everything autonomously.      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-29 |
| Last Modified | 2026-01-29 |
| Version | 2.0.0 |
| Status | ACTIVE |
| Authority | OPERATIONAL |
| Prerequisite | CL has marked records as INELIGIBLE |
| Previous Version | 1.0.0 (required export file) |
