#!/usr/bin/env python3
"""Deep dive into what's still blocked."""

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
print("BLOCKED RECORDS DEEP DIVE")
print("=" * 60)

# 1. What's the blocking reason for each?
print("\n1. ERROR TABLE BREAKDOWN")
print("-" * 40)

cur.execute("""
    SELECT failure_code, blocking_reason, COUNT(*) as cnt 
    FROM outreach.dol_errors
    GROUP BY failure_code, blocking_reason
    ORDER BY cnt DESC
    LIMIT 20
""")
for row in cur.fetchall():
    reason = row['blocking_reason'][:60] if row['blocking_reason'] else 'NULL'
    print(f"  {row['failure_code']:<15} | {reason:<60} | {row['cnt']:>6,}")

# 2. NO_STATE errors - do they actually have state now?
print("\n" + "=" * 60)
print("2. NO_STATE ERRORS - DO THEY HAVE STATE NOW?")
print("-" * 40)

cur.execute("""
    SELECT 
        CASE WHEN cm.address_state IS NOT NULL AND cm.address_state != '' 
             THEN 'Has State' ELSE 'No State' END as state_status,
        COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_STATE'
    GROUP BY 1
""")
for row in cur.fetchall():
    print(f"  {row['state_status']:<15}: {row['cnt']:>8,}")

# 3. NO_STATE with state - why are they still errored?
print("\n" + "=" * 60)
print("3. NO_STATE ERRORS THAT HAVE STATE - EIN STATUS")
print("-" * 40)

cur.execute("""
    SELECT 
        CASE WHEN cm.ein IS NOT NULL THEN 'Has EIN' ELSE 'No EIN' END as ein_status,
        COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_STATE'
    AND cm.address_state IS NOT NULL AND cm.address_state != ''
    GROUP BY 1
""")
for row in cur.fetchall():
    print(f"  {row['ein_status']:<15}: {row['cnt']:>8,}")

# 4. NO_STATE with state AND EIN - should match 5500!
print("\n" + "=" * 60)
print("4. NO_STATE WITH STATE+EIN - SHOULD HAVE DOL!")
print("-" * 40)

cur.execute("""
    SELECT de.outreach_id, cm.company_name, cm.address_state, cm.ein
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_STATE'
    AND cm.address_state IS NOT NULL AND cm.address_state != ''
    AND cm.ein IS NOT NULL
    LIMIT 10
""")
rows = cur.fetchall()
print(f"\nSample of {len(rows)} records with state+EIN but NO_STATE error:")
for row in rows:
    print(f"  {row['company_name'][:40]:<40} | {row['address_state']} | {row['ein']}")

# Check if these EINs exist in form_5500
if rows:
    eins = [row['ein'] for row in rows]
    cur.execute("""
        SELECT sponsor_dfe_ein, COUNT(*) as cnt 
        FROM dol.form_5500 
        WHERE sponsor_dfe_ein = ANY(%s)
        GROUP BY sponsor_dfe_ein
    """, (eins,))
    matches = cur.fetchall()
    print(f"\n  Of these EINs, {len(matches)} have form_5500 filings")

# 5. Could we re-run promotion for these?
print("\n" + "=" * 60)
print("5. NO_STATE ERRORS THAT COULD BE PROMOTED")
print("-" * 40)

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
    WHERE de.failure_code = 'NO_STATE'
    AND NOT EXISTS (SELECT 1 FROM outreach.dol d WHERE d.outreach_id = de.outreach_id)
""")
can_promote = cur.fetchone()['cnt']
print(f"\nNO_STATE errors that have matching 5500 filing: {can_promote:,}")
print("  (These could be promoted right now!)")

# 6. What about COLLISION?
print("\n" + "=" * 60)
print("6. COLLISION ERROR")
print("-" * 40)

cur.execute("""
    SELECT de.*, o.sovereign_id
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    WHERE de.failure_code = 'COLLISION'
""")
for row in cur.fetchall():
    print(f"  outreach_id: {row['outreach_id']}")
    print(f"  blocking_reason: {row['blocking_reason']}")

conn.close()
