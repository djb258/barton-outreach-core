#!/usr/bin/env python3
"""Check DOL data for signal sources."""

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

# 1. DOL schema
print('=== outreach.dol columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'dol'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

# 2. DOL count
print('\n=== DOL counts ===')
cur.execute("SELECT COUNT(*) as total FROM outreach.dol")
print(f"  Total DOL records: {cur.fetchone()['total']}")

# 3. DOL sample
print('\n=== DOL sample ===')
cur.execute("SELECT * FROM outreach.dol LIMIT 3")
for r in cur.fetchall():
    print(f"  {dict(r)}")

# 4. Check blog table
print('\n=== Blog tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND table_name LIKE '%blog%'
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 5. Check blog count
print('\n=== Blog counts ===')
try:
    cur.execute("SELECT COUNT(*) as total FROM outreach.blog")
    print(f"  Total blog records: {cur.fetchone()['total']}")
except Exception as e:
    print(f"  Error: {e}")

# 6. Check events table
print('\n=== Event tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND table_name LIKE '%event%'
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 7. Get company_unique_ids that exist in company_target
print('\n=== Companies in company_target ===')
cur.execute("""
    SELECT COUNT(*) as total FROM outreach.company_target WHERE company_unique_id IS NOT NULL
""")
print(f"  Companies with company_unique_id: {cur.fetchone()['total']}")

# 8. Check if outreach_id maps back
print('\n=== Sample company_target with outreach_id ===')
cur.execute("""
    SELECT outreach_id, company_unique_id, outreach_status, bit_score_snapshot
    FROM outreach.company_target
    WHERE company_unique_id IS NOT NULL
    LIMIT 5
""")
for r in cur.fetchall():
    print(f"  outreach_id={r['outreach_id']}, company={r['company_unique_id'][:12]}..., status={r['outreach_status']}, bit={r['bit_score_snapshot']}")

cur.close()
conn.close()
