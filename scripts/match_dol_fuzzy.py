#!/usr/bin/env python3
"""
Multi-strategy matching: DOL file to outreach_ids
Using Hunter's Organization name for fuzzy matching
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
    for suffix in [' LLC', ' INC', ' CORP', ' CO', ' LTD', ' LP', ' PLLC', ' PC', ' PA', ',', '.']:
        name = name.replace(suffix, '')
    # Remove punctuation
    name = re.sub(r'[^\w\s]', '', name)
    # Collapse whitespace
    name = ' '.join(name.split())
    return name.strip()

# Read DOL file
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

# Build DOL lookup structures - using HUNTER ORG name (not DOL company_name)
dol_by_domain = {}
dol_by_hunter_org = defaultdict(list)

for row in dol_rows:
    domain = row.get('Domain name', '').strip().lower()
    hunter_org = row.get('Organization', '')
    
    if domain:
        dol_by_domain[domain] = row
    
    norm_org = normalize_name(hunter_org)
    if norm_org:
        dol_by_hunter_org[norm_org].append(row)

print('DOL FILE INDEXED')
print('='*60)
print(f'Total rows: {len(dol_rows):,}')
print(f'Unique domains: {len(dol_by_domain):,}')
print(f'Unique Hunter org names (normalized): {len(dol_by_hunter_org):,}')

# Connect to database
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get all outreach domains
cur.execute('SELECT outreach_id, domain FROM outreach.outreach WHERE domain IS NOT NULL')
db_outreach = cur.fetchall()
print(f'\nOUTREACH RECORDS: {len(db_outreach):,}')

db_domain_to_outreach = {d.lower(): oid for oid, d in db_outreach if d}

# Strategy 1: Direct domain match
domain_matches = {}
for dol_domain, dol_row in dol_by_domain.items():
    if dol_domain in db_domain_to_outreach:
        outreach_id = db_domain_to_outreach[dol_domain]
        domain_matches[outreach_id] = dol_row

print(f'\nSTRATEGY 1 - Domain match: {len(domain_matches):,}')

# Strategy 2: Match Hunter Organization name to domain-derived company name
# Get company names from hunter_contact for our outreach domains
cur.execute('''
    SELECT DISTINCT ON (hc.domain) hc.domain, 
           COALESCE(
               (SELECT first_name || ' ' || last_name FROM enrichment.hunter_contact 
                WHERE domain = hc.domain AND job_title ILIKE '%ceo%' LIMIT 1),
               ''
           ) as ceo_name
    FROM enrichment.hunter_contact hc
    WHERE hc.domain IN (SELECT domain FROM outreach.outreach)
    LIMIT 100
''')

# Actually let's look at what company name data we can extract from the DOL file itself
# The DOL file has "Organization" which is Hunter's company name
# Let's see if those org names match our outreach domains when normalized

# Get unique orgs from DOL and see which match our outreach
print(f'\nSTRATEGY 2 - Fuzzy org name match:')
org_matches = {}

# We need to get company names for our outreach domains
# Since we don't have that in DB, let's try domain extraction
for outreach_id, domain in db_outreach:
    if not domain:
        continue
    # Extract company name from domain (crude but might work)
    # e.g., "gpstrategies.com" -> "GPSTRATEGIES" -> "GP STRATEGIES"
    domain_base = domain.lower().replace('.com', '').replace('.org', '').replace('.net', '').replace('.io', '')
    domain_base = domain_base.replace('-', ' ').replace('_', ' ')
    domain_norm = normalize_name(domain_base)
    
    if domain_norm in dol_by_hunter_org:
        org_matches[outreach_id] = dol_by_hunter_org[domain_norm][0]

print(f'  Domain-derived name matches: {len(org_matches):,}')

# Combine matches
all_matches = set(domain_matches.keys()) | set(org_matches.keys())

print(f'\n{"="*60}')
print(f'TOTAL MATCHED OUTREACH_IDS: {len(all_matches):,}')
print(f'Out of {len(db_outreach):,} ({len(all_matches)*100/len(db_outreach):.2f}%)')

# Show incremental
domain_only = set(domain_matches.keys())
org_new = set(org_matches.keys()) - domain_only

print(f'\nBREAKDOWN:')
print(f'  Domain match: {len(domain_only):,}')
print(f'  Org name adds: {len(org_new):,}')

# Sample the org matches to see quality
if org_new:
    print(f'\nSAMPLE ORG-NAME MATCHES:')
    for oid in list(org_new)[:5]:
        dol_row = org_matches[oid]
        domain = next(d for o, d in db_outreach if o == oid)
        hunter_org = dol_row.get('Organization', '')
        ein = dol_row.get('ein', '')
        print(f'  domain: {domain:<30} | Hunter org: {hunter_org:<25} | EIN: {ein}')

# Also try: see if any DOL company_name matches domain text
print(f'\nSTRATEGY 3 - DOL company name partial match to domain:')
dol_name_matches = {}
for row in dol_rows:
    dol_name = normalize_name(row.get('company_name', ''))
    if not dol_name:
        continue
    # Get first significant word
    words = [w for w in dol_name.split() if len(w) > 3]
    if not words:
        continue
    first_word = words[0]
    
    # Check against all our domains
    for outreach_id, domain in db_outreach:
        if not domain:
            continue
        if first_word.lower() in domain.lower():
            if outreach_id not in domain_matches:  # Don't double count
                dol_name_matches[outreach_id] = row
                break

print(f'  DOL company name -> domain partial matches: {len(dol_name_matches):,}')

# Final tally
final_matches = set(domain_matches.keys()) | set(org_matches.keys()) | set(dol_name_matches.keys())
print(f'\n{"="*60}')
print(f'FINAL TOTAL MATCHED: {len(final_matches):,} outreach_ids ({len(final_matches)*100/len(db_outreach):.2f}%)')

# These are outreach_ids we can link to EINs
print(f'\nThese {len(final_matches):,} outreach_ids can now be linked to DOL EINs')

conn.close()
