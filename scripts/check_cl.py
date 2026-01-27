#!/usr/bin/env python3
"""Check cl.company_identity structure and EIN coverage"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'cl' AND table_name = 'company_identity' 
    ORDER BY ordinal_position
""")
print('cl.company_identity columns:')
for r in cur.fetchall():
    print(f'  {r[0]}')

print()

# Count total
cur.execute('SELECT COUNT(*) FROM cl.company_identity')
total = cur.fetchone()[0]
print(f'Total: {total:,}')

# Check if EIN column exists
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'cl' AND table_name = 'company_identity' 
    AND column_name LIKE '%ein%'
""")
ein_cols = [r[0] for r in cur.fetchall()]
print(f'EIN columns: {ein_cols}')

cur.close()
conn.close()
