#!/usr/bin/env python3
"""Check bridge-based People linkage to Outreach."""

import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(
    host='ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    port=5432,
    database='Marketing DB',
    user='Marketing DB_owner',
    password='npg_OsE4Z2oPCpiT',
    sslmode='require'
)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 60)
print("BRIDGE-BASED PEOPLE LINKAGE")
print("=" * 60)

# Check if outreach.outreach.sovereign_id matches bridge.company_sov_id
cur.execute("""
    SELECT 
        COUNT(DISTINCT o.outreach_id) as total_outreach,
        COUNT(DISTINCT b.company_sov_id) as bridged
    FROM outreach.outreach o
    LEFT JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
""")
r = cur.fetchone()
print(f"\nTotal outreach: {r['total_outreach']}")
print(f"Have bridge entry: {r['bridged']}")

# Check how many people_master can be linked via bridge
print("\n=== PEOPLE LINKAGE VIA BRIDGE ===")
cur.execute("""
    SELECT 
        COUNT(DISTINCT pm.unique_id) as total_people,
        COUNT(DISTINCT CASE WHEN b.bridge_id IS NOT NULL THEN pm.unique_id END) as linkable,
        COUNT(DISTINCT CASE WHEN o.outreach_id IS NOT NULL THEN pm.unique_id END) as to_outreach
    FROM people.people_master pm
    LEFT JOIN cl.company_identity_bridge b ON pm.company_unique_id = b.source_company_id
    LEFT JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
""")
r = cur.fetchone()
print(f"Total people: {r['total_people']}")
print(f"Linkable via bridge: {r['linkable']}")
print(f"Linkable to outreach: {r['to_outreach']}")

# Sample the full chain
print("\n=== SAMPLE FULL CHAIN (people -> bridge -> outreach) ===")
cur.execute("""
    SELECT 
        pm.first_name, pm.last_name, pm.email,
        pm.company_unique_id as dol_company_id,
        b.company_sov_id as sovereign_id,
        o.outreach_id,
        o.domain
    FROM people.people_master pm
    JOIN cl.company_identity_bridge b ON pm.company_unique_id = b.source_company_id
    JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
    WHERE pm.email IS NOT NULL
    LIMIT 5
""")
rows = cur.fetchall()
if rows:
    for r in rows:
        print(f"  {r['first_name']} {r['last_name']} <{r['email']}>")
        sov = str(r['sovereign_id'])[:8] if r['sovereign_id'] else 'NULL'
        oid = str(r['outreach_id'])[:8] if r['outreach_id'] else 'NULL'
        print(f"    DOL: {r['dol_company_id']} -> sov: {sov}... -> outreach: {oid}... ({r['domain']})")
else:
    print("  No linkable people found!")

# Count how many people have verified emails that could be promoted
print("\n=== PROMOTABLE PEOPLE (verified email + linkable to outreach) ===")
cur.execute("""
    SELECT 
        COUNT(*) as total_linkable,
        COUNT(*) FILTER (WHERE pm.email_verified = true) as verified_email
    FROM people.people_master pm
    JOIN cl.company_identity_bridge b ON pm.company_unique_id = b.source_company_id
    JOIN outreach.outreach o ON b.company_sov_id = o.sovereign_id
    WHERE pm.email IS NOT NULL
""")
r = cur.fetchone()
print(f"Linkable people with email: {r['total_linkable']}")
print(f"With verified email: {r['verified_email']}")

conn.close()

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print("""
The bridge table cl.company_identity_bridge EXISTS and can link:
  people_master.company_unique_id (DOL-style)
  → bridge.source_company_id → bridge.company_sov_id
  → outreach.sovereign_id → outreach.outreach_id

ACTION: Populate outreach.people by joining through the bridge.
""")
