#!/usr/bin/env python3
"""Check domain format differences between DOL and outreach"""
import csv
import psycopg2
import os

# DOL domains
dol_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\dol-match-6-2129617.csv'
with open(dol_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_domains = set(r.get('Domain name', '').strip() for r in reader if r.get('Domain name'))

print('DOL DOMAIN SAMPLES:')
for d in sorted(list(dol_domains))[:15]:
    print(f'  "{d}"')

# Outreach domains
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute('SELECT DISTINCT domain FROM outreach.outreach WHERE domain IS NOT NULL ORDER BY domain LIMIT 15')

print()
print('OUTREACH DOMAIN SAMPLES:')
for r in cur.fetchall():
    print(f'  "{r[0]}"')

# Check for format differences
print()
print('='*60)
print('FORMAT ANALYSIS - DOL:')
dol_with_www = [d for d in dol_domains if d.lower().startswith('www.')]
dol_with_http = [d for d in dol_domains if d.lower().startswith('http')]
dol_with_slash = [d for d in dol_domains if '/' in d]
dol_uppercase = [d for d in dol_domains if d != d.lower()]
print(f'  Total unique domains: {len(dol_domains)}')
print(f'  Starting with www.: {len(dol_with_www)}')
print(f'  Starting with http: {len(dol_with_http)}')
print(f'  Contains slash: {len(dol_with_slash)}')
print(f'  Has uppercase: {len(dol_uppercase)}')

print()
print('FORMAT ANALYSIS - OUTREACH:')
cur.execute("SELECT COUNT(DISTINCT domain) FROM outreach.outreach WHERE domain IS NOT NULL")
print(f'  Total unique domains: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE domain LIKE 'www.%'")
print(f'  Starting with www.: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE domain LIKE 'http%'")
print(f'  Starting with http: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE domain LIKE '%/%'")
print(f'  Contains slash: {cur.fetchone()[0]}')

cur.execute("SELECT COUNT(*) FROM outreach.outreach WHERE domain != LOWER(domain)")
print(f'  Has uppercase: {cur.fetchone()[0]}')

# Now normalize and re-match
print()
print('='*60)
print('NORMALIZED MATCHING:')

def normalize_domain(d):
    """Normalize domain to base form"""
    if not d:
        return ''
    d = d.lower().strip()
    # Remove protocol
    d = d.replace('https://', '').replace('http://', '')
    # Remove www.
    if d.startswith('www.'):
        d = d[4:]
    # Remove trailing slash and path
    d = d.split('/')[0]
    # Remove port
    d = d.split(':')[0]
    return d

# Normalize DOL domains
dol_normalized = {}
for domain in dol_domains:
    norm = normalize_domain(domain)
    if norm:
        dol_normalized[norm] = domain  # Store original

# Normalize outreach domains
cur.execute('SELECT outreach_id, domain FROM outreach.outreach WHERE domain IS NOT NULL')
outreach_rows = cur.fetchall()

outreach_normalized = {}
for oid, domain in outreach_rows:
    norm = normalize_domain(domain)
    if norm:
        outreach_normalized[norm] = (oid, domain)

print(f'DOL normalized domains: {len(dol_normalized)}')
print(f'Outreach normalized domains: {len(outreach_normalized)}')

# Find matches after normalization
matches = set(dol_normalized.keys()) & set(outreach_normalized.keys())
print(f'Matches after normalization: {len(matches)}')

# Show some matches
print()
print('SAMPLE MATCHES:')
for norm in list(matches)[:10]:
    dol_orig = dol_normalized[norm]
    out_id, out_orig = outreach_normalized[norm]
    print(f'  Normalized: {norm:<30} | DOL: {dol_orig:<30} | Outreach: {out_orig}')

conn.close()
