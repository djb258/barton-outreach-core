#!/usr/bin/env python3
"""
Export 25 DOL companies (without URLs) for Hunter.io testing.
Include: company name, address, city, state, zip, phone, EIN.
"""
import psycopg2
import os
import csv

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Check columns available
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_schema = 'dol' AND table_name = 'form_5500_sf'
        ORDER BY ordinal_position
    """)
    cols = [r[0] for r in cur.fetchall()]
    print("form_5500_sf columns:", cols)
    print()
    
    # Get 25 DOL records that DON'T have a URL yet
    # These are EINs not matched to outreach
    cur.execute("""
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
        ORDER BY sf.sf_sponsor_name
        LIMIT 25
    """)
    
    rows = cur.fetchall()
    print(f"Found {len(rows)} DOL companies needing URL lookup")
    print()
    
    # Export to CSV
    output_file = 'dol_test_25_for_hunter.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ein', 'company_name', 'address', 'city', 'state', 'zip', 'phone'])
        for row in rows:
            writer.writerow(row)
    
    print(f"Exported to: {output_file}")
    print()
    print("Sample data:")
    for row in rows[:5]:
        print(f"  {row[1][:40]:40} | {row[4]} | {row[6]}")
    
    conn.close()

if __name__ == '__main__':
    main()
