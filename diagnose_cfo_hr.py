#!/usr/bin/env python3
"""Diagnose why CFO/HR slots aren't being filled."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*70)
    print('ALTERNATIVE: FILL BY JOB TITLE (IGNORE DEPARTMENT)')
    print('='*70)

    # CFO-like titles across ALL departments
    print('\n1. CFO-LIKE TITLES IN HUNTER (any department):')
    cur.execute('''
        SELECT job_title, department, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE LOWER(job_title) LIKE ANY(ARRAY['%cfo%', '%chief financial%', '%controller%', '%finance director%', '%vp finance%', '%treasurer%'])
        AND email IS NOT NULL
        GROUP BY job_title, department
        ORDER BY COUNT(*) DESC
        LIMIT 20
    ''')
    for r in cur.fetchall():
        dept = r[1] if r[1] else '(none)'
        print(f'   {r[0]:<40} {dept:<15} {r[2]:>5,}')

    # HR-like titles across ALL departments
    print('\n2. HR-LIKE TITLES IN HUNTER (any department):')
    cur.execute('''
        SELECT job_title, department, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE LOWER(job_title) LIKE ANY(ARRAY['%human resource%', '%hr %', '% hr', '%recrui%', '%talent%', '%people operation%'])
        AND email IS NOT NULL
        GROUP BY job_title, department
        ORDER BY COUNT(*) DESC
        LIMIT 20
    ''')
    for r in cur.fetchall():
        dept = r[1] if r[1] else '(none)'
        print(f'   {r[0]:<40} {dept:<15} {r[2]:>5,}')

    # How many fillable if we use TITLE instead of DEPARTMENT?
    print('\n3. FILLABLE IF WE USE TITLE-BASED MATCHING:')
    cur.execute('''
        WITH cm_domains AS (
            SELECT company_unique_id,
                   LOWER(REGEXP_REPLACE(REGEXP_REPLACE(website_url, '^https?://(www\\.)?', ''), '/.*$', '')) as domain
            FROM company.company_master WHERE website_url IS NOT NULL
        )
        SELECT COUNT(DISTINCT cs.slot_id)
        FROM people.company_slot cs
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.is_filled = false AND cs.slot_type = 'CFO'
        AND hc.email IS NOT NULL AND hc.first_name IS NOT NULL
        AND (LOWER(hc.job_title) LIKE '%cfo%' 
             OR LOWER(hc.job_title) LIKE '%chief financial%'
             OR LOWER(hc.job_title) LIKE '%controller%'
             OR LOWER(hc.job_title) LIKE '%finance%'
             OR LOWER(hc.job_title) LIKE '%treasurer%'
             OR LOWER(hc.job_title) LIKE '%accounting%')
    ''')
    cfo_by_title = cur.fetchone()[0]
    print(f'   CFO slots fillable by TITLE match: {cfo_by_title:,}')

    cur.execute('''
        WITH cm_domains AS (
            SELECT company_unique_id,
                   LOWER(REGEXP_REPLACE(REGEXP_REPLACE(website_url, '^https?://(www\\.)?', ''), '/.*$', '')) as domain
            FROM company.company_master WHERE website_url IS NOT NULL
        )
        SELECT COUNT(DISTINCT cs.slot_id)
        FROM people.company_slot cs
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.is_filled = false AND cs.slot_type = 'HR'
        AND hc.email IS NOT NULL AND hc.first_name IS NOT NULL
        AND (LOWER(hc.job_title) LIKE '%human resource%'
             OR LOWER(hc.job_title) LIKE '%hr %'
             OR LOWER(hc.job_title) LIKE '% hr'
             OR LOWER(hc.job_title) LIKE '%recrui%'
             OR LOWER(hc.job_title) LIKE '%talent%'
             OR LOWER(hc.job_title) LIKE '%people operation%')
    ''')
    hr_by_title = cur.fetchone()[0]
    print(f'   HR slots fillable by TITLE match: {hr_by_title:,}')

    conn.close()

if __name__ == '__main__':
    main()
