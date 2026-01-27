#!/usr/bin/env python3
"""
PROMOTE DOL DATA TO OUTREACH VIA BRIDGE
========================================
Creates outreach.dol records for outreach_ids that can be linked
via the identity bridge to company_master → form_5500.

Path: outreach → bridge → company_master.ein → form_5500 → outreach.dol
"""

import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
import sys

DB_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}


def analyze_promotable(cur):
    """Count how many outreach_ids can be promoted."""
    cur.execute("""
        SELECT COUNT(DISTINCT o.outreach_id) as promotable
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
        WHERE d.dol_id IS NULL
          AND cm.ein IS NOT NULL
    """)
    return cur.fetchone()['promotable']


def promote_dol(cur, dry_run=False):
    """Promote DOL data to outreach.dol."""
    
    # Get promotable count
    promotable = analyze_promotable(cur)
    print(f"  Promotable outreach_ids: {promotable:,}")
    
    if promotable == 0:
        print("  Nothing to promote.")
        return 0
    
    # Show samples
    cur.execute("""
        SELECT 
            o.outreach_id,
            o.domain,
            cm.ein,
            f.sponsor_dfe_name,
            f.tot_active_partcp_cnt as participants
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN dol.form_5500 f ON cm.ein = f.sponsor_dfe_ein
        WHERE d.dol_id IS NULL
          AND cm.ein IS NOT NULL
        ORDER BY f.tot_active_partcp_cnt DESC NULLS LAST
        LIMIT 10
    """)
    
    print("\n  Sample (top 10 by participants):")
    for row in cur.fetchall():
        domain = (row['domain'] or 'NULL')[:35]
        print(f"    {domain:35} | EIN: {row['ein']} | {row['participants'] or 0:,} participants")
    
    if dry_run:
        print(f"\n  [DRY RUN] Would promote {promotable:,} outreach_ids")
        return promotable
    
    # Perform the promotion
    # Get the latest filing for each EIN (most recent form_year)
    cur.execute("""
        WITH latest_filing AS (
            SELECT DISTINCT ON (sponsor_dfe_ein)
                sponsor_dfe_ein,
                sponsor_dfe_name,
                tot_active_partcp_cnt,
                sch_a_attached_ind,
                form_year
            FROM dol.form_5500
            WHERE sponsor_dfe_ein IS NOT NULL
            ORDER BY sponsor_dfe_ein, form_year DESC NULLS LAST
        ),
        to_promote AS (
            SELECT DISTINCT ON (o.outreach_id)
                o.outreach_id,
                cm.ein,
                lf.sch_a_attached_ind
            FROM outreach.outreach o
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
            JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
            JOIN latest_filing lf ON cm.ein = lf.sponsor_dfe_ein
            WHERE d.dol_id IS NULL
              AND cm.ein IS NOT NULL
        )
        INSERT INTO outreach.dol (
            dol_id,
            outreach_id,
            ein,
            filing_present,
            created_at,
            updated_at
        )
        SELECT 
            gen_random_uuid(),
            outreach_id,
            ein,
            true,
            NOW(),
            NOW()
        FROM to_promote
        ON CONFLICT DO NOTHING
    """)
    
    promoted = cur.rowcount
    print(f"\n  ✅ Promoted {promoted:,} outreach_ids to outreach.dol")
    
    return promoted


def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='Promote DOL data to outreach via bridge')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 70)
    print("PROMOTE DOL DATA VIA BRIDGE")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 70)
    
    # Before counts
    cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol")
    before = cur.fetchone()['cnt']
    print(f"\nBEFORE: {before:,} records in outreach.dol")
    
    print("\n" + "=" * 70)
    print("PROMOTING DOL DATA")
    print("=" * 70)
    
    promoted = promote_dol(cur, args.dry_run)
    
    if not args.dry_run and promoted > 0:
        conn.commit()
        print("\n  ✅ All changes committed!")
    
    # After counts
    cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol")
    after = cur.fetchone()['cnt']
    print(f"\nAFTER: {after:,} records in outreach.dol")
    print(f"NEW: {after - before:,} records created")
    
    cur.close()
    conn.close()


if __name__ == '__main__':
    main()
