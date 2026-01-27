#!/usr/bin/env python3
"""
Enhanced DOL EIN Matcher - Uses ALL 5500 sources
=================================================
Matches companies to DOL data using:
  1. form_5500 (230k filings, 146k EINs)
  2. form_5500_sf (760k filings, 693k EINs) - SHORT FORM!

Combined: 825,572 unique EINs

Usage:
    python ein_matcher_enhanced.py [--dry-run] [--threshold 0.7] [--state NC]
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import argparse
from datetime import datetime, timezone

NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}

def main():
    parser = argparse.ArgumentParser(description='Enhanced DOL EIN Matcher - uses ALL 5500 sources')
    parser.add_argument('--dry-run', action='store_true', help='Show matches without updating')
    parser.add_argument('--threshold', type=float, default=0.70, help='Similarity threshold (default: 0.70)')
    parser.add_argument('--limit', type=int, help='Limit number of updates')
    parser.add_argument('--state', type=str, help='Filter by state (e.g., NC)')
    args = parser.parse_args()

    dry_run = args.dry_run
    threshold = args.threshold
    limit = args.limit
    state = args.state.upper() if args.state else None

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 70)
    print("ENHANCED DOL EIN MATCHER")
    print("=" * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE UPDATE'}")
    print(f"Threshold: {threshold}")
    print(f"State: {state or 'All'}")
    print(f"Limit: {limit or 'None'}")
    print()
    print("Sources: form_5500 + form_5500_sf (825k unique EINs)")
    print()

    # Current status
    cur.execute('SELECT COUNT(*) as total FROM company.company_master WHERE company_unique_id IS NOT NULL')
    total = cur.fetchone()['total']
    
    cur.execute('SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL')
    with_ein = cur.fetchone()['with_ein']

    print(f"BEFORE:")
    print(f"  Total companies: {total:,}")
    print(f"  With EIN: {with_ein:,}")
    print(f"  Without EIN: {total - with_ein:,}")
    print()

    # Build query with BOTH tables
    limit_clause = f"LIMIT {limit}" if limit else ""
    state_clause = "AND cm.address_state = %s" if state else ""
    params = [threshold, threshold, state, state] if state else [threshold, threshold]

    print("Finding matches from BOTH form_5500 and form_5500_sf...")
    
    query = f'''
        WITH all_dol AS (
            -- form_5500 (regular filings)
            SELECT 
                sponsor_dfe_ein as ein,
                sponsor_dfe_name as name,
                spons_dfe_mail_us_city as city,
                spons_dfe_mail_us_state as state,
                'form_5500' as source
            FROM dol.form_5500
            WHERE sponsor_dfe_ein IS NOT NULL
            
            UNION ALL
            
            -- form_5500_sf (SHORT FORM - the big one!)
            SELECT 
                sf_spons_ein as ein,
                sf_sponsor_name as name,
                sf_spons_us_city as city,
                sf_spons_us_state as state,
                'form_5500_sf' as source
            FROM dol.form_5500_sf
            WHERE sf_spons_ein IS NOT NULL
        ),
        ranked_matches AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_city,
                cm.address_state,
                d.ein as dol_ein,
                d.name as dol_name,
                d.source as dol_source,
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
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.name)) > %s
              {state_clause.replace('%s', '%s')}
        )
        SELECT * FROM ranked_matches WHERE rn = 1
        ORDER BY similarity DESC
        {limit_clause}
    '''
    
    if state:
        cur.execute(query, [threshold, state])
    else:
        cur.execute(query, [threshold])
    
    matches = cur.fetchall()
    
    print(f"Found {len(matches):,} matches")
    print()

    # Source breakdown
    sources = {}
    for m in matches:
        src = m['dol_source']
        sources[src] = sources.get(src, 0) + 1
    
    print("MATCHES BY SOURCE:")
    for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {cnt:,}")
    print()

    # Sample matches
    print("SAMPLE MATCHES:")
    print("-" * 70)
    for match in matches[:15]:
        print(f"  [{match['similarity']:.2f}] {match['company_name'][:40]}")
        print(f"         → DOL ({match['dol_source']}): {match['dol_name'][:40]}")
        print(f"         {match['address_city']}, {match['address_state']} | EIN: {match['dol_ein']}")
        print()

    # Similarity distribution
    print("SIMILARITY DISTRIBUTION:")
    brackets = [
        (0.95, 1.01, "0.95-1.00"),
        (0.90, 0.95, "0.90-0.95"),
        (0.85, 0.90, "0.85-0.90"),
        (0.80, 0.85, "0.80-0.85"),
        (0.75, 0.80, "0.75-0.80"),
        (0.70, 0.75, "0.70-0.75"),
        (0.65, 0.70, "0.65-0.70"),
        (0.60, 0.65, "0.60-0.65"),
    ]
    for low, high, label in brackets:
        cnt = len([m for m in matches if low <= m['similarity'] < high])
        if cnt > 0:
            print(f"  {label}: {cnt:,}")
    print()

    if dry_run:
        print("DRY RUN - No changes made")
        print(f"Would update {len(matches):,} companies with EIN")
    else:
        print("UPDATING company_master...")
        updated = 0
        for match in matches:
            cur.execute('''
                UPDATE company.company_master
                SET ein = %s,
                    updated_at = %s
                WHERE company_unique_id = %s
                AND ein IS NULL
            ''', (match['dol_ein'], datetime.now(timezone.utc), match['company_unique_id']))
            updated += cur.rowcount
        
        conn.commit()
        print(f"Updated {updated:,} companies")

        # Final status
        cur.execute('SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL')
        new_with_ein = cur.fetchone()['with_ein']
        
        print()
        print(f"AFTER:")
        print(f"  With EIN: {new_with_ein:,}")
        print(f"  NEW: {new_with_ein - with_ein:,} EINs backfilled")

        if state:
            cur.execute('''
                SELECT COUNT(*) as cnt FROM company.company_master 
                WHERE ein IS NOT NULL AND address_state = %s
            ''', (state,))
            state_ein = cur.fetchone()['cnt']
            cur.execute('''
                SELECT COUNT(*) as cnt FROM company.company_master 
                WHERE address_state = %s
            ''', (state,))
            state_total = cur.fetchone()['cnt']
            print(f"  {state}: {state_ein:,}/{state_total:,} ({100*state_ein/state_total:.1f}%)")

    conn.close()

if __name__ == '__main__':
    main()
