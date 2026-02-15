#!/usr/bin/env python3
"""
Link outreach_ids to EINs from DOL match file.
Updates outreach.outreach.ein for matched records.
"""
import csv
import psycopg2
import os
import re

def normalize_domain(d):
    if not d:
        return ''
    d = d.lower().strip()
    d = d.replace('https://', '').replace('http://', '')
    if d.startswith('www.'):
        d = d[4:]
    d = d.split('/')[0].split(':')[0]
    return d

def normalize_phone(phone):
    if not phone:
        return ''
    return re.sub(r'\D', '', str(phone))[-10:]

# Load DOL file
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

# Build lookups
dol_by_domain = {}
dol_by_phone = {}

for row in dol_rows:
    domain = normalize_domain(row.get('Domain name', ''))
    phone = normalize_phone(row.get('phone', ''))
    ein = row.get('ein', '').strip()
    
    if domain and ein:
        dol_by_domain[domain] = ein
    if len(phone) == 10 and ein:
        dol_by_phone[phone] = ein

print(f'DOL domains with EIN: {len(dol_by_domain):,}')
print(f'DOL phones with EIN: {len(dol_by_phone):,}')

# Connect to DB
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get all outreach with Hunter phones
cur.execute('''
    SELECT o.outreach_id, o.domain, hc.phone_number
    FROM outreach.outreach o
    LEFT JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE o.domain IS NOT NULL AND o.ein IS NULL
''')
outreach_data = cur.fetchall()

# Dedupe
outreach_by_id = {}
for oid, domain, phone in outreach_data:
    if oid not in outreach_by_id:
        outreach_by_id[oid] = {'domain': domain, 'phones': set()}
    if phone:
        outreach_by_id[oid]['phones'].add(normalize_phone(phone))

print(f'Outreach records without EIN: {len(outreach_by_id):,}')

# Find matches
updates = []

for oid, data in outreach_by_id.items():
    ein = None
    match_type = None
    
    # Try domain first
    domain = normalize_domain(data['domain'])
    if domain in dol_by_domain:
        ein = dol_by_domain[domain]
        match_type = 'domain'
    
    # Try phone if no domain match
    if not ein:
        for phone in data['phones']:
            if phone in dol_by_phone:
                ein = dol_by_phone[phone]
                match_type = 'phone'
                break
    
    if ein:
        updates.append((ein, oid, match_type, data['domain']))

print(f'\nMatches found: {len(updates):,}')

# Execute updates
if updates:
    print('\nUpdating outreach.outreach.ein...')
    for ein, oid, match_type, domain in updates:
        cur.execute('''
            UPDATE outreach.outreach 
            SET ein = %s 
            WHERE outreach_id = %s
        ''', (ein, oid))
    
    conn.commit()
    print(f'Updated {len(updates)} records')
    
    # Show what was updated
    print('\nUPDATED RECORDS:')
    for ein, oid, match_type, domain in updates[:20]:
        print(f'  {domain:<35} | EIN: {ein} | via {match_type}')
    if len(updates) > 20:
        print(f'  ... and {len(updates) - 20} more')

# Verify
cur.execute('SELECT COUNT(*) FROM outreach.outreach WHERE ein IS NOT NULL')
print(f'\nTotal outreach records with EIN: {cur.fetchone()[0]:,}')

conn.close()
