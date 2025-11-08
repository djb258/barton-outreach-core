#!/usr/bin/env python3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("[*] Resetting promoted status...")

cursor.execute("UPDATE marketing.company_invalid SET promoted_to = NULL, promoted_at = NULL")
cursor.execute("UPDATE marketing.people_invalid SET promoted_to = NULL, promoted_at = NULL")

conn.commit()

cursor.execute("SELECT COUNT(*) FROM marketing.company_invalid WHERE promoted_to IS NULL")
company_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM marketing.people_invalid WHERE promoted_to IS NULL")
people_count = cursor.fetchone()[0]

print(f"[+] Reset complete!")
print(f"[+] Companies ready: {company_count}")
print(f"[+] People ready: {people_count}")

conn.close()
