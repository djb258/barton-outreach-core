#!/usr/bin/env python3
"""Export first 1000 DOL records needing URLs to CSV for Clay testing"""
import psycopg2
import os
import csv

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

states = ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE']
states_str = ','.join([f"'{s}'" for s in states])

# Get unmatched DOL records (5500 + 5500-SF combined)
query = f"""
WITH matched_eins AS (
    SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
),
dol_5500 AS (
    SELECT DISTINCT ON (sponsor_dfe_ein)
        sponsor_dfe_ein as ein,
        sponsor_dfe_name as company_name,
        spons_dfe_mail_us_address1 as address1,
        spons_dfe_mail_us_address2 as address2,
        spons_dfe_mail_us_city as city,
        spons_dfe_mail_us_state as state,
        spons_dfe_mail_us_zip as zip,
        spons_dfe_phone_num as phone,
        'form_5500' as source
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IN ({states_str})
    AND sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
    ORDER BY sponsor_dfe_ein, date_received DESC
),
dol_sf AS (
    SELECT DISTINCT ON (sf_spons_ein)
        sf_spons_ein as ein,
        sf_sponsor_name as company_name,
        sf_spons_us_address1 as address1,
        sf_spons_us_address2 as address2,
        sf_spons_us_city as city,
        sf_spons_us_state as state,
        sf_spons_us_zip as zip,
        sf_spons_phone_num as phone,
        'form_5500_sf' as source
    FROM dol.form_5500_sf
    WHERE sf_spons_us_state IN ({states_str})
    AND sf_spons_ein NOT IN (SELECT ein FROM matched_eins)
    AND sf_spons_ein NOT IN (SELECT ein FROM dol_5500)
    ORDER BY sf_spons_ein, date_received DESC
)
SELECT * FROM dol_5500
UNION ALL
SELECT * FROM dol_sf
LIMIT 1000
"""

cur.execute(query)
rows = cur.fetchall()

# Write CSV
output_path = 'scripts/dol_url_discovery_sample.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ein', 'company_name', 'address1', 'address2', 'city', 'state', 'zip', 'phone', 'source'])
    for row in rows:
        writer.writerow(row)

print(f"Exported {len(rows)} records to {output_path}")
print()
print("Sample records:")
print("-" * 80)
for row in rows[:5]:
    print(f"  {row[1][:40]:<40} | {row[4]}, {row[5]} | EIN: {row[0]}")

cur.close()
conn.close()
