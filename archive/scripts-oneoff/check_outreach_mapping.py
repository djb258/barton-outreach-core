#!/usr/bin/env python3
"""Check outreach_id to company_unique_id mapping."""

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

# Check if outreach_id exists in company_target
cur.execute("""
    SELECT outreach_id, company_unique_id 
    FROM outreach.company_target 
    WHERE company_unique_id IS NOT NULL 
    LIMIT 5
""")
print('=== company_target sample ===')
for r in cur.fetchall():
    print(f"outreach_id={r['outreach_id']}, company_unique_id={r['company_unique_id']}")

# Check outreach table schema
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'outreach' 
    ORDER BY ordinal_position
""")
print()
print('=== outreach.outreach columns ===')
for r in cur.fetchall():
    print(f"  {r['column_name']}")

# Check if outreach table has company_unique_id
cur.execute("""
    SELECT outreach_id, company_unique_id 
    FROM outreach.outreach 
    WHERE company_unique_id IS NOT NULL 
    LIMIT 5
""")
print()
print('=== outreach.outreach sample ===')
for r in cur.fetchall():
    print(f"outreach_id={r['outreach_id']}, company_unique_id={r['company_unique_id']}")

# Count outreach records with company_unique_id
cur.execute("""
    SELECT COUNT(*) as cnt 
    FROM outreach.outreach 
    WHERE company_unique_id IS NOT NULL
""")
print(f"\nOutreach records with company_unique_id: {cur.fetchone()['cnt']}")

cur.close()
conn.close()
