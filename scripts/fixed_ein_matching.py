"""
Fix the domain matching to handle www. prefix differences
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('FIXED DOMAIN MATCHING (handles www. prefix)')
print('='*70)

# Normalize BOTH sides - strip www. from both
cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            company_name,
            website_url,
            -- Strip www. and protocol, get base domain
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                    '/.*$', ''
                ),
                '^www\.', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    ),
    outreach_domains AS (
        SELECT 
            outreach_id,
            domain,
            -- Strip www. from outreach domain too
            LOWER(REGEXP_REPLACE(domain, '^www\.', '')) as normalized_domain
        FROM outreach.outreach
    )
    SELECT 
        COUNT(DISTINCT cm.ein) as matched_eins,
        COUNT(DISTINCT od.outreach_id) as matched_outreach
    FROM cm_domains cm
    JOIN outreach_domains od ON cm.normalized_domain = od.normalized_domain
""")
matched_eins, matched_outreach = cur.fetchone()
print(f'\nWith fixed matching:')
print(f'  EINs matched: {matched_eins:,}')
print(f'  Outreach records matched: {matched_outreach:,}')

# How many already in outreach.dol?
cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                    '/.*$', ''
                ),
                '^www\.', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    ),
    outreach_domains AS (
        SELECT 
            outreach_id,
            LOWER(REGEXP_REPLACE(domain, '^www\.', '')) as normalized_domain
        FROM outreach.outreach
    )
    SELECT COUNT(DISTINCT cm.ein)
    FROM cm_domains cm
    JOIN outreach_domains od ON cm.normalized_domain = od.normalized_domain
    WHERE EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = od.outreach_id AND d.ein IS NOT NULL
    )
""")
already_in_dol = cur.fetchone()[0]
print(f'  Already in outreach.dol: {already_in_dol:,}')
print(f'  NEW to add: {matched_eins - already_in_dol:,}')

# Still unmatched?
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
total_eins = cur.fetchone()[0]
still_unmatched = total_eins - matched_eins
print(f'\nStill unmatched: {still_unmatched:,}')

# What are those?
print('\n[STILL UNMATCHED - Companies NOT in 51K outreach]:')
cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            company_name,
            website_url,
            address_state,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                    '/.*$', ''
                ),
                '^www\.', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL
    ),
    outreach_domains AS (
        SELECT 
            LOWER(REGEXP_REPLACE(domain, '^www\.', '')) as normalized_domain
        FROM outreach.outreach
    )
    SELECT cm.normalized_domain, cm.company_name, cm.ein, cm.address_state
    FROM cm_domains cm
    WHERE cm.normalized_domain IS NOT NULL 
    AND cm.normalized_domain != ''
    AND NOT EXISTS (
        SELECT 1 FROM outreach_domains od WHERE od.normalized_domain = cm.normalized_domain
    )
    LIMIT 30
""")
print('\nSample companies with EIN that are NOT in the 51K outreach pipeline:')
for domain, name, ein, state in cur.fetchall():
    print(f'  {domain} | {state} | {ein} | {name[:40] if name else ""}')

# Summary
print('\n' + '='*70)
print('SUMMARY WITH FIXED MATCHING')
print('='*70)

cur.execute('SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL')
current_dol = cur.fetchone()[0]

new_eins = matched_eins - already_in_dol

print(f'''
Total EINs in company_master: {total_eins:,}
  - Matched to outreach (fixed): {matched_eins:,}
  - Already in outreach.dol: {already_in_dol:,}
  - NEW to add: {new_eins:,}
  - Cannot match (not in 51K): {still_unmatched:,}

Current outreach.dol EINs: {current_dol:,}
After migration: {current_dol + new_eins:,}
''')

conn.close()
