#!/usr/bin/env python3
"""Check potential signal sources for BIT scoring."""

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

# 1. People/slot data (people_subhub generates slot_filled signals)
print('=== People tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND table_name LIKE '%people%'
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 2. Check people table schema
print('\n=== outreach.people columns ===')
try:
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'outreach' AND table_name = 'people'
        ORDER BY ordinal_position
    """)
    for r in cur.fetchall():
        print(f"  {r['column_name']}: {r['data_type']}")
except Exception as e:
    print(f"  Error: {e}")

# 3. Check people count
print('\n=== People counts ===')
try:
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT company_unique_id) as companies_with_people
        FROM outreach.people
    """)
    r = cur.fetchone()
    print(f"  Total people: {r['total']}")
    print(f"  Companies with people: {r['companies_with_people']}")
except Exception as e:
    print(f"  Error: {e}")

# 4. Check DOL tables
print('\n=== DOL tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND (table_name LIKE '%dol%' OR table_name LIKE '%5500%' OR table_name LIKE '%filing%')
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 5. Check company_lifecycle or DOL link table
print('\n=== Looking for company_lifecycle ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema IN ('outreach', 'public')
    AND (table_name LIKE '%lifecycle%' OR table_name LIKE '%company_cl%')
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 6. Check company_people_link or similar
print('\n=== Link tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND table_name LIKE '%link%'
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 7. Check slots
print('\n=== Slot tables ===')
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach' 
    AND table_name LIKE '%slot%'
    ORDER BY table_name
""")
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# 8. Sample from people if it exists
print('\n=== People sample (slot data) ===')
try:
    cur.execute("""
        SELECT company_unique_id, slot_name, email_status, slot_status
        FROM outreach.people
        WHERE company_unique_id IS NOT NULL
        AND slot_status IS NOT NULL
        LIMIT 5
    """)
    for r in cur.fetchall():
        print(f"  company={r['company_unique_id'][:8]}..., slot={r['slot_name']}, email={r['email_status']}, status={r['slot_status']}")
except Exception as e:
    print(f"  Error: {e}")

cur.close()
conn.close()
