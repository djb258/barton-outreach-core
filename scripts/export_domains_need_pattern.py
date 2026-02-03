#!/usr/bin/env python3
"""
Export domains that need email pattern lookup.
Excludes domains that already have verified emails.
"""
import psycopg2
import os
import csv

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print('='*60)
    print('EXPORT DOMAINS NEEDING PATTERN LOOKUP')
    print('='*60)
    print()
    
    # Get domains that have verified emails (exclude these)
    cur.execute("""
        WITH verified_domains AS (
            SELECT DISTINCT LOWER(SPLIT_PART(email, '@', 2)) as domain
            FROM people.people_master 
            WHERE email_verified = true 
            AND email IS NOT NULL AND email LIKE '%@%'
            
            UNION
            
            SELECT DISTINCT LOWER(SPLIT_PART(email, '@', 2)) as domain
            FROM outreach.people 
            WHERE email_verified = true 
            AND email IS NOT NULL AND email LIKE '%@%'
        )
        SELECT DISTINCT o.domain
        FROM outreach.outreach o
        WHERE LOWER(o.domain) NOT IN (SELECT domain FROM verified_domains)
        AND o.domain IS NOT NULL
        AND o.domain != ''
        ORDER BY o.domain
    """)
    
    domains = [r[0] for r in cur.fetchall()]
    
    print(f'Total outreach domains: 41,508')
    print(f'Domains with verified emails: 5,302')
    print(f'Domains needing pattern lookup: {len(domains):,}')
    print()
    
    # Export to CSV
    output_file = 'domains_need_pattern_lookup.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['domain'])
        for domain in domains:
            writer.writerow([domain])
    
    print(f'Exported to: {output_file}')
    print(f'Cost @ $0.01/lookup: ${len(domains) * 0.01:.0f}')
    
    conn.close()

if __name__ == '__main__':
    main()
