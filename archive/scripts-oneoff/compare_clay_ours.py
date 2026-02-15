#!/usr/bin/env python3
"""Check Clay results more carefully"""
import csv

with open('scripts/clay_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("Clay columns:", list(rows[0].keys()))
print()

# Check Domain column
domains = [r.get('Domain', '') for r in rows]
empty = sum(1 for d in domains if not d)
has_value = sum(1 for d in domains if d)

print(f"Empty Domain: {empty}")
print(f"Has Domain: {has_value}")
print()

print("First 10 rows Domain values:")
for r in rows[:10]:
    print(f"  EIN: {r['ein']} | Domain: [{r.get('Domain', '')}]")

# Now compare properly
print()
print("=" * 70)

with open('scripts/domain_construction_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    our_results = list(reader)

# Build lookup
our_lookup = {r['ein']: r for r in our_results}

# Check matches where BOTH have values
both_have = 0
our_only = 0
clay_only = 0
both_match = 0
both_differ = 0

for r in rows:
    ein = r['ein']
    clay_domain = r.get('Domain', '').lower().replace('www.', '')
    our_data = our_lookup.get(ein, {})
    our_domain = (our_data.get('our_domain') or '').lower().replace('www.', '')
    
    if clay_domain and our_domain:
        both_have += 1
        if clay_domain == our_domain:
            both_match += 1
        else:
            both_differ += 1
    elif our_domain and not clay_domain:
        our_only += 1
    elif clay_domain and not our_domain:
        clay_only += 1

print(f"Both have domain: {both_have}")
print(f"  - Match: {both_match}")
print(f"  - Differ: {both_differ}")
print(f"Only we found: {our_only}")
print(f"Only Clay found: {clay_only}")
