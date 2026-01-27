#!/usr/bin/env python3
"""Get sample DOL records for enrichment testing."""
import os
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get DOL records that are NOT in company_master - enrichment candidates
cur.execute("""
    SELECT 
        d.sponsor_dfe_ein as ein,
        d.sponsor_dfe_name as company_name,
        d.spons_dfe_mail_us_city as city,
        d.spons_dfe_mail_us_state as state,
        d.spons_dfe_mail_us_zip as zip
    FROM dol.form_5500 d
    WHERE d.spons_dfe_mail_us_state IN ('NC', 'PA', 'OH', 'VA')
    AND d.sponsor_dfe_ein IS NOT NULL
    AND d.sponsor_dfe_ein NOT IN (
        SELECT ein FROM company.company_master WHERE ein IS NOT NULL
    )
    ORDER BY d.sponsor_dfe_name
    LIMIT 10
""")

print('='*80)
print('SAMPLE DOL RECORDS - CANDIDATES FOR ENRICHMENT')
print('These have EINs but are NOT in company_master')
print('='*80)

for row in cur.fetchall():
    ein, name, city, state, zip_code = row
    print(f"""
EIN:     {ein}
Company: {name}
City:    {city}
State:   {state}
ZIP:     {zip_code}
---""")

cur.close()
conn.close()
