#!/usr/bin/env python3
"""Check company_master details"""

import os, psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

print("COMPANY_MASTER Statistics:")
print("=" * 60)

# Total count
cursor.execute("SELECT COUNT(*) FROM marketing.company_master")
total = cursor.fetchone()[0]
print(f"Total Companies: {total}\n")

# Count by state
cursor.execute("""
    SELECT address_state, COUNT(*) as count
    FROM marketing.company_master
    WHERE address_state IS NOT NULL
    GROUP BY address_state
    ORDER BY count DESC
    LIMIT 10
""")

print("Top 10 States:")
print("-" * 60)
for state, count in cursor.fetchall():
    print(f"  {state}: {count} companies")

# Check WV specifically
cursor.execute("""
    SELECT COUNT(*)
    FROM marketing.company_master
    WHERE address_state = 'WV'
""")
wv_count = cursor.fetchone()[0]
print(f"\nWest Virginia (WV): {wv_count} companies")

# Sample WV companies
if wv_count > 0:
    print("\nSample WV Companies:")
    print("-" * 60)
    cursor.execute("""
        SELECT company_name, website_url, address_city
        FROM marketing.company_master
        WHERE address_state = 'WV'
        LIMIT 5
    """)
    for name, website, city in cursor.fetchall():
        print(f"  - {name} | {website} | {city}, WV")

# Check for validation_status column
cursor.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'marketing'
    AND table_name = 'company_master'
    AND column_name IN ('validation_status', 'validated_at', 'batch_id')
""")

validation_cols = [row[0] for row in cursor.fetchall()]
print(f"\nValidation columns present: {validation_cols}")

cursor.close()
conn.close()
