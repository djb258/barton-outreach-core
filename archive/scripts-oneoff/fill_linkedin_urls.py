#!/usr/bin/env python3
"""
Fill missing LinkedIn URLs in people.people_master using Hunter contact data.

This script:
1. Identifies people_master records missing LinkedIn URLs
2. Matches to Hunter contacts that have LinkedIn URLs (by email)
3. Updates people_master with LinkedIn URLs from Hunter
4. Reports coverage statistics

Author: Database Expert
Date: 2026-02-06
"""

import psycopg2
import os
from datetime import datetime

print('=' * 80)
print('  LINKEDIN URL BACKFILL - people.people_master from Hunter Data')
print(f'  Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 80)
print()

# Connect to Neon
try:
    conn = psycopg2.connect(
        host=os.getenv('NEON_HOST', 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech'),
        database=os.getenv('NEON_DATABASE', 'Marketing DB'),
        user=os.getenv('NEON_USER', 'Marketing DB_owner'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )
    cur = conn.cursor()
    print('[CONNECTED] Successfully connected to Neon PostgreSQL')
    print()
except Exception as e:
    print(f'[ERROR] Failed to connect to database: {e}')
    exit(1)

# ============================================================================
# STEP 1: Analyze current LinkedIn URL coverage in people_master
# ============================================================================
print('STEP 1: Current LinkedIn URL Coverage in people.people_master')
print('-' * 80)

cur.execute("""
    SELECT
        COUNT(*) as total_people,
        COUNT(linkedin_url) as has_linkedin,
        COUNT(*) - COUNT(linkedin_url) as missing_linkedin,
        ROUND(100.0 * COUNT(linkedin_url) / NULLIF(COUNT(*), 0), 2) as linkedin_coverage_pct
    FROM people.people_master;
""")

result = cur.fetchone()
total_people, has_linkedin, missing_linkedin, coverage_pct = result

print(f'  Total People Records: {total_people:,}')
print(f'  Has LinkedIn URL: {has_linkedin:,}')
print(f'  Missing LinkedIn URL: {missing_linkedin:,}')
print(f'  Current Coverage: {coverage_pct}%')
print()

# ============================================================================
# STEP 2: Check potential matches in Hunter data
# ============================================================================
print('STEP 2: Analyze Potential Matches in Hunter Data')
print('-' * 80)

cur.execute("""
    SELECT
        COUNT(*) as people_missing_linkedin,
        COUNT(DISTINCT hc.email) as hunter_matches_available,
        COUNT(DISTINCT CASE WHEN hc.linkedin_url IS NOT NULL AND hc.linkedin_url != '' THEN hc.email END) as hunter_with_linkedin
    FROM people.people_master pm
    LEFT JOIN enrichment.hunter_contact hc
        ON LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email))
    WHERE pm.linkedin_url IS NULL
        AND pm.email IS NOT NULL
        AND pm.email != '';
""")

result = cur.fetchone()
people_missing, hunter_matches, hunter_with_linkedin = result

print(f'  People Missing LinkedIn: {people_missing:,}')
print(f'  Hunter Matches (by email): {hunter_matches:,}')
print(f'  Hunter Matches with LinkedIn: {hunter_with_linkedin:,}')
print(f'  Potential Update Rate: {round(100.0 * hunter_with_linkedin / people_missing, 2) if people_missing > 0 else 0}%')
print()

# ============================================================================
# STEP 3: Preview sample matches
# ============================================================================
print('STEP 3: Preview Sample Matches (First 10)')
print('-' * 80)

cur.execute("""
    SELECT
        pm.unique_id as people_master_id,
        pm.full_name,
        pm.email,
        hc.linkedin_url as hunter_linkedin_url
    FROM people.people_master pm
    INNER JOIN enrichment.hunter_contact hc
        ON LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email))
    WHERE pm.linkedin_url IS NULL
        AND hc.linkedin_url IS NOT NULL
        AND hc.linkedin_url != ''
    LIMIT 10;
""")

preview_rows = cur.fetchall()
for row in preview_rows:
    pm_id, full_name, email, linkedin = row
    print(f'  ID: {pm_id} | {full_name} | {email}')
    print(f'    → LinkedIn: {linkedin}')
print()

# ============================================================================
# STEP 4: Execute the update
# ============================================================================
print('STEP 4: Execute LinkedIn URL Update')
print('-' * 80)

# Prompt for confirmation
response = input('Proceed with update? (yes/no): ').strip().lower()
if response != 'yes':
    print('[ABORTED] Update cancelled by user.')
    cur.close()
    conn.close()
    exit(0)

print()
print('  Executing update...')

try:
    cur.execute("""
        UPDATE people.people_master pm
        SET
            linkedin_url = hc.linkedin_url,
            updated_at = NOW()
        FROM enrichment.hunter_contact hc
        WHERE pm.linkedin_url IS NULL
            AND hc.linkedin_url IS NOT NULL
            AND hc.linkedin_url != ''
            AND LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email));
    """)

    updated_count = cur.rowcount
    conn.commit()

    print(f'  [SUCCESS] Updated {updated_count:,} records with LinkedIn URLs from Hunter')
    print()

except Exception as e:
    print(f'  [ERROR] Update failed: {e}')
    conn.rollback()
    cur.close()
    conn.close()
    exit(1)

# ============================================================================
# STEP 5: Post-update coverage analysis
# ============================================================================
print('STEP 5: Post-Update LinkedIn URL Coverage')
print('-' * 80)

cur.execute("""
    SELECT
        COUNT(*) as total_people,
        COUNT(linkedin_url) as has_linkedin,
        COUNT(*) - COUNT(linkedin_url) as missing_linkedin,
        ROUND(100.0 * COUNT(linkedin_url) / NULLIF(COUNT(*), 0), 2) as linkedin_coverage_pct
    FROM people.people_master;
""")

result = cur.fetchone()
total_people_post, has_linkedin_post, missing_linkedin_post, coverage_pct_post = result

print(f'  Total People Records: {total_people_post:,}')
print(f'  Has LinkedIn URL: {has_linkedin_post:,}')
print(f'  Missing LinkedIn URL: {missing_linkedin_post:,}')
print(f'  Current Coverage: {coverage_pct_post}%')
print()

# ============================================================================
# STEP 6: Summary report
# ============================================================================
print('=' * 80)
print('  SUMMARY REPORT')
print('=' * 80)
print()
print(f'  BEFORE:')
print(f'    - LinkedIn Coverage: {coverage_pct}%')
print(f'    - Missing LinkedIn URLs: {missing_linkedin:,}')
print()
print(f'  AFTER:')
print(f'    - LinkedIn Coverage: {coverage_pct_post}%')
print(f'    - Missing LinkedIn URLs: {missing_linkedin_post:,}')
print()
print(f'  CHANGE:')
print(f'    - Records Updated: {updated_count:,}')
print(f'    - Coverage Improvement: +{round(coverage_pct_post - coverage_pct, 2)}%')
print(f'    - Still Missing (No Hunter Match): {missing_linkedin_post:,}')
print()

# Check if there are still records missing LinkedIn
if missing_linkedin_post > 0:
    print(f'  NOTE: {missing_linkedin_post:,} records still missing LinkedIn URLs')
    print(f'        These records either:')
    print(f'          - Have no matching email in Hunter data')
    print(f'          - Hunter contact exists but has no LinkedIn URL')
    print()

# ============================================================================
# STEP 7: Additional analysis - Why still missing?
# ============================================================================
print('STEP 7: Analysis of Remaining Missing LinkedIn URLs')
print('-' * 80)

cur.execute("""
    SELECT
        COUNT(*) as still_missing,
        COUNT(CASE WHEN pm.email IS NULL OR pm.email = '' THEN 1 END) as no_email,
        COUNT(CASE WHEN pm.email IS NOT NULL AND pm.email != '' AND hc.email IS NULL THEN 1 END) as no_hunter_match,
        COUNT(CASE WHEN hc.email IS NOT NULL AND (hc.linkedin_url IS NULL OR hc.linkedin_url = '') THEN 1 END) as hunter_no_linkedin
    FROM people.people_master pm
    LEFT JOIN enrichment.hunter_contact hc
        ON LOWER(TRIM(pm.email)) = LOWER(TRIM(hc.email))
    WHERE pm.linkedin_url IS NULL;
""")

result = cur.fetchone()
still_missing, no_email, no_hunter_match, hunter_no_linkedin = result

print(f'  Total Still Missing: {still_missing:,}')
print(f'    - No Email in people_master: {no_email:,}')
print(f'    - No Hunter Match: {no_hunter_match:,}')
print(f'    - Hunter Match but No LinkedIn: {hunter_no_linkedin:,}')
print()

print('=' * 80)
print('  LINKEDIN URL BACKFILL COMPLETE')
print('=' * 80)

# Cleanup
cur.close()
conn.close()
