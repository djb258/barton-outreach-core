#!/usr/bin/env python3
"""Check updated DOL status distribution."""

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

print('DOL Status Distribution (Updated):')
print('=' * 50)
cur.execute("""
    SELECT dol_status, COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    GROUP BY dol_status
    ORDER BY cnt DESC
""")
total = 0
for row in cur.fetchall():
    print(f"  {row['dol_status']:<15}: {row['cnt']:>8,}")
    total += row['cnt']
print(f"  {'TOTAL':<15}: {total:>8,}")

print()
print('NC Specific:')
cur.execute("""
    SELECT d.dol_status, COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic d
    JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE cm.address_state = 'NC'
    GROUP BY d.dol_status
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row['dol_status']:<15}: {row['cnt']:>8,}")

conn.close()
