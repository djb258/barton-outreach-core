#!/usr/bin/env python3
"""Check error tables in the database."""

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

# Find all _errors tables
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name LIKE '%error%'
    ORDER BY table_schema, table_name
""")
print('=== Error Tables ===')
for r in cur.fetchall():
    print(f"  {r['table_schema']}.{r['table_name']}")

# Check outreach_errors schema
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach_errors'
    ORDER BY table_name
""")
print('\n=== outreach_errors schema ===')
for r in cur.fetchall():
    print(f"  {r['table_name']}")

# Check outreach error tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach'
    AND table_name LIKE '%error%'
    ORDER BY table_name
""")
print('\n=== outreach schema error tables ===')
for r in cur.fetchall():
    print(f"  {r['table_name']}")

cur.close()
conn.close()
