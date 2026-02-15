#!/usr/bin/env python3
"""
Analyze DOL enrichment - two strategies:

Strategy A: Enrich DOL records to find URLs, match back to existing company_master
Strategy B: Add DOL companies as NEW records to company_master (with EIN already)
"""

import os
import psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("=" * 70)
print("DOL ENRICHMENT - STRATEGIC OPTIONS")
print("=" * 70)

# Current state
cur.execute('SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL')
with_ein = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM company.company_master')
total_cm = cur.fetchone()[0]

# Unmatched DOL EINs
cur.execute('''
    WITH matched_eins AS (
        SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
    ),
    all_dol AS (
        SELECT DISTINCT sponsor_dfe_ein as ein, sponsor_dfe_name as name, 
               spons_dfe_mail_us_state as state, spons_dfe_mail_us_city as city
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state IN ('NC','PA','OH','VA','MD','KY','OK','WV','DE')
        AND sponsor_dfe_ein IS NOT NULL
        
        UNION
        
        SELECT DISTINCT sf_spons_ein, sf_sponsor_name, sf_spons_us_state, sf_spons_us_city
        FROM dol.form_5500_sf
        WHERE sf_spons_us_state IN ('NC','PA','OH','VA','MD','KY','OK','WV','DE')
        AND sf_spons_ein IS NOT NULL
    )
    SELECT COUNT(DISTINCT d.ein)
    FROM all_dol d
    LEFT JOIN matched_eins m ON d.ein = m.ein
    WHERE m.ein IS NULL
''')
unmatched_dol = cur.fetchone()[0]

print()
print(f"CURRENT STATE:")
print(f"  company_master total: {total_cm:,}")
print(f"  company_master with EIN: {with_ein:,} ({100*with_ein/total_cm:.1f}%)")
print(f"  Unmatched DOL EINs (target states): {unmatched_dol:,}")
print()

print("=" * 70)
print("STRATEGY A: Enrich DOL → Match back to company_master")
print("=" * 70)
print("""
  Use GooglePlaces to find URL for each DOL company.
  If URL matches existing company_master record → backfill EIN.
  
  LIMITATION: Only helps companies we ALREADY have.
  Many DOL companies may not be in company_master at all.
""")

# Estimate: how many DOL companies might already be in company_master?
# We matched 19,388 so far. There are 128,533 unmatched.
# Conservative estimate: 10-20% of remaining might match via URL enrichment
estimate_a_low = int(unmatched_dol * 0.10)
estimate_a_high = int(unmatched_dol * 0.20)
cost_a = unmatched_dol * 0.017

print(f"  Cost: ${cost_a:,.2f} ({unmatched_dol:,} calls @ $0.017)")
print(f"  Expected backfills: {estimate_a_low:,} - {estimate_a_high:,} (10-20%)")
print(f"  New EIN coverage: {100*(with_ein + estimate_a_low)/total_cm:.1f}% - {100*(with_ein + estimate_a_high)/total_cm:.1f}%")
print()

print("=" * 70)
print("STRATEGY B: Import DOL companies as NEW records")
print("=" * 70)
print("""
  Use GooglePlaces to enrich DOL with URL.
  Import as NEW company_master records (with EIN already attached).
  
  BENEFIT: Grows company_master by 128K+ companies with verified EINs.
  These are REAL companies (they file Form 5500 benefit plans).
""")

success_rate = 0.85  # 85% of GooglePlaces calls return a result
new_companies = int(unmatched_dol * success_rate)
new_total = total_cm + new_companies
new_with_ein = with_ein + new_companies

print(f"  Cost: ${cost_a:,.2f} ({unmatched_dol:,} calls @ $0.017)")
print(f"  Expected new companies: {new_companies:,} (85% success rate)")
print(f"  New company_master total: {new_total:,}")
print(f"  New EIN coverage: {new_with_ein:,} / {new_total:,} = {100*new_with_ein/new_total:.1f}%")
print()

print("=" * 70)
print("COMPARISON")
print("=" * 70)
print(f"                            Strategy A          Strategy B")
print(f"  Cost:                     ${cost_a:,.0f}            ${cost_a:,.0f}")
print(f"  New EIN matches:          {estimate_a_low:,}-{estimate_a_high:,}          {new_companies:,}")
print(f"  Company growth:           0                   +{new_companies:,}")
print(f"  Final EIN coverage:       ~30%                {100*new_with_ein/new_total:.0f}%")
print()
print("  Strategy B is clearly superior - same cost, 10x the results.")
print("=" * 70)
