#!/usr/bin/env python3
"""
Full People Data Audit
======================
Shows ALL people data across all schemas.
"""

import psycopg2
import os


def main():
    conn = psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )
    cur = conn.cursor()

    print('=' * 70)
    print('PEOPLE DATA SUMMARY - KEY TABLES')
    print('=' * 70)

    # Key tables with counts
    tables = [
        'people.people_master',
        'people.people_staging', 
        'people.company_slot',
        'intake.people_raw_intake',
        'outreach.people',
    ]

    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f'{table:35} | {count:>10,} records')
        except Exception as e:
            print(f'{table:35} | ERROR')
            conn.rollback()

    # Check people.company_slot in detail
    print()
    print('=' * 70)
    print('PEOPLE.COMPANY_SLOT - SLOT FILL STATUS')
    print('=' * 70)
    cur.execute("""
        SELECT 
            COUNT(*) as total_slots,
            COUNT(*) FILTER (WHERE is_filled = TRUE) as filled,
            COUNT(*) FILTER (WHERE person_unique_id IS NOT NULL) as has_person,
            COUNT(DISTINCT company_unique_id) as unique_companies
        FROM people.company_slot
    """)
    row = cur.fetchone()
    print(f'Total Slots:      {row[0]:,}')
    print(f'Filled:           {row[1]:,}')
    print(f'Has Person Link:  {row[2]:,}')
    print(f'Unique Companies: {row[3]:,}')

    # Breakdown by slot type
    print()
    print('BY SLOT TYPE:')
    cur.execute("""
        SELECT 
            slot_type,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE is_filled = TRUE) as filled,
            COUNT(*) FILTER (WHERE person_unique_id IS NOT NULL) as has_person
        FROM people.company_slot
        GROUP BY slot_type
        ORDER BY total DESC
    """)
    for row in cur.fetchall():
        print(f'  {row[0]:12} | Total: {row[1]:>6,} | Filled: {row[2]:>6,} | Has Person: {row[3]:>6,}')

    # Check people_master emails
    print()
    print('=' * 70)
    print('PEOPLE.PEOPLE_MASTER - EMAIL STATUS')
    print('=' * 70)
    cur.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
            COUNT(*) FILTER (WHERE email_verified = TRUE) as verified,
            COUNT(*) FILTER (WHERE email_verified = FALSE OR email_verified IS NULL) as unverified,
            COUNT(*) FILTER (WHERE email_verified_at IS NOT NULL) as has_timestamp,
            COUNT(DISTINCT company_unique_id) as unique_companies
        FROM people.people_master
    """)
    row = cur.fetchone()
    print(f'Total People:     {row[0]:,}')
    print(f'Has Email:        {row[1]:,}')
    print(f'Verified (flag):  {row[2]:,}')
    print(f'Unverified:       {row[3]:,}')
    print(f'Has Timestamp:    {row[4]:,} (actually API verified)')
    print(f'Unique Companies: {row[5]:,}')

    # Breakdown by verification status
    print()
    print('VERIFICATION BREAKDOWN:')
    cur.execute("""
        SELECT 
            CASE 
                WHEN email IS NULL OR email = '' THEN 'No Email'
                WHEN email_verified = TRUE AND email_verified_at IS NOT NULL THEN 'API Verified'
                WHEN email_verified = TRUE AND email_verified_at IS NULL THEN 'Flagged (not API verified)'
                ELSE 'Unverified'
            END as status,
            COUNT(*) as cnt
        FROM people.people_master
        GROUP BY 1
        ORDER BY cnt DESC
    """)
    for row in cur.fetchall():
        print(f'  {row[0]:35} | {row[1]:>8,}')

    # Sample emails from people_master
    print()
    print('SAMPLE EMAILS FROM people.people_master (first 10 with email):')
    cur.execute("""
        SELECT unique_id, full_name, email, email_verified, email_verified_at
        FROM people.people_master
        WHERE email IS NOT NULL AND email != ''
        ORDER BY created_at DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        pid = str(row[0])[:12] if row[0] else 'N/A'
        name = str(row[1])[:20] if row[1] else 'N/A'
        email = str(row[2])[:30] if row[2] else 'N/A'
        verified = '✓' if row[3] else '✗'
        ts = '(API)' if row[4] else '(no ts)'
        print(f'  {pid:14} | {name:20} | {email:30} | {verified} {ts}')

    # Filled slots with people_master join
    print()
    print('=' * 70)
    print('FILLED SLOTS WITH EMAILS (company_slot + people_master)')
    print('=' * 70)
    cur.execute("""
        SELECT 
            COUNT(*) as filled_slots,
            COUNT(*) FILTER (WHERE pm.email IS NOT NULL AND pm.email != '') as has_email,
            COUNT(*) FILTER (WHERE pm.email_verified = TRUE) as verified,
            COUNT(*) FILTER (WHERE pm.email_verified_at IS NOT NULL) as api_verified
        FROM people.company_slot cs
        JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
        WHERE cs.is_filled = TRUE
    """)
    row = cur.fetchone()
    print(f'Filled Slots:     {row[0]:,}')
    print(f'Has Email:        {row[1]:,}')
    print(f'Verified (flag):  {row[2]:,}')
    print(f'API Verified:     {row[3]:,}')

    # VERIFICATION STATUS across tables
    print()
    print('=' * 70)
    print('EMAILS AVAILABLE FOR MILLIONVERIFIER')
    print('=' * 70)
    
    # Unverified emails in people_master
    cur.execute("""
        SELECT COUNT(*) 
        FROM people.people_master
        WHERE email IS NOT NULL AND email != ''
        AND (email_verified = FALSE OR email_verified IS NULL OR email_verified_at IS NULL)
    """)
    unverified = cur.fetchone()[0]
    
    # Total emails in people_master
    cur.execute("""
        SELECT COUNT(*) 
        FROM people.people_master
        WHERE email IS NOT NULL AND email != ''
    """)
    total_emails = cur.fetchone()[0]
    
    print(f'Total emails in people_master:   {total_emails:,}')
    print(f'Need verification (no API ts):   {unverified:,}')
    print()
    print(f'ESTIMATED COST @ $0.001/email:   ${unverified * 0.001:,.2f}')

    conn.close()


if __name__ == "__main__":
    main()
