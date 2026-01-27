#!/usr/bin/env python3
"""
Analyze current fuzzy matching approach vs SNAP_ON_TOOLBOX spec.
Identify gaps and improvement opportunities.
"""

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
print("FUZZY MATCH ANALYSIS - GAPS VS SNAP_ON_TOOLBOX SPEC")
print("=" * 70)

print("""
SNAP_ON_TOOLBOX SPEC (EINMatcher):
  - Trigram similarity matching (>0.8 threshold)
  - State → City → Name cascade
  - DBA/trade name resolution  <-- ARE WE DOING THIS?
  - Software: pg_trgm + rapidfuzz
  - Accuracy: 85-95% (depends on name cleanliness)
""")

# 1. Check if form_5500 has DBA names
print("=" * 70)
print("1. DBA NAME AVAILABILITY IN 5500 DATA")
print("-" * 50)

cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(spons_dfe_dba_name) as has_dba,
        COUNT(CASE WHEN spons_dfe_dba_name IS NOT NULL AND spons_dfe_dba_name != '' 
                   AND spons_dfe_dba_name != sponsor_dfe_name THEN 1 END) as different_dba
    FROM dol.form_5500
""")
row = cur.fetchone()
print(f"  form_5500:")
print(f"    Total records: {row['total']:,}")
print(f"    Has DBA field: {row['has_dba']:,}")
print(f"    DBA different from name: {row['different_dba']:,}")

cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(sf_sponsor_dfe_dba_name) as has_dba,
        COUNT(CASE WHEN sf_sponsor_dfe_dba_name IS NOT NULL AND sf_sponsor_dfe_dba_name != '' 
                   AND sf_sponsor_dfe_dba_name != sf_sponsor_name THEN 1 END) as different_dba
    FROM dol.form_5500_sf
""")
row = cur.fetchone()
print(f"\n  form_5500_sf:")
print(f"    Total records: {row['total']:,}")
print(f"    Has DBA field: {row['has_dba']:,}")
print(f"    DBA different from name: {row['different_dba']:,}")

# 2. Sample DBA names that differ
print("\n" + "=" * 70)
print("2. SAMPLE DBA NAMES (where different from sponsor name)")
print("-" * 50)

cur.execute("""
    SELECT sponsor_dfe_name, spons_dfe_dba_name, sponsor_dfe_ein, spons_dfe_mail_us_state
    FROM dol.form_5500
    WHERE spons_dfe_dba_name IS NOT NULL 
    AND spons_dfe_dba_name != ''
    AND LOWER(spons_dfe_dba_name) != LOWER(sponsor_dfe_name)
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  Legal: {row['sponsor_dfe_name'][:35]:<35}")
    print(f"    DBA: {row['spons_dfe_dba_name'][:35]:<35} | {row['spons_dfe_mail_us_state']} | {row['sponsor_dfe_ein']}")
    print()

# 3. Check if our blocked companies might match DBA names
print("=" * 70)
print("3. BLOCKED COMPANIES - COULD THEY MATCH VIA DBA?")
print("-" * 50)

# Sample blocked company names
cur.execute("""
    SELECT cm.company_name, cm.address_state, cm.address_city
    FROM outreach.dol_errors de
    JOIN outreach.outreach o ON de.outreach_id = o.outreach_id
    JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
    JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
    WHERE cm.ein IS NULL
    AND cm.address_state = 'NC'
    ORDER BY RANDOM()
    LIMIT 20
""")
blocked = cur.fetchall()

print(f"\nSample 20 blocked NC companies - checking for DBA matches:")
matches_found = 0
for company in blocked:
    # Try matching against DBA names
    cur.execute("""
        SELECT spons_dfe_dba_name, sponsor_dfe_name, sponsor_dfe_ein,
               SIMILARITY(LOWER(%s), LOWER(spons_dfe_dba_name)) as dba_sim,
               SIMILARITY(LOWER(%s), LOWER(sponsor_dfe_name)) as name_sim
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = %s
        AND spons_dfe_dba_name IS NOT NULL AND spons_dfe_dba_name != ''
        AND (
            SIMILARITY(LOWER(%s), LOWER(spons_dfe_dba_name)) > 0.6
            OR SIMILARITY(LOWER(%s), LOWER(sponsor_dfe_name)) > 0.6
        )
        ORDER BY GREATEST(
            SIMILARITY(LOWER(%s), LOWER(spons_dfe_dba_name)),
            SIMILARITY(LOWER(%s), LOWER(sponsor_dfe_name))
        ) DESC
        LIMIT 1
    """, (company['company_name'], company['company_name'], company['address_state'],
          company['company_name'], company['company_name'],
          company['company_name'], company['company_name']))
    
    match = cur.fetchone()
    if match:
        matches_found += 1
        print(f"\n  '{company['company_name'][:40]}'")
        print(f"    → DBA Match: {match['spons_dfe_dba_name'][:40]} (sim: {match['dba_sim']:.2f})")
        print(f"      Legal: {match['sponsor_dfe_name'][:40]} (sim: {match['name_sim']:.2f})")
        print(f"      EIN: {match['sponsor_dfe_ein']}")

print(f"\n  RESULT: {matches_found}/20 found matches via DBA names")

# 4. Current matching only uses State+City+Name
print("\n" + "=" * 70)
print("4. CURRENT MATCHING CONSTRAINTS")
print("-" * 50)
print("""
  CURRENT: State + City + Name (trigram)
  
  PROBLEMS IDENTIFIED:
  1. City mismatch - company may have different address than 5500 filing
  2. DBA names not used - legal name vs trade name
  3. Only using sponsor_dfe_name, not spons_dfe_dba_name
""")

# 5. What if we relax city requirement?
print("=" * 70)
print("5. POTENTIAL GAIN: STATE + NAME ONLY (no city)")
print("-" * 50)

cur.execute("""
    WITH all_dol AS (
        SELECT sponsor_dfe_ein as ein, sponsor_dfe_name as name, 
               spons_dfe_mail_us_state as state, spons_dfe_dba_name as dba
        FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
        UNION ALL
        SELECT sf_spons_ein as ein, sf_sponsor_name as name,
               sf_spons_us_state as state, sf_sponsor_dfe_dba_name as dba
        FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
    )
    SELECT COUNT(DISTINCT cm.company_unique_id) as potential_matches
    FROM company.company_master cm
    JOIN all_dol d ON cm.address_state = d.state
    WHERE cm.ein IS NULL
    AND cm.company_unique_id IS NOT NULL
    AND (
        SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) > 0.7
        OR (d.dba IS NOT NULL AND SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) > 0.7)
    )
""")
state_only = cur.fetchone()['potential_matches']
print(f"\n  State + Name/DBA only (0.70 threshold): {state_only:,} potential matches")
print(f"  (Currently blocked without EIN: ~55,000)")

# 6. Check name variations that might not match
print("\n" + "=" * 70)
print("6. NAME NORMALIZATION ISSUES")
print("-" * 50)

# Sample company names that might have issues
cur.execute("""
    SELECT company_name
    FROM company.company_master
    WHERE ein IS NULL
    AND address_state = 'NC'
    AND (
        company_name LIKE '%LLC%'
        OR company_name LIKE '%Inc%'
        OR company_name LIKE '%Corp%'
        OR company_name LIKE '%&%'
        OR company_name LIKE '%, %'
    )
    LIMIT 10
""")
print("\nSample company names with potential normalization issues:")
for row in cur.fetchall():
    print(f"  {row['company_name']}")

print("""
\nRECOMMENDED IMPROVEMENTS:
  1. Add DBA name matching (check BOTH sponsor_dfe_name AND spons_dfe_dba_name)
  2. Relax city requirement (try State+Name first, then State+City+Name)
  3. Normalize names: remove LLC/Inc/Corp, normalize &/and, trim suffixes
  4. Consider phonetic matching (Soundex/Metaphone) for typos
""")

conn.close()
