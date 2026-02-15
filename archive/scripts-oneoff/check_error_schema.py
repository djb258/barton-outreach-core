#!/usr/bin/env python3
"""Check error table schemas and sample data."""

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

# Check company_target_errors schema (representative)
print('=== outreach.company_target_errors columns ===')
cur.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'company_target_errors'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']} (nullable={r['is_nullable']})")

# Check error counts per table
print('\n=== Error Counts Per Table ===')
error_tables = [
    'outreach.company_target_errors',
    'outreach.dol_errors',
    'outreach.people_errors',
    'outreach.blog_errors',
    'outreach.bit_errors',
    'outreach.outreach_errors',
]
for table in error_tables:
    try:
        cur.execute(f"SELECT COUNT(*) as cnt FROM {table}")
        print(f"  {table}: {cur.fetchone()['cnt']}")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

# Check shq.error_master schema
print('\n=== shq.error_master columns ===')
try:
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_schema = 'shq' AND table_name = 'error_master'
        ORDER BY ordinal_position
    """)
    for r in cur.fetchall():
        print(f"  {r['column_name']}: {r['data_type']} (nullable={r['is_nullable']})")
except Exception as e:
    print(f"  ERROR: {e}")

# Sample from company_target_errors
print('\n=== Sample company_target_errors ===')
cur.execute("""
    SELECT * FROM outreach.company_target_errors LIMIT 3
""")
for r in cur.fetchall():
    print(f"  {dict(r)}")

cur.close()
conn.close()
