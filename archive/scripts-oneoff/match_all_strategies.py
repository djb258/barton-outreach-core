#!/usr/bin/env python3
"""
Try all matching strategies and combine results
"""
import csv
import psycopg2
import os
import re
from collections import defaultdict

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

def normalize_name(name):
    if not name:
        return ''
    name = name.upper()
    for suffix in [' LLC', ' INC', ' CORP', ' CO', ' LTD', ' LP', ' PLLC', ' PC', ' PA', ',', '.']:
        name = name.replace(suffix, '')
    name = re.sub(r'[^\w\s]', '', name)
    return ' '.join(name.split()).strip()

# Load DOL
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

# Build all DOL lookups
dol_by_domain = {}
dol_by_phone = {}
dol_by_hunter_city_state = defaultdict(list)  # Hunter's City/State
dol_by_dol_city_state = defaultdict(list)     # DOL filing city/state

for row in dol_rows:
    domain = normalize_domain(row.get('Domain name', ''))
    phone = normalize_phone(row.get('phone', ''))
    
    # Hunter location (actual HQ)
    hunter_city = (row.get('City') or '').upper().strip()
    hunter_state = (row.get('State') or '').upper().strip()
    
    # DOL filing location
    dol_city = (row.get('city') or '').upper().strip()
    dol_state = (row.get('state') or '').upper().strip()
    
    hunter_org = normalize_name(row.get('Organization', ''))
    
    if domain:
        dol_by_domain[domain] = row
    if len(phone) == 10:
        dol_by_phone[phone] = row
    if hunter_city and hunter_state and hunter_org:
        dol_by_hunter_city_state[(hunter_city, hunter_state, hunter_org)].append(row)
    if dol_city and dol_state:
        dol_by_dol_city_state[(dol_city, dol_state)].append(row)

print('DOL INDEXES:')
print(f'  By domain: {len(dol_by_domain):,}')
print(f'  By phone: {len(dol_by_phone):,}')
print(f'  By Hunter city+state+org: {len(dol_by_hunter_city_state):,}')
print(f'  By DOL city+state: {len(dol_by_dol_city_state):,}')

# Connect to DB
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get outreach with Hunter data
cur.execute('''
    SELECT o.outreach_id, o.domain, hc.phone_number
    FROM outreach.outreach o
    LEFT JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
    WHERE o.domain IS NOT NULL
''')
outreach_data = cur.fetchall()
print(f'\nOUTREACH RECORDS: {len(outreach_data):,}')

# Dedupe by outreach_id
outreach_by_id = {}
for oid, domain, phone in outreach_data:
    if oid not in outreach_by_id:
        outreach_by_id[oid] = {'domain': domain, 'phones': set()}
    if phone:
        outreach_by_id[oid]['phones'].add(normalize_phone(phone))

print(f'Unique outreach_ids: {len(outreach_by_id):,}')

# MATCHING
matches = {}

# Strategy 1: Domain
for oid, data in outreach_by_id.items():
    domain = normalize_domain(data['domain'])
    if domain in dol_by_domain:
        dol_row = dol_by_domain[domain]
        matches[oid] = {
            'strategy': 'domain',
            'ein': dol_row.get('ein'),
            'dol_company': dol_row.get('company_name'),
            'matched_on': domain,
        }

print(f'\nStrategy 1 (domain): {len(matches):,}')

# Strategy 2: Phone
for oid, data in outreach_by_id.items():
    if oid in matches:
        continue
    for phone in data['phones']:
        if phone in dol_by_phone:
            dol_row = dol_by_phone[phone]
            matches[oid] = {
                'strategy': 'phone',
                'ein': dol_row.get('ein'),
                'dol_company': dol_row.get('company_name'),
                'matched_on': phone,
            }
            break

print(f'Strategy 2 (phone): {len(matches):,} total')

# RESULTS
print('\n' + '='*60)
print('FINAL RESULTS')
print('='*60)
print(f'Total outreach_ids matched to EIN: {len(matches):,}')
print(f'Out of {len(outreach_by_id):,} ({len(matches)*100/len(outreach_by_id):.2f}%)')

by_strategy = defaultdict(int)
for m in matches.values():
    by_strategy[m['strategy']] += 1
print('\nBy strategy:')
for s, c in sorted(by_strategy.items()):
    print(f'  {s}: {c:,}')

unique_eins = set(m['ein'] for m in matches.values() if m.get('ein'))
print(f'\nUnique EINs linked: {len(unique_eins):,}')

# Sample
print('\nSAMPLE MATCHES:')
for oid, data in list(matches.items())[:15]:
    dol_co = (data.get('dol_company') or '')[:30]
    ein = data.get('ein', '')
    strat = data.get('strategy', '')
    matched = data.get('matched_on', '')[:25]
    print(f'  {strat:<8} | {matched:<25} | EIN: {ein} | {dol_co}')

conn.close()
