#!/usr/bin/env python3
"""See what titles are available on domains with empty slots."""

import psycopg2
import os

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    print('='*70)
    print('JOB TITLES ON DOMAINS WITH EMPTY CFO SLOTS')
    print('='*70)

    cur.execute('''
        WITH empty_cfo_domains AS (
            SELECT DISTINCT LOWER(o.domain) as domain
            FROM people.company_slot cs
            JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            WHERE cs.is_filled = false AND cs.slot_type = 'CFO'
        )
        SELECT hc.job_title, COUNT(*)
        FROM enrichment.hunter_contact hc
        JOIN empty_cfo_domains d ON LOWER(hc.domain) = d.domain
        WHERE hc.email IS NOT NULL
        GROUP BY hc.job_title
        ORDER BY COUNT(*) DESC
        LIMIT 60
    ''')
    print('\nTop 60 job titles on domains with empty CFO slots:')
    for r in cur.fetchall():
        title = r[0] if r[0] else '(no title)'
        print(f'   {title:<50} {r[1]:>5,}')

    # Now filter for CFO-like in those domains
    print('\n' + '='*70)
    print('CFO-LIKE TITLES ON EMPTY CFO SLOT DOMAINS')
    print('='*70)
    cur.execute('''
        WITH empty_cfo_domains AS (
            SELECT DISTINCT LOWER(o.domain) as domain
            FROM people.company_slot cs
            JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            WHERE cs.is_filled = false AND cs.slot_type = 'CFO'
        )
        SELECT hc.job_title, hc.department, COUNT(*)
        FROM enrichment.hunter_contact hc
        JOIN empty_cfo_domains d ON LOWER(hc.domain) = d.domain
        WHERE hc.email IS NOT NULL
        AND (LOWER(hc.job_title) LIKE '%cfo%'
             OR LOWER(hc.job_title) LIKE '%chief financial%'
             OR LOWER(hc.job_title) LIKE '%controller%'
             OR LOWER(hc.job_title) LIKE '%finance%'
             OR LOWER(hc.job_title) LIKE '%treasurer%'
             OR LOWER(hc.job_title) LIKE '%accounting%')
        GROUP BY hc.job_title, hc.department
        ORDER BY COUNT(*) DESC
        LIMIT 30
    ''')
    total = 0
    for r in cur.fetchall():
        title = r[0] if r[0] else '(no title)'
        dept = r[1] if r[1] else '(NULL)'
        print(f'   {title:<40} {dept:<15} {r[2]:>5,}')
        total += r[2]
    print(f'\n   TOTAL CFO-LIKE ON EMPTY SLOT DOMAINS: {total:,}')

    # Same for HR
    print('\n' + '='*70)
    print('HR-LIKE TITLES ON EMPTY HR SLOT DOMAINS')
    print('='*70)
    cur.execute('''
        WITH empty_hr_domains AS (
            SELECT DISTINCT LOWER(o.domain) as domain
            FROM people.company_slot cs
            JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
            JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
            WHERE cs.is_filled = false AND cs.slot_type = 'HR'
        )
        SELECT hc.job_title, hc.department, COUNT(*)
        FROM enrichment.hunter_contact hc
        JOIN empty_hr_domains d ON LOWER(hc.domain) = d.domain
        WHERE hc.email IS NOT NULL
        AND (LOWER(hc.job_title) LIKE '%human resource%'
             OR LOWER(hc.job_title) LIKE '%hr %'
             OR LOWER(hc.job_title) LIKE '% hr'
             OR LOWER(hc.job_title) LIKE '%recrui%'
             OR LOWER(hc.job_title) LIKE '%talent%'
             OR LOWER(hc.job_title) LIKE '%people operation%'
             OR LOWER(hc.job_title) LIKE '%chro%'
             OR LOWER(hc.job_title) LIKE '%chief people%')
        GROUP BY hc.job_title, hc.department
        ORDER BY COUNT(*) DESC
        LIMIT 30
    ''')
    total = 0
    for r in cur.fetchall():
        title = r[0] if r[0] else '(no title)'
        dept = r[1] if r[1] else '(NULL)'
        print(f'   {title:<40} {dept:<15} {r[2]:>5,}')
        total += r[2]
    print(f'\n   TOTAL HR-LIKE ON EMPTY SLOT DOMAINS: {total:,}')

    conn.close()

if __name__ == '__main__':
    main()
