#!/usr/bin/env python3
"""
Check Email Verification Status
================================
Quick script to check current state of emails in outreach.people table.

Usage:
    doppler run -- python scripts/check_email_status.py
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

    # Current people stats
    cur.execute("""
        SELECT 
            COUNT(*) as total_people,
            COUNT(DISTINCT outreach_id) as unique_companies,
            COUNT(*) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
            COUNT(*) FILTER (WHERE email_verified = TRUE) as verified,
            COUNT(*) FILTER (WHERE email_verified = FALSE OR email_verified IS NULL) as unverified
        FROM outreach.people
    """)
    row = cur.fetchone()
    print('=' * 60)
    print('CURRENT PEOPLE DATA STATUS')
    print('=' * 60)
    print(f'Total People Records: {row[0]}')
    print(f'Unique Companies:     {row[1]}')
    print(f'Have Email:           {row[2]}')
    print(f'Verified (TRUE):      {row[3]}')
    print(f'Unverified:           {row[4]}')

    # Breakdown by slot type
    print()
    print('BY SLOT TYPE:')
    cur.execute("""
        SELECT 
            COALESCE(slot_type, 'UNKNOWN') as slot,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE email IS NOT NULL) as has_email,
            COUNT(*) FILTER (WHERE email_verified = TRUE) as verified
        FROM outreach.people
        GROUP BY slot_type
        ORDER BY total DESC
    """)
    for row in cur.fetchall():
        print(f'  {row[0]:12} | Total: {row[1]:4} | Has Email: {row[2]:4} | Verified: {row[3]:4}')

    # Sample emails (verified or unverified)
    print()
    print('SAMPLE EMAILS (first 10):')
    cur.execute("""
        SELECT person_id, email, COALESCE(slot_type, 'N/A'), outreach_id, email_verified
        FROM outreach.people
        WHERE email IS NOT NULL AND email != ''
        ORDER BY created_at DESC
        LIMIT 10
    """)
    for row in cur.fetchall():
        pid = str(row[0])[:8] if row[0] else 'N/A'
        email = str(row[1])[:35] if row[1] else 'N/A'
        slot = str(row[2]) if row[2] else 'N/A'
        verified = '✓' if row[4] else '✗'
        print(f'  {pid:10} | {email:35} | {slot:10} | {verified}')

    # Get unverified count for cost estimate
    cur.execute("""
        SELECT COUNT(*) FROM outreach.people
        WHERE email IS NOT NULL AND email != ''
          AND (email_verified = FALSE OR email_verified IS NULL)
    """)
    unverified_count = cur.fetchone()[0]
    print()
    print('VERIFICATION COST ESTIMATE:')
    print(f'  Emails to verify: {unverified_count}')
    print(f'  Estimated cost:   ${unverified_count * 0.001:.2f} (@ $0.001/email)')

    conn.close()


if __name__ == "__main__":
    main()
