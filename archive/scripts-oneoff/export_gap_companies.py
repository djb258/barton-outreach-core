#!/usr/bin/env python3
"""
Export Gap Companies
Generate CSV files for companies needing re-processing
"""

import os
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_neon_connection():
    """Get Neon PostgreSQL connection"""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def export_ct_blog_gaps(conn, output_dir):
    """Export companies missing Company Target and Blog"""
    print("\n[1] Exporting Company Target & Blog gaps...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                o.outreach_id,
                o.sovereign_id,
                o.domain,
                o.ein,
                o.created_at,
                o.updated_at
            FROM outreach.outreach o
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            WHERE ct.outreach_id IS NULL
            ORDER BY o.created_at DESC
        """)
        results = cur.fetchall()

    if not results:
        print("  No gaps found!")
        return

    filename = os.path.join(output_dir, f"ct_blog_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'outreach_id',
            'sovereign_id',
            'domain',
            'ein',
            'created_at',
            'updated_at'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"  Exported {len(results):,} companies to: {filename}")
    return filename

def export_people_slot_gaps(conn, output_dir):
    """Export companies missing People Slots"""
    print("\n[2] Exporting People Slot gaps...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                o.outreach_id,
                o.sovereign_id,
                o.domain,
                ct.email_method,
                ct.method_type,
                ct.confidence_score,
                ct.execution_status,
                o.created_at,
                o.updated_at
            FROM outreach.outreach o
            INNER JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            LEFT JOIN people.company_slot cs ON o.outreach_id = cs.outreach_id
            WHERE cs.outreach_id IS NULL
            ORDER BY o.created_at DESC
        """)
        results = cur.fetchall()

    if not results:
        print("  No gaps found!")
        return

    filename = os.path.join(output_dir, f"people_slot_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'outreach_id',
            'sovereign_id',
            'domain',
            'email_method',
            'method_type',
            'confidence_score',
            'execution_status',
            'created_at',
            'updated_at'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"  Exported {len(results):,} companies to: {filename}")
    return filename

def export_combined_report(conn, output_dir):
    """Export combined gap report"""
    print("\n[3] Generating combined gap report...")

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                o.outreach_id,
                o.sovereign_id,
                o.domain,
                CASE WHEN ct.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_ct,
                CASE WHEN b.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_blog,
                CASE WHEN cs.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_slots,
                CASE WHEN d.outreach_id IS NOT NULL THEN 'YES' ELSE 'NO' END as has_dol,
                o.created_at,
                o.updated_at
            FROM outreach.outreach o
            LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
            LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
            LEFT JOIN (SELECT DISTINCT outreach_id FROM people.company_slot) cs ON o.outreach_id = cs.outreach_id
            LEFT JOIN (SELECT DISTINCT outreach_id FROM outreach.dol) d ON o.outreach_id = d.outreach_id
            WHERE ct.outreach_id IS NULL
               OR cs.outreach_id IS NULL
            ORDER BY o.created_at DESC
        """)
        results = cur.fetchall()

    if not results:
        print("  No gaps found!")
        return

    filename = os.path.join(output_dir, f"combined_gap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'outreach_id',
            'sovereign_id',
            'domain',
            'has_ct',
            'has_blog',
            'has_slots',
            'has_dol',
            'created_at',
            'updated_at'
        ])
        writer.writeheader()
        writer.writerows(results)

    print(f"  Exported {len(results):,} companies to: {filename}")
    return filename

def main():
    print(f"\n{'='*80}")
    print(f"  EXPORT GAP COMPANIES")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print(f"{'='*80}")

    # Create output directory
    output_dir = os.path.join(
        os.path.dirname(__file__),
        'gap_exports'
    )
    os.makedirs(output_dir, exist_ok=True)

    conn = get_neon_connection()

    try:
        # Export each gap type
        ct_file = export_ct_blog_gaps(conn, output_dir)
        people_file = export_people_slot_gaps(conn, output_dir)
        combined_file = export_combined_report(conn, output_dir)

        print(f"\n{'='*80}")
        print("  EXPORT COMPLETE")
        print(f"{'='*80}")

        print("\nGenerated files:")
        if ct_file:
            print(f"  1. {ct_file}")
        if people_file:
            print(f"  2. {people_file}")
        if combined_file:
            print(f"  3. {combined_file}")

        print("\nNext steps:")
        print("  1. Review exported CSV files")
        print("  2. Re-run Company Target pipeline for CT gaps")
        print("  3. Re-run People Intelligence pipeline for Slot gaps")
        print("  4. Re-run audit to verify 100% coverage")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
