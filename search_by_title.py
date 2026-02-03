#!/usr/bin/env python3
"""Search all departments for CFO/HR titles."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*70)
    print('SEARCHING ALL DEPARTMENTS FOR CFO/HR BY JOB TITLE')
    print('='*70)

    # CFO-like titles across ALL departments
    print('\n' + '='*70)
    print('CFO-LIKE TITLES (searching by job_title, ANY department)')
    print('='*70)
    cur.execute('''
        SELECT job_title, department, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE email IS NOT NULL
        AND (LOWER(job_title) LIKE '%cfo%'
             OR LOWER(job_title) LIKE '%chief financial%'
             OR LOWER(job_title) LIKE '%controller%'
             OR LOWER(job_title) LIKE '%finance%'
             OR LOWER(job_title) LIKE '%treasurer%'
             OR LOWER(job_title) LIKE '%accounting%'
             OR LOWER(job_title) LIKE '%bookkeeper%')
        GROUP BY job_title, department
        ORDER BY COUNT(*) DESC
        LIMIT 40
    ''')
    total = 0
    for r in cur.fetchall():
        dept = r[1] if r[1] else '(NULL)'
        print(f'   {r[0]:<45} {dept:<15} {r[2]:>5,}')
        total += r[2]
    print(f'\n   SUBTOTAL (top 40): {total:,}')

    # Total CFO-like
    cur.execute('''
        SELECT COUNT(*)
        FROM enrichment.hunter_contact
        WHERE email IS NOT NULL
        AND (LOWER(job_title) LIKE '%cfo%'
             OR LOWER(job_title) LIKE '%chief financial%'
             OR LOWER(job_title) LIKE '%controller%'
             OR LOWER(job_title) LIKE '%finance%'
             OR LOWER(job_title) LIKE '%treasurer%'
             OR LOWER(job_title) LIKE '%accounting%'
             OR LOWER(job_title) LIKE '%bookkeeper%')
    ''')
    print(f'   TOTAL CFO-LIKE CONTACTS: {cur.fetchone()[0]:,}')

    # HR-like titles across ALL departments
    print('\n' + '='*70)
    print('HR-LIKE TITLES (searching by job_title, ANY department)')
    print('='*70)
    cur.execute('''
        SELECT job_title, department, COUNT(*)
        FROM enrichment.hunter_contact
        WHERE email IS NOT NULL
        AND (LOWER(job_title) LIKE '%human resource%'
             OR LOWER(job_title) LIKE '%hr %'
             OR LOWER(job_title) LIKE '% hr'
             OR LOWER(job_title) LIKE '%recrui%'
             OR LOWER(job_title) LIKE '%talent%'
             OR LOWER(job_title) LIKE '%people operation%'
             OR LOWER(job_title) LIKE '%chro%'
             OR LOWER(job_title) LIKE '%chief people%')
        GROUP BY job_title, department
        ORDER BY COUNT(*) DESC
        LIMIT 40
    ''')
    total = 0
    for r in cur.fetchall():
        dept = r[1] if r[1] else '(NULL)'
        print(f'   {r[0]:<45} {dept:<15} {r[2]:>5,}')
        total += r[2]
    print(f'\n   SUBTOTAL (top 40): {total:,}')

    # Total HR-like
    cur.execute('''
        SELECT COUNT(*)
        FROM enrichment.hunter_contact
        WHERE email IS NOT NULL
        AND (LOWER(job_title) LIKE '%human resource%'
             OR LOWER(job_title) LIKE '%hr %'
             OR LOWER(job_title) LIKE '% hr'
             OR LOWER(job_title) LIKE '%recrui%'
             OR LOWER(job_title) LIKE '%talent%'
             OR LOWER(job_title) LIKE '%people operation%'
             OR LOWER(job_title) LIKE '%chro%'
             OR LOWER(job_title) LIKE '%chief people%')
    ''')
    print(f'   TOTAL HR-LIKE CONTACTS: {cur.fetchone()[0]:,}')

    # Now the key question: how many of these match EMPTY SLOT DOMAINS?
    print('\n' + '='*70)
    print('FILLABLE SLOTS (title-based, ignore department)')
    print('='*70)

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
             OR LOWER(hc.job_title) LIKE '%accounting%'
             OR LOWER(hc.job_title) LIKE '%bookkeeper%')
    ''')
    cfo_fillable = cur.fetchone()[0]
    print(f'   CFO slots fillable (by title): {cfo_fillable:,}')

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
             OR LOWER(hc.job_title) LIKE '%people operation%'
             OR LOWER(hc.job_title) LIKE '%chro%'
             OR LOWER(hc.job_title) LIKE '%chief people%')
    ''')
    hr_fillable = cur.fetchone()[0]
    print(f'   HR slots fillable (by title): {hr_fillable:,}')

    conn.close()

if __name__ == '__main__':
    main()
