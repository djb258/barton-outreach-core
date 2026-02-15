#!/usr/bin/env python3
"""Check column types for proper join"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'company' AND table_name = 'company_master' 
    AND column_name = 'company_unique_id'
""")
print('company.company_master.company_unique_id:', cur.fetchone())

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'cl' AND table_name = 'company_identity' 
    AND column_name = 'company_unique_id'
""")
print('cl.company_identity.company_unique_id:', cur.fetchone())

# Check what links them
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'cl' AND table_name = 'company_identity'
    ORDER BY ordinal_position
""")
print()
print("cl.company_identity columns:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

cur.close()
conn.close()
