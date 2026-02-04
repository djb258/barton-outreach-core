#!/usr/bin/env python3
"""
FINAL DOL -> Outreach Match Analysis
Conservative matching to minimize false positives
"""
import csv
import psycopg2
import os
import re
from collections import defaultdict

def normalize_name(name):
    if not name:
        return ''
    name = name.upper()
    for suffix in [' LLC', ' INC', ' CORP', ' CO', ' LTD', ' LP', ' PLLC', ' PC', ' PA', ',', '.']:
        name = name.replace(suffix, '')
    name = re.sub(r'[^\w\s]', '', name)
    return ' '.join(name.split()).strip()

def extract_domain_base(domain):
    """Extract meaningful part of domain"""
    if not domain:
        return ''
    # Remove TLD
    base = domain.lower()
    for tld in ['.com', '.org', '.net', '.io', '.co', '.us', '.edu']:
        base = base.replace(tld, '')
    return base

dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

# Build DOL lookups
dol_by_domain = {}
dol_by_ein = {}
ein_to_row = {}

for row in dol_rows:
    domain = row.get('Domain name', '').strip().lower()
    ein = row.get('ein', '').strip()
    
    if domain:
        dol_by_domain[domain] = row
    if ein:
        if ein not in ein_to_row:  # First occurrence
            ein_to_row[ein] = row

print('DOL MATCH FILE')
print('='*60)
print(f'Total rows: {len(dol_rows):,}')
print(f'Unique EINs: {len(ein_to_row):,}')
print(f'Unique domains: {len(dol_by_domain):,}')

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get all outreach domains
cur.execute('SELECT outreach_id, domain FROM outreach.outreach WHERE domain IS NOT NULL')
db_outreach = cur.fetchall()
print(f'\nOUTREACH COMPANIES: {len(db_outreach):,}')

# Build lookup
outreach_domain_to_id = {d.lower(): oid for oid, d in db_outreach if d}

# MATCHING STRATEGIES
matches = {}

# Strategy 1: Exact domain match (HIGH CONFIDENCE)
print('\n' + '='*60)
print('STRATEGY 1: Exact Domain Match')
for dol_domain, dol_row in dol_by_domain.items():
    if dol_domain in outreach_domain_to_id:
        outreach_id = outreach_domain_to_id[dol_domain]
        matches[outreach_id] = {
            'strategy': 'domain',
            'confidence': 'HIGH',
            'ein': dol_row.get('ein'),
            'dol_company': dol_row.get('company_name'),
            'domain': dol_domain,
        }
print(f'Matches: {len(matches):,}')

# Strategy 2: Domain base equals Hunter Organization normalized
# e.g., domain "abcinc.com" matches Hunter org "ABC Inc"
print('\nSTRATEGY 2: Domain base = Hunter Org name')
hunter_org_to_domain = {}
for row in dol_rows:
    hunter_org = normalize_name(row.get('Organization', ''))
    domain = row.get('Domain name', '').strip().lower()
    if hunter_org and domain:
        hunter_org_to_domain[hunter_org] = row

strategy2_new = 0
for outreach_id, domain in db_outreach:
    if outreach_id in matches:
        continue
    if not domain:
        continue
    
    # Normalize domain to company-like name
    domain_base = extract_domain_base(domain)
    domain_norm = normalize_name(domain_base.replace('-', ' ').replace('_', ' '))
    
    if domain_norm in hunter_org_to_domain:
        dol_row = hunter_org_to_domain[domain_norm]
        matches[outreach_id] = {
            'strategy': 'domain_org_name',
            'confidence': 'MEDIUM',
            'ein': dol_row.get('ein'),
            'dol_company': dol_row.get('company_name'),
            'domain': domain,
            'hunter_org': dol_row.get('Organization'),
        }
        strategy2_new += 1

print(f'New matches: {strategy2_new:,}')

# FINAL SUMMARY
print('\n' + '='*60)
print('FINAL RESULTS')
print('='*60)
print(f'Total outreach_ids matched to EINs: {len(matches):,}')
print(f'Out of {len(db_outreach):,} ({len(matches)*100/len(db_outreach):.2f}%)')

by_confidence = defaultdict(list)
for oid, data in matches.items():
    by_confidence[data['confidence']].append(oid)

print('\nBy confidence:')
for conf, oids in sorted(by_confidence.items()):
    print(f'  {conf}: {len(oids):,}')

by_strategy = defaultdict(list)
for oid, data in matches.items():
    by_strategy[data['strategy']].append(oid)

print('\nBy strategy:')
for strat, oids in sorted(by_strategy.items()):
    print(f'  {strat}: {len(oids):,}')

# Sample output
print('\nSAMPLE MATCHES:')
for i, (oid, data) in enumerate(list(matches.items())[:15]):
    dol_co = (data.get('dol_company') or '')[:35]
    ein = data.get('ein', '')
    domain = data.get('domain', '')
    conf = data.get('confidence', '')
    print(f'  {domain:<30} | EIN: {ein} | {conf:<6} | {dol_co}')

# EINs matched
unique_eins = set(m['ein'] for m in matches.values() if m.get('ein'))
print(f'\nUnique EINs linked: {len(unique_eins):,}')

conn.close()
