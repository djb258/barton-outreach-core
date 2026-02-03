#!/usr/bin/env python3
"""Check Executive/Management departments for CFO and HR titles."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*70)
    print('CFO/HR TITLES IN EXECUTIVE & MANAGEMENT DEPARTMENTS')
    print('='*70)

    # CFO-like titles in Executive/Management
    print('\nCFO-LIKE TITLES IN EXECUTIVE/MANAGEMENT/OPS:')
    cur.execute("""
        SELECT job_title, department, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE department IN ('Executive', 'Management', 'Operations & logistics')
        AND (LOWER(job_title) LIKE '%cfo%' 
             OR LOWER(job_title) LIKE '%chief financial%'
             OR LOWER(job_title) LIKE '%controller%'
             OR LOWER(job_title) LIKE '%finance%'
             OR LOWER(job_title) LIKE '%treasurer%'
             OR LOWER(job_title) LIKE '%accounting%')
        AND email IS NOT NULL
        GROUP BY job_title, department
        ORDER BY COUNT(*) DESC
        LIMIT 25
    """)
    total_cfo = 0
    for r in cur.fetchall():
        print(f'  {r[0]:<45} {r[1]:<15} {r[2]:>5,}')
        total_cfo += r[2]
    print(f'\n  TOTAL CFO-like in Exec/Mgmt/Ops: {total_cfo:,}')

    # HR-like titles in Executive/Management  
    print('\n' + '-'*70)
    print('HR-LIKE TITLES IN EXECUTIVE/MANAGEMENT/OPS:')
    cur.execute("""
        SELECT job_title, department, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE department IN ('Executive', 'Management', 'Operations & logistics')
        AND (LOWER(job_title) LIKE '%human resource%'
             OR LOWER(job_title) LIKE '%hr %'
             OR LOWER(job_title) LIKE '% hr'
             OR LOWER(job_title) LIKE '%recrui%'
             OR LOWER(job_title) LIKE '%talent%'
             OR LOWER(job_title) LIKE '%people operation%'
             OR LOWER(job_title) LIKE '%chro%')
        AND email IS NOT NULL
        GROUP BY job_title, department
        ORDER BY COUNT(*) DESC
        LIMIT 25
    """)
    total_hr = 0
    for r in cur.fetchall():
        print(f'  {r[0]:<45} {r[1]:<15} {r[2]:>5,}')
        total_hr += r[2]
    print(f'\n  TOTAL HR-like in Exec/Mgmt/Ops: {total_hr:,}')

    # Now check how many can fill EMPTY slots
    print('\n' + '='*70)
    print('FILLABLE EMPTY SLOTS FROM EXEC/MGMT DEPARTMENTS')
    print('='*70)
    
    # CFO slots fillable from Executive/Management with CFO titles
    cur.execute("""
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
        AND hc.department IN ('Executive', 'Management', 'Operations & logistics')
        AND (LOWER(hc.job_title) LIKE '%cfo%' 
             OR LOWER(hc.job_title) LIKE '%chief financial%'
             OR LOWER(hc.job_title) LIKE '%controller%'
             OR LOWER(hc.job_title) LIKE '%finance%'
             OR LOWER(hc.job_title) LIKE '%treasurer%'
             OR LOWER(hc.job_title) LIKE '%accounting%')
    """)
    cfo_fillable = cur.fetchone()[0]
    print(f'\n  CFO slots fillable from Exec/Mgmt with CFO titles: {cfo_fillable:,}')

    # HR slots fillable from Executive/Management with HR titles
    cur.execute("""
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
        AND hc.department IN ('Executive', 'Management', 'Operations & logistics')
        AND (LOWER(hc.job_title) LIKE '%human resource%'
             OR LOWER(hc.job_title) LIKE '%hr %'
             OR LOWER(hc.job_title) LIKE '% hr'
             OR LOWER(hc.job_title) LIKE '%recrui%'
             OR LOWER(hc.job_title) LIKE '%talent%'
             OR LOWER(hc.job_title) LIKE '%people operation%'
             OR LOWER(hc.job_title) LIKE '%chro%')
    """)
    hr_fillable = cur.fetchone()[0]
    print(f'  HR slots fillable from Exec/Mgmt with HR titles: {hr_fillable:,}')

    conn.close()

if __name__ == '__main__':
    main()
