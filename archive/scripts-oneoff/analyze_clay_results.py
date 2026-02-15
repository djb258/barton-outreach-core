#!/usr/bin/env python3
"""Analyze Clay URL discovery results"""
import csv

with open('scripts/clay_results.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

total = len(rows)
has_domain = sum(1 for r in rows if r.get('Domain'))
no_domain = total - has_domain

print("Clay URL Discovery Results")
print("=" * 60)
print(f"Total records: {total}")
print(f"Has Domain: {has_domain} ({has_domain/total*100:.1f}%)")
print(f"No Domain: {no_domain} ({no_domain/total*100:.1f}%)")
print()

# Check for suspicious domains (generic sites, not company sites)
suspicious = ['yahoo.com', 'mapquest.com', 'sunbiz.org', 'eindata.com', 'b2bhint.com', 
              'bloomberg.com', 'linkedin.com', 'facebook.com', 'google.com', 'yelp.com',
              'dnb.com', 'zoominfo.com', 'bizapedia.com', 'opencorporates.com']

suspicious_count = 0
suspicious_examples = []
for r in rows:
    domain = r.get('Domain', '').lower()
    for s in suspicious:
        if s in domain:
            suspicious_count += 1
            if len(suspicious_examples) < 10:
                suspicious_examples.append((r['company_name'], domain))
            break

print(f"Suspicious/generic domains: {suspicious_count}")
print()

# Domain patterns
domains = [r.get('Domain', '') for r in rows if r.get('Domain')]
unique_domains = set(domains)
print(f"Unique domains: {len(unique_domains)}")

# Check for .co.uk and other non-US TLDs (potential mismatches)
non_us = sum(1 for d in domains if '.co.uk' in d or '.ca' in d or '.de' in d or '.uk' in d)
print(f"Non-US TLDs (.co.uk, .ca, etc.): {non_us}")

print()
print("Sample suspicious domains:")
print("-" * 60)
for name, domain in suspicious_examples:
    print(f"  {name[:40]:<40} → {domain}")

print()
print("Sample good-looking domains:")
print("-" * 60)
good = 0
for r in rows:
    domain = r.get('Domain', '').lower()
    name = r.get('company_name', '').lower()
    if domain and not any(s in domain for s in suspicious):
        # Check if company name partially matches domain
        name_words = name.replace(',', '').replace('.', '').split()
        if any(w in domain for w in name_words if len(w) > 3):
            print(f"  {r['company_name'][:40]:<40} → {domain}")
            good += 1
            if good >= 10:
                break

print()
print("=" * 60)
print("QUALITY ASSESSMENT:")
print(f"  Total with domains: {has_domain}")
print(f"  Suspicious/generic: {suspicious_count} ({suspicious_count/has_domain*100:.1f}%)")
print(f"  Potentially valid: {has_domain - suspicious_count} ({(has_domain-suspicious_count)/total*100:.1f}%)")
