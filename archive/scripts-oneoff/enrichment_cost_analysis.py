#!/usr/bin/env python3
"""Analyze cost and potential ROI of GooglePlaces enrichment for DOL records."""

import os
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Count unmatched DOL EINs in target states
cur.execute('''
    WITH matched_eins AS (
        SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
    ),
    all_dol_eins AS (
        SELECT DISTINCT sponsor_dfe_ein as ein, spons_dfe_mail_us_state as state
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state IN ('NC','PA','OH','VA','MD','KY','OK','WV','DE')
        AND sponsor_dfe_ein IS NOT NULL
        
        UNION
        
        SELECT DISTINCT sf_spons_ein as ein, sf_spons_us_state as state
        FROM dol.form_5500_sf
        WHERE sf_spons_us_state IN ('NC','PA','OH','VA','MD','KY','OK','WV','DE')
        AND sf_spons_ein IS NOT NULL
    )
    SELECT COUNT(DISTINCT d.ein)
    FROM all_dol_eins d
    LEFT JOIN matched_eins m ON d.ein = m.ein
    WHERE m.ein IS NULL
''')
unmatched = cur.fetchone()[0]

# Current company_master with EIN
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
with_ein = cur.fetchone()[0]

# Total company_master
cur.execute('SELECT COUNT(*) FROM company.company_master')
total = cur.fetchone()[0]

print("=" * 70)
print("DOL ENRICHMENT COST/BENEFIT ANALYSIS")
print("=" * 70)
print()
print("CURRENT STATE:")
print(f"  company_master with EIN: {with_ein:,} / {total:,} ({100*with_ein/total:.1f}%)")
print(f"  Unmatched DOL EINs in target states: {unmatched:,}")
print()
print("GOOGLEPLACES ENRICHMENT (Tier 1):")
print(f"  Cost per call: $0.017")
print(f"  Total calls needed: {unmatched:,}")
print(f"  TOTAL COST: ${unmatched * 0.017:,.2f}")
print()
print("PROJECTED RESULTS (conservative 80% match rate):")
new_matches = int(unmatched * 0.8)
print(f"  Expected new EIN matches: {new_matches:,}")
print(f"  New total with EIN: {with_ein + new_matches:,}")
print(f"  New EIN coverage: {100*(with_ein + new_matches)/total:.1f}%")
print()
print("PROJECTED RESULTS (optimistic 90% match rate):")
new_matches_90 = int(unmatched * 0.9)
print(f"  Expected new EIN matches: {new_matches_90:,}")
print(f"  New total with EIN: {with_ein + new_matches_90:,}")
print(f"  New EIN coverage: {100*(with_ein + new_matches_90)/total:.1f}%")
print()
print("-" * 70)
print("COST PER NEW EIN:")
print(f"  @ 80% match: ${(unmatched * 0.017) / new_matches:.3f} per EIN")
print(f"  @ 90% match: ${(unmatched * 0.017) / new_matches_90:.3f} per EIN")
print("=" * 70)
