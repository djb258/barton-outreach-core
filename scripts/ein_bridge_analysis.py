"""
Analyze how to connect the 23K EINs from company.company_master 
to outreach.dol (the DOL sub-hub)
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('EIN BRIDGE ANALYSIS: company_master → outreach.dol')
print('='*70)

# Current state of outreach.dol
print('\n[1] CURRENT outreach.dol STATUS:')
cur.execute('SELECT COUNT(*) FROM outreach.dol')
total_dol = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL')
with_ein = cur.fetchone()[0]
print(f'  Total records: {total_dol:,}')
print(f'  With EIN: {with_ein:,}')
print(f'  Without EIN: {total_dol - with_ein:,}')

# company_master EINs
print('\n[2] company.company_master EINs:')
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
cm_ein = cur.fetchone()[0]
print(f'  Records with EIN: {cm_ein:,}')

# What do we have to match on?
print('\n[3] MATCHING STRATEGY - Check available fields:')

# Does company_master have domain/website?
cur.execute("""
    SELECT COUNT(*) FROM company.company_master 
    WHERE ein IS NOT NULL AND website_url IS NOT NULL
""")
print(f'  company_master with EIN + website_url: {cur.fetchone()[0]:,}')

# Get outreach domains
print('\n[4] DOMAIN MATCHING TEST:')

# Normalize domains and try to match
cur.execute("""
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
    ),
    outreach_domains AS (
        SELECT 
            o.outreach_id,
            o.domain,
            ci.company_name
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.outreach_id = ci.outreach_id
    )
    SELECT COUNT(DISTINCT od.outreach_id)
    FROM outreach_domains od
    JOIN cm_domains cm ON od.domain = cm.normalized_domain
""")
domain_matches = cur.fetchone()[0]
print(f'  Outreach records matching company_master by domain: {domain_matches:,}')

# How many of those already have EIN in outreach.dol?
cur.execute("""
    WITH cm_domains AS (
        SELECT 
            ein,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    ),
    outreach_domains AS (
        SELECT 
            o.outreach_id,
            o.domain
        FROM outreach.outreach o
    )
    SELECT COUNT(DISTINCT od.outreach_id)
    FROM outreach_domains od
    JOIN cm_domains cm ON od.domain = cm.normalized_domain
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = od.outreach_id AND d.ein IS NOT NULL
    )
""")
new_ein_matches = cur.fetchone()[0]
print(f'  Of those, without EIN in outreach.dol: {new_ein_matches:,}')

# Sample matches
print('\n[5] SAMPLE MATCHES:')
cur.execute("""
    WITH cm_domains AS (
        SELECT 
            ein,
            company_name as cm_name,
            website_url,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    ),
    outreach_data AS (
        SELECT 
            o.outreach_id,
            o.domain,
            ci.company_name as outreach_name
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.outreach_id = ci.outreach_id
    )
    SELECT 
        od.outreach_id,
        od.domain,
        od.outreach_name,
        cm.cm_name,
        cm.ein
    FROM outreach_data od
    JOIN cm_domains cm ON od.domain = cm.normalized_domain
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = od.outreach_id AND d.ein IS NOT NULL
    )
    LIMIT 10
""")

for oid, domain, oname, cmname, ein in cur.fetchall():
    print(f'  Domain: {domain}')
    print(f'    Outreach: {oname[:40] if oname else "NULL"}')
    print(f'    Clay: {cmname[:40] if cmname else "NULL"}')
    print(f'    EIN: {ein}')
    print()

# Summary
print('='*70)
print('SUMMARY:')
print('='*70)
print(f'''
Current EIN coverage in outreach.dol: {with_ein:,} / {total_dol:,}
EINs available in company_master: {cm_ein:,}
Matchable by domain (NEW): {new_ein_matches:,}

PROPOSED ACTION:
- Match company_master to outreach via domain
- INSERT new records into outreach.dol with the EIN
- This would add ~{new_ein_matches:,} EINs to the DOL sub-hub
''')

conn.close()
