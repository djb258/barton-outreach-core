#!/usr/bin/env python3
"""
Link DOL Filings to Company Master via EIN
============================================
Direct EIN join - no fuzzy matching. Fast and simple.

Usage:
    python scripts/link_dol_by_ein.py [--dry-run]
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import argparse

NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}


def link_dol_by_ein(dry_run=False):
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("LINK DOL FILINGS BY EIN")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    # Get target states from company_master
    cur.execute('''
        SELECT DISTINCT address_state
        FROM company.company_master
        WHERE address_state IS NOT NULL
    ''')
    target_states = [r['address_state'] for r in cur.fetchall()]
    print(f"Target states: {', '.join(sorted(target_states))}")
    print()

    # Count what we can link
    cur.execute('''
        SELECT COUNT(*) as linkable
        FROM dol.form_5500 d
        JOIN company.company_master cm ON d.sponsor_dfe_ein = cm.ein
        WHERE d.company_unique_id IS NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
    ''', (target_states,))
    linkable = cur.fetchone()['linkable']

    print(f"DOL filings ready to link: {linkable:,}")
    print()

    if linkable == 0:
        print("Nothing to link!")
        cur.close()
        conn.close()
        return

    # Show sample of what will be linked
    cur.execute('''
        SELECT
            d.sponsor_dfe_name,
            d.sponsor_dfe_ein,
            cm.company_name,
            cm.company_unique_id,
            d.tot_active_partcp_cnt
        FROM dol.form_5500 d
        JOIN company.company_master cm ON d.sponsor_dfe_ein = cm.ein
        WHERE d.company_unique_id IS NULL
          AND d.spons_dfe_mail_us_state = ANY(%s)
        ORDER BY d.tot_active_partcp_cnt DESC NULLS LAST
        LIMIT 10
    ''', (target_states,))

    print("Sample matches:")
    print("-" * 60)
    for row in cur.fetchall():
        dol_name = (row['sponsor_dfe_name'] or '')[:30]
        company_name = (row['company_name'] or '')[:30]
        print(f"  {row['sponsor_dfe_ein']}: {dol_name}")
        print(f"       -> {company_name}")
        print()

    if dry_run:
        print(f"[DRY RUN] Would link {linkable:,} filings")
    else:
        # Do the update
        cur.execute('''
            UPDATE dol.form_5500 d
            SET company_unique_id = cm.company_unique_id
            FROM company.company_master cm
            WHERE d.sponsor_dfe_ein = cm.ein
              AND d.company_unique_id IS NULL
              AND d.spons_dfe_mail_us_state = ANY(%s)
        ''', (target_states,))

        updated = cur.rowcount
        conn.commit()

        print(f"LINKED: {updated:,} DOL filings to company_master")

    cur.close()
    conn.close()

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Link DOL filings by EIN')
    parser.add_argument('--dry-run', action='store_true', help='Preview without updating')
    args = parser.parse_args()
    link_dol_by_ein(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
