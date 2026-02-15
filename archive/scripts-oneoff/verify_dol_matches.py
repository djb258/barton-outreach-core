#!/usr/bin/env python3
"""
Verify DOL domain matches are actually correct
Check if the discovered URL actually matches the domain in outreach
"""
import csv

# Load the matches
with open('scripts/outreach_blog_from_dol.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    matches = list(reader)

print("Verifying DOL→Outreach Matches")
print("=" * 70)

# Check if dol_url contains the domain
correct = []
incorrect = []

for m in matches:
    outreach_domain = m['domain'].lower().replace('www.', '')
    dol_url = m.get('dol_url', '').lower()
    
    if outreach_domain in dol_url:
        correct.append(m)
    else:
        incorrect.append(m)

print(f"Correct (URL contains domain): {len(correct):,}")
print(f"Incorrect (URL mismatch): {len(incorrect):,}")

print()
print("Sample INCORRECT matches (false positives):")
print("-" * 70)
for m in incorrect[:15]:
    print(f"  Outreach domain: {m['domain']}")
    print(f"  DOL URL: {m.get('dol_url', 'None')}")
    print(f"  DOL company: {m['dol_company'][:50]}")
    print()

print()
print("Sample CORRECT matches:")
print("-" * 70)
for m in correct[:10]:
    print(f"  {m['domain']} → {m['dol_company'][:50]}")

# Save verified matches only
with open('scripts/outreach_blog_verified.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['outreach_id', 'domain', 'ein', 'dol_company', 'dol_url'])
    for m in correct:
        writer.writerow([m['outreach_id'], m['domain'], m['ein'], m['dol_company'], m['dol_url']])

print()
print(f"Saved {len(correct):,} VERIFIED matches to scripts/outreach_blog_verified.csv")
