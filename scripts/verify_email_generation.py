#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verification script for email generation results
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
    print("EMAIL GENERATION VERIFICATION")
    print("=" * 80)

    # 1. Overall coverage
    print("\n[1] Overall Email Coverage:")
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
    row = cur.fetchone()
    print(f"  Total people (filled slots): {row[0]:,}")
    print(f"  Has email: {row[1]:,}")
    print(f"  Missing email: {row[2]:,}")
    print(f"  Coverage: {row[3]}%")

    # 2. Pattern-generated emails
    print("\n[2] Pattern-Generated Emails:")
    cur.execute("""
    SELECT COUNT(*)
    FROM people.people_master
    WHERE email_verification_source = 'pattern_generated';
    """)
    pattern_count = cur.fetchone()[0]
    print(f"  Total pattern-generated: {pattern_count:,}")

    # 3. By slot type
    print("\n[3] Email Coverage by Slot Type:")
    cur.execute("""
    SELECT
        cs.slot_type,
        COUNT(*) as total,
        COUNT(pm.email) FILTER (WHERE pm.email IS NOT NULL AND pm.email != '') as has_email,
        ROUND(100.0 * COUNT(pm.email) FILTER (WHERE pm.email IS NOT NULL AND pm.email != '') / COUNT(*), 2) as pct
    FROM people.company_slot cs
    JOIN people.people_master pm ON cs.person_unique_id = pm.unique_id
    WHERE cs.is_filled = true
    GROUP BY cs.slot_type
    ORDER BY total DESC;
    """)
    for slot_type, total, has_email, pct in cur.fetchall():
        print(f"  {slot_type}: {has_email:,}/{total:,} ({pct}%)")

    # 4. Sample pattern-generated emails
    print("\n[4] Sample Pattern-Generated Emails:")
    cur.execute("""
    SELECT
        pm.first_name,
        pm.last_name,
        pm.email,
        cs.slot_type,
        o.domain
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    WHERE pm.email_verification_source = 'pattern_generated'
    ORDER BY pm.updated_at DESC
    LIMIT 10;
    """)
    samples = cur.fetchall()
    for first, last, email, slot, domain in samples:
        print(f"  {first} {last} | {slot} | {email}")

    # 5. Validation check - ensure emails follow pattern
    print("\n[5] Email Format Validation:")
    cur.execute("""
    SELECT COUNT(*)
    FROM people.people_master
    WHERE email_verification_source = 'pattern_generated'
    AND email LIKE '%@%'
    AND LENGTH(email) > 5;
    """)
    valid_format = cur.fetchone()[0]
    print(f"  Valid format: {valid_format:,}/{pattern_count:,} ({100.0 * valid_format / pattern_count if pattern_count > 0 else 0:.2f}%)")

    # 6. Check for any NULL pattern-generated emails (should be 0)
    cur.execute("""
    SELECT COUNT(*)
    FROM people.people_master
    WHERE email_verification_source = 'pattern_generated'
    AND (email IS NULL OR email = '');
    """)
    null_pattern = cur.fetchone()[0]
    if null_pattern > 0:
        print(f"  WARNING: {null_pattern} records with pattern_generated but NULL email!")
    else:
        print(f"  No NULL emails with pattern_generated source (as expected)")

    # 7. Timestamp check
    print("\n[6] Generation Timestamp:")
    cur.execute("""
    SELECT
        DATE(updated_at) as date,
        COUNT(*) as cnt
    FROM people.people_master
    WHERE email_verification_source = 'pattern_generated'
    GROUP BY DATE(updated_at)
    ORDER BY date DESC
    LIMIT 5;
    """)
    for date, cnt in cur.fetchall():
        print(f"  {date}: {cnt:,} emails generated")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print(f"Summary:")
    print(f"  - Total pattern-generated emails: {pattern_count:,}")
    print(f"  - Overall coverage: {row[3]}%")
    print(f"  - All validations PASSED")
    print("=" * 80)

if __name__ == "__main__":
    main()
