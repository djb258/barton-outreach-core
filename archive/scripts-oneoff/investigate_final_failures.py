#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investigate the final 1,559 people who couldn't get emails generated
"""

import psycopg2
import os
import sys

# Ensure UTF-8 output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def main():
    database_url = os.environ['DATABASE_URL']
    if 'sslmode=' not in database_url:
        database_url += '?sslmode=require'

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    print("=" * 80)
    print("INVESTIGATING FINAL FAILURES")
    print("=" * 80)

    # Investigate the 6 people with {first}.{last} pattern
    print("\n[1] The 6 people with {first}.{last} pattern that failed:")
    cur.execute("""
    SELECT
        pm.unique_id,
        pm.first_name,
        pm.last_name,
        pm.full_name,
        o.domain,
        ct.email_method,
        LENGTH(REGEXP_REPLACE(pm.first_name, '[^a-zA-Z]', '', 'g')) as first_clean_len,
        LENGTH(REGEXP_REPLACE(pm.last_name, '[^a-zA-Z]', '', 'g')) as last_clean_len
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    AND CASE
            WHEN ct.email_method LIKE '%@%' THEN SPLIT_PART(ct.email_method, '@', 1)
            ELSE ct.email_method
        END = '{first}.{last}'
    LIMIT 10;
    """)

    failed_pattern = cur.fetchall()
    if failed_pattern:
        for row in failed_pattern:
            uid, first, last, full, domain, method, first_len, last_len = row
            print(f"\n  Person ID: {uid}")
            print(f"  First: '{first}' (clean length: {first_len})")
            print(f"  Last: '{last}' (clean length: {last_len})")
            print(f"  Full: '{full}'")
            print(f"  Domain: {domain}")
            print(f"  Method: {method}")
    else:
        print("  No records found")

    # Check NULL email_method breakdown
    print("\n[2] Breakdown of 848 people with NULL email_method:")
    cur.execute("""
    SELECT
        cs.slot_type,
        COUNT(*) as cnt
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    AND ct.email_method IS NULL
    GROUP BY cs.slot_type
    ORDER BY cnt DESC;
    """)

    null_breakdown = cur.fetchall()
    print("  By slot type:")
    for slot_type, count in null_breakdown:
        print(f"    {slot_type}: {count:,}")

    # Sample some NULL email_method companies
    print("\n[3] Sample companies with NULL email_method:")
    cur.execute("""
    SELECT DISTINCT
        o.outreach_id,
        o.domain
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    AND ct.email_method IS NULL
    LIMIT 10;
    """)

    null_companies = cur.fetchall()
    for oid, domain in null_companies:
        print(f"\n  Outreach ID: {oid}")
        print(f"  Domain: {domain}")

    # Overall summary
    print("\n[4] Overall email coverage summary:")
    cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
        COUNT(*) FILTER (WHERE email IS NULL OR email = '') as missing,
        ROUND(100.0 * COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') / COUNT(*), 2) as pct
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id
        AND cs.is_filled = true
    );
    """)

    summary = cur.fetchone()
    print(f"  Total people: {summary[0]:,}")
    print(f"  Has email: {summary[1]:,}")
    print(f"  Missing email: {summary[2]:,}")
    print(f"  Coverage: {summary[3]}%")

    # Check email_method distribution for companies
    print("\n[5] Email method distribution for companies:")
    cur.execute("""
    SELECT
        CASE
            WHEN ct.email_method IS NULL THEN 'NULL'
            WHEN ct.email_method LIKE '%@%' THEN SPLIT_PART(ct.email_method, '@', 1)
            ELSE ct.email_method
        END as pattern,
        COUNT(DISTINCT ct.outreach_id) as companies
    FROM outreach.company_target ct
    GROUP BY 1
    ORDER BY companies DESC
    LIMIT 15;
    """)

    method_dist = cur.fetchall()
    for pattern, count in method_dist:
        print(f"  {pattern}: {count:,} companies")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
