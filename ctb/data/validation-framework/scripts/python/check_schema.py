#!/usr/bin/env python3
"""Check actual schema of company_master and people_master"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

print("company_master columns:")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name = 'company_master'
    ORDER BY ordinal_position
""")

for col, dtype in cursor.fetchall():
    print(f"  - {col} ({dtype})")

print("\npeople_master columns:")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name = 'people_master'
    ORDER BY ordinal_position
""")

for col, dtype in cursor.fetchall():
    print(f"  - {col} ({dtype})")

cursor.close()
conn.close()
