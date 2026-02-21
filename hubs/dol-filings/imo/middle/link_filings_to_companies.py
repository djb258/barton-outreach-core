#!/usr/bin/env python3
"""
Link DOL Filings to Companies by EIN
=====================================
Populates company_unique_id on dol.form_5500 where EIN matches company_master.

DOCTRINE: Exact EIN match only (ADR-DOL-001). No fuzzy. Fail closed.

Usage:
    python link_filings_to_companies.py [--dry-run]

Examples:
    # Preview what would be linked
    python link_filings_to_companies.py --dry-run

    # Execute the linking
    python link_filings_to_companies.py
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import argparse
from datetime import datetime, timezone

# Neon connection (via Doppler env vars)
NEON_CONFIG = {
    'host': os.environ['NEON_HOST'],
    'port': 5432,
    'database': os.environ['NEON_DATABASE'],
    'user': os.environ['NEON_USER'],
    'password': os.environ['NEON_PASSWORD'],
    'sslmode': 'require'
}


def link_filings_to_companies(dry_run=False):
    """
    Link DOL Form 5500 filings to company_master by exact EIN match.

    DOCTRINE: Exact match only. No similarity/fuzzy matching.
    Only links filings in states where we have company_master coverage.
    """
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print('=' * 70)
    print('LINK DOL FILINGS TO COMPANIES')
    print('=' * 70)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Doctrine: Exact EIN match only (ADR-DOL-001)")
    print()

    # Step 1: Get target states from company_master
    cur.execute('''
        SELECT DISTINCT address_state
        FROM company.company_master
        WHERE address_state IS NOT NULL
    ''')
    target_states = [r['address_state'] for r in cur.fetchall()]
    print(f"Target states: {', '.join(sorted(target_states))}")
    print()

    # Step 2: Current state
    cur.execute('''
        SELECT
            COUNT(*) as total,
            COUNT(company_unique_id) as linked
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = ANY(%s)
    ''', (target_states,))
    before = cur.fetchone()
    print(f"BEFORE:")
    print(f"  Total filings (target states): {before['total']:,}")
    print(f"  Already linked: {before['linked']:,}")
    print(f"  Unlinked: {before['total'] - before['linked']:,}")
    print()

    # Step 3: Find linkable filings (exact EIN match)
    cur.execute('''
        SELECT COUNT(*) as linkable
        FROM dol.form_5500 d
        JOIN company.company_master cm
            ON d.sponsor_dfe_ein = cm.ein
        WHERE d.company_unique_id IS NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
          AND cm.ein IS NOT NULL
    ''', (target_states,))
    linkable = cur.fetchone()['linkable']
    print(f"Filings ready to link (exact EIN match): {linkable:,}")
    print()

    if linkable == 0:
        print("Nothing to link. Exiting.")
        cur.close()
        conn.close()
        return {'linked': 0, 'already_linked': before['linked']}

    # Step 4: Show sample matches
    cur.execute('''
        SELECT
            d.sponsor_dfe_ein as ein,
            d.sponsor_dfe_name as dol_name,
            cm.company_name,
            cm.company_unique_id,
            d.tot_active_partcp_cnt as participants,
            d.spons_dfe_mail_us_state as state
        FROM dol.form_5500 d
        JOIN company.company_master cm
            ON d.sponsor_dfe_ein = cm.ein
        WHERE d.company_unique_id IS NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
          AND cm.ein IS NOT NULL
        ORDER BY d.tot_active_partcp_cnt DESC NULLS LAST
        LIMIT 10
    ''', (target_states,))

    samples = cur.fetchall()
    print("SAMPLE MATCHES (top 10 by participants):")
    print("-" * 70)
    for row in samples:
        print(f"  EIN: {row['ein']} | {row['state']}")
        print(f"    DOL: {row['dol_name'][:50]}")
        print(f"    CM:  {row['company_name'][:50]}")
        print(f"    Participants: {row['participants'] or 0:,}")
        print()

    # Step 5: By-state breakdown
    cur.execute('''
        SELECT
            d.spons_dfe_mail_us_state as state,
            COUNT(*) as linkable_count
        FROM dol.form_5500 d
        JOIN company.company_master cm
            ON d.sponsor_dfe_ein = cm.ein
        WHERE d.company_unique_id IS NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
          AND cm.ein IS NOT NULL
        GROUP BY d.spons_dfe_mail_us_state
        ORDER BY linkable_count DESC
    ''', (target_states,))

    print("LINKABLE BY STATE:")
    print("-" * 30)
    for row in cur.fetchall():
        print(f"  {row['state']}: {row['linkable_count']:,}")
    print()

    # Step 6: Execute or preview
    if dry_run:
        print(f"[DRY RUN] Would link {linkable:,} filings")
    else:
        print("LINKING...")
        # Enable import mode to bypass read-only guard
        cur.execute("SET session dol.import_mode = 'active'")

        cur.execute('''
            UPDATE dol.form_5500 d
            SET company_unique_id = cm.company_unique_id,
                updated_at = %s
            FROM company.company_master cm
            WHERE d.sponsor_dfe_ein = cm.ein
              AND d.company_unique_id IS NULL
              AND d.spons_dfe_mail_us_state = ANY(%s)
              AND cm.ein IS NOT NULL
        ''', (datetime.now(timezone.utc), target_states))

        linked = cur.rowcount
        conn.commit()
        print(f"LINKED: {linked:,} filings")

    # Step 7: Final counts
    cur.execute('''
        SELECT
            COUNT(*) as total,
            COUNT(company_unique_id) as linked
        FROM dol.form_5500
        WHERE spons_dfe_mail_us_state = ANY(%s)
    ''', (target_states,))
    after = cur.fetchone()

    print()
    print('=' * 70)
    print('RESULTS')
    print('=' * 70)
    print(f"BEFORE: {before['linked']:,} linked")
    print(f"AFTER:  {after['linked']:,} linked")
    print(f"NEW:    {after['linked'] - before['linked']:,} filings linked")
    print()

    match_rate = 100 * after['linked'] / after['total'] if after['total'] > 0 else 0
    print(f"Match Rate: {match_rate:.1f}% of filings in target states")

    if dry_run:
        print()
        print("[DRY RUN - No changes made]")

    cur.close()
    conn.close()

    return {
        'linked': after['linked'] - before['linked'] if not dry_run else 0,
        'total_linked': after['linked'],
        'match_rate': match_rate
    }


def main():
    parser = argparse.ArgumentParser(description='Link DOL filings to companies by EIN')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating')
    args = parser.parse_args()

    link_filings_to_companies(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
