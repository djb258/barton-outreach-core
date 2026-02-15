#!/usr/bin/env python3
"""Summary of DOL matching session."""

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
print("DOL MATCHING SESSION SUMMARY")
print("=" * 70)

# 1. DOL Status
print("\n1. DOL STATUS DISTRIBUTION")
print("-" * 50)

cur.execute("""
    SELECT dol_status, COUNT(*) as cnt
    FROM outreach.v_outreach_diagnostic
    GROUP BY dol_status
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row['dol_status']:<15}: {row['cnt']:>8,}")

# 2. EIN coverage in company_master
print("\n2. EIN COVERAGE IN COMPANY_MASTER")
print("-" * 50)

cur.execute("SELECT COUNT(*) as total FROM company.company_master")
total = cur.fetchone()['total']

cur.execute("SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL")
with_ein = cur.fetchone()['with_ein']

print(f"  Total companies: {total:,}")
print(f"  With EIN: {with_ein:,} ({100*with_ein/total:.1f}%)")
print(f"  Without EIN: {total - with_ein:,}")

# 3. EIN by state
print("\n3. EIN COVERAGE BY STATE (blocked states)")
print("-" * 50)

cur.execute("""
    SELECT address_state,
           COUNT(*) as total,
           COUNT(ein) as with_ein,
           ROUND(100.0 * COUNT(ein) / COUNT(*), 1) as pct
    FROM company.company_master
    WHERE address_state IN ('NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE')
    GROUP BY address_state
    ORDER BY total DESC
""")
print(f"  {'State':<6} | {'Total':>8} | {'With EIN':>10} | {'%':>6}")
print("  " + "-" * 40)
for row in cur.fetchall():
    print(f"  {row['address_state']:<6} | {row['total']:>8,} | {row['with_ein']:>10,} | {row['pct']:>5.1f}%")

# 4. Gap analysis - why still blocked?
print("\n4. REMAINING BLOCKED BREAKDOWN")
print("-" * 50)

cur.execute("""
    SELECT 
        CASE 
            WHEN cm.ein IS NULL THEN 'NO_EIN - Need fuzzy match'
            WHEN NOT EXISTS (
                SELECT 1 FROM dol.form_5500 f WHERE f.sponsor_dfe_ein = cm.ein
                UNION
                SELECT 1 FROM dol.form_5500_sf sf WHERE sf.sf_spons_ein = cm.ein
            ) THEN 'EIN_NOT_IN_5500 - Missing filing data'
            ELSE 'SHOULD_MATCH'
        END as gap_reason,
        COUNT(*) as cnt
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    GROUP BY 1
    ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row['gap_reason']:<40}: {row['cnt']:>8,}")

# 5. Error table status
print("\n5. DOL ERROR TABLE")
print("-" * 50)

cur.execute("""
    SELECT failure_code, COUNT(*) as cnt 
    FROM outreach.dol_errors
    GROUP BY failure_code
    ORDER BY cnt DESC
""")
total_errors = 0
for row in cur.fetchall():
    print(f"  {row['failure_code']:<20}: {row['cnt']:>8,}")
    total_errors += row['cnt']
print(f"  {'TOTAL':<20}: {total_errors:>8,}")

# 6. DOL records
print("\n6. OUTREACH.DOL TABLE")
print("-" * 50)

cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol")
dol_records = cur.fetchone()['cnt']
print(f"  Total DOL records: {dol_records:,}")

cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol WHERE ein IS NOT NULL")
with_ein_dol = cur.fetchone()['cnt']
print(f"  With EIN: {with_ein_dol:,}")

conn.close()
