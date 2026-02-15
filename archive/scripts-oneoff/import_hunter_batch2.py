#!/usr/bin/env python3
"""
Import Hunter batch 2 into enrichment database.
"""
import csv
import psycopg2
from psycopg2.extras import execute_values
import os

HUNTER_FILE = r"C:\Users\CUSTOM PC\Desktop\Hunter IO\domanins-need-pattern-2-2129565.csv"

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Read Hunter batch 2
    companies = {}
    contacts = []
    
    with open(HUNTER_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = (row.get('domain') or row.get('Domain name') or '').strip().lower()
            if not domain:
                continue
            
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
            
            email = row.get('Email address', '').strip() or None
            first_name = row.get('First name', '').strip() or None
            last_name = row.get('Last name', '').strip() or None
            
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
    
    print(f'Batch 2 parsed:')
    print(f'  Companies: {len(companies):,}')
    print(f'  Contacts:  {len(contacts):,}')
    
    # Insert companies (upsert)
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
            organization = COALESCE(EXCLUDED.organization, enrichment.hunter_company.organization),
            headcount = COALESCE(EXCLUDED.headcount, enrichment.hunter_company.headcount),
            country = COALESCE(EXCLUDED.country, enrichment.hunter_company.country),
            state = COALESCE(EXCLUDED.state, enrichment.hunter_company.state),
            city = COALESCE(EXCLUDED.city, enrichment.hunter_company.city),
            postal_code = COALESCE(EXCLUDED.postal_code, enrichment.hunter_company.postal_code),
            street = COALESCE(EXCLUDED.street, enrichment.hunter_company.street),
            email_pattern = COALESCE(EXCLUDED.email_pattern, enrichment.hunter_company.email_pattern),
            company_type = COALESCE(EXCLUDED.company_type, enrichment.hunter_company.company_type),
            industry = COALESCE(EXCLUDED.industry, enrichment.hunter_company.industry),
            enriched_at = NOW(),
            updated_at = NOW()
    """, company_values, page_size=1000)
    print(f'  Upserted {len(company_values):,} companies')
    
    # Insert contacts
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
    
    # Link to outreach
    cur.execute("""
        UPDATE enrichment.hunter_company hc
        SET outreach_id = o.outreach_id
        FROM outreach.outreach o
        WHERE hc.domain = o.domain AND hc.outreach_id IS NULL
    """)
    print(f'  Linked {cur.rowcount:,} new companies to outreach_id')
    
    cur.execute("""
        UPDATE enrichment.hunter_contact hcon
        SET outreach_id = hc.outreach_id
        FROM enrichment.hunter_company hc
        WHERE hcon.domain = hc.domain AND hcon.outreach_id IS NULL AND hc.outreach_id IS NOT NULL
    """)
    print(f'  Linked {cur.rowcount:,} new contacts to outreach_id')
    
    conn.commit()
    
    # Totals
    print('\n--- TOTALS ---')
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company")
    print(f'Total companies now: {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
    print(f'Total contacts now: {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE email IS NOT NULL")
    print(f'Total emails: {cur.fetchone()[0]:,}')
    
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE outreach_id IS NOT NULL")
    print(f'Contacts linked to outreach: {cur.fetchone()[0]:,}')
    
    conn.close()
    print('\nDone!')

if __name__ == '__main__':
    main()
