#!/usr/bin/env python3
"""Deep dive into why we can't match more companies."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*80)
    print('DEEP DIVE: Why cant we match more?')
    print('='*80)

    # 1. How many companies without EIN are in states we have 5500 data for?
    print()
    print('1. STATE COVERAGE ANALYSIS:')
    print('-'*60)
    cur.execute('''
        WITH cm_states AS (
            SELECT address_state, COUNT(*) as cnt
            FROM company.company_master
            WHERE ein IS NULL
            GROUP BY address_state
        ),
        f5500_states AS (
            SELECT DISTINCT spons_dfe_mail_us_state as state
            FROM dol.form_5500
            UNION
            SELECT DISTINCT sf_spons_us_state as state
            FROM dol.form_5500_sf
        )
        SELECT 
            cm.address_state,
            cm.cnt as companies_without_ein,
            CASE WHEN f.state IS NOT NULL THEN 'YES' ELSE 'NO' END as in_5500
        FROM cm_states cm
        LEFT JOIN f5500_states f ON cm.address_state = f.state
        ORDER BY cm.cnt DESC
        LIMIT 20
    ''')
    print('  State | Companies w/o EIN | In 5500?')
    print('  ------+-------------------+---------')
    for r in cur.fetchall():
        print(f'  {r[0]:5} | {r[1]:17,} | {r[2]}')

    # 2. Sample unmatched companies - what do their names look like?
    print()
    print('2. SAMPLE UNMATCHED COMPANIES (random):')
    print('-'*60)
    cur.execute('''
        SELECT company_name, address_city, address_state
        FROM company.company_master
        WHERE ein IS NULL
        ORDER BY RANDOM()
        LIMIT 20
    ''')
    for r in cur.fetchall():
        city = r[1] if r[1] else ''
        print(f'  {r[0][:50]:50} | {city[:20]:20} | {r[2]}')

    # 3. Check for exact name matches we might be missing
    print()
    print('3. EXACT NAME MATCHES (case-insensitive):')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(*)
        FROM company.company_master cm
        WHERE cm.ein IS NULL
        AND EXISTS (
            SELECT 1 FROM dol.form_5500 f
            WHERE UPPER(f.sponsor_dfe_name) = UPPER(cm.company_name)
            AND f.spons_dfe_mail_us_state = cm.address_state
        )
    ''')
    r = cur.fetchone()
    print(f'  Exact matches in form_5500: {r[0]:,}')

    cur.execute('''
        SELECT COUNT(*)
        FROM company.company_master cm
        WHERE cm.ein IS NULL
        AND EXISTS (
            SELECT 1 FROM dol.form_5500_sf f
            WHERE UPPER(f.sf_sponsor_name) = UPPER(cm.company_name)
            AND f.sf_spons_us_state = cm.address_state
        )
    ''')
    r = cur.fetchone()
    print(f'  Exact matches in form_5500_sf: {r[0]:,}')

    # 4. Check similarity score distribution for near-misses
    print()
    print('4. NEAR-MISS ANALYSIS (0.50-0.84 similarity):')
    print('-'*60)
    cur.execute('''
        WITH sample_companies AS (
            SELECT company_name, address_state, address_city
            FROM company.company_master
            WHERE ein IS NULL
            ORDER BY RANDOM()
            LIMIT 100
        )
        SELECT 
            cm.company_name,
            f.sponsor_dfe_name,
            SIMILARITY(UPPER(cm.company_name), UPPER(f.sponsor_dfe_name)) as sim
        FROM sample_companies cm
        CROSS JOIN LATERAL (
            SELECT sponsor_dfe_name
            FROM dol.form_5500
            WHERE spons_dfe_mail_us_state = cm.address_state
            ORDER BY SIMILARITY(UPPER(sponsor_dfe_name), UPPER(cm.company_name)) DESC
            LIMIT 1
        ) f
        WHERE SIMILARITY(UPPER(cm.company_name), UPPER(f.sponsor_dfe_name)) BETWEEN 0.50 AND 0.84
        ORDER BY sim DESC
        LIMIT 15
    ''')
    print('  Company Name                           | 5500 Name                           | Sim')
    print('  ---------------------------------------+-------------------------------------+-----')
    for r in cur.fetchall():
        print(f'  {r[0][:39]:39} | {r[1][:37]:37} | {r[2]:.2f}')

    # 5. Companies that might be subsidiaries or DBAs
    print()
    print('5. POTENTIAL SUBSIDIARY/DBA PATTERNS:')
    print('-'*60)
    cur.execute('''
        SELECT company_name
        FROM company.company_master
        WHERE ein IS NULL
        AND (
            company_name ILIKE '%dba %'
            OR company_name ILIKE '% llc'
            OR company_name ILIKE '% inc'
            OR company_name ILIKE '% corp'
            OR company_name ILIKE '% of %'
        )
        ORDER BY RANDOM()
        LIMIT 15
    ''')
    print('  Sample companies with subsidiary/DBA patterns:')
    for r in cur.fetchall():
        print(f'    {r[0]}')

    # 6. Check if companies exist in 5500 with DIFFERENT state
    print()
    print('6. CROSS-STATE MATCHING POTENTIAL:')
    print('-'*60)
    cur.execute('''
        SELECT COUNT(*)
        FROM company.company_master cm
        WHERE cm.ein IS NULL
        AND EXISTS (
            SELECT 1 FROM dol.form_5500 f
            WHERE UPPER(f.sponsor_dfe_name) = UPPER(cm.company_name)
            AND f.spons_dfe_mail_us_state != cm.address_state
        )
    ''')
    r = cur.fetchone()
    print(f'  Companies with exact name match but DIFFERENT state: {r[0]:,}')
    
    # Sample
    cur.execute('''
        SELECT DISTINCT cm.company_name, cm.address_state as cm_state, f.spons_dfe_mail_us_state as f5500_state
        FROM company.company_master cm
        JOIN dol.form_5500 f ON UPPER(f.sponsor_dfe_name) = UPPER(cm.company_name)
        WHERE cm.ein IS NULL
        AND f.spons_dfe_mail_us_state != cm.address_state
        LIMIT 10
    ''')
    if cur.rowcount > 0:
        print()
        print('  Examples:')
        for r in cur.fetchall():
            print(f'    {r[0][:40]:40} | Our: {r[1]} | 5500: {r[2]}')

    # 7. Name normalization issues
    print()
    print('7. NAME NORMALIZATION ISSUES:')
    print('-'*60)
    cur.execute('''
        SELECT company_name
        FROM company.company_master
        WHERE ein IS NULL
        AND (
            company_name ~ '[0-9]{4,}'  -- Has 4+ digit numbers
            OR company_name ~ '^The '   -- Starts with The
            OR company_name ~ ', Inc\\.'  -- Has ", Inc."
            OR company_name ~ '&'       -- Has ampersand
        )
        ORDER BY RANDOM()
        LIMIT 15
    ''')
    print('  Companies with potential normalization issues:')
    for r in cur.fetchall():
        print(f'    {r[0]}')

    conn.close()

if __name__ == '__main__':
    main()
