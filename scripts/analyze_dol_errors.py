#!/usr/bin/env python3
"""Analyze DOL errors and what can be cleared."""

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

# 1. Check dol_errors table structure
print("=" * 60)
print("DOL_ERRORS TABLE STRUCTURE")
print("=" * 60)

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'dol_errors'
    ORDER BY ordinal_position
""")
print("\nColumns:")
for c in cur.fetchall():
    print(f"  {c['column_name']}: {c['data_type']}")

# 2. DOL errors distribution
print("\n" + "=" * 60)
print("DOL_ERRORS DISTRIBUTION")
print("=" * 60)

cur.execute("""
    SELECT failure_code, COUNT(*) as cnt 
    FROM outreach.dol_errors
    GROUP BY failure_code
    ORDER BY cnt DESC
""")
print("\nBy failure_code:")
total_errors = 0
for row in cur.fetchall():
    print(f"  {row['failure_code']:<30}: {row['cnt']:>8,}")
    total_errors += row['cnt']
print(f"  {'TOTAL':<30}: {total_errors:>8,}")

# 3. Check how diagnostic view determines status
print("\n" + "=" * 60)
print("DIAGNOSTIC VIEW - DOL STATUS LOGIC")
print("=" * 60)

cur.execute("""
    SELECT pg_get_viewdef('outreach.v_outreach_diagnostic', true)
""")
view_def = cur.fetchone()['pg_get_viewdef']
# Extract just the DOL status logic
import re
dol_match = re.search(r'dol_status.*?(?=,\s*\w+_status|$)', view_def, re.DOTALL | re.IGNORECASE)
if dol_match:
    print("\nDOL status logic from view:")
    print(dol_match.group(0)[:500] + "...")

# 4. Key question: Are errors for records we already promoted to dol?
print("\n" + "=" * 60)
print("ERRORS vs DOL TABLE OVERLAP")
print("=" * 60)

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM outreach.dol_errors de
    WHERE EXISTS (
        SELECT 1 FROM outreach.dol d WHERE d.outreach_id = de.outreach_id
    )
""")
overlap = cur.fetchone()['cnt']
print(f"\nErrors that ALSO have record in outreach.dol: {overlap:,}")
print("  (These should be cleared from error table)")

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM outreach.dol_errors de
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.dol d WHERE d.outreach_id = de.outreach_id
    )
""")
no_overlap = cur.fetchone()['cnt']
print(f"\nErrors with NO record in outreach.dol: {no_overlap:,}")
print("  (These are legitimately blocked)")

# 5. Break down the overlap by error code
print("\n" + "=" * 60)
print("ERRORS THAT CAN BE CLEARED (have dol record)")
print("=" * 60)

cur.execute("""
    SELECT de.failure_code, COUNT(*) as cnt
    FROM outreach.dol_errors de
    WHERE EXISTS (
        SELECT 1 FROM outreach.dol d WHERE d.outreach_id = de.outreach_id
    )
    GROUP BY de.failure_code
    ORDER BY cnt DESC
""")
print("\nBy failure_code:")
clearable = 0
for row in cur.fetchall():
    print(f"  {row['failure_code']:<30}: {row['cnt']:>8,}")
    clearable += row['cnt']
print(f"  {'CLEARABLE TOTAL':<30}: {clearable:>8,}")

# 6. What's still legitimately blocked?
print("\n" + "=" * 60)
print("LEGITIMATELY BLOCKED (no dol record)")
print("=" * 60)

cur.execute("""
    SELECT de.failure_code, COUNT(*) as cnt
    FROM outreach.dol_errors de
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.dol d WHERE d.outreach_id = de.outreach_id
    )
    GROUP BY de.failure_code
    ORDER BY cnt DESC
""")
print("\nBy failure_code:")
for row in cur.fetchall():
    print(f"  {row['failure_code']:<30}: {row['cnt']:>8,}")

# 7. Sample the NO_EIN errors - do any now have EIN?
print("\n" + "=" * 60)
print("NO_EIN ERRORS THAT NOW HAVE EIN")
print("=" * 60)

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_EIN'
    AND cm.ein IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM outreach.dol d WHERE d.outreach_id = de.outreach_id)
""")
can_match = cur.fetchone()['cnt']
print(f"\nNO_EIN errors where company now HAS EIN: {can_match:,}")
print("  (These could be promoted if they match form_5500)")

conn.close()
