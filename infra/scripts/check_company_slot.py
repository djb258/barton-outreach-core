#!/usr/bin/env python3
"""Check people.company_slot structure."""

import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

database_url = os.getenv("DATABASE_URL")
import psycopg2
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# Check people.company_slot columns
print("=== people.company_slot COLUMNS ===")
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'people' AND table_name = 'company_slot'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable={row[2]}, default={row[3]})")

# Check company.company_slots columns
print("\n=== company.company_slots COLUMNS ===")
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'company' AND table_name = 'company_slots'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} (nullable={row[2]}, default={row[3]})")

# Check existing triggers on people.company_slot
print("\n=== TRIGGERS ON people.company_slot ===")
cursor.execute("""
    SELECT trigger_name, event_manipulation, action_timing
    FROM information_schema.triggers
    WHERE event_object_schema = 'people' AND event_object_table = 'company_slot'
""")
triggers = cursor.fetchall()
if triggers:
    for row in triggers:
        print(f"  {row[0]}: {row[2]} {row[1]}")
else:
    print("  (no triggers)")

# Sample data
print("\n=== SAMPLE DATA FROM people.company_slot (5 rows) ===")
cursor.execute("SELECT * FROM people.company_slot LIMIT 5")
cols = [desc[0] for desc in cursor.description]
print(f"  Columns: {cols}")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.close()
conn.close()
