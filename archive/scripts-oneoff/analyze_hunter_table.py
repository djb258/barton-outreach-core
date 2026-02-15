#!/usr/bin/env python3
"""Analyze the hunter_contact table for slot filling potential."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*70)
    print('HUNTER_CONTACT TABLE ANALYSIS')
    print('='*70)

    # Total records
    cur.execute('SELECT COUNT(*) FROM enrichment.hunter_contact')
    total = cur.fetchone()[0]
    print(f'\nTotal contacts: {total:,}')

    # Department distribution
    print('\n' + '-'*70)
    print('DEPARTMENT DISTRIBUTION')
    print('-'*70)
    cur.execute('''
        SELECT department, COUNT(*) as cnt
        FROM enrichment.hunter_contact
        GROUP BY department
        ORDER BY cnt DESC
    ''')
    for row in cur.fetchall():
        dept = row[0] if row[0] else '(NULL)'
        print(f'  {dept:<30} {row[1]:>8,}')

    # Current slot status
    print('\n' + '-'*70)
    print('CURRENT SLOT STATUS')
    print('-'*70)
    cur.execute('''
        SELECT slot_type, 
               COUNT(*) as total,
               SUM(CASE WHEN is_filled THEN 1 ELSE 0 END) as filled,
               SUM(CASE WHEN NOT is_filled THEN 1 ELSE 0 END) as empty
        FROM people.company_slot
        GROUP BY slot_type
        ORDER BY slot_type
    ''')
    for row in cur.fetchall():
        print(f'  {row[0]}: {row[1]:,} total | {row[2]:,} filled | {row[3]:,} empty')

    # Fillable slots by department
    print('\n' + '-'*70)
    print('FILLABLE SLOTS BY DEPARTMENT')
    print('-'*70)
    
    mappings = [
        ('CEO', 'Executive'),
        ('CEO', 'Management'),
        ('CFO', 'Finance'),
        ('HR', 'HR'),
    ]
    
    for slot_type, department in mappings:
        cur.execute('''
            WITH cm_domains AS (
                SELECT 
                    company_unique_id,
                    LOWER(REGEXP_REPLACE(
                        REGEXP_REPLACE(website_url, '^https?://(www\\.)?', ''),
                        '/.*$', ''
                    )) as domain
                FROM company.company_master
                WHERE website_url IS NOT NULL
            )
            SELECT COUNT(DISTINCT cs.slot_id)
            FROM people.company_slot cs
            JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
            JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
            WHERE cs.is_filled = false
            AND cs.slot_type = %s
            AND hc.email IS NOT NULL
            AND hc.first_name IS NOT NULL
            AND hc.department = %s
        ''', (slot_type, department))
        fillable = cur.fetchone()[0]
        print(f'  {slot_type} from {department:<15}: {fillable:,} slots')

    # Top job titles in Executive department
    print('\n' + '-'*70)
    print('TOP JOB TITLES IN EXECUTIVE DEPARTMENT')
    print('-'*70)
    cur.execute('''
        SELECT job_title, COUNT(*) as cnt
        FROM enrichment.hunter_contact
        WHERE department = 'Executive'
        GROUP BY job_title
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    for row in cur.fetchall():
        print(f'  {row[0]:<45} {row[1]:>6,}')

    # Top job titles in Finance department
    print('\n' + '-'*70)
    print('TOP JOB TITLES IN FINANCE DEPARTMENT')
    print('-'*70)
    cur.execute('''
        SELECT job_title, COUNT(*) as cnt
        FROM enrichment.hunter_contact
        WHERE department = 'Finance'
        GROUP BY job_title
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    for row in cur.fetchall():
        print(f'  {row[0]:<45} {row[1]:>6,}')

    # Top job titles in HR department
    print('\n' + '-'*70)
    print('TOP JOB TITLES IN HR DEPARTMENT')
    print('-'*70)
    cur.execute('''
        SELECT job_title, COUNT(*) as cnt
        FROM enrichment.hunter_contact
        WHERE department = 'HR'
        GROUP BY job_title
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    for row in cur.fetchall():
        print(f'  {row[0]:<45} {row[1]:>6,}')

    # Top job titles in Management department
    print('\n' + '-'*70)
    print('TOP JOB TITLES IN MANAGEMENT DEPARTMENT')
    print('-'*70)
    cur.execute('''
        SELECT job_title, COUNT(*) as cnt
        FROM enrichment.hunter_contact
        WHERE department = 'Management'
        GROUP BY job_title
        ORDER BY cnt DESC
        LIMIT 20
    ''')
    for row in cur.fetchall():
        print(f'  {row[0]:<45} {row[1]:>6,}')

    conn.close()

if __name__ == '__main__':
    main()
