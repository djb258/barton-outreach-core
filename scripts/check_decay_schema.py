#!/usr/bin/env python3
"""Check bit_signals schema for decay implementation."""

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

print('=== bit_signals columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'bit_signals'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

print('\n=== bit_scores columns ===')
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'bit_scores'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

# Check if there's a last_signal_at or similar timestamp
print('\n=== Looking for freshness tracking ===')
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' 
    AND table_name IN ('bit_scores', 'bit_signals')
    AND (column_name LIKE '%time%' OR column_name LIKE '%at%' OR column_name LIKE '%date%')
""")
for r in cur.fetchall():
    print(f"  {r['column_name']}")

cur.close()
conn.close()
