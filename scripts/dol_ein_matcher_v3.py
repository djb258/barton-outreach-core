#!/usr/bin/env python3
"""
DOL EIN Matcher V3 - Pure Database Cross-Match.

TIER 0 FREE - Uses only existing data:
1. DOL has: EIN + Company Name + City + State
2. company_master has: Company Name + City + State + URL (but missing EIN)

Strategy: Fuzzy match DOL names to company_master names in same location.
When matched, backfill EIN from DOL to company_master.

This is FREE (no external APIs) and can find matches we missed.
"""

import os
import psycopg2
from rapidfuzz import fuzz
import argparse

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def get_unmatched_dol_by_state(cur, state: str, limit: int = 1000):
    """Get DOL records that haven't been matched to company_master."""
    cur.execute("""
        WITH matched_eins AS (
            SELECT DISTINCT ein FROM company.company_master WHERE ein IS NOT NULL
        )
        SELECT DISTINCT ON (sponsor_dfe_ein)
            sponsor_dfe_ein as ein,
            sponsor_dfe_name as name,
            spons_dfe_mail_us_city as city
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = %s
        AND sponsor_dfe_ein IS NOT NULL
        AND sponsor_dfe_name IS NOT NULL
        AND sponsor_dfe_ein NOT IN (SELECT ein FROM matched_eins)
        ORDER BY sponsor_dfe_ein
        LIMIT %s
    """, (state, limit))
    return cur.fetchall()


def get_company_master_by_state_city(cur, state: str, city: str):
    """Get company_master records in same state/city without EIN."""
    cur.execute("""
        SELECT company_unique_id, company_name, website_url
        FROM company.company_master
        WHERE address_state = %s
        AND address_city ILIKE %s
        AND ein IS NULL
        AND website_url IS NOT NULL
    """, (state, f'%{city}%'))
    return cur.fetchall()


def normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    n = name.upper()
    # Remove common suffixes
    for suffix in [' INC', ' LLC', ' CORP', ' CORPORATION', ' CO', ' LTD', ' LIMITED', 
                   ' LP', ' LLP', ' PA', ' PC', ' PLLC', '.', ',']:
        n = n.replace(suffix, '')
    return n.strip()


def find_best_match(dol_name: str, candidates: list) -> tuple:
    """Find best fuzzy match among candidates."""
    dol_norm = normalize_name(dol_name)
    
    best_score = 0
    best_match = None
    
    for cid, cm_name, url in candidates:
        cm_norm = normalize_name(cm_name)
        
        # Use multiple fuzzy match strategies
        ratio = fuzz.ratio(dol_norm, cm_norm)
        partial = fuzz.partial_ratio(dol_norm, cm_norm)
        token_sort = fuzz.token_sort_ratio(dol_norm, cm_norm)
        
        # Weighted score
        score = (ratio * 0.4) + (partial * 0.3) + (token_sort * 0.3)
        
        if score > best_score:
            best_score = score
            best_match = (cid, cm_name, url)
    
    return best_match, best_score


def process_state(state: str, limit: int = 1000, threshold: float = 80.0, dry_run: bool = False):
    """Process DOL records for a state and find matches."""
    print(f"\n{'='*70}")
    print(f"PROCESSING STATE: {state}")
    print(f"{'='*70}")
    
    conn = get_conn()
    cur = conn.cursor()
    
    # Get unmatched DOL records
    dol_records = get_unmatched_dol_by_state(cur, state, limit)
    print(f"Unmatched DOL records: {len(dol_records)}")
    
    if not dol_records:
        print("No records to process!")
        cur.close()
        conn.close()
        return []
    
    # Group by city for efficient matching
    by_city = {}
    for ein, name, city in dol_records:
        if city:
            city_key = city.upper()
            if city_key not in by_city:
                by_city[city_key] = []
            by_city[city_key].append((ein, name, city))
    
    print(f"Unique cities: {len(by_city)}")
    
    # Find matches
    matches = []
    no_candidates = 0
    below_threshold = 0
    
    for city, records in by_city.items():
        # Get company_master candidates for this city
        candidates = get_company_master_by_state_city(cur, state, city)
        
        if not candidates:
            no_candidates += len(records)
            continue
        
        for ein, dol_name, _ in records:
            best, score = find_best_match(dol_name, candidates)
            
            if score >= threshold:
                matches.append({
                    'ein': ein,
                    'dol_name': dol_name,
                    'company_id': best[0],
                    'cm_name': best[1],
                    'url': best[2],
                    'score': score
                })
            else:
                below_threshold += 1
    
    # Summary
    print(f"\n{'='*70}")
    print(f"RESULTS FOR {state}")
    print(f"{'='*70}")
    print(f"  DOL records processed: {len(dol_records)}")
    print(f"  No candidates in company_master: {no_candidates}")
    print(f"  Below threshold ({threshold}%): {below_threshold}")
    print(f"  MATCHES FOUND: {len(matches)}")
    
    if matches:
        print(f"\nTop matches (score >= {threshold}):")
        for m in sorted(matches, key=lambda x: -x['score'])[:20]:
            print(f"  {m['score']:.1f}% | {m['dol_name'][:30]:<30} → {m['cm_name'][:30]}")
    
    # Apply if not dry run
    if not dry_run and matches:
        print(f"\nApplying {len(matches)} EIN backfills...")
        applied = 0
        for m in matches:
            try:
                cur.execute("""
                    UPDATE company.company_master
                    SET ein = %s
                    WHERE company_unique_id = %s
                    AND ein IS NULL
                """, (m['ein'], m['company_id']))
                if cur.rowcount > 0:
                    applied += 1
            except Exception as e:
                print(f"  Error: {e}")
        
        conn.commit()
        print(f"Applied: {applied}")
    
    cur.close()
    conn.close()
    
    return matches


def main():
    parser = argparse.ArgumentParser(description='DOL EIN Matcher V3 - Database Cross-Match')
    parser.add_argument('--state', help='State abbreviation (NC, PA, etc) or ALL')
    parser.add_argument('--limit', type=int, default=5000, help='Max records per state')
    parser.add_argument('--threshold', type=float, default=85.0, help='Min match score (0-100)')
    parser.add_argument('--dry-run', action='store_true', help='Do not apply changes')
    parser.add_argument('--stats', action='store_true', help='Show stats only')
    args = parser.parse_args()
    
    print("="*70)
    print("DOL EIN MATCHER V3 - DATABASE CROSS-MATCH")
    print("="*70)
    print(f"Threshold: {args.threshold}%")
    print(f"Limit: {args.limit}")
    print(f"Dry run: {args.dry_run}")
    print()
    print("Method: Fuzzy match DOL names to company_master names")
    print("Cost: $0 (Tier 0 FREE)")
    
    if args.stats:
        conn = get_conn()
        cur = conn.cursor()
        
        # Get stats
        cur.execute("SELECT COUNT(*) FROM company.company_master WHERE ein IS NOT NULL")
        with_ein = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM company.company_master")
        total = cur.fetchone()[0]
        
        cur.execute("""
            SELECT COUNT(DISTINCT sponsor_dfe_ein) 
            FROM dol.form_5500 
            WHERE sponsor_dfe_ein NOT IN (
                SELECT ein FROM company.company_master WHERE ein IS NOT NULL
            )
        """)
        unmatched_dol = cur.fetchone()[0]
        
        print(f"\nCURRENT STATS:")
        print(f"  company_master total: {total:,}")
        print(f"  company_master with EIN: {with_ein:,} ({100*with_ein/total:.1f}%)")
        print(f"  DOL EINs not in company_master: {unmatched_dol:,}")
        
        cur.close()
        conn.close()
        return
    
    target_states = ['NC', 'PA', 'OH', 'VA', 'MD', 'KY', 'OK', 'WV', 'DE']
    
    if args.state == 'ALL':
        for state in target_states:
            process_state(state, args.limit, args.threshold, args.dry_run)
    elif args.state:
        process_state(args.state, args.limit, args.threshold, args.dry_run)
    else:
        print("\nUsage: --state NC (or ALL for all states)")
        print("       --stats to show current stats")


if __name__ == "__main__":
    main()
