#!/usr/bin/env python3
"""Combine and summarize all state domain results"""
import csv
import os

states = ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE']

print("Domain Construction Results - All States")
print("=" * 70)

total_processed = 0
total_found = 0
all_results = []

for state in states:
    filepath = f'scripts/domain_results_{state}.csv'
    if not os.path.exists(filepath):
        print(f"  {state}: FILE MISSING")
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    processed = len(rows)
    found = sum(1 for r in rows if r.get('found') == 'True')
    pct = found / processed * 100 if processed > 0 else 0
    
    print(f"  {state}: {processed:,} processed → {found:,} found ({pct:.1f}%)")
    
    total_processed += processed
    total_found += found
    all_results.extend(rows)

print()
print("=" * 70)
print(f"TOTAL: {total_processed:,} processed → {total_found:,} found ({total_found/total_processed*100:.1f}%)")
print(f"NOT FOUND: {total_processed - total_found:,}")
print()

# Save combined file
combined_path = 'scripts/domain_results_ALL.csv'
with open(combined_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['ein', 'company_name', 'city', 'state', 'found', 'domain', 'url'])
    for r in all_results:
        writer.writerow([r['ein'], r['company_name'], r['city'], r['state'], 
                        r.get('found'), r.get('domain'), r.get('url')])

print(f"Combined results saved to {combined_path}")
print(f"File size: {os.path.getsize(combined_path) / 1024 / 1024:.1f} MB")
