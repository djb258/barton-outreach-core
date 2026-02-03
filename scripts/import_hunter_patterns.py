#!/usr/bin/env python3
"""
Import Hunter email patterns into outreach.company_target.email_method
"""
import psycopg2
import os
import csv
from collections import defaultdict

def main():
    # Read Hunter results
    hunter_file = r'C:\Users\CUSTOM PC\Desktop\Hunter IO\domanins-need-pattern-1-2129528 first 24k succeded.csv'
    
    # Extract unique domain -> pattern (take highest confidence pattern per domain)
    domain_patterns = {}
    domain_confidence = {}
    
    with open(hunter_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row.get('domain', '').strip().lower()
            pattern = row.get('Pattern', '').strip()
            confidence = int(row.get('Confidence score', 0) or 0)
            
            if domain and pattern:
                # Keep highest confidence pattern for each domain
                if domain not in domain_patterns or confidence > domain_confidence.get(domain, 0):
                    domain_patterns[domain] = pattern
                    domain_confidence[domain] = confidence
    
    print(f'Unique domains with patterns: {len(domain_patterns):,}')
    print()
    
    # Show pattern distribution
    pattern_counts = defaultdict(int)
    for p in domain_patterns.values():
        pattern_counts[p] += 1
    
    print('TOP PATTERNS:')
    for p, c in sorted(pattern_counts.items(), key=lambda x: -x[1])[:10]:
        print(f'  {p:<20} | {c:,}')
    print()
    
    # Connect to database
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Match domains to outreach and check company_target
    cur.execute('SELECT outreach_id, domain FROM outreach.outreach')
    outreach_domains = {row[1].lower(): row[0] for row in cur.fetchall() if row[1]}
    
    print(f'Outreach domains: {len(outreach_domains):,}')
    
    # Find matches
    matched = 0
    not_in_outreach = 0
    
    updates = []
    for domain, pattern in domain_patterns.items():
        if domain in outreach_domains:
            matched += 1
            outreach_id = outreach_domains[domain]
            updates.append((domain, pattern, outreach_id))
        else:
            not_in_outreach += 1
    
    print(f'Matched to outreach: {matched:,}')
    print(f'Not in outreach: {not_in_outreach:,}')
    print()
    
    # Check how many already have patterns vs need patterns
    cur.execute('''
        SELECT ct.company_unique_id, o.domain, ct.email_method
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    ''')
    existing = {row[1].lower(): (row[0], row[2]) for row in cur.fetchall() if row[1]}
    
    # Hunter patterns are VERIFIED - supersede all existing guessed patterns
    updated = 0
    no_company_target = 0
    
    for domain, pattern, outreach_id in updates:
        if domain in existing:
            cuid, current_pattern = existing[domain]
            # Update regardless of whether pattern exists - Hunter is verified
            cur.execute('''
                UPDATE outreach.company_target
                SET email_method = %s, updated_at = NOW()
                WHERE company_unique_id = %s
            ''', (pattern, cuid))
            updated += 1
        else:
            no_company_target += 1
    
    conn.commit()
    
    print('UPDATE COMPLETE:')
    print(f'  Updated with Hunter pattern: {updated:,}')
    print(f'  No company_target record:    {no_company_target:,}')
    
    conn.close()

if __name__ == '__main__':
    main()
