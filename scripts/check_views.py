#!/usr/bin/env python3
"""Check hub_registry schema and sovereign completion view."""

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

# 1. hub_registry schema
print('=== hub_registry columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'hub_registry'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

# 2. hub_registry data
print('\n=== hub_registry contents ===')
cur.execute("SELECT * FROM outreach.hub_registry ORDER BY hub_name")
for r in cur.fetchall():
    print(f"  {dict(r)}")

# 3. All outreach views
print('\n=== All outreach views ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.views 
    WHERE table_schema = 'outreach' 
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 4. Check vw_sovereign_completion
print('\n=== vw_sovereign_completion sample ===')
try:
    cur.execute("""
        SELECT * FROM outreach.vw_sovereign_completion LIMIT 3
    """)
    for r in cur.fetchall():
        print(f"  {dict(r)}")
except Exception as e:
    print(f"  Error: {e}")

# 5. Check vw_marketing_eligibility
print('\n=== vw_marketing_eligibility_with_overrides sample ===')
try:
    cur.execute("""
        SELECT * FROM outreach.vw_marketing_eligibility_with_overrides LIMIT 3
    """)
    for r in cur.fetchall():
        print(f"  {dict(r)}")
except Exception as e:
    print(f"  Error: {e}")

cur.close()
conn.close()
