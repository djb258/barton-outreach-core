#!/usr/bin/env python3
"""
Check domain matches - verify company names match, not just domains
"""
import csv
import re

def normalize_name(name):
    """Normalize company name for comparison"""
    name = name.upper()
    # Remove common suffixes
    suffixes = [' INC.', ' INC', ' LLC', ' LLC.', ' LLP', ' CORP.', ' CORP', 
                ' CO.', ' CO', ' COMPANY', ' GROUP', ' HOLDINGS', ' LTD.', ' LTD']
    for s in suffixes:
        if name.endswith(s):
            name = name[:-len(s)]
    # Remove punctuation
    name = re.sub(r'[^A-Z0-9\s]', '', name)
    # Get first 2-3 significant words
    words = [w for w in name.split() if w not in ['THE', 'AND', 'OF', 'A', 'AN']]
    return set(words)

# Load matches
with open('scripts/outreach_blog_from_dol.csv', 'r', encoding='utf-8') as f:
    matches = list(csv.DictReader(f))

# Load outreach company names (we need to query DB for this)
# For now, check by domain correlation
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Get outreach company info via sovereign_id → cl.company_identity
outreach_ids = [m['outreach_id'] for m in matches]

print("Checking name correlation for domain matches...")
print("=" * 70)

# Query outreach names
cur.execute("""
    SELECT o.outreach_id, o.domain, ci.company_name
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
    WHERE o.outreach_id = ANY(%s::uuid[])
""", (outreach_ids,))

outreach_names = {str(r[0]): {'domain': r[1], 'name': r[2]} for r in cur.fetchall()}

print(f"Retrieved {len(outreach_names):,} outreach company names")

# Compare names
good_matches = []
bad_matches = []

for m in matches:
    oid = m['outreach_id']
    if oid not in outreach_names:
        continue
    
    outreach_name = outreach_names[oid]['name'] or ''
    dol_name = m['dol_company'] or ''
    
    out_words = normalize_name(outreach_name)
    dol_words = normalize_name(dol_name)
    
    # Check overlap
    overlap = out_words & dol_words
    
    if len(overlap) >= 1 and len(overlap) >= min(len(out_words), len(dol_words)) * 0.5:
        good_matches.append({
            'outreach_id': oid,
            'domain': m['domain'],
            'outreach_name': outreach_name,
            'dol_name': dol_name,
            'ein': m['ein'],
            'overlap': overlap
        })
    else:
        bad_matches.append({
            'outreach_id': oid,
            'domain': m['domain'],
            'outreach_name': outreach_name,
            'dol_name': dol_name,
            'ein': m['ein'],
            'overlap': overlap
        })

print(f"Good name matches: {len(good_matches):,}")
print(f"Bad name matches (likely wrong company): {len(bad_matches):,}")

print()
print("Sample BAD matches (domain matches but company name doesn't):")
print("-" * 70)
for m in bad_matches[:15]:
    print(f"  Domain: {m['domain']}")
    print(f"    Outreach: {m['outreach_name'][:50]}")
    print(f"    DOL:      {m['dol_name'][:50]}")
    print()

print()
print("Sample GOOD matches:")
print("-" * 70)
for m in good_matches[:10]:
    print(f"  {m['domain']} | EIN: {m['ein']}")
    print(f"    Outreach: {m['outreach_name'][:50]}")
    print(f"    DOL:      {m['dol_name'][:50]}")
    print()

# Save verified good matches
with open('scripts/outreach_blog_name_verified.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['outreach_id', 'domain', 'ein', 'outreach_name', 'dol_name'])
    for m in good_matches:
        writer.writerow([m['outreach_id'], m['domain'], m['ein'], m['outreach_name'], m['dol_name']])

print(f"\nSaved {len(good_matches):,} NAME-VERIFIED matches to scripts/outreach_blog_name_verified.csv")

cur.close()
conn.close()
