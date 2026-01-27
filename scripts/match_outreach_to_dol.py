#!/usr/bin/env python3
"""
Match outreach records to DOL via domain name similarity
For enriching blog.source_url from DOL discovered URLs
"""
import psycopg2
import csv
import os
import re

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("Outreach → DOL Domain Matching")
print("=" * 70)

# Load our valid DOL domains
with open('scripts/domain_results_VALID.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_data = list(reader)

# Build domain lookup
dol_by_domain = {}
for r in dol_data:
    domain = r.get('domain', '').lower().replace('www.', '')
    if domain:
        dol_by_domain[domain] = {
            'ein': r['ein'],
            'company_name': r['company_name'],
            'url': r.get('url', ''),
            'city': r.get('city', ''),
            'state': r.get('state', '')
        }

print(f"DOL domains indexed: {len(dol_by_domain):,}")

# Get outreach records needing blog URL
cur.execute("""
    SELECT o.outreach_id, o.domain, b.source_url
    FROM outreach.outreach o
    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
    WHERE b.source_url IS NULL OR b.source_url = ''
""")
outreach_needing_url = cur.fetchall()
print(f"Outreach records needing blog URL: {len(outreach_needing_url):,}")

# Match by domain
matches = []
for outreach_id, domain, _ in outreach_needing_url:
    if not domain:
        continue
    
    domain_norm = domain.lower().replace('www.', '')
    
    if domain_norm in dol_by_domain:
        dol = dol_by_domain[domain_norm]
        matches.append({
            'outreach_id': outreach_id,
            'domain': domain,
            'ein': dol['ein'],
            'dol_company': dol['company_name'],
            'dol_url': dol['url']
        })

print(f"Domain matches found: {len(matches):,}")

# Save matches
with open('scripts/outreach_blog_from_dol.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['outreach_id', 'domain', 'ein', 'dol_company', 'dol_url'])
    for m in matches:
        writer.writerow([m['outreach_id'], m['domain'], m['ein'], m['dol_company'], m['dol_url']])

print(f"Saved matches to scripts/outreach_blog_from_dol.csv")

# Show samples
print()
print("Sample matches (first 10):")
print("-" * 70)
for m in matches[:10]:
    print(f"  {m['domain']} → EIN {m['ein']}")
    print(f"    DOL: {m['dol_company'][:50]}")
    print()

cur.close()
conn.close()
