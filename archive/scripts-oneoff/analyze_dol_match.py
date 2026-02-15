#!/usr/bin/env python3
"""
Analyze DOL match file and check how many can match to existing outreach IDs.
READ-ONLY analysis - no database writes.
"""
import csv
import psycopg2
import os
from collections import defaultdict

# Read the DOL match file
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'

with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print('DOL MATCH FILE ANALYSIS')
print('='*60)
print(f'Total rows: {len(rows):,}')

# Unique EINs
eins = set(r['ein'] for r in rows if r.get('ein'))
print(f'Unique EINs: {len(eins):,}')

# Unique domains
domains = set(r['Domain name'] for r in rows if r.get('Domain name'))
print(f'Unique domains: {len(domains):,}')

# Rows with both EIN and domain
both = [r for r in rows if r.get('ein') and r.get('Domain name')]
print(f'Rows with EIN + domain: {len(both):,}')

# EIN to domain mapping
ein_to_domains = defaultdict(set)
for r in rows:
    if r.get('ein') and r.get('Domain name'):
        ein_to_domains[r['ein']].add(r['Domain name'])

print(f'EINs with at least one domain: {len(ein_to_domains):,}')

# Sample
print()
print('SAMPLE ROWS:')
for r in rows[:5]:
    ein = r.get('ein', 'N/A')
    domain = r.get('Domain name', 'N/A')
    company = r.get('company_name', 'N/A')[:40]
    print(f'  EIN: {ein}, Domain: {domain}, Company: {company}')

# Now check against database
print()
print('='*60)
print('MATCHING AGAINST DATABASE')
print('='*60)

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get all domains from outreach table
cur.execute("SELECT DISTINCT domain FROM outreach.outreach WHERE domain IS NOT NULL")
db_domains = set(r[0] for r in cur.fetchall())
print(f'Domains in outreach.outreach: {len(db_domains):,}')

# Match: DOL domains that exist in our outreach table
matching_domains = domains & db_domains
print(f'DOL domains that match outreach: {len(matching_domains):,}')

# How many EINs can we link via domain match?
eins_with_matching_domain = set()
for ein, ein_domains in ein_to_domains.items():
    if ein_domains & db_domains:
        eins_with_matching_domain.add(ein)

print(f'EINs matchable via domain: {len(eins_with_matching_domain):,}')

# Get more detail on matches
print()
print('MATCH SUMMARY:')
print(f'  Total unique EINs in DOL file: {len(eins):,}')
print(f'  EINs we can link to outreach_id: {len(eins_with_matching_domain):,}')
print(f'  Match rate: {len(eins_with_matching_domain)*100/len(eins):.1f}%')

# Sample of matched EINs
print()
print('SAMPLE MATCHED EINs:')
sample_matched = list(eins_with_matching_domain)[:10]
for ein in sample_matched:
    domains_for_ein = ein_to_domains[ein]
    matched_domains = domains_for_ein & db_domains
    
    # Get outreach_ids for these domains
    domain_list = ",".join(f"'{d}'" for d in matched_domains)
    cur.execute(f"SELECT outreach_id, domain FROM outreach.outreach WHERE domain IN ({domain_list}) LIMIT 3")
    outreach_rows = cur.fetchall()
    
    print(f'  EIN {ein}:')
    for oid, dom in outreach_rows:
        print(f'    -> outreach_id: {oid}, domain: {dom}')

conn.close()
