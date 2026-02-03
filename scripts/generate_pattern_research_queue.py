#!/usr/bin/env python3
"""
Generate Pattern Research Queue
================================
Creates a prioritized list of companies that need email pattern research
because all their current emails failed MillionVerifier validation.

Output: CSV and DB table for pattern research queue
"""

import os
import sys
import psycopg2
import csv
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def main():
    print("="*70)
    print("PATTERN RESEARCH QUEUE GENERATOR")
    print("="*70)
    print()
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all companies where ALL emails failed
    print("[QUERY] Finding companies with all failed emails...")
    cur.execute('''
    WITH company_email_status AS (
        SELECT 
            pm.company_unique_id,
            BOOL_OR(pm.email_verified = TRUE) as has_verified,
            BOOL_OR(pm.email_verified = FALSE) as has_failed,
            COUNT(*) as people_count,
            ARRAY_AGG(pm.email) as failed_emails,
            ARRAY_AGG(DISTINCT pm.source_system) as sources
        FROM people.people_master pm
        WHERE pm.email IS NOT NULL AND pm.email != ''
        GROUP BY pm.company_unique_id
    ),
    failed_companies AS (
        SELECT 
            ces.company_unique_id,
            ces.people_count,
            ces.failed_emails[1:5] as sample_emails,
            ces.sources
        FROM company_email_status ces
        WHERE ces.has_verified = FALSE  -- no verified emails
          AND ces.has_failed = TRUE     -- has failed emails
    )
    SELECT 
        fc.company_unique_id,
        c.company_name,
        c.website_url,
        c.employee_count,
        c.industry,
        fc.people_count,
        fc.sample_emails,
        fc.sources
    FROM failed_companies fc
    JOIN company.company_master c ON c.company_unique_id = fc.company_unique_id
    ORDER BY fc.people_count DESC, c.employee_count DESC NULLS LAST
    ''')
    
    rows = cur.fetchall()
    print(f"[FOUND] {len(rows):,} companies need pattern research")
    print()
    
    # Write to CSV
    csv_filename = f"pattern_research_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'output', csv_filename)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'company_unique_id', 'company_name', 'website_url', 'domain',
            'employee_count', 'industry', 'people_count', 'sample_emails', 'sources',
            'research_status', 'new_pattern', 'notes'
        ])
        
        for row in rows:
            company_id, name, website, employees, industry, people_count, emails, sources = row
            
            # Extract domain from website
            domain = ''
            if website:
                domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
            
            # Format sample emails
            email_list = ', '.join(emails[:3]) if emails else ''
            source_list = ', '.join(sources) if sources else ''
            
            writer.writerow([
                company_id, name, website, domain, employees, industry,
                people_count, email_list, source_list,
                'pending', '', ''  # research_status, new_pattern, notes
            ])
    
    print(f"[CSV] Written to: {csv_path}")
    
    # Summary by source
    print()
    print("="*70)
    print("SUMMARY BY DATA SOURCE")
    print("="*70)
    
    cur.execute('''
    WITH company_email_status AS (
        SELECT 
            pm.company_unique_id,
            BOOL_OR(pm.email_verified = TRUE) as has_verified,
            pm.source_system
        FROM people.people_master pm
        WHERE pm.email IS NOT NULL
        GROUP BY pm.company_unique_id, pm.source_system
    )
    SELECT 
        ces.source_system,
        COUNT(*) FILTER (WHERE has_verified) as verified_count,
        COUNT(*) FILTER (WHERE NOT has_verified) as failed_count,
        COUNT(*) as total,
        ROUND(100.0 * COUNT(*) FILTER (WHERE has_verified) / NULLIF(COUNT(*), 0), 1) as success_rate
    FROM company_email_status ces
    GROUP BY ces.source_system
    ORDER BY failed_count DESC
    ''')
    
    print(f"{'Source':<25} | {'Verified':>10} | {'Failed':>10} | {'Rate':>8}")
    print("-"*60)
    for row in cur.fetchall():
        source = row[0] or 'unknown'
        print(f"{source:<25} | {row[1]:>10,} | {row[2]:>10,} | {row[4]:>7.1f}%")
    
    # Priority breakdown
    print()
    print("="*70)
    print("PRIORITY BREAKDOWN (by # of people)")
    print("="*70)
    
    cur.execute('''
    WITH failed_companies AS (
        SELECT 
            pm.company_unique_id,
            COUNT(*) as people_count
        FROM people.people_master pm
        WHERE pm.email IS NOT NULL
        GROUP BY pm.company_unique_id
        HAVING BOOL_OR(pm.email_verified = TRUE) = FALSE
    )
    SELECT 
        CASE 
            WHEN people_count >= 10 THEN '10+ people'
            WHEN people_count >= 5 THEN '5-9 people'
            WHEN people_count >= 2 THEN '2-4 people'
            ELSE '1 person'
        END as bucket,
        COUNT(*) as company_count,
        SUM(people_count) as total_people
    FROM failed_companies
    GROUP BY 1
    ORDER BY MIN(people_count) DESC
    ''')
    
    print(f"{'Bucket':<15} | {'Companies':>12} | {'Total People':>12}")
    print("-"*45)
    for row in cur.fetchall():
        print(f"{row[0]:<15} | {row[1]:>12,} | {row[2]:>12,}")
    
    # Next steps
    print()
    print("="*70)
    print("NEXT STEPS FOR PATTERN RESEARCH")
    print("="*70)
    print("""
1. HIGH PRIORITY: Companies with 5+ people
   - More data points to try different patterns
   - Higher value targets (multiple contacts)

2. RESEARCH METHODS:
   a) Hunter.io domain search - find real email patterns
   b) Apollo.io company lookup - discover additional contacts
   c) LinkedIn + email permutator - test common patterns
   d) Website contact page scraping

3. PATTERN OPTIONS TO TEST:
   - first.last@domain.com (most common - 80%)
   - flast@domain.com
   - first_last@domain.com
   - firstl@domain.com
   - first@domain.com

4. AFTER RESEARCH:
   - Update company.company_master.email_pattern
   - Re-generate emails for all people
   - Re-validate with MillionVerifier
""")
    
    conn.close()
    print()
    print(f"[DONE] Queue saved to: {csv_path}")

if __name__ == '__main__':
    main()
