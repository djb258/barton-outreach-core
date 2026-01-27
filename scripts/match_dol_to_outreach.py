#!/usr/bin/env python3
"""
Match DOL discovered URLs to outreach records via EIN
Update outreach.blog.source_url
"""
import psycopg2
import csv
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("DOL URL → Outreach Matching")
print("=" * 70)

# Load our valid DOL domains (119,469)
with open('scripts/domain_results_VALID.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    dol_domains = {r['ein']: {'domain': r['domain'], 'url': r.get('url', ''), 'company_name': r['company_name']} 
                   for r in reader if r.get('ein')}

print(f"Loaded {len(dol_domains):,} valid DOL domains")

# Check outreach.dol records
cur.execute("SELECT COUNT(*) FROM outreach.dol")
total_dol = cur.fetchone()[0]
print(f"outreach.dol total records: {total_dol:,}")

# Get outreach.dol records with EIN
cur.execute("""
    SELECT d.outreach_id, d.ein, o.domain as current_domain, b.source_url as blog_url
    FROM outreach.dol d
    JOIN outreach.outreach o ON d.outreach_id = o.outreach_id
    LEFT JOIN outreach.blog b ON d.outreach_id = b.outreach_id
    WHERE d.ein IS NOT NULL
""")
outreach_dol = cur.fetchall()
print(f"outreach.dol with EIN: {len(outreach_dol):,}")

# Match against our DOL domains
matches = []
already_has_blog_url = 0
already_matches = 0
new_url_found = 0
no_match = 0

for row in outreach_dol:
    outreach_id, ein, current_domain, blog_url = row
    
    if blog_url:
        already_has_blog_url += 1
        continue
    
    # Look up EIN in our DOL domains
    if ein in dol_domains:
        discovered = dol_domains[ein]
        discovered_domain = discovered['domain'].lower().replace('www.', '')
        current_norm = (current_domain or '').lower().replace('www.', '')
        
        if discovered_domain == current_norm:
            already_matches += 1
        else:
            new_url_found += 1
            matches.append({
                'outreach_id': outreach_id,
                'ein': ein,
                'current_domain': current_domain,
                'discovered_domain': discovered['domain'],
                'discovered_url': discovered['url'],
                'company_name': discovered['company_name']
            })
    else:
        no_match += 1

print()
print("Match Results:")
print(f"  Already has blog URL: {already_has_blog_url:,}")
print(f"  Domain already matches: {already_matches:,}")
print(f"  NEW URL discovered: {new_url_found:,}")
print(f"  No EIN match in DOL: {no_match:,}")

# Show sample matches
print()
print("Sample NEW matches (first 15):")
print("-" * 70)
for m in matches[:15]:
    print(f"  {m['company_name'][:40]}")
    print(f"    Current: {m['current_domain']}")
    print(f"    Found:   {m['discovered_domain']}")
    print()

# Save matches for review/update
with open('scripts/blog_url_updates.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['outreach_id', 'ein', 'company_name', 'current_domain', 'discovered_domain', 'discovered_url'])
    for m in matches:
        writer.writerow([m['outreach_id'], m['ein'], m['company_name'], 
                        m['current_domain'], m['discovered_domain'], m['discovered_url']])

print(f"Saved {len(matches):,} potential updates to scripts/blog_url_updates.csv")

cur.close()
conn.close()
