"""Investigate the 74K company.company_master table"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('INVESTIGATING company.company_master (74K records)')
print('='*70)

# Total count
cur.execute('SELECT COUNT(*) FROM company.company_master')
print(f'Total records: {cur.fetchone()[0]:,}')

# Source breakdown
print('\nBy source_system:')
cur.execute('SELECT source_system, COUNT(*) FROM company.company_master GROUP BY source_system ORDER BY COUNT(*) DESC')
for src, cnt in cur.fetchall():
    print(f'  {src if src else "NULL"}: {cnt:,}')

# Import batch breakdown
print('\nBy import_batch_id (top 10):')
cur.execute('SELECT import_batch_id, COUNT(*) FROM company.company_master GROUP BY import_batch_id ORDER BY COUNT(*) DESC LIMIT 10')
for batch, cnt in cur.fetchall():
    print(f'  {batch if batch else "NULL"}: {cnt:,}')

# ID format analysis
print('\ncompany_unique_id format samples:')
cur.execute('SELECT company_unique_id FROM company.company_master LIMIT 10')
for (cuid,) in cur.fetchall():
    print(f'  {cuid}')

# Check created_at range
print('\nDate range:')
cur.execute('SELECT MIN(created_at), MAX(created_at) FROM company.company_master')
min_dt, max_dt = cur.fetchone()
print(f'  Oldest: {min_dt}')
print(f'  Newest: {max_dt}')

# EIN coverage
print('\nEIN coverage:')
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
with_ein = cur.fetchone()[0]
print(f'  With EIN: {with_ein:,}')

# Now compare to the ACTUAL master - outreach.outreach
print('\n' + '='*70)
print('THE REAL MASTER: outreach.outreach')
print('='*70)

cur.execute('SELECT COUNT(*) FROM outreach.outreach')
print(f'outreach.outreach: {cur.fetchone()[0]:,}')

cur.execute('SELECT COUNT(*) FROM outreach.company_target')
print(f'outreach.company_target: {cur.fetchone()[0]:,}')

# Sample from each
print('\nSample company_master records:')
cur.execute("""
    SELECT company_unique_id, company_name, source_system
    FROM company.company_master
    LIMIT 5
""")
for cuid, name, src in cur.fetchall():
    name_trunc = (name[:35] + '...') if name and len(name) > 35 else name
    print(f'  ID: {cuid}')
    print(f'  Name: {name_trunc}')
    print(f'  Source: {src}')
    print()

print('\nSample outreach records (the REAL data):')
cur.execute("""
    SELECT ct.outreach_id, ct.company_unique_id, ci.company_name, o.domain
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
    JOIN cl.company_identity ci ON ct.outreach_id = ci.outreach_id
    LIMIT 5
""")
for oid, cuid, name, domain in cur.fetchall():
    name_trunc = (name[:35] + '...') if name and len(name) > 35 else name
    print(f'  outreach_id: {oid}')
    print(f'  company_unique_id: {cuid}')
    print(f'  Name: {name_trunc}')
    print(f'  Domain: {domain}')
    print()

conn.close()
