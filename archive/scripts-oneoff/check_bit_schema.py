#!/usr/bin/env python3
"""Check BIT tables schema and data."""

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

# Check bit_scores schema
cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'bit_scores'
    ORDER BY ordinal_position
""")
print('=== outreach.bit_scores schema ===')
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

# Check bit_signals schema
cur.execute("""
    SELECT column_name, data_type, is_nullable 
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'bit_signals'
    ORDER BY ordinal_position
""")
print()
print('=== outreach.bit_signals schema ===')
for r in cur.fetchall():
    print(f"  {r['column_name']}: {r['data_type']}")

# Count signals by type
cur.execute('SELECT signal_type, COUNT(*) as cnt FROM outreach.bit_signals GROUP BY signal_type')
print()
print('=== Signal counts by type ===')
for r in cur.fetchall():
    print(f"  {r['signal_type']}: {r['cnt']}")

# Total signals
cur.execute('SELECT COUNT(*) as cnt FROM outreach.bit_signals')
print(f"\nTotal signals: {cur.fetchone()['cnt']}")

# Sample scores
cur.execute('SELECT * FROM outreach.bit_scores LIMIT 5')
print()
print('=== Sample bit_scores ===')
for r in cur.fetchall():
    print(dict(r))

# Check for companies with company_unique_id
cur.execute("""
    SELECT COUNT(DISTINCT company_unique_id) as companies_with_id
    FROM outreach.company_target 
    WHERE company_unique_id IS NOT NULL
""")
print(f"\nCompanies with company_unique_id: {cur.fetchone()['companies_with_id']}")

cur.close()
conn.close()
