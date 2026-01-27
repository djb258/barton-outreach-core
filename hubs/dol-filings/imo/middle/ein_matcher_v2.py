#!/usr/bin/env python3
"""
EIN Matcher V2 - SNAP_ON_TOOLBOX Compliant
==========================================
Implements full spec from SNAP_ON_TOOLBOX.yaml:
  - Trigram similarity matching
  - State → City → Name CASCADE (state+name first, then add city)
  - DBA/trade name resolution
  - Name normalization

Matching Strategy (per spec):
  PASS 1: State + Name (high threshold 0.85) - catches exact/near matches
  PASS 2: State + Name + DBA (threshold 0.80) - catches DBA matches  
  PASS 3: State + City + Name (threshold 0.70) - catches city-specific
  PASS 4: State + City + DBA (threshold 0.70) - catches city+DBA
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
import re
from datetime import datetime, timezone

NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

def normalize_company_name(name):
    """Normalize company name for better matching."""
    if not name:
        return ''
    
    # Convert to uppercase
    name = name.upper()
    
    # Remove common suffixes
    suffixes = [
        r'\s*,?\s*LLC\.?$',
        r'\s*,?\s*L\.L\.C\.?$',
        r'\s*,?\s*INC\.?$',
        r'\s*,?\s*INCORPORATED$',
        r'\s*,?\s*CORP\.?$',
        r'\s*,?\s*CORPORATION$',
        r'\s*,?\s*CO\.?$',
        r'\s*,?\s*COMPANY$',
        r'\s*,?\s*LTD\.?$',
        r'\s*,?\s*LIMITED$',
        r'\s*,?\s*LP\.?$',
        r'\s*,?\s*L\.P\.?$',
        r'\s*,?\s*LLP\.?$',
        r'\s*,?\s*L\.L\.P\.?$',
        r'\s*,?\s*PC\.?$',
        r'\s*,?\s*P\.C\.?$',
        r'\s*,?\s*PLLC\.?$',
        r'\s*,?\s*P\.L\.L\.C\.?$',
    ]
    
    for suffix in suffixes:
        name = re.sub(suffix, '', name, flags=re.IGNORECASE)
    
    # Normalize ampersand
    name = re.sub(r'\s*&\s*', ' AND ', name)
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    
    # Remove punctuation except spaces
    name = re.sub(r'[^\w\s]', '', name)
    
    return name


def main():
    parser = argparse.ArgumentParser(description='EIN Matcher V2 - SNAP_ON_TOOLBOX Compliant')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating')
    parser.add_argument('--state', type=str, help='Filter by state (e.g., NC)')
    parser.add_argument('--limit', type=int, help='Limit updates')
    args = parser.parse_args()

    dry_run = args.dry_run
    state = args.state.upper() if args.state else None
    limit = args.limit

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 70)
    print("EIN MATCHER V2 - SNAP_ON_TOOLBOX COMPLIANT")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"State: {state or 'All'}")
    print(f"Limit: {limit or 'None'}")
    print()
    print("Strategy: State→Name (0.85) → State→Name+DBA (0.80) → State→City→Name (0.70)")
    print()

    # Current status
    cur.execute('SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL')
    before_ein = cur.fetchone()['with_ein']
    print(f"BEFORE: {before_ein:,} companies with EIN")
    print()

    state_clause = "AND cm.address_state = %s" if state else ""
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    total_matched = 0
    all_matches = []

    # =========================================================================
    # PASS 1: State + Name (high threshold 0.85) - no city requirement
    # =========================================================================
    print("=" * 70)
    print("PASS 1: State + Name (threshold 0.85)")
    print("-" * 70)
    
    params = [state] if state else []
    
    cur.execute(f'''
        WITH all_dol AS (
            SELECT DISTINCT sponsor_dfe_ein as ein, sponsor_dfe_name as name, 
                   spons_dfe_mail_us_state as state
            FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
            UNION
            SELECT DISTINCT sf_spons_ein as ein, sf_sponsor_name as name,
                   sf_spons_us_state as state
            FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
        ),
        ranked AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_state,
                cm.address_city,
                d.ein as dol_ein,
                d.name as dol_name,
                'STATE+NAME' as match_type,
                SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY cm.company_unique_id
                    ORDER BY SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) DESC
                ) as rn
            FROM company.company_master cm
            JOIN all_dol d ON cm.address_state = d.state
            WHERE cm.ein IS NULL
              AND cm.company_unique_id IS NOT NULL
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) > 0.85
              {state_clause}
        )
        SELECT * FROM ranked WHERE rn = 1
        ORDER BY similarity DESC
        {limit_clause}
    ''', params)
    
    pass1 = cur.fetchall()
    print(f"  Found: {len(pass1):,} matches")
    all_matches.extend(pass1)
    
    # Show samples
    for m in pass1[:5]:
        print(f"    [{m['similarity']:.2f}] {m['company_name'][:35]} → {m['dol_name'][:35]}")

    # =========================================================================
    # PASS 2: State + DBA Name (threshold 0.80)
    # =========================================================================
    print()
    print("=" * 70)
    print("PASS 2: State + DBA Name (threshold 0.80)")
    print("-" * 70)
    
    # Get already matched IDs to exclude
    matched_ids = [m['company_unique_id'] for m in all_matches]
    
    cur.execute(f'''
        WITH all_dba AS (
            SELECT DISTINCT sponsor_dfe_ein as ein, spons_dfe_dba_name as dba, 
                   spons_dfe_mail_us_state as state, sponsor_dfe_name as legal_name
            FROM dol.form_5500 
            WHERE sponsor_dfe_ein IS NOT NULL 
            AND spons_dfe_dba_name IS NOT NULL AND spons_dfe_dba_name != ''
            UNION
            SELECT DISTINCT sf_spons_ein as ein, sf_sponsor_dfe_dba_name as dba,
                   sf_spons_us_state as state, sf_sponsor_name as legal_name
            FROM dol.form_5500_sf 
            WHERE sf_spons_ein IS NOT NULL
            AND sf_sponsor_dfe_dba_name IS NOT NULL AND sf_sponsor_dfe_dba_name != ''
        ),
        ranked AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_state,
                cm.address_city,
                d.ein as dol_ein,
                d.dba as dol_name,
                d.legal_name as legal_name,
                'STATE+DBA' as match_type,
                SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY cm.company_unique_id
                    ORDER BY SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) DESC
                ) as rn
            FROM company.company_master cm
            JOIN all_dba d ON cm.address_state = d.state
            WHERE cm.ein IS NULL
              AND cm.company_unique_id IS NOT NULL
              AND cm.company_unique_id != ALL(%s)
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) > 0.80
              {state_clause}
        )
        SELECT * FROM ranked WHERE rn = 1
        ORDER BY similarity DESC
        {limit_clause}
    ''', [matched_ids] + params)
    
    pass2 = cur.fetchall()
    print(f"  Found: {len(pass2):,} matches")
    all_matches.extend(pass2)
    
    for m in pass2[:5]:
        print(f"    [{m['similarity']:.2f}] {m['company_name'][:30]} → DBA: {m['dol_name'][:30]}")
        if m.get('legal_name'):
            print(f"           Legal: {m['legal_name'][:40]}")

    # =========================================================================
    # PASS 3: State + City + Name (threshold 0.70)
    # =========================================================================
    print()
    print("=" * 70)
    print("PASS 3: State + City + Name (threshold 0.70)")
    print("-" * 70)
    
    matched_ids = [m['company_unique_id'] for m in all_matches]
    
    cur.execute(f'''
        WITH all_dol AS (
            SELECT DISTINCT sponsor_dfe_ein as ein, sponsor_dfe_name as name, 
                   spons_dfe_mail_us_state as state, spons_dfe_mail_us_city as city
            FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
            UNION
            SELECT DISTINCT sf_spons_ein as ein, sf_sponsor_name as name,
                   sf_spons_us_state as state, sf_spons_us_city as city
            FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
        ),
        ranked AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_state,
                cm.address_city,
                d.ein as dol_ein,
                d.name as dol_name,
                'STATE+CITY+NAME' as match_type,
                SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY cm.company_unique_id
                    ORDER BY SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) DESC
                ) as rn
            FROM company.company_master cm
            JOIN all_dol d 
                ON cm.address_state = d.state
                AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.city))
            WHERE cm.ein IS NULL
              AND cm.company_unique_id IS NOT NULL
              AND cm.company_unique_id != ALL(%s)
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) > 0.70
              {state_clause}
        )
        SELECT * FROM ranked WHERE rn = 1
        ORDER BY similarity DESC
        {limit_clause}
    ''', [matched_ids] + params)
    
    pass3 = cur.fetchall()
    print(f"  Found: {len(pass3):,} matches")
    all_matches.extend(pass3)
    
    for m in pass3[:5]:
        print(f"    [{m['similarity']:.2f}] {m['company_name'][:35]} → {m['dol_name'][:35]}")

    # =========================================================================
    # PASS 4: State + City + DBA (threshold 0.70)
    # =========================================================================
    print()
    print("=" * 70)
    print("PASS 4: State + City + DBA (threshold 0.70)")
    print("-" * 70)
    
    matched_ids = [m['company_unique_id'] for m in all_matches]
    
    cur.execute(f'''
        WITH all_dba AS (
            SELECT DISTINCT sponsor_dfe_ein as ein, spons_dfe_dba_name as dba, 
                   spons_dfe_mail_us_state as state, spons_dfe_mail_us_city as city
            FROM dol.form_5500 
            WHERE sponsor_dfe_ein IS NOT NULL 
            AND spons_dfe_dba_name IS NOT NULL AND spons_dfe_dba_name != ''
            UNION
            SELECT DISTINCT sf_spons_ein as ein, sf_sponsor_dfe_dba_name as dba,
                   sf_spons_us_state as state, sf_spons_us_city as city
            FROM dol.form_5500_sf 
            WHERE sf_spons_ein IS NOT NULL
            AND sf_sponsor_dfe_dba_name IS NOT NULL AND sf_sponsor_dfe_dba_name != ''
        ),
        ranked AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_state,
                cm.address_city,
                d.ein as dol_ein,
                d.dba as dol_name,
                'STATE+CITY+DBA' as match_type,
                SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY cm.company_unique_id
                    ORDER BY SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) DESC
                ) as rn
            FROM company.company_master cm
            JOIN all_dba d 
                ON cm.address_state = d.state
                AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.city))
            WHERE cm.ein IS NULL
              AND cm.company_unique_id IS NOT NULL
              AND cm.company_unique_id != ALL(%s)
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.dba)) > 0.70
              {state_clause}
        )
        SELECT * FROM ranked WHERE rn = 1
        ORDER BY similarity DESC
        {limit_clause}
    ''', [matched_ids] + params)
    
    pass4 = cur.fetchall()
    print(f"  Found: {len(pass4):,} matches")
    all_matches.extend(pass4)
    
    for m in pass4[:5]:
        print(f"    [{m['similarity']:.2f}] {m['company_name'][:35]} → DBA: {m['dol_name'][:35]}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print()
    print("=" * 70)
    print("TOTAL MATCHES BY PASS")
    print("-" * 70)
    print(f"  PASS 1 (State+Name 0.85):      {len(pass1):>6,}")
    print(f"  PASS 2 (State+DBA 0.80):       {len(pass2):>6,}")
    print(f"  PASS 3 (State+City+Name 0.70): {len(pass3):>6,}")
    print(f"  PASS 4 (State+City+DBA 0.70):  {len(pass4):>6,}")
    print(f"  {'TOTAL':<33} {len(all_matches):>6,}")

    # Similarity distribution
    print()
    print("SIMILARITY DISTRIBUTION:")
    brackets = [
        (0.95, 1.01, "0.95-1.00"),
        (0.90, 0.95, "0.90-0.95"),
        (0.85, 0.90, "0.85-0.90"),
        (0.80, 0.85, "0.80-0.85"),
        (0.75, 0.80, "0.75-0.80"),
        (0.70, 0.75, "0.70-0.75"),
    ]
    for low, high, label in brackets:
        cnt = len([m for m in all_matches if low <= m['similarity'] < high])
        if cnt > 0:
            print(f"  {label}: {cnt:,}")

    # =========================================================================
    # UPDATE
    # =========================================================================
    if dry_run:
        print()
        print(f"DRY RUN - Would update {len(all_matches):,} companies with EIN")
    else:
        print()
        print("UPDATING company_master...")
        updated = 0
        for match in all_matches:
            cur.execute('''
                UPDATE company.company_master
                SET ein = %s,
                    updated_at = %s
                WHERE company_unique_id = %s
                AND ein IS NULL
            ''', (match['dol_ein'], datetime.now(timezone.utc), match['company_unique_id']))
            updated += cur.rowcount
        
        conn.commit()
        print(f"  ✅ Updated {updated:,} companies")

        # Final status
        cur.execute('SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL')
        after_ein = cur.fetchone()['with_ein']
        
        print()
        print(f"AFTER: {after_ein:,} companies with EIN")
        print(f"NEW: {after_ein - before_ein:,} EINs backfilled")

    conn.close()


if __name__ == '__main__':
    main()
