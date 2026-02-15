#!/usr/bin/env python3
"""Analyze differences between our construction and Clay"""
import csv

# Load both
with open('scripts/clay_results.csv', 'r', encoding='utf-8') as f:
    clay = {r['ein']: r for r in csv.DictReader(f)}

with open('scripts/domain_construction_results.csv', 'r', encoding='utf-8') as f:
    ours = {r['ein']: r for r in csv.DictReader(f)}

print("Analysis of Differences")
print("=" * 70)

# Where Clay found but we didn't
clay_only = []
for ein, c in clay.items():
    o = ours.get(ein, {})
    clay_domain = c.get('Domain', '').lower()
    our_domain = (o.get('our_domain') or '').lower()
    
    if clay_domain and not our_domain:
        clay_only.append({
            'name': c['company_name'],
            'clay': clay_domain
        })

print(f"\nClay found, we didn't: {len(clay_only)}")
print("-" * 70)
for item in clay_only[:15]:
    print(f"  {item['name'][:40]:<40} → {item['clay']}")

# Where we differ
differ = []
for ein, c in clay.items():
    o = ours.get(ein, {})
    clay_domain = c.get('Domain', '').lower().replace('www.', '')
    our_domain = (o.get('our_domain') or '').lower().replace('www.', '')
    
    if clay_domain and our_domain and clay_domain != our_domain:
        differ.append({
            'name': c['company_name'],
            'clay': c.get('Domain', ''),
            'ours': o.get('our_domain', '')
        })

print(f"\nBoth found but different: {len(differ)}")
print("-" * 70)
for item in differ[:20]:
    print(f"  {item['name'][:40]}")
    print(f"    Clay: {item['clay']}")
    print(f"    Ours: {item['ours']}")
    print()

# Analyze what patterns Clay found that we didn't construct
print("=" * 70)
print("PATTERN ANALYSIS - Clay domains we couldn't guess:")
print("-" * 70)

# Check if Clay's domain shares any words with company name
import re

could_not_guess = 0
could_guess_missed = 0

for item in differ[:50]:
    name = item['name'].upper()
    clay_domain = item['clay'].lower().replace('.com', '').replace('.org', '').replace('.net', '')
    
    # Normalize name
    name_words = set(re.sub(r'[^a-zA-Z\s]', '', name).lower().split())
    name_words = {w for w in name_words if len(w) > 2}
    
    # Check if any word appears in clay domain
    overlap = any(w in clay_domain for w in name_words)
    
    if overlap:
        could_guess_missed += 1
    else:
        could_not_guess += 1
        if could_not_guess <= 10:
            print(f"  {item['name'][:40]}")
            print(f"    Clay: {item['clay']} (no name overlap)")
            print()

print(f"\nOf first 50 differences:")
print(f"  Could have guessed (name overlap): {could_guess_missed}")
print(f"  Could NOT have guessed (no overlap): {could_not_guess}")
