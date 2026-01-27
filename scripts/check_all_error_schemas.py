#!/usr/bin/env python3
"""Check all error table schemas."""

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

tables = [
    'outreach.company_target_errors',
    'outreach.dol_errors',
    'outreach.people_errors',
    'outreach.blog_errors',
    'outreach.bit_errors',
    'outreach.outreach_errors',
]

for table in tables:
    schema, table_name = table.split('.')
    print(f'\n=== {table} ===')
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
    """, (schema, table_name))
    for r in cur.fetchall():
        print(f"  {r['column_name']}: {r['data_type']}")

cur.close()
conn.close()
