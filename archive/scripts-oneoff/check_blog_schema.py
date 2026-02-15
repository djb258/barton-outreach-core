#!/usr/bin/env python3
"""Check blog table schema."""

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

print('=== outreach.blog columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'blog'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

print('\n=== Sample blog record ===')
cur.execute("SELECT * FROM outreach.blog LIMIT 1")
for r in cur.fetchall():
    print(f"  {dict(r)}")

cur.close()
conn.close()
