#!/usr/bin/env python3
"""
ENHANCED PROMOTE DOL DATA - Uses ALL 5500 sources
==================================================
Creates outreach.dol records using BOTH:
  - form_5500 (regular filings)
  - form_5500_sf (SHORT FORM - 760k filings!)
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


def main():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    parser = argparse.ArgumentParser(description='Enhanced DOL promoter - uses ALL 5500 sources')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    args = parser.parse_args()
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 70)
    print("ENHANCED DOL PROMOTER - ALL 5500 SOURCES")
    print(f"Run at: {datetime.now(timezone.utc).isoformat()}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print("=" * 70)
    
    # Before count
    cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol")
    before = cur.fetchone()['cnt']
    print(f"\nBEFORE: {before:,} records in outreach.dol")
    
    # Analyze promotable - using BOTH tables
    print("\n" + "=" * 70)
    print("ANALYZING PROMOTABLE RECORDS")
    print("=" * 70)
    
    cur.execute("""
        WITH all_5500_eins AS (
            SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
            UNION
            SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
        )
        SELECT COUNT(DISTINCT o.outreach_id) as promotable
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN all_5500_eins ae ON cm.ein = ae.ein
        WHERE d.dol_id IS NULL
          AND cm.ein IS NOT NULL
    """)
    promotable = cur.fetchone()['promotable']
    print(f"\n  Promotable outreach_ids: {promotable:,}")
    
    if promotable == 0:
        print("  Nothing to promote.")
        conn.close()
        return
    
    # Show sample
    cur.execute("""
        WITH all_5500_eins AS (
            SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
            UNION
            SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
        )
        SELECT 
            o.outreach_id,
            o.domain,
            cm.ein,
            cm.company_name
        FROM outreach.outreach o
        LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
        JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
        JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
        JOIN all_5500_eins ae ON cm.ein = ae.ein
        WHERE d.dol_id IS NULL
          AND cm.ein IS NOT NULL
        LIMIT 15
    """)
    
    print("\n  Sample records:")
    for row in cur.fetchall():
        domain = (row['domain'] or 'NULL')[:25]
        name = (row['company_name'] or '')[:30]
        print(f"    {domain:25} | {name:30} | EIN: {row['ein']}")
    
    if args.dry_run:
        print(f"\n  [DRY RUN] Would promote {promotable:,} outreach_ids")
        conn.close()
        return
    
    # Promote!
    print("\n  Promoting...")
    
    cur.execute("""
        WITH all_5500_eins AS (
            SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500 WHERE sponsor_dfe_ein IS NOT NULL
            UNION
            SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf WHERE sf_spons_ein IS NOT NULL
        ),
        to_promote AS (
            SELECT DISTINCT ON (o.outreach_id)
                o.outreach_id,
                cm.ein
            FROM outreach.outreach o
            LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
            JOIN cl.company_identity_bridge b ON o.sovereign_id = b.company_sov_id
            JOIN company.company_master cm ON b.source_company_id = cm.company_unique_id
            JOIN all_5500_eins ae ON cm.ein = ae.ein
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
    print(f"  ✅ Promoted {promoted:,} outreach_ids to outreach.dol")
    
    conn.commit()
    print("  ✅ Changes committed!")
    
    # After count
    cur.execute("SELECT COUNT(*) as cnt FROM outreach.dol")
    after = cur.fetchone()['cnt']
    print(f"\nAFTER: {after:,} records in outreach.dol")
    print(f"NEW: {after - before:,} records created")
    
    conn.close()


if __name__ == '__main__':
    main()
