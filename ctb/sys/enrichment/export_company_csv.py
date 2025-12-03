#!/usr/bin/env python3
"""
Export company.company_master to CSV for matching analysis.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import csv
from datetime import datetime

NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

OUTPUT_FILE = 'ctb/sys/enrichment/output/company_master_export.csv'

print("Exporting company.company_master to CSV...")

conn = psycopg2.connect(**NEON_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Export query - get all relevant columns
cur.execute("""
    SELECT
        company_unique_id,
        company_name,
        website_url,
        linkedin_url,
        ein,
        address_city,
        address_state,
        employee_count,
        industry,
        source_system
    FROM company.company_master
    ORDER BY address_state, company_name
""")

records = cur.fetchall()
print(f"Fetched {len(records):,} companies")

# Write to CSV
with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
    if records:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)

print(f"Exported to: {OUTPUT_FILE}")
print(f"Total records: {len(records):,}")

# Summary stats
cur.execute("""
    SELECT
        address_state,
        COUNT(*) as count,
        SUM(CASE WHEN ein IS NOT NULL THEN 1 ELSE 0 END) as has_ein,
        SUM(CASE WHEN website_url IS NOT NULL THEN 1 ELSE 0 END) as has_url
    FROM company.company_master
    GROUP BY address_state
    ORDER BY count DESC
""")

print("\nBreakdown by state:")
for row in cur.fetchall():
    print(f"  {row['address_state']:2} | {row['count']:6,} companies | EIN: {row['has_ein']:5,} ({100*row['has_ein']/row['count']:5.1f}%) | URL: {row['has_url']:5,} ({100*row['has_url']/row['count']:5.1f}%)")

conn.close()
print("\nDone!")

