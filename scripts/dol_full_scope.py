#!/usr/bin/env python3
"""
Count unmatched Form 5500 and 5500-SF records in target states
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

states = ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE']
states_str = ','.join([f"'{s}'" for s in states])

print('DOL Unmatched Records in Target States')
print('=' * 60)

# Form 5500 (larger companies)
cur.execute(f'''
    SELECT COUNT(DISTINCT d.sponsor_dfe_ein)
    FROM dol.form_5500 d
    WHERE d.spons_dfe_mail_us_state IN ({states_str})
    AND d.sponsor_dfe_ein NOT IN (
        SELECT ein FROM company.company_master WHERE ein IS NOT NULL
    )
''')
f5500_unmatched = cur.fetchone()[0]

# Form 5500-SF (smaller companies)
cur.execute(f'''
    SELECT COUNT(DISTINCT d.sf_spons_ein)
    FROM dol.form_5500_sf d
    WHERE d.sf_spons_us_state IN ({states_str})
    AND d.sf_spons_ein NOT IN (
        SELECT ein FROM company.company_master WHERE ein IS NOT NULL
    )
''')
sf_unmatched = cur.fetchone()[0]

print(f'Form 5500 (large):    {f5500_unmatched:,} unmatched EINs')
print(f'Form 5500-SF (small): {sf_unmatched:,} unmatched EINs')
print(f'COMBINED:             {f5500_unmatched + sf_unmatched:,}')
print()

# Check for overlap (EINs in both tables)
cur.execute(f'''
    WITH f5500_unmatched AS (
        SELECT DISTINCT sponsor_dfe_ein as ein
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state IN ({states_str})
        AND sponsor_dfe_ein NOT IN (
            SELECT ein FROM company.company_master WHERE ein IS NOT NULL
        )
    ),
    sf_unmatched AS (
        SELECT DISTINCT sf_spons_ein as ein
        FROM dol.form_5500_sf
        WHERE sf_spons_us_state IN ({states_str})
        AND sf_spons_ein NOT IN (
            SELECT ein FROM company.company_master WHERE ein IS NOT NULL
        )
    )
    SELECT COUNT(*) FROM (
        SELECT ein FROM f5500_unmatched
        INTERSECT
        SELECT ein FROM sf_unmatched
    ) overlap
''')
overlap = cur.fetchone()[0]

unique_total = f5500_unmatched + sf_unmatched - overlap
print(f'Overlap (in both):    {overlap:,}')
print(f'UNIQUE TOTAL:         {unique_total:,}')
print()

# Cost estimate
print('=' * 60)
print('Google Places Cost Estimate:')
print(f'  {unique_total:,} x $0.017 = ${unique_total * 0.017:,.2f}')
print('=' * 60)
print()

print('Breakdown by state:')
print('-' * 60)
print(f"{'State':<6} {'5500':>10} {'5500-SF':>12} {'Total':>10}")
print('-' * 60)

for state in states:
    cur.execute('''
        SELECT COUNT(DISTINCT sponsor_dfe_ein)
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = %s
        AND sponsor_dfe_ein NOT IN (
            SELECT ein FROM company.company_master WHERE ein IS NOT NULL
        )
    ''', (state,))
    f5500 = cur.fetchone()[0]
    
    cur.execute('''
        SELECT COUNT(DISTINCT sf_spons_ein)
        FROM dol.form_5500_sf
        WHERE sf_spons_us_state = %s
        AND sf_spons_ein NOT IN (
            SELECT ein FROM company.company_master WHERE ein IS NOT NULL
        )
    ''', (state,))
    sf = cur.fetchone()[0]
    
    print(f'{state:<6} {f5500:>10,} {sf:>12,} {f5500+sf:>10,}')

print('-' * 60)
print(f"{'TOTAL':<6} {f5500_unmatched:>10,} {sf_unmatched:>12,} {f5500_unmatched+sf_unmatched:>10,}")

cur.close()
conn.close()
