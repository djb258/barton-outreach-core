#!/usr/bin/env python3
"""Verify the diagnostic view after people promotion."""

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

print("=" * 70)
print("DIAGNOSTIC VIEW STATUS AFTER PEOPLE PROMOTION")
print("=" * 70)

# Check the diagnostic view
cur.execute("""
    SELECT 
        people_status,
        COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    GROUP BY people_status
    ORDER BY cnt DESC
""")
print("\n=== People Status Distribution ===")
for row in cur.fetchall():
    print(f"  {row['people_status']}: {row['cnt']:,}")

# Check outreach_ready
cur.execute("""
    SELECT 
        outreach_ready,
        COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    GROUP BY outreach_ready
    ORDER BY cnt DESC
""")
print("\n=== Outreach Ready Distribution ===")
for row in cur.fetchall():
    print(f"  {row['outreach_ready']}: {row['cnt']:,}")

# Bottleneck analysis
cur.execute("""
    SELECT 
        bottleneck_hub,
        bottleneck_reason,
        COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    WHERE outreach_ready = false
    GROUP BY bottleneck_hub, bottleneck_reason
    ORDER BY cnt DESC
    LIMIT 15
""")
print("\n=== Bottleneck Analysis (top 15) ===")
for row in cur.fetchall():
    print(f"  {row['bottleneck_hub']}: {row['bottleneck_reason']} - {row['cnt']:,}")

# Sample of ready outreach
cur.execute("""
    SELECT 
        d.outreach_id,
        d.domain,
        d.ct_status,
        d.people_status,
        d.dol_status
    FROM outreach.v_outreach_diagnostic d
    WHERE d.outreach_ready = true
    LIMIT 10
""")
print("\n=== Sample Ready Outreach (outreach_ready=true) ===")
for row in cur.fetchall():
    print(f"  {row['domain']}: CT={row['ct_status']}, People={row['people_status']}, DOL={row['dol_status']}")

# Check people table directly
cur.execute("SELECT COUNT(*) as cnt FROM outreach.people")
r = cur.fetchone()
print(f"\n=== Direct people table count: {r['cnt']} ===")

# Check how many unique outreach_ids have people
cur.execute("SELECT COUNT(DISTINCT outreach_id) as cnt FROM outreach.people")
r = cur.fetchone()
print(f"=== Unique outreach_ids with people: {r['cnt']} ===")

conn.close()
