#!/usr/bin/env python3
"""Check if Hunter DOL domains match outreach and can link EINs."""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Check outreach columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'outreach' AND table_name = 'outreach'")
print('outreach.outreach columns:', [r[0] for r in cur.fetchall()])
print()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'outreach' AND table_name = 'dol'")
print('outreach.dol columns:', [r[0] for r in cur.fetchall()])
print()

# Domains that ARE in outreach from Hunter results
matches = [
    ('scsglobalservices.com', '412261159'),  # Wrong company match
    ('11thhourstaffing.com', '263831039'),   # Correct
    ('1seo.com', '921929641'),               # Correct
    ('1spatial.com', '541558482'),           # Correct
]

print('='*70)
print('HUNTER DOMAINS vs OUTREACH - EIN CHECK')
print('='*70)

for domain, dol_ein in matches:
    cur.execute('''
        SELECT o.outreach_id, d.ein 
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        WHERE LOWER(o.domain) = LOWER(%s)
    ''', (domain,))
    row = cur.fetchone()
    if row:
        oid, existing_ein = row
        if existing_ein:
            match_status = 'MATCH' if existing_ein == dol_ein else f'MISMATCH (has {existing_ein})'
            print(f'{domain:30} | DOL EIN: {dol_ein} | {match_status}')
        else:
            print(f'{domain:30} | DOL EIN: {dol_ein} | NO EIN - CAN LINK!')
    else:
        print(f'{domain:30} | NOT FOUND IN OUTREACH')

conn.close()
