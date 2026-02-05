#!/usr/bin/env python3
"""
Email Generation Script v3
Adds support for {last}{first} pattern
"""

import psycopg2
import os

def main():
    # Use DATABASE_URL directly
    database_url = os.environ['DATABASE_URL']
    if 'sslmode=' not in database_url:
        database_url += '?sslmode=require'

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    print("=" * 80)
    print("EMAIL GENERATION PIPELINE v3 - FINAL PASS")
    print("=" * 80)

    # Step 1: Count people missing emails who can be generated
    print("\n[Step 1] Counting people missing emails who can be generated...")
    cur.execute("""
    SELECT COUNT(*) as people_missing_emails
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    AND pm.first_name IS NOT NULL AND pm.first_name != ''
    AND pm.last_name IS NOT NULL AND pm.last_name != ''
    AND ct.email_method IS NOT NULL AND ct.email_method != ''
    AND o.domain IS NOT NULL;
    """)
    can_generate = cur.fetchone()[0]
    print(f"People missing emails (can be generated): {can_generate:,}")

    # Step 2: Check email coverage BEFORE generation
    print("\n[Step 2] Checking email coverage BEFORE generation...")
    cur.execute("""
    SELECT
        COUNT(*) as total_people,
        COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
        COUNT(*) FILTER (WHERE email IS NULL OR email = '') as missing_email,
        ROUND(100.0 * COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') / COUNT(*), 2) as email_pct
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id
        AND cs.is_filled = true
    );
    """)
    before = cur.fetchone()
    print(f"Total people (filled slots): {before[0]:,}")
    print(f"Has email: {before[1]:,}")
    print(f"Missing email: {before[2]:,}")
    print(f"Email coverage: {before[3]}%")

    # Step 3: Generate emails with {last}{first} pattern added
    print("\n[Step 3] Generating emails with {last}{first} pattern...")

    cur.execute("""
    WITH pattern_extract AS (
        SELECT
            pm.unique_id,
            pm.first_name,
            pm.last_name,
            o.domain,
            -- Extract pattern (remove @domain if present)
            CASE
                WHEN ct.email_method LIKE '%@%' THEN SPLIT_PART(ct.email_method, '@', 1)
                ELSE ct.email_method
            END as pattern
        FROM people.people_master pm
        JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
        JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
        JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
        WHERE cs.is_filled = true
        AND (pm.email IS NULL OR pm.email = '')
        AND pm.first_name IS NOT NULL AND pm.first_name != ''
        AND pm.last_name IS NOT NULL AND pm.last_name != ''
        AND ct.email_method IS NOT NULL AND ct.email_method != ''
        AND o.domain IS NOT NULL
        AND LENGTH(REGEXP_REPLACE(pm.first_name, '[^a-zA-Z]', '', 'g')) > 0
        AND LENGTH(REGEXP_REPLACE(pm.last_name, '[^a-zA-Z]', '', 'g')) > 0
    )
    UPDATE people.people_master pm
    SET email = CASE pe.pattern
        WHEN '{last}{first}' THEN
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) ||
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        ELSE NULL
    END,
    email_verification_source = 'pattern_generated',
    updated_at = NOW()
    FROM pattern_extract pe
    WHERE pm.unique_id = pe.unique_id
    AND pe.pattern = '{last}{first}';
    """)

    emails_generated = cur.rowcount
    conn.commit()
    print(f"\nEmails generated with {{last}}{{first}} pattern: {emails_generated:,}")

    # Step 4: Check email coverage AFTER generation
    print("\n[Step 4] Checking email coverage AFTER generation...")
    cur.execute("""
    SELECT
        COUNT(*) as total_people,
        COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') as has_email,
        COUNT(*) FILTER (WHERE email IS NULL OR email = '') as missing_email,
        ROUND(100.0 * COUNT(email) FILTER (WHERE email IS NOT NULL AND email != '') / COUNT(*), 2) as email_pct
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id
        AND cs.is_filled = true
    );
    """)
    after = cur.fetchone()
    print(f"Total people (filled slots): {after[0]:,}")
    print(f"Has email: {after[1]:,}")
    print(f"Missing email: {after[2]:,}")
    print(f"Email coverage: {after[3]}%")

    # Calculate improvement
    improvement = after[3] - before[3]
    print(f"\nCoverage improvement: +{improvement}%")

    # Step 5: Final breakdown
    print("\n[Step 5] Final breakdown of remaining missing emails...")
    cur.execute("""
    SELECT
        CASE
            WHEN ct.email_method LIKE '%@%' THEN SPLIT_PART(ct.email_method, '@', 1)
            ELSE ct.email_method
        END as pattern,
        COUNT(*) as cnt
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    GROUP BY 1
    ORDER BY cnt DESC;
    """)

    remaining = cur.fetchall()
    print(f"\nRemaining patterns (total: {len(remaining)}):")
    for pattern, count in remaining:
        print(f"  {pattern or 'NULL'}: {count:,}")

    # Step 6: Final summary
    print("\n[Step 6] Total emails generated across all runs:")
    cur.execute("""
    SELECT COUNT(*)
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id
        AND cs.is_filled = true
    )
    AND email_verification_source = 'pattern_generated';
    """)
    total_generated = cur.fetchone()[0]
    print(f"Total pattern-generated emails: {total_generated:,}")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("EMAIL GENERATION COMPLETE")
    print("=" * 80)
    print(f"Summary:")
    print(f"  - Emails generated (this run): {emails_generated:,}")
    print(f"  - Total pattern-generated: {total_generated:,}")
    print(f"  - Final coverage: {after[3]}%")
    print(f"  - Remaining missing: {after[2]:,}")
    print("=" * 80)

if __name__ == "__main__":
    main()
