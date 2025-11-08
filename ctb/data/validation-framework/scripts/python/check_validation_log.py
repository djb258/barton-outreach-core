#!/usr/bin/env python3
import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("public.shq_validation_log columns:")
cursor.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'shq_validation_log'
    ORDER BY ordinal_position
""")

for col, dtype in cursor.fetchall():
    print(f"  - {col} ({dtype})")

cursor.close()
conn.close()
