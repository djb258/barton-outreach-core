#!/usr/bin/env python3
"""
Count DOL records needing URL discovery in target states
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Target states
states = ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE']
states_str = ','.join([f"'{s}'" for s in states])

print("DOL URL Discovery Scope Analysis")
print("=" * 60)

# Count DOL records in target states NOT in company_master
cur.execute(f'''
    SELECT COUNT(DISTINCT d.sponsor_dfe_ein)
    FROM dol.form_5500 d
    WHERE d.spons_dfe_mail_us_state IN ({states_str})
    AND d.sponsor_dfe_ein NOT IN (
        SELECT ein FROM company.company_master WHERE ein IS NOT NULL
    )
''')
unmatched = cur.fetchone()[0]
print(f'DOL EINs in target states NOT in company_master: {unmatched:,}')

# How many already have URLs via EIN match?
cur.execute(f'''
    SELECT COUNT(DISTINCT d.sponsor_dfe_ein)
    FROM dol.form_5500 d
    JOIN company.company_master cm ON d.sponsor_dfe_ein = cm.ein
    WHERE d.spons_dfe_mail_us_state IN ({states_str})
    AND cm.website_url IS NOT NULL
''')
with_urls = cur.fetchone()[0]
print(f'DOL EINs in target states WITH URLs (via company_master): {with_urls:,}')

# Total DOL in target states
cur.execute(f'''
    SELECT COUNT(DISTINCT sponsor_dfe_ein)
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IN ({states_str})
''')
total = cur.fetchone()[0]
print(f'Total DOL EINs in target states: {total:,}')

print()
print("=" * 60)
print(f'NEED URL DISCOVERY: {unmatched:,} companies')
print(f'At 5,000/day Yelp limit = {unmatched // 5000 + 1} days')
print("=" * 60)

# Breakdown by state
print("\nBreakdown by state (unmatched):")
for state in states:
    cur.execute(f'''
        SELECT COUNT(DISTINCT d.sponsor_dfe_ein)
        FROM dol.form_5500 d
        WHERE d.spons_dfe_mail_us_state = %s
        AND d.sponsor_dfe_ein NOT IN (
            SELECT ein FROM company.company_master WHERE ein IS NOT NULL
        )
    ''', (state,))
    count = cur.fetchone()[0]
    print(f'  {state}: {count:,}')

cur.close()
conn.close()
