"""
Migration: Add 4,398 EINs from company.company_master to outreach.dol
Matches via normalized domain (handles www. prefix differences)
"""
import psycopg2
import os
from datetime import datetime

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('EIN MIGRATION: company_master → outreach.dol')
print(f'Started: {datetime.now()}')
print('='*70)

# First check current state
cur.execute('SELECT COUNT(*) FROM outreach.dol')
before_total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL')
before_ein = cur.fetchone()[0]
print(f'\nBEFORE: outreach.dol has {before_total:,} rows, {before_ein:,} with EIN')

# Get the EINs to insert
cur.execute(r"""
    WITH cm_domains AS (
        SELECT 
            ein,
            company_name as cm_company_name,
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
            LOWER(REGEXP_REPLACE(domain, '^www\.', '')) as normalized_domain
        FROM outreach.outreach
    )
    SELECT DISTINCT 
        od.outreach_id,
        cm.ein,
        cm.cm_company_name
    FROM cm_domains cm
    JOIN outreach_domains od ON cm.normalized_domain = od.normalized_domain
    WHERE NOT EXISTS (
        SELECT 1 FROM outreach.dol d 
        WHERE d.outreach_id = od.outreach_id
    )
""")

to_insert = cur.fetchall()
print(f'\nRecords to INSERT: {len(to_insert):,}')

# Show sample
print('\nSample (first 10):')
for oid, ein, name in to_insert[:10]:
    print(f'  {oid} | {ein} | {name[:40] if name else ""}')

# Confirm and insert
print('\n' + '-'*70)
print('INSERTING...')

inserted = 0
for outreach_id, ein, company_name in to_insert:
    try:
        cur.execute("""
            INSERT INTO outreach.dol (outreach_id, ein, created_at, updated_at)
            VALUES (%s, %s, NOW(), NOW())
        """, (outreach_id, ein))
        inserted += 1
    except Exception as e:
        print(f'  Error inserting {outreach_id}: {e}')

conn.commit()

# Verify
cur.execute('SELECT COUNT(*) FROM outreach.dol')
after_total = cur.fetchone()[0]
cur.execute('SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL')
after_ein = cur.fetchone()[0]

print(f'\nAFTER: outreach.dol has {after_total:,} rows, {after_ein:,} with EIN')
print(f'\nSUMMARY:')
print(f'  Inserted: {inserted:,}')
print(f'  EIN coverage: {before_ein:,} → {after_ein:,} (+{after_ein - before_ein:,})')
print(f'  Coverage rate: {after_ein/51148*100:.1f}% of 51K outreach')

conn.close()
print(f'\nCompleted: {datetime.now()}')
