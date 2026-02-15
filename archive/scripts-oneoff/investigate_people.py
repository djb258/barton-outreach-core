#!/usr/bin/env python3
"""Investigate People pipeline state and identity bridge."""

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
print("PEOPLE PIPELINE INVESTIGATION")
print("=" * 60)

print("\n1. outreach.people table:")
cur.execute("SELECT COUNT(*) as cnt FROM outreach.people")
print(f"   Total records: {cur.fetchone()['cnt']}")

print("\n2. people.people_master table:")
cur.execute("SELECT COUNT(*) as cnt FROM people.people_master")
print(f"   Total records: {cur.fetchone()['cnt']}")

print("\n3. intake.people_raw_intake table:")
cur.execute("SELECT COUNT(*) as cnt FROM intake.people_raw_intake")
print(f"   Total records: {cur.fetchone()['cnt']}")

print("\n4. people.company_slot table:")
cur.execute("SELECT COUNT(*) as cnt FROM people.company_slot")
print(f"   Total records: {cur.fetchone()['cnt']}")

print("\n5. people.people_candidate table:")
cur.execute("SELECT COUNT(*) as cnt FROM people.people_candidate")
print(f"   Total records: {cur.fetchone()['cnt']}")

# Check company_unique_id format
print("\n6. company_unique_id format comparison:")
cur.execute("SELECT company_unique_id FROM people.people_master LIMIT 3")
print("   people_master samples:")
for r in cur.fetchall():
    print(f"     {r['company_unique_id']}")

cur.execute("SELECT company_unique_id FROM outreach.company_target LIMIT 3")
print("   company_target samples:")
for r in cur.fetchall():
    print(f"     {r['company_unique_id']}")

# Check overlap
print("\n7. Company overlap between people_master and company_target:")
cur.execute("""
    SELECT 
        COUNT(DISTINCT pm.company_unique_id) as pm_companies,
        COUNT(DISTINCT ct.company_unique_id) as ct_companies,
        COUNT(DISTINCT CASE WHEN pm.company_unique_id = ct.company_unique_id THEN pm.company_unique_id END) as overlap
    FROM people.people_master pm
    FULL OUTER JOIN outreach.company_target ct ON pm.company_unique_id::text = ct.company_unique_id::text
""")
r = cur.fetchone()
print(f"   people_master companies: {r['pm_companies']}")
print(f"   company_target companies: {r['ct_companies']}")
print(f"   Overlap: {r['overlap']}")

# Check if outreach.people is linked via outreach_id
print("\n8. outreach.people schema:")
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'people'
    ORDER BY ordinal_position
""")
cols = [r['column_name'] for r in cur.fetchall()]
print(f"   Columns: {cols}")

# Check identity bridge
print("\n" + "=" * 60)
print("IDENTITY BRIDGE CHECK")
print("=" * 60)

print("\n9. cl.company_identity_bridge:")
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema = 'cl' AND table_name = 'company_identity_bridge'
    ORDER BY ordinal_position
""")
cols = [r['column_name'] for r in cur.fetchall()]
print(f"   Columns: {cols}")

if cols:
    cur.execute("SELECT COUNT(*) as cnt FROM cl.company_identity_bridge")
    cnt = cur.fetchone()['cnt']
    print(f"   Records: {cnt}")
    
    if cnt > 0:
        cur.execute("SELECT * FROM cl.company_identity_bridge LIMIT 3")
        print("   Sample:")
        for r in cur.fetchall():
            print(f"     {dict(r)}")

# Check company.company_master for domain
print("\n10. company.company_master columns:")
cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema = 'company' AND table_name = 'company_master'
    ORDER BY ordinal_position
""")
cols = [r['column_name'] for r in cur.fetchall()]
print(f"    {cols}")

# Can we match via domain?
print("\n11. Domain-based matching potential:")
cur.execute("""
    SELECT 
        COUNT(DISTINCT o.domain) as outreach_domains
    FROM outreach.outreach o
    WHERE o.domain IS NOT NULL
""")
print(f"    Outreach domains: {cur.fetchone()['outreach_domains']}")

cur.execute("""
    SELECT 
        COUNT(DISTINCT cm.website_url) as company_domains
    FROM company.company_master cm
    WHERE cm.website_url IS NOT NULL
""")
print(f"    company_master domains: {cur.fetchone()['company_domains']}")

conn.close()
