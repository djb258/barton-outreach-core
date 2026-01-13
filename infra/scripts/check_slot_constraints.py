#!/usr/bin/env python3
"""Check people.company_slot constraints."""

import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

database_url = os.getenv("DATABASE_URL")
import psycopg2
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Check constraints
print("=== CONSTRAINTS ON people.company_slot ===")
cursor.execute("""
    SELECT conname, contype, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'people.company_slot'::regclass
""")
for row in cursor.fetchall():
    contype_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'c': 'CHECK', 'f': 'FOREIGN KEY'}
    print(f"  {row[0]}: {contype_map.get(row[1], row[1])} - {row[2]}")

# Check indexes
print("\n=== INDEXES ON people.company_slot ===")
cursor.execute("""
    SELECT indexname, indexdef
    FROM pg_indexes
    WHERE tablename = 'company_slot' AND schemaname = 'people'
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

cursor.close()
conn.close()
