#!/usr/bin/env python3
"""Check Barton ID constraint"""

import os, psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# Get constraint definition
cursor.execute("""
    SELECT
        con.conname AS constraint_name,
        pg_get_constraintdef(con.oid) AS constraint_definition
    FROM pg_constraint con
    JOIN pg_class rel ON rel.oid = con.conrelid
    JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
    WHERE nsp.nspname = 'marketing'
    AND rel.relname = 'company_master'
    AND con.contype = 'c'
""")

print("Check Constraints on company_master:")
print("=" * 70)
for name, definition in cursor.fetchall():
    print(f"\n{name}:")
    print(f"  {definition}")

# Check existing IDs format
print("\n\nExisting Barton IDs (sample):")
print("=" * 70)
cursor.execute("""
    SELECT company_unique_id, company_name
    FROM marketing.company_master
    LIMIT 10
""")

for uid, name in cursor.fetchall():
    print(f"  {uid} - {name}")

cursor.close()
conn.close()
