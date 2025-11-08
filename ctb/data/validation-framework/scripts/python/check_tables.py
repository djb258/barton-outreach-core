#!/usr/bin/env python3
"""Check if validation tables exist in Neon"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

print("Checking validation tables...\n")

# Check for validation tables
cursor.execute("""
    SELECT
        table_schema,
        table_name
    FROM information_schema.tables
    WHERE table_schema IN ('shq', 'marketing')
    AND table_name IN ('validation_log', 'company_invalid', 'people_invalid',
                       'company_raw_wv', 'people_raw_wv',
                       'company_master', 'people_master')
    ORDER BY table_schema, table_name
""")

tables = cursor.fetchall()

if tables:
    print("Tables found:")
    for schema, table in tables:
        print(f"  {schema}.{table}")
else:
    print("No tables found!")

# Check WV data counts
print("\nChecking WV data counts...")

try:
    cursor.execute("SELECT COUNT(*) FROM marketing.company_raw_wv WHERE state = 'WV'")
    company_count = cursor.fetchone()[0]
    print(f"  company_raw_wv (WV): {company_count} records")
except:
    print("  company_raw_wv: Table not found or error")

try:
    cursor.execute("SELECT COUNT(*) FROM marketing.people_raw_wv WHERE state = 'WV'")
    people_count = cursor.fetchone()[0]
    print(f"  people_raw_wv (WV): {people_count} records")
except:
    print("  people_raw_wv: Table not found or error")

cursor.close()
conn.close()
