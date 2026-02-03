#!/usr/bin/env python3
"""
Import Hunter enrichment data into Neon tables.
Populates enrichment.hunter_company and enrichment.hunter_contact
"""
import csv
import psycopg2
from psycopg2.extras import execute_values
import os

HUNTER_FILE = r"C:\Users\CUSTOM PC\Desktop\Hunter IO\domanins-need-pattern-1-2129528 first 24k succeded.csv"

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Read Hunter data
    companies = {}  # domain -> company data
    contacts = []   # list of contact records
    
    with open(HUNTER_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = (row.get('domain') or row.get('Domain name') or '').strip().lower()
            if not domain:
                continue
            
            # Company data (one per domain, take first occurrence)
            if domain not in companies:
                companies[domain] = {
                    'domain': domain,
                    'organization': row.get('Organization', '').strip() or None,
                    'headcount': row.get('Headcount', '').strip() or None,
                    'country': row.get('Country', '').strip() or None,
                    'state': row.get('State', '').strip() or None,
                    'city': row.get('City', '').strip() or None,
                    'postal_code': row.get('Postal code', '').strip() or None,
                    'street': row.get('Street', '').strip() or None,
                    'email_pattern': row.get('Pattern', '').strip() or None,
                    'company_type': row.get('Company type', '').strip() or None,
                    'industry': row.get('Industry', '').strip() or None,
                }
            
            # Contact data (multiple per domain)
            email = row.get('Email address', '').strip() or None
            first_name = row.get('First name', '').strip() or None
            last_name = row.get('Last name', '').strip() or None
            
            # Only add if there's an email or name
            if email or first_name or last_name:
                conf_str = row.get('Confidence score', '').strip()
                sources_str = row.get('Number of sources', '').strip()
                
                contacts.append({
                    'domain': domain,
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'department': row.get('Department', '').strip() or None,
                    'job_title': row.get('Job title', '').strip() or None,
                    'position_raw': row.get('Position raw', '').strip() or None,
                    'linkedin_url': row.get('LinkedIn URL', '').strip() or None,
                    'twitter_handle': row.get('Twitter handle', '').strip() or None,
                    'phone_number': row.get('Phone number', '').strip() or None,
                    'confidence_score': int(conf_str) if conf_str.isdigit() else None,
                    'email_type': row.get('Type', '').strip() or None,
                    'num_sources': int(sources_str) if sources_str.isdigit() else None,
                })
    
    print(f'Parsed Hunter file:')
    print(f'  Companies: {len(companies):,}')
    print(f'  Contacts:  {len(contacts):,}')
    
    # Insert companies
    company_values = [
        (c['domain'], c['organization'], c['headcount'], c['country'], 
         c['state'], c['city'], c['postal_code'], c['street'],
         c['email_pattern'], c['company_type'], c['industry'])
        for c in companies.values()
    ]
    
    execute_values(cur, """
        INSERT INTO enrichment.hunter_company 
        (domain, organization, headcount, country, state, city, postal_code, street, 
         email_pattern, company_type, industry)
        VALUES %s
        ON CONFLICT (domain) DO UPDATE SET
            organization = EXCLUDED.organization,
            headcount = EXCLUDED.headcount,
            country = EXCLUDED.country,
            state = EXCLUDED.state,
            city = EXCLUDED.city,
            postal_code = EXCLUDED.postal_code,
            street = EXCLUDED.street,
            email_pattern = EXCLUDED.email_pattern,
            company_type = EXCLUDED.company_type,
            industry = EXCLUDED.industry,
            enriched_at = NOW(),
            updated_at = NOW()
    """, company_values, page_size=1000)
    
    print(f'  Inserted/updated {len(company_values):,} companies')
    
    # Insert contacts (delete existing first for clean import)
    cur.execute("DELETE FROM enrichment.hunter_contact")
    
    contact_values = [
        (c['domain'], c['email'], c['first_name'], c['last_name'],
         c['department'], c['job_title'], c['position_raw'],
         c['linkedin_url'], c['twitter_handle'], c['phone_number'],
         c['confidence_score'], c['email_type'], c['num_sources'])
        for c in contacts
    ]
    
    execute_values(cur, """
        INSERT INTO enrichment.hunter_contact 
        (domain, email, first_name, last_name, department, job_title, position_raw,
         linkedin_url, twitter_handle, phone_number, confidence_score, email_type, num_sources)
        VALUES %s
    """, contact_values, page_size=1000)
    
    print(f'  Inserted {len(contact_values):,} contacts')
    
    conn.commit()
    
    # Summary stats
    print('\n--- Summary ---')
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company")
    print(f'Total companies: {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
    print(f'Total contacts:  {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company WHERE email_pattern IS NOT NULL")
    print(f'Companies with pattern: {cur.fetchone()[0]:,}')
    
    cur.execute("""
        SELECT email_pattern, COUNT(*) 
        FROM enrichment.hunter_company 
        WHERE email_pattern IS NOT NULL 
        GROUP BY email_pattern 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    print('\nTop patterns:')
    for pattern, cnt in cur.fetchall():
        print(f'  {pattern}: {cnt:,}')
    
    cur.execute("""
        SELECT industry, COUNT(*) 
        FROM enrichment.hunter_company 
        WHERE industry IS NOT NULL AND industry != ''
        GROUP BY industry 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    print('\nTop industries:')
    for ind, cnt in cur.fetchall():
        print(f'  {ind}: {cnt:,}')
    
    conn.close()
    print('\nDone!')

if __name__ == '__main__':
    main()
