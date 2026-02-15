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

# 1. NO_MATCH breakdown - do they have EIN?
print("\n1. NO_MATCH ERRORS - EIN STATUS")
print("-" * 50)

cur.execute("""
    SELECT 
        CASE WHEN cm.ein IS NOT NULL THEN 'Has EIN' ELSE 'No EIN' END as ein_status,
        COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_MATCH'
    GROUP BY 1
""")
for row in cur.fetchall():
    print(f"  {row['ein_status']:<15}: {row['cnt']:>8,}")

# 2. NO_MATCH with EIN - why doesn't it match form_5500?
print("\n2. NO_MATCH WITH EIN - DO THEIR EINs EXIST IN FORM_5500?")
print("-" * 50)

cur.execute("""
    SELECT COUNT(DISTINCT cm.ein) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_MATCH'
    AND cm.ein IS NOT NULL
""")
has_ein = cur.fetchone()['cnt']
print(f"  NO_MATCH records with EIN: {has_ein:,} unique EINs")

cur.execute("""
    SELECT COUNT(DISTINCT cm.ein) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_MATCH'
    AND cm.ein IS NOT NULL
    AND EXISTS (SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein)
""")
in_5500 = cur.fetchone()['cnt']
print(f"  Of those, EINs found in form_5500: {in_5500:,}")
print(f"  EINs NOT in form_5500: {has_ein - in_5500:,}")

# 3. Sample NO_MATCH with EIN that's NOT in 5500
print("\n3. SAMPLE: NO_MATCH WITH EIN NOT IN FORM_5500")
print("-" * 50)

cur.execute("""
    SELECT cm.company_name, cm.address_state, cm.address_city, cm.ein
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_MATCH'
    AND cm.ein IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein)
    LIMIT 15
""")
print("\nCompanies with EIN but no 5500 filing found:")
for row in cur.fetchall():
    print(f"  {row['company_name'][:35]:<35} | {row['address_state']} | {row['address_city'][:15]:<15} | {row['ein']}")

# 4. What states are NO_MATCH concentrated in?
print("\n4. NO_MATCH BY STATE")
print("-" * 50)

cur.execute("""
    SELECT cm.address_state, COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE de.failure_code = 'NO_MATCH'
    GROUP BY cm.address_state
    ORDER BY cnt DESC
    LIMIT 15
""")
for row in cur.fetchall():
    print(f"  {row['address_state']:<5}: {row['cnt']:>8,}")

# 5. Compare to form_5500 coverage by state
print("\n5. FORM_5500 COVERAGE BY STATE (top states from errors)")
print("-" * 50)

cur.execute("""
    SELECT sponsor_dfe_state, COUNT(DISTINCT sponsor_dfe_ein) as unique_eins
    FROM dol.form_5500
    WHERE sponsor_dfe_state IN ('NC', 'PA', 'OH', 'WV', 'VA')
    GROUP BY sponsor_dfe_state
    ORDER BY unique_eins DESC
""")
print("\nUnique EINs in form_5500 by state:")
for row in cur.fetchall():
    print(f"  {row['sponsor_dfe_state']:<5}: {row['unique_eins']:>8,}")

# 6. What years of 5500 data do we have?
print("\n6. FORM_5500 PLAN YEARS AVAILABLE")
print("-" * 50)

cur.execute("""
    SELECT plan_year, COUNT(*) as cnt
    FROM dol.form_5500
    GROUP BY plan_year
    ORDER BY plan_year DESC
    LIMIT 10
""")
for row in cur.fetchall():
    yr = row['plan_year']
    print(f"  {yr}: {row['cnt']:>8,}")

# 7. Are NO_MATCH companies maybe filing under parent/different name?
print("\n7. NO_MATCH - FUZZY NAME MATCH POTENTIAL")
print("-" * 50)
print("(Checking if company names have close matches in 5500 for their state)")

cur.execute("""
    WITH no_match_companies AS (
        SELECT DISTINCT cm.company_name, cm.address_state, cm.address_city
        FROM outreach.dol_errors de
        JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        WHERE de.failure_code = 'NO_MATCH'
        AND cm.ein IS NULL
        LIMIT 1000
    )
    SELECT 
        nm.company_name,
        nm.address_state,
        f.sponsor_dfe_name as form_5500_name,
        similarity(UPPER(nm.company_name), UPPER(f.sponsor_dfe_name)) as sim
    FROM no_match_companies nm
    JOIN dol.form_5500 f ON f.sponsor_dfe_state = nm.address_state
    WHERE similarity(UPPER(nm.company_name), UPPER(f.sponsor_dfe_name)) > 0.5
    ORDER BY sim DESC
    LIMIT 20
""")
rows = cur.fetchall()
if rows:
    print("\nHigh similarity matches (>0.5) - potential matches:")
    for row in rows:
        print(f"  {row['sim']:.2f} | {row['company_name'][:30]:<30} → {row['form_5500_name'][:30]}")
else:
    print("\nNo high similarity matches found in sample")

# 8. Total opportunity summary
print("\n" + "=" * 70)
print("SUMMARY: WHY CAN'T WE MATCH?")
print("=" * 70)

cur.execute("""
    SELECT 
        CASE 
            WHEN cm.ein IS NULL THEN 'NO_EIN'
            WHEN NOT EXISTS (SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein) THEN 'EIN_NOT_IN_5500'
            ELSE 'SHOULD_MATCH'
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
print("\nBlocked records breakdown:")
for row in cur.fetchall():
    print(f"  {row['gap_reason']:<20}: {row['cnt']:>8,}")

conn.close()
