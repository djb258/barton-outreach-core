#!/usr/bin/env python3
import os, psycopg2, re
from dotenv import load_dotenv

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# Get max Barton ID
cursor.execute("""
    SELECT company_unique_id
    FROM marketing.company_master
    ORDER BY company_unique_id DESC
    LIMIT 10
""")

print("Highest Barton IDs:")
for (uid,) in cursor.fetchall():
    # Extract the number parts
    match = re.match(r'04\.04\.01\.(\d{2})\.(\d{5})\.(\d{3})', uid)
    if match:
        p1, p2, p3 = match.groups()
        print(f"  {uid} -> parts: {p1}, {p2}, {p3}")

# Check total count
cursor.execute("SELECT COUNT(*) FROM marketing.company_master")
print(f"\nTotal in company_master: {cursor.fetchone()[0]}")

cursor.close()
conn.close()
