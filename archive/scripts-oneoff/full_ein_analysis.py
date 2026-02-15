"""
Full analysis: How many of the 23K EINs can match to the 51K outreach records?
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('FULL EIN MATCHING ANALYSIS')
print('='*70)

# Total EINs in company_master
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
total_eins = cur.fetchone()[0]
print(f'\nTotal EINs in company.company_master: {total_eins:,}')

# How many have website_url to match on?
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL AND website_url IS NOT NULL')
with_url = cur.fetchone()[0]
print(f'With website_url: {with_url:,}')
print(f'Without website_url (cannot match): {total_eins - with_url:,}')

# Normalize and match
print('\n[1] DOMAIN MATCHING TO OUTREACH:')

cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            company_name,
            website_url,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    )
    SELECT COUNT(DISTINCT cm.ein)
    FROM cm_domains cm
    JOIN outreach.outreach o ON o.domain = cm.normalized_domain
""")
matched_eins = cur.fetchone()[0]
print(f'EINs that match an outreach domain: {matched_eins:,}')
print(f'EINs that do NOT match any outreach domain: {with_url - matched_eins:,}')

# Of those that match, how many already in outreach.dol?
cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    )
    SELECT COUNT(DISTINCT cm.ein)
    FROM cm_domains cm
    JOIN outreach.outreach o ON o.domain = cm.normalized_domain
    WHERE EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = o.outreach_id AND d.ein IS NOT NULL
    )
""")
already_in_dol = cur.fetchone()[0]
print(f'\nOf those, already have EIN in outreach.dol: {already_in_dol:,}')
print(f'NEW EINs to add to outreach.dol: {matched_eins - already_in_dol:,}')

# Why don't the others match?
print('\n[2] ANALYZING NON-MATCHES:')

cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            company_name,
            website_url,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    )
    SELECT cm.normalized_domain, cm.company_name, cm.ein
    FROM cm_domains cm
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.domain = cm.normalized_domain
    )
    LIMIT 20
""")

print('\nSample EINs with domains NOT in outreach (first 20):')
for domain, name, ein in cur.fetchall():
    name_short = (name[:35] + '...') if name and len(name) > 35 else name
    print(f'  {domain} | {ein} | {name_short}')

# Summary
print('\n' + '='*70)
print('SUMMARY')
print('='*70)

cur.execute('SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL')
current_dol_eins = cur.fetchone()[0]

new_eins = matched_eins - already_in_dol

print(f'''
company.company_master EINs: {total_eins:,}
  - With website_url: {with_url:,}
  - Match outreach domain: {matched_eins:,}
  - Already in outreach.dol: {already_in_dol:,}
  - NEW to add: {new_eins:,}

Current outreach.dol EINs: {current_dol_eins:,}
After migration: {current_dol_eins + new_eins:,}

EINs that CANNOT be connected (domain not in 51K): {with_url - matched_eins:,}
''')

conn.close()
