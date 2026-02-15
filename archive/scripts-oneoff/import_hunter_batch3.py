#!/usr/bin/env python3
"""
Import Hunter.io enrichment data - Batch 3 (remaining companies)
Imports company and contact data into enrichment.hunter_company and enrichment.hunter_contact
"""
import psycopg2
import csv
import os
from datetime import datetime

CSV_PATH = r"C:\Users\CUSTOM PC\Desktop\Hunter IO\remaining-companies-2129584.csv"

def parse_headcount(headcount_str):
    """Parse headcount string like '201-500' into min/max."""
    if not headcount_str:
        return None, None
    headcount_str = str(headcount_str).strip()
    if '-' in headcount_str:
        parts = headcount_str.split('-')
        try:
            return int(parts[0].replace(',', '')), int(parts[1].replace(',', '').replace('+', ''))
        except:
            return None, None
    elif '+' in headcount_str:
        try:
            return int(headcount_str.replace('+', '').replace(',', '')), None
        except:
            return None, None
    else:
        try:
            val = int(headcount_str.replace(',', ''))
            return val, val
        except:
            return None, None

def classify_seniority(title):
    """Classify job title into seniority level."""
    if not title:
        return 'Unknown'
    title_lower = title.lower()
    
    if any(x in title_lower for x in ['ceo', 'cfo', 'cto', 'coo', 'cmo', 'cio', 'chief', 'owner', 'founder', 'president', 'partner']):
        return 'C-Level/Owner'
    elif any(x in title_lower for x in ['vice president', 'vp ', 'v.p.', 'svp', 'evp']):
        return 'VP'
    elif any(x in title_lower for x in ['director', 'head of']):
        return 'Director'
    elif any(x in title_lower for x in ['manager', 'supervisor', 'lead', 'team lead']):
        return 'Manager'
    elif any(x in title_lower for x in ['senior', 'sr.', 'sr ', 'principal']):
        return 'Senior'
    elif any(x in title_lower for x in ['junior', 'jr.', 'jr ', 'associate', 'assistant', 'intern', 'trainee']):
        return 'Junior'
    else:
        return 'Individual Contributor'

def normalize_department(dept):
    """Normalize department names."""
    if not dept:
        return None
    dept_lower = dept.lower()
    
    mapping = {
        'executive': 'Executive',
        'management': 'Management',
        'sales': 'Sales',
        'marketing': 'Marketing',
        'finance': 'Finance',
        'hr': 'Human Resources',
        'human resources': 'Human Resources',
        'it': 'IT/Engineering',
        'engineering': 'IT/Engineering',
        'it / engineering': 'IT/Engineering',
        'operations': 'Operations',
        'operations & logistics': 'Operations',
        'legal': 'Legal',
        'support': 'Support',
        'medical': 'Medical/Health',
        'medical & health': 'Medical/Health',
    }
    
    for key, value in mapping.items():
        if key in dept_lower:
            return value
    return dept

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    print('='*70)
    print('HUNTER ENRICHMENT IMPORT - BATCH 3 (Remaining Companies)')
    print('='*70)
    
    # Get current counts
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company")
    companies_before = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
    contacts_before = cur.fetchone()[0]
    
    print(f'\nBefore: {companies_before:,} companies, {contacts_before:,} contacts')
    
    # Build domain -> outreach_id mapping
    print('\nBuilding domain -> outreach_id mapping...')
    cur.execute("SELECT LOWER(domain), sovereign_id FROM outreach.outreach WHERE domain IS NOT NULL")
    domain_to_outreach = {r[0]: r[1] for r in cur.fetchall()}
    print(f'  {len(domain_to_outreach):,} domains mapped')
    
    # Read CSV and group by domain
    print(f'\nReading {CSV_PATH}...')
    companies = {}
    contacts = []
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            domain = row.get('Domain name', '').lower().strip()
            if not domain:
                continue
            
            # Aggregate company info (first row per domain wins for company data)
            if domain not in companies:
                hc_min, hc_max = parse_headcount(row.get('Headcount', ''))
                companies[domain] = {
                    'domain': domain,
                    'organization': row.get('Organization', ''),
                    'headcount': row.get('Headcount', ''),
                    'headcount_min': hc_min,
                    'headcount_max': hc_max,
                    'country': row.get('Country', ''),
                    'state': row.get('State', ''),
                    'city': row.get('City', ''),
                    'postal_code': row.get('Postal code', ''),
                    'street': row.get('Street', ''),
                    'email_pattern': row.get('Pattern', ''),
                    'company_type': row.get('Company type', ''),
                    'industry': row.get('Industry', ''),
                }
            
            # Collect contact info
            email = row.get('Email address', '').strip()
            if email and row.get('Type', '') == 'personal':
                contacts.append({
                    'domain': domain,
                    'email': email,
                    'first_name': row.get('First name', ''),
                    'last_name': row.get('Last name', ''),
                    'department': row.get('Department', ''),
                    'job_title': row.get('Job title', ''),
                    'position_raw': row.get('Position raw', ''),
                    'linkedin_url': row.get('LinkedIn URL', ''),
                    'twitter_handle': row.get('Twitter handle', ''),
                    'phone_number': row.get('Phone number', ''),
                    'confidence_score': int(row.get('Confidence score', 0) or 0),
                    'num_sources': int(row.get('Number of sources', 0) or 0),
                })
    
    print(f'  Found {len(companies):,} unique companies')
    print(f'  Found {len(contacts):,} personal contacts')
    
    # Insert/update companies
    print('\nInserting companies...')
    companies_inserted = 0
    companies_updated = 0
    
    for domain, c in companies.items():
        outreach_id = domain_to_outreach.get(domain)
        
        cur.execute("""
            INSERT INTO enrichment.hunter_company (
                domain, organization, headcount, headcount_min, headcount_max,
                country, state, city, postal_code, street,
                email_pattern, company_type, industry, industry_normalized,
                outreach_id, source, enriched_at, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                'hunter_batch3', NOW(), NOW(), NOW()
            )
            ON CONFLICT (domain) DO UPDATE SET
                organization = COALESCE(EXCLUDED.organization, enrichment.hunter_company.organization),
                headcount = COALESCE(EXCLUDED.headcount, enrichment.hunter_company.headcount),
                headcount_min = COALESCE(EXCLUDED.headcount_min, enrichment.hunter_company.headcount_min),
                headcount_max = COALESCE(EXCLUDED.headcount_max, enrichment.hunter_company.headcount_max),
                email_pattern = COALESCE(EXCLUDED.email_pattern, enrichment.hunter_company.email_pattern),
                updated_at = NOW()
            RETURNING (xmax = 0) AS inserted
        """, (
            c['domain'], c['organization'], c['headcount'], c['headcount_min'], c['headcount_max'],
            c['country'], c['state'], c['city'], c['postal_code'], c['street'],
            c['email_pattern'], c['company_type'], c['industry'], c['industry'],
            outreach_id
        ))
        result = cur.fetchone()
        if result and result[0]:
            companies_inserted += 1
        else:
            companies_updated += 1
        
        if (companies_inserted + companies_updated) % 500 == 0:
            conn.commit()
            print(f'    {companies_inserted + companies_updated:,} companies processed...')
    
    conn.commit()
    print(f'  Inserted: {companies_inserted:,}, Updated: {companies_updated:,}')
    
    # Build domain -> hunter_company.id mapping
    cur.execute("SELECT domain, id, outreach_id FROM enrichment.hunter_company")
    domain_to_company = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    
    # Insert contacts
    print('\nInserting contacts...')
    contacts_inserted = 0
    contacts_skipped = 0
    
    for c in contacts:
        company_info = domain_to_company.get(c['domain'])
        if not company_info:
            contacts_skipped += 1
            continue
        
        company_id, outreach_id = company_info
        seniority = classify_seniority(c['job_title'])
        dept_normalized = normalize_department(c['department'])
        is_decision_maker = seniority in ['C-Level/Owner', 'VP', 'Director']
        
        full_name = f"{c['first_name']} {c['last_name']}".strip() if c['first_name'] or c['last_name'] else None
        
        try:
            cur.execute("""
                INSERT INTO enrichment.hunter_contact (
                    hunter_company_id, domain, email, first_name, last_name, full_name,
                    department, department_normalized, job_title, position_raw,
                    seniority_level, is_decision_maker,
                    linkedin_url, twitter_handle, phone_number,
                    confidence_score, num_sources, outreach_id,
                    source, created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    'hunter_batch3', NOW(), NOW()
                )
                ON CONFLICT (email) DO UPDATE SET
                    job_title = COALESCE(EXCLUDED.job_title, enrichment.hunter_contact.job_title),
                    linkedin_url = COALESCE(EXCLUDED.linkedin_url, enrichment.hunter_contact.linkedin_url),
                    confidence_score = GREATEST(EXCLUDED.confidence_score, enrichment.hunter_contact.confidence_score),
                    updated_at = NOW()
            """, (
                company_id, c['domain'], c['email'], c['first_name'], c['last_name'], full_name,
                c['department'], dept_normalized, c['job_title'], c['position_raw'],
                seniority, is_decision_maker,
                c['linkedin_url'] or None, c['twitter_handle'] or None, c['phone_number'] or None,
                c['confidence_score'], c['num_sources'], outreach_id
            ))
            contacts_inserted += 1
        except Exception as e:
            contacts_skipped += 1
            if contacts_skipped <= 3:
                print(f'    Error: {str(e)[:60]}')
        
        if contacts_inserted % 1000 == 0:
            conn.commit()
            print(f'    {contacts_inserted:,} contacts inserted...')
    
    conn.commit()
    print(f'  Inserted/Updated: {contacts_inserted:,}, Skipped: {contacts_skipped:,}')
    
    # Final counts
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_company")
    companies_after = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrichment.hunter_contact")
    contacts_after = cur.fetchone()[0]
    
    # Stats on new data
    cur.execute("""
        SELECT COUNT(*), COUNT(DISTINCT outreach_id)
        FROM enrichment.hunter_contact
        WHERE source = 'hunter_batch3'
    """)
    batch3_contacts, batch3_linked = cur.fetchone()
    
    cur.execute("""
        SELECT seniority_level, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE source = 'hunter_batch3'
        GROUP BY seniority_level
        ORDER BY COUNT(*) DESC
    """)
    print('\nBatch 3 Seniority Breakdown:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]:,}')
    
    print('\n' + '='*70)
    print('IMPORT COMPLETE')
    print('='*70)
    print(f'Companies: {companies_before:,} -> {companies_after:,} (+{companies_after - companies_before:,})')
    print(f'Contacts: {contacts_before:,} -> {contacts_after:,} (+{contacts_after - contacts_before:,})')
    print(f'Batch 3 contacts linked to outreach: {batch3_linked:,}')
    
    conn.close()

if __name__ == '__main__':
    main()
