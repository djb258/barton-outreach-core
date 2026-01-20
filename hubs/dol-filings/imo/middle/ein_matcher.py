#!/usr/bin/env python3
"""
DOL EIN Backfill Script
========================
Matches companies in company.company_master to DOL Form 5500 data
and backfills the EIN (Employer Identification Number).

Matching Strategy (State → City → Name):
1. State: Exact match on address_state = mail_state
2. City: Exact match (case-insensitive)
3. Name: Trigram similarity > 0.8 for high confidence

Usage:
    python backfill_ein_from_dol.py [--dry-run] [--threshold 0.8] [--limit 100]

Examples:
    # Dry run - see what would be updated
    python backfill_ein_from_dol.py --dry-run

    # Backfill with default threshold (0.8)
    python backfill_ein_from_dol.py

    # Backfill with custom threshold
    python backfill_ein_from_dol.py --threshold 0.9
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import argparse
from datetime import datetime, timezone

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}


def backfill_ein(dry_run=False, threshold=0.8, limit=None, state=None):
    """
    Backfill EIN from DOL Form 5500 data to company.company_master.

    Args:
        dry_run: If True, don't make any changes
        threshold: Minimum trigram similarity threshold (0.0-1.0)
        limit: Optional limit on records to process
        state: Optional state filter (e.g., 'NC', 'PA')
    """
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 70)
    print('DOL EIN BACKFILL')
    print('=' * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Similarity threshold: {threshold}")
    print(f"Limit: {limit or 'None'}")
    print(f"State filter: {state or 'All states'}")
    print()

    # Step 1: Check current EIN status
    cur.execute('SELECT COUNT(*) as total FROM company.company_master')
    total = cur.fetchone()['total']

    cur.execute('SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL')
    with_ein = cur.fetchone()['with_ein']

    cur.execute('SELECT COUNT(*) as without_ein FROM company.company_master WHERE ein IS NULL')
    without_ein = cur.fetchone()['without_ein']

    print(f"BEFORE:")
    print(f"  Total companies: {total:,}")
    print(f"  With EIN: {with_ein:,}")
    print(f"  Without EIN: {without_ein:,}")
    print()

    # Step 2: Find matches
    print("Finding matches (State → City → Name)...")

    limit_clause = f"LIMIT {limit}" if limit else ""
    state_clause = "AND cm.address_state = %s" if state else ""
    params = [threshold, state] if state else [threshold]

    cur.execute(f'''
        WITH ranked_matches AS (
            SELECT
                cm.company_unique_id,
                cm.company_name,
                cm.address_city,
                cm.address_state,
                d.sponsor_dfe_ein as dol_ein,
                d.sponsor_dfe_name as dol_name,
                SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) as similarity,
                ROW_NUMBER() OVER (
                    PARTITION BY cm.company_unique_id
                    ORDER BY SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) DESC
                ) as rn
            FROM company.company_master cm
            JOIN dol.form_5500 d
                ON cm.address_state = d.spons_dfe_mail_us_state
                AND LOWER(TRIM(cm.address_city)) = LOWER(TRIM(d.spons_dfe_mail_us_city))
            WHERE cm.ein IS NULL
              AND d.sponsor_dfe_ein IS NOT NULL
              AND SIMILARITY(LOWER(cm.company_name), LOWER(d.sponsor_dfe_name)) > %s
              {state_clause}
        )
        SELECT * FROM ranked_matches WHERE rn = 1
        ORDER BY similarity DESC
        {limit_clause}
    ''', params)

    matches = cur.fetchall()

    print(f"Found {len(matches):,} matches")
    print()

    # Step 3: Show sample matches
    print("SAMPLE MATCHES:")
    print("-" * 70)
    for match in matches[:10]:
        print(f"  [{match['similarity']:.2f}] {match['company_name'][:40]}")
        print(f"         → DOL: {match['dol_name'][:40]}")
        print(f"         {match['address_city']}, {match['address_state']} | EIN: {match['dol_ein']}")
        print()

    if len(matches) > 10:
        print(f"  ... and {len(matches) - 10:,} more")
    print()

    # Step 4: Similarity distribution
    print("SIMILARITY DISTRIBUTION:")
    print("-" * 70)
    brackets = [
        (0.95, 1.01, "0.95-1.00 (Excellent)"),
        (0.90, 0.95, "0.90-0.95 (Very High)"),
        (0.85, 0.90, "0.85-0.90 (High)"),
        (0.80, 0.85, "0.80-0.85 (Good)"),
        (threshold, 0.80, f"{threshold}-0.80 (Threshold)")
    ]

    for low, high, label in brackets:
        count = sum(1 for m in matches if low <= m['similarity'] < high)
        if count > 0:
            print(f"  {label}: {count:,}")
    print()

    # Step 5: Update records
    if not dry_run and matches:
        print("UPDATING RECORDS...")
        print("-" * 70)

        updated = 0
        for match in matches:
            cur.execute('''
                UPDATE company.company_master
                SET ein = %s,
                    updated_at = %s
                WHERE company_unique_id = %s
                  AND ein IS NULL
            ''', (
                match['dol_ein'],
                datetime.now(timezone.utc),
                match['company_unique_id']
            ))
            updated += cur.rowcount

            if updated % 500 == 0:
                conn.commit()
                print(f"  Updated {updated:,} records...")

        conn.commit()
        print(f"  Total updated: {updated:,}")
        print()
    else:
        updated = 0
        if dry_run:
            print(f"[DRY RUN] Would update {len(matches):,} records")
            print()

    # Step 6: Final count
    cur.execute('SELECT COUNT(*) as with_ein FROM company.company_master WHERE ein IS NOT NULL')
    after_ein = cur.fetchone()['with_ein']

    print('=' * 70)
    print('FINAL RESULTS')
    print('=' * 70)
    print(f"BEFORE: {with_ein:,} companies with EIN")
    print(f"AFTER: {after_ein:,} companies with EIN")
    print(f"NEW: {after_ein - with_ein:,} EINs backfilled")

    if dry_run:
        print()
        print("[DRY RUN - No changes made]")

    # Step 7: By state breakdown
    print()
    print("EIN COVERAGE BY STATE (after):")
    cur.execute('''
        SELECT
            address_state,
            COUNT(*) as total,
            COUNT(ein) as with_ein,
            ROUND(100.0 * COUNT(ein) / COUNT(*), 1) as pct
        FROM company.company_master
        GROUP BY address_state
        ORDER BY total DESC
    ''')
    for row in cur.fetchall():
        print(f"  {row['address_state']}: {row['with_ein']:,}/{row['total']:,} ({row['pct']}%)")

    cur.close()
    conn.close()

    return {
        'matches_found': len(matches),
        'updated': updated if not dry_run else 0,
        'before_ein': with_ein,
        'after_ein': after_ein
    }


def main():
    parser = argparse.ArgumentParser(description='Backfill EIN from DOL Form 5500 data')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without updating')
    parser.add_argument('--threshold', type=float, default=0.8, help='Minimum similarity threshold (default: 0.8)')
    parser.add_argument('--limit', type=int, help='Limit number of records to process')
    parser.add_argument('--state', type=str, help='Filter by state (e.g., NC, PA)')

    args = parser.parse_args()

    if args.threshold < 0.5 or args.threshold > 1.0:
        print("Error: Threshold must be between 0.5 and 1.0")
        sys.exit(1)

    backfill_ein(
        dry_run=args.dry_run,
        threshold=args.threshold,
        limit=args.limit,
        state=args.state.upper() if args.state else None
    )


if __name__ == '__main__':
    main()
