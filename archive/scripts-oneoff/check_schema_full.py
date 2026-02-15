#!/usr/bin/env python3
"""Check company_target schema and hub_registry."""

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

# 1. company_target schema
print('=== company_target columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'company_target'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

# 2. Check hub_registry
print('\n=== hub_registry contents ===')
cur.execute("""
    SELECT hub_name, hub_type, sovereign_required, tier_unlock
    FROM outreach.hub_registry
    ORDER BY hub_name
""")
for r in cur.fetchall():
    print(f"  {r['hub_name']}: type={r['hub_type']}, required={r['sovereign_required']}, unlock={r['tier_unlock']}")

# 3. Check sovereign_completion_view or hub status tables
print('\n=== Looking for hub status storage ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND (table_name LIKE '%hub%' 
         OR table_name LIKE '%status%'
         OR table_name LIKE '%completion%')
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 4. Check views
print('\n=== Outreach views ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.views 
    WHERE table_schema = 'outreach' 
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

cur.close()
conn.close()
