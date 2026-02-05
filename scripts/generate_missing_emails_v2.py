#!/usr/bin/env python3
"""
Email Generation Script v2
Handles both pattern formats:
- Pattern only: {first}.{last}
- Pattern with domain: {first}.{last}@domain.com
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
    print("EMAIL GENERATION PIPELINE v2 - LIVE EXECUTION")
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

    # Step 3: Generate emails based on Hunter patterns
    # This version extracts the pattern from email_method (before @) if it contains @
    print("\n[Step 3] Generating emails using company email patterns...")
    print("Hunter patterns supported:")
    print("  - {first}.{last}")
    print("  - {f}{last}")
    print("  - {first}")
    print("  - {first}{last}")
    print("  - {first}{l}")
    print("  - {f}.{last}")
    print("  - {last}")
    print("  - {last}{f}")
    print("  - {first}.{l}")
    print("  - {first}_{last}")
    print("\nNote: Names will be sanitized (alphanumeric only, spaces removed)")
    print("Note: Handles patterns with or without @domain suffix")

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
        WHEN '{first}.{last}' THEN
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) || '.' ||
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        WHEN '{f}{last}' THEN
            LOWER(SUBSTRING(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g'), 1, 1)) ||
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        WHEN '{first}' THEN
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        WHEN '{first}{last}' THEN
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) ||
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        WHEN '{first}{l}' THEN
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) ||
            LOWER(SUBSTRING(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g'), 1, 1)) || '@' || pe.domain
        WHEN '{f}.{last}' THEN
            LOWER(SUBSTRING(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g'), 1, 1)) || '.' ||
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        WHEN '{last}' THEN
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        WHEN '{last}{f}' THEN
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) ||
            LOWER(SUBSTRING(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g'), 1, 1)) || '@' || pe.domain
        WHEN '{first}.{l}' THEN
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) || '.' ||
            LOWER(SUBSTRING(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g'), 1, 1)) || '@' || pe.domain
        WHEN '{first}_{last}' THEN
            LOWER(REGEXP_REPLACE(pe.first_name, '[^a-zA-Z]', '', 'g')) || '_' ||
            LOWER(REGEXP_REPLACE(pe.last_name, '[^a-zA-Z]', '', 'g')) || '@' || pe.domain
        ELSE NULL
    END,
    email_verification_source = 'pattern_generated',
    updated_at = NOW()
    FROM pattern_extract pe
    WHERE pm.unique_id = pe.unique_id
    AND pe.pattern IN ('{first}.{last}', '{f}{last}', '{first}', '{first}{last}', '{first}{l}', '{f}.{last}', '{last}', '{last}{f}', '{first}.{l}', '{first}_{last}');
    """)

    emails_generated = cur.rowcount
    conn.commit()
    print(f"\nEmails generated: {emails_generated:,}")

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

    # Step 5: Check what patterns couldn't be matched
    print("\n[Step 5] Checking patterns for remaining missing emails...")
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
    ORDER BY cnt DESC
    LIMIT 10;
    """)

    unmatched = cur.fetchall()
    if unmatched:
        print("\nTop unmatched patterns (people still missing emails):")
        for pattern, count in unmatched:
            print(f"  {pattern or 'NULL'}: {count:,}")
    else:
        print("\nAll patterns matched successfully!")

    # Step 6: Check by email_verification_source
    print("\n[Step 6] Email verification sources:")
    cur.execute("""
    SELECT
        COALESCE(email_verification_source, 'NULL') as source,
        COUNT(*) as cnt
    FROM people.people_master pm
    WHERE EXISTS (
        SELECT 1 FROM people.company_slot cs
        WHERE cs.person_unique_id = pm.unique_id
        AND cs.is_filled = true
    )
    AND email IS NOT NULL AND email != ''
    GROUP BY email_verification_source
    ORDER BY cnt DESC;
    """)
    sources = cur.fetchall()
    for source, count in sources:
        print(f"  {source}: {count:,}")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)
    print("EMAIL GENERATION COMPLETE")
    print("=" * 80)
    print(f"Summary:")
    print(f"  - Emails generated: {emails_generated:,}")
    print(f"  - Before coverage: {before[3]}%")
    print(f"  - After coverage: {after[3]}%")
    print(f"  - Improvement: +{improvement}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
