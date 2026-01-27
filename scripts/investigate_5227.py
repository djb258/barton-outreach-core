"""
Deep investigation: Why can't 5,227 EINs match to outreach?
Are they unique companies not in the pipeline, or matching issues?
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('INVESTIGATING THE 5,227 UNMATCHED EINS')
print('='*70)

# Get the unmatched records
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
    SELECT cm.normalized_domain, cm.company_name, cm.ein, cm.website_url
    FROM cm_domains cm
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.outreach o WHERE o.domain = cm.normalized_domain
    )
""")
unmatched = cur.fetchall()
print(f'\nTotal unmatched: {len(unmatched):,}')

# Check what domains look like
print('\n[1] SAMPLE UNMATCHED DOMAINS:')
for domain, name, ein, url in unmatched[:15]:
    print(f'  Domain: "{domain}"')
    print(f'    URL: {url}')
    print(f'    Name: {name[:50] if name else "NULL"}')
    print(f'    EIN: {ein}')
    print()

# Check if it's a domain format issue - maybe outreach uses different format
print('\n[2] CHECKING OUTREACH DOMAIN FORMAT:')
cur.execute('SELECT domain FROM outreach.outreach LIMIT 10')
for (d,) in cur.fetchall():
    print(f'  outreach.domain: "{d}"')

# Check for partial matches
print('\n[3] CHECKING FOR PARTIAL DOMAIN MATCHES:')
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
    ),
    unmatched AS (
        SELECT cm.*
        FROM cm_domains cm
        WHERE NOT EXISTS (
            SELECT 1 FROM outreach.outreach o WHERE o.domain = cm.normalized_domain
        )
    )
    SELECT u.normalized_domain, u.company_name, o.domain as outreach_domain
    FROM unmatched u
    JOIN outreach.outreach o ON o.domain LIKE '%' || SPLIT_PART(u.normalized_domain, '.', 1) || '%'
    LIMIT 20
""")
partial = cur.fetchall()
print(f'Partial matches found: {len(partial)}')
for cm_domain, name, o_domain in partial[:10]:
    print(f'  CM: {cm_domain} → Outreach: {o_domain} | {name[:40] if name else ""}')

# Check if these companies exist in cl.company_identity by name
print('\n[4] CHECKING IF UNMATCHED EXIST IN CL BY NAME:')
cur.execute(r"""
    WITH cm_unmatched AS (
        SELECT 
            ein,
            company_name,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    ),
    unmatched AS (
        SELECT cm.*
        FROM cm_unmatched cm
        WHERE NOT EXISTS (
            SELECT 1 FROM outreach.outreach o WHERE o.domain = cm.normalized_domain
        )
    )
    SELECT COUNT(*) 
    FROM unmatched u
    WHERE EXISTS (
        SELECT 1 FROM cl.company_identity ci 
        WHERE LOWER(ci.company_name) = LOWER(u.company_name)
    )
""")
name_matches = cur.fetchone()[0]
print(f'Unmatched EINs that match CL by company name: {name_matches:,}')

# Check if these are companies we SHOULD have in outreach
print('\n[5] STATE DISTRIBUTION OF UNMATCHED:')
cur.execute(r"""
    WITH cm_unmatched AS (
        SELECT 
            ein,
            company_name,
            address_state,
            LOWER(REGEXP_REPLACE(
                REGEXP_REPLACE(website_url, '^https?://(www\.)?', ''),
                '/.*$', ''
            )) as normalized_domain
        FROM company.company_master
        WHERE ein IS NOT NULL AND website_url IS NOT NULL
    ),
    unmatched AS (
        SELECT cm.*
        FROM cm_unmatched cm
        WHERE NOT EXISTS (
            SELECT 1 FROM outreach.outreach o WHERE o.domain = cm.normalized_domain
        )
    )
    SELECT address_state, COUNT(*) as cnt
    FROM unmatched
    GROUP BY address_state
    ORDER BY cnt DESC
    LIMIT 15
""")
print('State distribution of unmatched EINs:')
for state, cnt in cur.fetchall():
    print(f'  {state if state else "NULL"}: {cnt:,}')

# Are these companies in the 51K at all? Check by normalized domain parts
print('\n[6] DEEPER DOMAIN ANALYSIS:')
cur.execute(r"""
    WITH cm_unmatched AS (
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
    unmatched AS (
        SELECT cm.*
        FROM cm_unmatched cm
        WHERE NOT EXISTS (
            SELECT 1 FROM outreach.outreach o WHERE o.domain = cm.normalized_domain
        )
    )
    SELECT 
        u.normalized_domain as cm_domain,
        u.website_url,
        o.domain as closest_outreach,
        ci.company_name as outreach_company
    FROM unmatched u
    LEFT JOIN LATERAL (
        SELECT domain FROM outreach.outreach 
        WHERE domain ILIKE '%' || SUBSTRING(u.normalized_domain FROM 1 FOR 5) || '%'
        LIMIT 1
    ) o ON true
    LEFT JOIN cl.company_identity ci ON ci.outreach_id = (
        SELECT outreach_id FROM outreach.outreach WHERE domain = o.domain LIMIT 1
    )
    WHERE o.domain IS NOT NULL
    LIMIT 15
""")
print('Possible domain mismatches:')
for cm_domain, url, o_domain, o_name in cur.fetchall():
    print(f'  CM: {cm_domain}')
    print(f'    URL: {url}')
    print(f'    Closest outreach: {o_domain} ({o_name[:30] if o_name else "?"})')
    print()

conn.close()
