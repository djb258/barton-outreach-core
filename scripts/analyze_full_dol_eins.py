#!/usr/bin/env python3
"""Analyze all EIN sources for matching - form_5500, form_5500_sf, schedule_a."""

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
print("FULL DOL EIN INVENTORY")
print("=" * 70)

# 1. Total unique EINs across all sources
print("\n1. TOTAL UNIQUE EINs ACROSS ALL SOURCES")
print("-" * 50)

cur.execute("""
    SELECT COUNT(DISTINCT ein) as cnt
    FROM (
        SELECT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
        UNION
        SELECT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
        UNION
        SELECT sch_a_ein as ein FROM dol.schedule_a WHERE sch_a_ein IS NOT NULL
    ) all_eins
""")
total_eins = cur.fetchone()['cnt']
print(f"  Total unique EINs: {total_eins:,}")

# 2. EINs by state - form_5500
print("\n2. form_5500 - EINs BY STATE")
print("-" * 50)

cur.execute("""
    SELECT spons_dfe_mail_us_state as state, COUNT(DISTINCT sponsor_dfe_ein) as eins
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IS NOT NULL
    GROUP BY spons_dfe_mail_us_state
    ORDER BY eins DESC
    LIMIT 15
""")
for row in cur.fetchall():
    print(f"  {row['state']:<5}: {row['eins']:>8,}")

# 3. EINs by state - form_5500_sf (SHORT FORM - the big one!)
print("\n3. form_5500_sf (SHORT FORM) - EINs BY STATE")
print("-" * 50)

cur.execute("""
    SELECT sf_spons_us_state as state, COUNT(DISTINCT sf_spons_ein) as eins
    FROM dol.form_5500_sf
    WHERE sf_spons_us_state IS NOT NULL
    GROUP BY sf_spons_us_state
    ORDER BY eins DESC
    LIMIT 15
""")
for row in cur.fetchall():
    print(f"  {row['state']:<5}: {row['eins']:>8,}")

# 4. Combined EINs by state
print("\n4. COMBINED EINs BY STATE (all sources)")
print("-" * 50)

cur.execute("""
    SELECT state, COUNT(DISTINCT ein) as eins
    FROM (
        SELECT spons_dfe_mail_us_state as state, sponsor_dfe_ein as ein 
        FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
        UNION ALL
        SELECT sf_spons_us_state as state, sf_spons_ein as ein 
        FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
    ) combined
    WHERE state IS NOT NULL
    GROUP BY state
    ORDER BY eins DESC
    LIMIT 15
""")
for row in cur.fetchall():
    print(f"  {row['state']:<5}: {row['eins']:>8,}")

# 5. Our blocked states vs available EINs
print("\n5. BLOCKED COMPANIES vs AVAILABLE EINs BY STATE")
print("-" * 50)

blocked_states = ['PA', 'OH', 'VA', 'NC', 'MD', 'KY', 'OK', 'WV', 'DE']

cur.execute("""
    WITH blocked AS (
        SELECT cm.address_state, COUNT(*) as blocked_cnt
        FROM outreach.dol_errors de
        JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        WHERE de.failure_code IN ('NO_MATCH', 'NO_STATE')
        AND cm.ein IS NULL
        GROUP BY cm.address_state
    ),
    available_5500 AS (
        SELECT spons_dfe_mail_us_state as state, COUNT(DISTINCT sponsor_dfe_ein) as eins
        FROM dol.form_5500
        GROUP BY spons_dfe_mail_us_state
    ),
    available_sf AS (
        SELECT sf_spons_us_state as state, COUNT(DISTINCT sf_spons_ein) as eins
        FROM dol.form_5500_sf
        GROUP BY sf_spons_us_state
    )
    SELECT 
        b.address_state,
        b.blocked_cnt,
        COALESCE(a5.eins, 0) as form_5500_eins,
        COALESCE(asf.eins, 0) as form_5500_sf_eins,
        COALESCE(a5.eins, 0) + COALESCE(asf.eins, 0) as total_eins
    FROM blocked b
    LEFT JOIN available_5500 a5 ON b.address_state = a5.state
    LEFT JOIN available_sf asf ON b.address_state = asf.state
    ORDER BY b.blocked_cnt DESC
""")
print(f"  {'State':<6} | {'Blocked':>10} | {'5500 EINs':>10} | {'5500-SF EINs':>12} | {'TOTAL':>10}")
print("  " + "-" * 60)
for row in cur.fetchall():
    print(f"  {row['address_state']:<6} | {row['blocked_cnt']:>10,} | {row['form_5500_eins']:>10,} | {row['form_5500_sf_eins']:>12,} | {row['total_eins']:>10,}")

# 6. form_5500_sf structure - for matching
print("\n6. form_5500_sf COLUMNS (for matching)")
print("-" * 50)

cur.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = 'dol' AND table_name = 'form_5500_sf'
    AND (column_name LIKE '%name%' OR column_name LIKE '%city%' OR column_name LIKE '%state%' OR column_name LIKE '%ein%')
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  {row['column_name']}")

# 7. Sample form_5500_sf data
print("\n7. SAMPLE form_5500_sf DATA")
print("-" * 50)

cur.execute("""
    SELECT sf_spons_ein, sf_spons_entity_name, sf_spons_us_city, sf_spons_us_state
    FROM dol.form_5500_sf
    WHERE sf_spons_us_state = 'NC'
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row['sf_spons_ein']} | {row['sf_spons_entity_name'][:40]:<40} | {row['sf_spons_us_city']:<15} | {row['sf_spons_us_state']}")

conn.close()
