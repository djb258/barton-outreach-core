#!/usr/bin/env python3
"""Export 25 UNMATCHED DOL companies for Hunter testing."""
import psycopg2
import os
import csv

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get 25 DOL companies NOT matched to outreach (no URL in ein_urls)
cur.execute('''
    SELECT DISTINCT
        sf.sf_spons_ein,
        sf.sf_sponsor_name,
        sf.sf_spons_us_address1,
        sf.sf_spons_us_city,
        sf.sf_spons_us_state,
        sf.sf_spons_us_zip,
        sf.sf_spons_phone_num
    FROM dol.form_5500_sf sf
    LEFT JOIN dol.ein_urls eu ON sf.sf_spons_ein = eu.ein
    WHERE eu.ein IS NULL
    AND sf.sf_spons_us_state IN ('WV','VA','MD','OH','PA','KY','NC','DC')
    AND sf.sf_spons_phone_num IS NOT NULL
    AND sf.sf_spons_phone_num != ''
    AND sf.sf_sponsor_name NOT LIKE '1%'
    ORDER BY sf.sf_sponsor_name
    LIMIT 25
''')

rows = cur.fetchall()

with open('dol_unmatched_25.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ein', 'company_name', 'address', 'city', 'state', 'zip', 'phone'])
    for row in rows:
        writer.writerow(row)

print('Exported 25 UNMATCHED DOL companies to dol_unmatched_25.csv')
print()
for row in rows:
    name = row[1][:45] if row[1] else ''
    city = row[3][:15] if row[3] else ''
    state = row[4] if row[4] else ''
    print(f'{name:45} | {city:15} | {state}')

conn.close()
