#!/usr/bin/env python3
"""Analyze gap between companies and people_master."""
import os
import psycopg2

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    
    # Total companies
    cur.execute('SELECT COUNT(*) FROM company.company_master')
    total_companies = cur.fetchone()[0]
    print(f'Total companies: {total_companies:,}')
    
    # Companies in target states
    cur.execute('''
        SELECT address_state, COUNT(*) 
        FROM company.company_master 
        WHERE address_state IN ('PA','OH','VA','NC','MD','KY','OK','DE','WV')
        GROUP BY address_state
        ORDER BY 2 DESC
    ''')
    print('\nCompanies by target state:')
    target_total = 0
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]:,}')
        target_total += row[1]
    print(f'  TOTAL: {target_total:,}')
    
    # Companies WITH people
    cur.execute('SELECT COUNT(DISTINCT company_unique_id) FROM people.people_master')
    companies_with_people = cur.fetchone()[0]
    print(f'\nCompanies WITH people: {companies_with_people:,}')
    
    # Gap
    print(f'Companies WITHOUT people: {target_total - companies_with_people:,}')
    
    # Companies with URLs but no people extracted yet
    cur.execute('''
        SELECT COUNT(DISTINCT cm.company_unique_id)
        FROM company.company_master cm
        JOIN company.company_source_urls csu ON cm.company_unique_id = csu.company_unique_id
        WHERE cm.address_state IN ('PA','OH','VA','NC','MD','KY','OK','DE','WV')
        AND NOT EXISTS (
            SELECT 1 FROM people.people_master pm 
            WHERE pm.company_unique_id = cm.company_unique_id
        )
    ''')
    print(f'\nCompanies with URLs but NO people: {cur.fetchone()[0]:,}')
    
    # Check staging - are there people in staging not yet promoted?
    cur.execute('''
        SELECT status, COUNT(*) 
        FROM people.people_staging 
        GROUP BY status
        ORDER BY 2 DESC
    ''')
    print('\nStaging status:')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]:,}')
    
    # Companies in staging not in people_master
    cur.execute('''
        SELECT COUNT(DISTINCT ps.company_unique_id)
        FROM people.people_staging ps
        WHERE NOT EXISTS (
            SELECT 1 FROM people.people_master pm 
            WHERE pm.company_unique_id = ps.company_unique_id
        )
    ''')
    print(f'\nCompanies in staging but not in people_master: {cur.fetchone()[0]:,}')
    
    # Check web_pages_combined - companies with pages but no people
    # First find the schema
    cur.execute("""
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_name = 'web_pages_combined'
    """)
    result = cur.fetchone()
    if result:
        schema, table = result
        print(f'\nweb_pages_combined found in schema: {schema}')
        cur.execute(f'''
            SELECT COUNT(DISTINCT wpc.company_unique_id)
            FROM {schema}.web_pages_combined wpc
            JOIN company.company_master cm ON wpc.company_unique_id = cm.company_unique_id
            WHERE cm.address_state IN ('PA','OH','VA','NC','MD','KY','OK','DE','WV')
            AND wpc.source_type IN ('leadership_page', 'team_page', 'about_page', 'blog')
            AND NOT EXISTS (
                SELECT 1 FROM people.people_master pm 
                WHERE pm.company_unique_id = wpc.company_unique_id
            )
        ''')
        print(f'Companies with web pages (4 types) but no people: {cur.fetchone()[0]:,}')
    else:
        print('\nweb_pages_combined table not found, checking company_source_urls...')
        cur.execute('''
            SELECT COUNT(DISTINCT csu.company_unique_id)
            FROM company.company_source_urls csu
            JOIN company.company_master cm ON csu.company_unique_id = cm.company_unique_id
            WHERE cm.address_state IN ('PA','OH','VA','NC','MD','KY','OK','DE','WV')
            AND csu.source_type IN ('leadership_page', 'team_page', 'about_page', 'blog')
            AND NOT EXISTS (
                SELECT 1 FROM people.people_master pm 
                WHERE pm.company_unique_id = csu.company_unique_id
            )
        ''')
        print(f'Companies with URLs (4 types) but no people: {cur.fetchone()[0]:,}')
    
    conn.close()

if __name__ == '__main__':
    main()
