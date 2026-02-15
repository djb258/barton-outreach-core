#!/usr/bin/env python3
"""Clear DOL errors for records that now have successful dol entries."""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 60)
print("CLEARING DOL ERRORS FOR PROMOTED RECORDS")
print("=" * 60)

# 1. Count before
cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol_errors")
before = cur.fetchone()['cnt']
print(f"\nDOL errors BEFORE: {before:,}")

# 2. Find records to clear (have both error and successful dol entry)
cur.execute("""
    SELECT COUNT(*) as cnt
    FROM outreach.dol_errors de
    WHERE EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = de.outreach_id
        AND d.ein IS NOT NULL
    )
""")
to_clear = cur.fetchone()['cnt']
print(f"Records to clear: {to_clear:,}")

# 3. Delete the errors (or mark resolved)
print("\nClearing errors...")

# Option A: Delete entirely
cur.execute("""
    DELETE FROM outreach.dol_errors de
    WHERE EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = de.outreach_id
        AND d.ein IS NOT NULL
    )
""")
deleted = cur.rowcount
print(f"Deleted: {deleted:,} error records")

conn.commit()

# 4. Count after
cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol_errors")
after = cur.fetchone()['cnt']
print(f"\nDOL errors AFTER: {after:,}")

# 5. Verify diagnostic view now correct
print("\n" + "=" * 60)
print("UPDATED DOL STATUS DISTRIBUTION")
print("=" * 60)

cur.execute("""
    SELECT dol_status, COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    GROUP BY dol_status
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row['dol_status']:<15}: {row['cnt']:>8,}")

# 6. Remaining errors breakdown
print("\n" + "=" * 60)
print("REMAINING ERROR BREAKDOWN")
print("=" * 60)

cur.execute("""
    SELECT failure_code, COUNT(*) as cnt 
    FROM outreach.dol_errors
    GROUP BY failure_code
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row['failure_code']:<30}: {row['cnt']:>8,}")

conn.close()
