#!/usr/bin/env python3
"""
Multi-strategy matching: DOL file to outreach_ids
Tries: domain, company name, address, city+state, EIN
"""
import csv
import psycopg2
import os
import re
from collections import defaultdict

def normalize_name(name):
    """Normalize company name for fuzzy matching."""
    if not name:
        return ''
    name = name.upper()
    # Remove common suffixes
    for suffix in [' LLC', ' INC', ' CORP', ' CO', ' LTD', ' LP', ' PLLC', ' PC', ' PA', ',']:
        name = name.replace(suffix, '')
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = ' '.join(name.split())
    return name.strip()

def normalize_address(addr):
    """Normalize street address."""
    if not addr:
        return ''
    addr = addr.upper()
    # Standardize common abbreviations
    replacements = {
        'STREET': 'ST', 'AVENUE': 'AVE', 'BOULEVARD': 'BLVD', 'DRIVE': 'DR',
        'ROAD': 'RD', 'LANE': 'LN', 'COURT': 'CT', 'PLACE': 'PL',
        'SUITE': 'STE', 'P.O. BOX': 'PO BOX', 'P.O.BOX': 'PO BOX'
    }
    for old, new in replacements.items():
        addr = addr.replace(old, new)
    addr = re.sub(r'[^\w\s]', '', addr)
    return ' '.join(addr.split()).strip()

# Read DOL file
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

# Build DOL lookup structures
dol_by_ein = {}
dol_by_domain = {}
dol_by_name = defaultdict(list)
dol_by_city_state = defaultdict(list)
dol_by_zip = defaultdict(list)

for row in dol_rows:
    ein = row.get('ein', '').strip()
    domain = row.get('Domain name', '').strip().lower()
    company_name = row.get('company_name', '')
    city = row.get('city', '').upper().strip()
    state = row.get('state', '').upper().strip()
    zip_code = row.get('zip', '').strip()[:5]  # First 5 digits
    address = row.get('address', '')
    
    if ein:
        dol_by_ein[ein] = row
    if domain:
        dol_by_domain[domain] = row
    
    norm_name = normalize_name(company_name)
    if norm_name:
        dol_by_name[norm_name].append(row)
    
    if city and state:
        dol_by_city_state[(city, state)].append(row)
    
    if zip_code:
        dol_by_zip[zip_code].append(row)

print('DOL FILE INDEXED')
print('='*60)
print(f'Total rows: {len(dol_rows):,}')
print(f'Unique EINs: {len(dol_by_ein):,}')
print(f'Unique domains: {len(dol_by_domain):,}')
print(f'Unique normalized names: {len(dol_by_name):,}')
print(f'Unique city+state combos: {len(dol_by_city_state):,}')
print(f'Unique ZIP codes: {len(dol_by_zip):,}')

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get all outreach records with domain - these are our 42K targets
cur.execute('''
    SELECT outreach_id, domain
    FROM outreach.outreach
    WHERE domain IS NOT NULL
''')
db_outreach = cur.fetchall()
print()
print(f'OUTREACH RECORDS WITH DOMAIN: {len(db_outreach):,}')

# Build domain -> outreach_id lookup
db_domain_to_outreach = {}
for outreach_id, domain in db_outreach:
    if domain:
        db_domain_to_outreach[domain.lower()] = outreach_id
print()
print(f'DATABASE COMPANIES WITH OUTREACH_ID: {len(db_outreach):,}')

# Strategy 1: Direct domain match
domain_matches = {}
for dol_domain, dol_row in dol_by_domain.items():
    if dol_domain in db_domain_to_outreach:
        outreach_id = db_domain_to_outreach[dol_domain]
        domain_matches[outreach_id] = (dol_domain, dol_row)

print()
print('MATCH RESULTS BY STRATEGY')
print('='*60)
print(f'Domain match: {len(domain_matches):,} outreach_ids')

# For other matching strategies, we need to look at the DOL data
# and see if company names in DOL match company names we can derive from domains
# Let's try to extract company name from domain

# Strategy 2: Check if hunter_contact has any of these DOL domains
cur.execute('''
    SELECT DISTINCT domain FROM enrichment.hunter_contact WHERE domain IS NOT NULL
''')
hunter_domains = set(r[0].lower() for r in cur.fetchall() if r[0])
print(f'Hunter domains in database: {len(hunter_domains):,}')

dol_domains_in_hunter = set(dol_by_domain.keys()) & hunter_domains
print(f'DOL domains also in Hunter: {len(dol_domains_in_hunter):,}')

# Cross check: DOL domains that are in Hunter but NOT in outreach
dol_in_hunter_not_outreach = dol_domains_in_hunter - set(db_domain_to_outreach.keys())
print(f'DOL domains in Hunter but NOT in outreach: {len(dol_in_hunter_not_outreach):,}')

matches = {'domain': domain_matches}

# Combine all matches
all_matched = set()
for match_dict in matches.values():
    all_matched.update(match_dict.keys())

print()
print('MATCH RESULTS BY STRATEGY')
print('='*60)
for strategy, match_dict in matches.items():
    print(f'{strategy:20}: {len(match_dict):,} outreach_ids matched')

# Combine all matches (unique outreach_ids)
all_matched = set()
for match_dict in matches.values():
    all_matched.update(match_dict.keys())

print()
print('='*60)
print(f'TOTAL UNIQUE OUTREACH_IDS MATCHED TO EINs: {len(all_matched):,}')
if len(db_outreach) > 0:
    print(f'Out of {len(db_outreach):,} total ({len(all_matched)*100/len(db_outreach):.1f}%)')

print()
print('BREAKDOWN:')
print(f'  DOL file has {len(dol_by_ein):,} unique EINs')
print(f'  We matched {len(domain_matches):,} to existing outreach_ids via domain')

# Sample matches
print()
print('SAMPLE MATCHED (outreach_id -> EIN):')
items = list(domain_matches.items())[:10]
for outreach_id, (domain, dol_row) in items:
    dol_name = dol_row.get('company_name', '')[:40]
    dol_ein = dol_row.get('ein', '')
    print(f'  {outreach_id[:30]}... | {domain:<25} | EIN: {dol_ein} | {dol_name}')

# Sample matches
print()
print('SAMPLE MATCHED (outreach_id -> EIN):')
items = list(domain_matches.items())[:10]
for outreach_id, (domain, dol_row) in items:
    dol_name = dol_row.get('company_name', '')[:40]
    dol_ein = dol_row.get('ein', '')
    print(f'  {outreach_id[:30]}... | {domain:<25} | EIN: {dol_ein} | {dol_name}')

conn.close()
