#!/usr/bin/env python3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("\n[*] Checking Neon for enriched records...")

cursor.execute("""
    SELECT id, company_name, domain, validation_status, updated_at
    FROM marketing.company_invalid
    WHERE validation_status = 'READY'
    ORDER BY updated_at DESC
    LIMIT 5
""")

results = cursor.fetchall()

if results:
    print(f"\n[+] Found {len(results)} READY companies in Neon:")
    for row in results:
        print(f"   ID {row[0]}: {row[1]} | {row[2]} | {row[3]} | Updated: {row[4]}")
else:
    print("\n[!] No READY companies found in Neon")

conn.close()
