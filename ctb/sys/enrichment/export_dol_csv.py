#!/usr/bin/env python3
"""
Export DOL data (form_5500 + form_5500_sf) to CSV for matching analysis.
"""
import psycopg2
from psycopg2.extras import RealDictCursor
import csv

NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

OUTPUT_FORM_5500 = 'ctb/sys/enrichment/output/dol_form_5500_export.csv'
OUTPUT_FORM_5500_SF = 'ctb/sys/enrichment/output/dol_form_5500_sf_export.csv'

print("Exporting DOL data to CSV...")

conn = psycopg2.connect(**NEON_CONFIG)
cur = conn.cursor(cursor_factory=RealDictCursor)

# Export Form 5500 (large plans)
print("\n1. Exporting dol.form_5500...")
cur.execute("""
    SELECT
        ack_id,
        sponsor_dfe_ein as ein,
        sponsor_dfe_name as sponsor_name,
        plan_name,
        spons_dfe_mail_us_state as state,
        tot_active_partcp_cnt as participant_count,
        form_year,
        company_unique_id,
        spons_dfe_mail_us_city as city,
        spons_dfe_phone_num as phone
    FROM dol.form_5500
    ORDER BY spons_dfe_mail_us_state, sponsor_dfe_name
""")

records_5500 = cur.fetchall()
print(f"   Fetched {len(records_5500):,} Form 5500 records")

with open(OUTPUT_FORM_5500, 'w', newline='', encoding='utf-8') as f:
    if records_5500:
        writer = csv.DictWriter(f, fieldnames=records_5500[0].keys())
        writer.writeheader()
        writer.writerows(records_5500)

print(f"   Exported to: {OUTPUT_FORM_5500}")

# Export Form 5500-SF (small plans)
print("\n2. Exporting dol.form_5500_sf...")
cur.execute("""
    SELECT
        ack_id,
        sponsor_dfe_ein as ein,
        sponsor_dfe_name as sponsor_name,
        plan_name,
        spons_dfe_mail_us_state as state,
        tot_partcp_eoy_cnt as participant_count,
        form_year,
        company_unique_id
    FROM dol.form_5500_sf
    ORDER BY spons_dfe_mail_us_state, sponsor_dfe_name
""")

records_5500_sf = cur.fetchall()
print(f"   Fetched {len(records_5500_sf):,} Form 5500-SF records")

with open(OUTPUT_FORM_5500_SF, 'w', newline='', encoding='utf-8') as f:
    if records_5500_sf:
        writer = csv.DictWriter(f, fieldnames=records_5500_sf[0].keys())
        writer.writeheader()
        writer.writerows(records_5500_sf)

print(f"   Exported to: {OUTPUT_FORM_5500_SF}")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

cur.execute("""
    SELECT
        spons_dfe_mail_us_state as state,
        COUNT(*) as count,
        SUM(CASE WHEN sponsor_dfe_ein IS NOT NULL AND sponsor_dfe_ein != '' THEN 1 ELSE 0 END) as has_ein,
        AVG(tot_active_partcp_cnt) as avg_participants
    FROM dol.form_5500
    WHERE spons_dfe_mail_us_state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
    GROUP BY spons_dfe_mail_us_state
    ORDER BY count DESC
""")

print("\nForm 5500 (Large Plans) - Target States:")
for row in cur.fetchall():
    print(f"  {row['state']:2} | {row['count']:6,} plans | EIN: {row['has_ein']:6,} ({100*row['has_ein']/row['count']:5.1f}%) | Avg participants: {row['avg_participants']:6.0f}")

cur.execute("""
    SELECT
        spons_dfe_mail_us_state as state,
        COUNT(*) as count,
        SUM(CASE WHEN sponsor_dfe_ein IS NOT NULL AND sponsor_dfe_ein != '' THEN 1 ELSE 0 END) as has_ein,
        AVG(tot_partcp_eoy_cnt) as avg_participants
    FROM dol.form_5500_sf
    WHERE spons_dfe_mail_us_state IN ('PA', 'VA', 'MD', 'OH', 'WV', 'KY', 'DE', 'OK')
    GROUP BY spons_dfe_mail_us_state
    ORDER BY count DESC
""")

print("\nForm 5500-SF (Small Plans) - Target States:")
for row in cur.fetchall():
    print(f"  {row['state']:2} | {row['count']:6,} plans | EIN: {row['has_ein']:6,} ({100*row['has_ein']/row['count']:5.1f}%) | Avg participants: {row['avg_participants']:6.0f}")

# Check for already matched records
cur.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN company_unique_id IS NOT NULL THEN 1 ELSE 0 END) as already_matched
    FROM dol.form_5500
""")
matched = cur.fetchone()
print(f"\nForm 5500 matching status:")
print(f"  Total: {matched['total']:,}")
print(f"  Already matched to companies: {matched['already_matched']:,} ({100*matched['already_matched']/matched['total']:.1f}%)")

cur.execute("""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN company_unique_id IS NOT NULL THEN 1 ELSE 0 END) as already_matched
    FROM dol.form_5500_sf
""")
matched_sf = cur.fetchone()
print(f"\nForm 5500-SF matching status:")
print(f"  Total: {matched_sf['total']:,}")
print(f"  Already matched to companies: {matched_sf['already_matched']:,} ({100*matched_sf['already_matched']/matched_sf['total']:.1f}%)")

conn.close()
print("\nDone!")

