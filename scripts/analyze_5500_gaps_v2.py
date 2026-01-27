#!/usr/bin/env python3
"""Analyze why 50+ employee companies aren't matching to 5500s."""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

print("=" * 70)
print("WHY CAN'T WE MATCH 50+ EMPLOYEE COMPANIES TO 5500s?")
print("=" * 70)

# Summary first
print("\n*** ALL BLOCKED = COMPANIES WITH 50+ EMPLOYEES THAT SHOULD HAVE 5500s ***")
print()

# 1. Overall breakdown
print("1. OVERALL BLOCKED BREAKDOWN")
print("-" * 50)

cur.execute("""
    SELECT 
        CASE 
            WHEN cm.ein IS NULL THEN 'NO_EIN - Cannot search 5500'
            WHEN NOT EXISTS (SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein) 
                THEN 'HAS_EIN - But EIN not in our 5500 data'
            ELSE 'SHOULD_MATCH - Has EIN and EIN exists in 5500'
        END as gap_reason,
        COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
    GROUP BY 1
    ORDER BY cnt DESC
""")
total = 0
for row in cur.fetchall():
    print(f"  {row['gap_reason']:<45}: {row['cnt']:>8,}")
    total += row['cnt']
print(f"  {'TOTAL BLOCKED':<45}: {total:>8,}")

# 2. State breakdown of NO_EIN
print("\n2. NO_EIN RECORDS BY STATE")
print("-" * 50)

cur.execute("""
    SELECT cm.address_state, COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
    AND cm.ein IS NULL
    GROUP BY cm.address_state
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row['address_state']:<5}: {row['cnt']:>8,}")

# 3. How many 5500s do we have per state?
print("\n3. FORM_5500 COVERAGE - UNIQUE EINs BY STATE")
print("-" * 50)

cur.execute("""
    SELECT spons_dfe_mail_us_state as state, COUNT(DISTINCT sponsor_dfe_ein) as unique_eins
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IN ('NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE')
    GROUP BY spons_dfe_mail_us_state
    ORDER BY unique_eins DESC
""")
print("(States with blocked records)")
for row in cur.fetchall():
    st = row['state'] if row['state'] else 'NULL'
    print(f"  {st:<5}: {row['unique_eins']:>8,} unique EINs")

# 4. Total 5500 coverage
print("\n4. TOTAL FORM_5500 DATA")
print("-" * 50)

cur.execute("SELECT COUNT(*) as cnt FROM dol.form_5500")
total_filings = cur.fetchone()['cnt']
print(f"  Total filings: {total_filings:,}")

cur.execute("SELECT COUNT(DISTINCT sponsor_dfe_ein) as cnt FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL")
unique_eins = cur.fetchone()['cnt']
print(f"  Unique EINs: {unique_eins:,}")

cur.execute("""
    SELECT plan_year, COUNT(*) as cnt
    FROM dol.form_5500
    GROUP BY plan_year
    ORDER BY plan_year DESC
    LIMIT 5
""")
print(f"\n  Plan years:")
for row in cur.fetchall():
    print(f"    {row['plan_year']}: {row['cnt']:>8,}")

# 5. Companies with EIN but not in 5500 - why?
print("\n5. EINs WE HAVE THAT AREN'T IN FORM_5500")
print("-" * 50)

cur.execute("""
    SELECT COUNT(DISTINCT cm.ein) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
    AND cm.ein IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein)
""")
missing_eins = cur.fetchone()['cnt']
print(f"  Companies with EIN not found in form_5500: {missing_eins:,}")

print("\n  Sample of these companies:")
cur.execute("""
    SELECT cm.company_name, cm.address_state, cm.ein
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
    AND cm.ein IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein)
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"    {row['company_name'][:40]:<40} | {row['address_state']} | {row['ein']}")

# 6. Fuzzy match potential - how many could we match with names?
print("\n6. FUZZY MATCH POTENTIAL (NO EIN → Name Match)")
print("-" * 50)

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM (
        SELECT DISTINCT cm.company_unique_id
        FROM outreach.dol_errors de
        JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f 
            ON cm.address_state = f.spons_dfe_mail_us_state
            AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(f.spons_dfe_mail_us_city))
        WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
        AND cm.ein IS NULL
        AND SIMILARITY(LOWER(cm.company_name), LOWER(f.sponsor_dfe_name)) > 0.6
        LIMIT 5000
    ) matches
""")
fuzzy_matches = cur.fetchone()['cnt']
print(f"  Companies matchable at 0.60 threshold: {fuzzy_matches:,}")

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM (
        SELECT DISTINCT cm.company_unique_id
        FROM outreach.dol_errors de
        JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f 
            ON cm.address_state = f.spons_dfe_mail_us_state
            AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(f.spons_dfe_mail_us_city))
        WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
        AND cm.ein IS NULL
        AND SIMILARITY(LOWER(cm.company_name), LOWER(f.sponsor_dfe_name)) > 0.5
        LIMIT 5000
    ) matches
""")
fuzzy_matches_50 = cur.fetchone()['cnt']
print(f"  Companies matchable at 0.50 threshold: {fuzzy_matches_50:,}")

# 7. What if we relax city requirement?
print("\n7. MATCH BY STATE + NAME ONLY (no city requirement)")
print("-" * 50)

cur.execute("""
    SELECT COUNT(*) as cnt
    FROM (
        SELECT DISTINCT cm.company_unique_id
        FROM outreach.dol_errors de
        JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f 
            ON cm.address_state = f.spons_dfe_mail_us_state
        WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
        AND cm.ein IS NULL
        AND SIMILARITY(LOWER(cm.company_name), LOWER(f.sponsor_dfe_name)) > 0.7
        LIMIT 10000
    ) matches
""")
state_only = cur.fetchone()['cnt']
print(f"  State + Name (0.70 sim) only: {state_only:,}")

print("\n" + "=" * 70)
print("SUMMARY: THE GAP")
print("=" * 70)
print(f"""
Total Blocked Companies (50+ employees, should have 5500): {total:,}

Root Causes:
  1. NO EIN in company_master → Can't lookup by EIN
  2. EIN exists but not in our 5500 data → Missing 5500 filing data
  
Potential Solutions:
  1. Run fuzzy matching at lower threshold to get more EINs
  2. Acquire more Form 5500 data (different years? EFAST2?)
  3. Use alternative EIN sources (SEC, state registries)
  4. Accept some companies may file under parent company EIN
""")

conn.close()
