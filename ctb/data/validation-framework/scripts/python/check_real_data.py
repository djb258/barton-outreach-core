#!/usr/bin/env python3
"""Check actual data tables and record counts"""

import os, psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("Checking marketing schema tables with record counts:\n")

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'marketing'
    AND table_type = 'BASE TABLE'
    AND (table_name LIKE '%company%' OR table_name LIKE '%people%' OR table_name LIKE '%person%')
    ORDER BY table_name
""")

tables = cursor.fetchall()

print("COMPANY TABLES:")
print("-" * 60)
for (table_name,) in tables:
    if 'company' in table_name.lower():
        try:
            cursor.execute(f'SELECT COUNT(*) FROM marketing."{table_name}"')
            count = cursor.fetchone()[0]
            print(f"  marketing.{table_name}: {count:,} records")
        except Exception as e:
            print(f"  marketing.{table_name}: Error - {e}")

print("\nPEOPLE TABLES:")
print("-" * 60)
for (table_name,) in tables:
    if 'people' in table_name.lower() or 'person' in table_name.lower():
        try:
            cursor.execute(f'SELECT COUNT(*) FROM marketing."{table_name}"')
            count = cursor.fetchone()[0]
            print(f"  marketing.{table_name}: {count:,} records")
        except Exception as e:
            print(f"  marketing.{table_name}: Error - {e}")

# Check intake schema too
print("\nINTAKE SCHEMA:")
print("-" * 60)
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'intake'
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")

intake_tables = cursor.fetchall()
for (table_name,) in intake_tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM intake."{table_name}"')
        count = cursor.fetchone()[0]
        print(f"  intake.{table_name}: {count:,} records")
    except Exception as e:
        print(f"  intake.{table_name}: Error")

cursor.close()
conn.close()
