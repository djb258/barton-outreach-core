#!/usr/bin/env python3
"""
Match outreach domains to DOL discovered URLs
Update blog.source_url with validated URLs
"""
import psycopg2
import csv
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("Outreach Domain → DOL URL Matching")
print("=" * 70)

# Load our valid DOL domains with full URLs
with open('scripts/domain_results_VALID.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_data = list(reader)

# Build domain → URL lookup (use full URL from our discovery)
dol_url_lookup = {}
for r in dol_data:
    domain = r.get('domain', '').lower().replace('www.', '')
    url = r.get('url', '')
    if domain and url:
        dol_url_lookup[domain] = {
            'url': url,
            'ein': r['ein'],
            'company_name': r['company_name']
        }

print(f"DOL URLs indexed: {len(dol_url_lookup):,}")

# Get ALL outreach records with their domain
cur.execute("""
    SELECT o.outreach_id, o.domain, b.source_url
    FROM outreach.outreach o
    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
""")
outreach_records = cur.fetchall()
print(f"Outreach records: {len(outreach_records):,}")

# Match
matches = []
already_has_url = 0
domain_not_in_dol = 0

for outreach_id, domain, current_source_url in outreach_records:
    # Skip if already has source_url
    if current_source_url:
        already_has_url += 1
        continue
    
    if not domain:
        continue
    
    domain_norm = domain.lower().replace('www.', '')
    
    if domain_norm in dol_url_lookup:
        dol = dol_url_lookup[domain_norm]
        matches.append({
            'outreach_id': outreach_id,
            'domain': domain,
            'dol_url': dol['url'],
            'ein': dol['ein'],
            'dol_company': dol['company_name']
        })
    else:
        domain_not_in_dol += 1

print()
print("Match Results:")
print(f"  Already has source_url: {already_has_url:,}")
print(f"  Matched to DOL URL: {len(matches):,}")
print(f"  Domain not in DOL discovery: {domain_not_in_dol:,}")

# Save matches for update
with open('scripts/outreach_blog_url_matches.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['outreach_id', 'domain', 'dol_url', 'ein', 'dol_company'])
    for m in matches:
        writer.writerow([m['outreach_id'], m['domain'], m['dol_url'], m['ein'], m['dol_company']])

print(f"\nSaved {len(matches):,} matches to scripts/outreach_blog_url_matches.csv")

# Show samples
print()
print("Sample matches (first 15):")
print("-" * 70)
for m in matches[:15]:
    print(f"  {m['domain']} → {m['dol_url'][:60]}")

cur.close()
conn.close()
