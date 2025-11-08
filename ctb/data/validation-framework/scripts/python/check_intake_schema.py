#!/usr/bin/env python3
import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("intake.company_raw_intake columns:")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'intake'
    AND table_name = 'company_raw_intake'
    ORDER BY ordinal_position
""")

for col, dtype in cursor.fetchall():
    print(f"  - {col} ({dtype})")

# Sample data
print("\nSample data (first 2 rows):")
cursor.execute("SELECT * FROM intake.company_raw_intake LIMIT 2")
rows = cursor.fetchall()
cursor.execute("""
    SELECT column_name FROM information_schema.columns
    WHERE table_schema = 'intake' AND table_name = 'company_raw_intake'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cursor.fetchall()]

for row in rows:
    print("\nRecord:")
    for i, col in enumerate(cols):
        print(f"  {col}: {row[i]}")

cursor.close()
conn.close()
