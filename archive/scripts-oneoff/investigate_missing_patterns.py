#!/usr/bin/env python3
"""
Investigate why emails weren't generated for all eligible people
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
    print("INVESTIGATING UNMATCHED PATTERNS")
    print("=" * 80)

    # Check patterns that weren't in the supported list
    print("\n[1] Email patterns NOT in supported list:")
    cur.execute("""
    SELECT ct.email_method, COUNT(*) as cnt
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
    AND ct.email_method NOT IN ('{first}.{last}', '{f}{last}', '{first}', '{first}{last}', '{first}{l}', '{f}.{last}', '{last}', '{last}{f}', '{first}.{l}', '{first}_{last}')
    GROUP BY ct.email_method
    ORDER BY cnt DESC
    LIMIT 20;
    """)

    unsupported = cur.fetchall()
    if unsupported:
        print(f"Found {len(unsupported)} unsupported patterns:")
        for pattern, count in unsupported:
            print(f"  {pattern}: {count:,}")
    else:
        print("All patterns are supported!")

    # Check companies with NULL email_method
    print("\n[2] Companies with NULL email_method:")
    cur.execute("""
    SELECT COUNT(DISTINCT cs.outreach_id) as companies,
           COUNT(*) as people
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    AND ct.email_method IS NULL;
    """)
    null_pattern = cur.fetchone()
    print(f"Companies: {null_pattern[0]:,}")
    print(f"People: {null_pattern[1]:,}")

    # Check people with names that sanitize to empty string
    print("\n[3] People with names that sanitize to empty:")
    cur.execute("""
    SELECT pm.first_name, pm.last_name, pm.full_name, COUNT(*) as cnt
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
    AND ct.email_method IN ('{first}.{last}', '{f}{last}', '{first}', '{first}{last}', '{first}{l}', '{f}.{last}', '{last}', '{last}{f}', '{first}.{l}', '{first}_{last}')
    AND (LENGTH(REGEXP_REPLACE(pm.first_name, '[^a-zA-Z]', '', 'g')) = 0
         OR LENGTH(REGEXP_REPLACE(pm.last_name, '[^a-zA-Z]', '', 'g')) = 0)
    GROUP BY pm.first_name, pm.last_name, pm.full_name
    ORDER BY cnt DESC
    LIMIT 20;
    """)

    invalid_names = cur.fetchall()
    if invalid_names:
        print(f"Found {len(invalid_names)} distinct invalid name combinations:")
        for first, last, full, count in invalid_names:
            print(f"  '{first}' | '{last}' | '{full}': {count}")
    else:
        print("All names can be sanitized!")

    # Check patterns that look unusual (contain @domain)
    print("\n[4] Unusual patterns (contain @domain):")
    cur.execute("""
    SELECT ct.email_method, COUNT(*) as cnt
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id
    JOIN outreach.outreach o ON cs.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE cs.is_filled = true
    AND (pm.email IS NULL OR pm.email = '')
    AND ct.email_method LIKE '%@%'
    GROUP BY ct.email_method
    ORDER BY cnt DESC
    LIMIT 20;
    """)

    unusual = cur.fetchall()
    if unusual:
        print(f"Found {len(unusual)} patterns containing @domain:")
        for pattern, count in unusual:
            print(f"  {pattern}: {count:,}")
        print("\nThese appear to be full email addresses, not patterns!")
    else:
        print("No unusual patterns found.")

    # Get breakdown of why emails can't be generated
    print("\n[5] Breakdown of why 3,479 eligible emails weren't all generated:")

    total_missing = 3479
    print(f"Total eligible (from Step 1): {total_missing:,}")

    # Actually generated
    print(f"Actually generated: 135")

    # Calculate remaining
    remaining = total_missing - 135
    print(f"Remaining ungenerated: {remaining:,}")

    # Breakdown
    unsupported_count = sum(count for _, count in unsupported)
    null_pattern_count = null_pattern[1] if null_pattern else 0
    invalid_names_count = sum(count for _, _, _, count in invalid_names)

    print(f"\nBreakdown:")
    print(f"  - Unsupported patterns: {unsupported_count:,}")
    print(f"  - NULL email_method: {null_pattern_count:,}")
    print(f"  - Invalid names (sanitize to empty): {invalid_names_count:,}")
    print(f"  - Other reasons: {remaining - unsupported_count - null_pattern_count - invalid_names_count:,}")

    cur.close()
    conn.close()

    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
