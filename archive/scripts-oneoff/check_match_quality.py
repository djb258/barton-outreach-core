#!/usr/bin/env python3
"""Check quality of partial matches"""
import csv
import psycopg2
import os
import re

def normalize_name(name):
    if not name:
        return ''
    name = name.upper()
    for suffix in [' LLC', ' INC', ' CORP', ' CO', ' LTD', ' LP', ' PLLC', ' PC', ' PA', ',', '.']:
        name = name.replace(suffix, '')
    name = re.sub(r'[^\w\s]', '', name)
    return ' '.join(name.split()).strip()

dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_rows = list(reader)

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT outreach_id, domain FROM outreach.outreach WHERE domain IS NOT NULL')
db_outreach = cur.fetchall()

# Get sample partial matches with details
print('SAMPLE PARTIAL MATCHES (DOL company name contains word from domain):')
print('='*100)
count = 0
seen_domains = set()
for row in dol_rows:
    dol_name = normalize_name(row.get('company_name', ''))
    if not dol_name:
        continue
    words = [w for w in dol_name.split() if len(w) > 3]
    if not words:
        continue
    first_word = words[0]
    
    for outreach_id, domain in db_outreach:
        if not domain or domain in seen_domains:
            continue
        if first_word.lower() in domain.lower():
            dol_company = row.get('company_name', '')[:40]
            ein = row.get('ein', '')
            print(f'DOL: {dol_company:<40} | Domain: {domain:<30} | EIN: {ein}')
            seen_domains.add(domain)
            count += 1
            if count >= 25:
                break
    if count >= 25:
        break

conn.close()
