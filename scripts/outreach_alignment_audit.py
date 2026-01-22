#!/usr/bin/env python3
"""
Outreach Sub-Hub Alignment Audit
================================
Audits all Outreach-owned tables against CL authority count.
This is a READ-ONLY diagnostic - no changes made.

Usage:
    doppler run -- python scripts/outreach_alignment_audit.py
"""

import os
import psycopg2
from datetime import datetime

def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def run_audit():
    """Run comprehensive alignment audit."""
    conn = connect_db()
    cur = conn.cursor()

    print("=" * 80)
    print("OUTREACH SUB-HUB ALIGNMENT AUDIT")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. Get CL authority count
    print("\n[1] CL AUTHORITY COUNT")
    print("-" * 40)

    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE identity_status = 'PASS') as pass_count,
            COUNT(*) FILTER (WHERE identity_status = 'FAIL') as fail_count,
            COUNT(*) FILTER (WHERE outreach_id IS NOT NULL) as outreach_claimed
        FROM cl.company_identity
    """)
    cl_stats = cur.fetchone()
    print(f"  Total:            {cl_stats[0]:,}")
    print(f"  PASS:             {cl_stats[1]:,}")
    print(f"  FAIL:             {cl_stats[2]:,}")
    print(f"  Outreach claimed: {cl_stats[3]:,}")

    authority_count = cl_stats[1]  # PASS count is authority
    print(f"\n  AUTHORITY COUNT (PASS): {authority_count:,}")

    # 2. Audit Outreach spine
    print("\n[2] OUTREACH SPINE (outreach.outreach)")
    print("-" * 40)

    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    outreach_count = cur.fetchone()[0]
    print(f"  Current count: {outreach_count:,}")

    # Check for orphans (not in CL PASS)
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.company_unique_id = o.sovereign_id
            AND ci.identity_status = 'PASS'
        )
    """)
    orphan_count = cur.fetchone()[0]
    print(f"  Orphaned (not in CL PASS): {orphan_count:,}")
    print(f"  Delta from authority: {outreach_count - authority_count:+,}")

    # 3. Audit all Outreach sub-hub tables
    print("\n[3] OUTREACH SUB-HUB TABLES")
    print("-" * 40)

    tables = [
        ("outreach.company_target", "outreach_id"),
        ("outreach.company_target_errors", "outreach_id"),
        ("outreach.dol", "outreach_id"),
        ("outreach.dol_errors", "outreach_id"),
        ("outreach.people", "outreach_id"),
        ("outreach.people_errors", "outreach_id"),
        ("outreach.blog", "outreach_id"),
        ("outreach.blog_errors", "outreach_id"),
        ("outreach.bit_scores", "outreach_id"),
        ("outreach.bit_signals", "outreach_id"),
        ("outreach.bit_input_history", "outreach_id"),
        ("outreach.blog_source_history", "outreach_id"),
        ("outreach.engagement_events", "outreach_id"),
        ("outreach.send_log", "target_id"),
        ("outreach.company_hub_status", "company_unique_id"),
        ("people.company_slot", "outreach_id"),
        ("people.people_master", "company_unique_id"),
        ("people.people_resolution_history", "outreach_id"),
    ]

    results = []

    for table, join_col in tables:
        try:
            # Get current count
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            current = cur.fetchone()[0]

            # Check for orphans based on join column
            if join_col == "outreach_id":
                cur.execute(f"""
                    SELECT COUNT(*) FROM {table} t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM outreach.outreach o
                        WHERE o.outreach_id = t.outreach_id
                    )
                """)
            elif join_col == "company_unique_id":
                cur.execute(f"""
                    SELECT COUNT(*) FROM {table} t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM cl.company_identity ci
                        WHERE ci.company_unique_id = t.company_unique_id
                        AND ci.identity_status = 'PASS'
                    )
                """)
            elif join_col == "target_id":
                cur.execute(f"""
                    SELECT COUNT(*) FROM {table} t
                    WHERE NOT EXISTS (
                        SELECT 1 FROM outreach.company_target ct
                        WHERE ct.target_id = t.target_id
                    )
                """)
            else:
                orphans = 0

            orphans = cur.fetchone()[0]

            results.append({
                'table': table,
                'current': current,
                'orphans': orphans,
                'clean': current - orphans
            })

            status = "OK" if orphans == 0 else f"NEEDS CLEANUP ({orphans:,} orphans)"
            print(f"  {table:45} {current:>10,} rows  {status}")

        except Exception as e:
            print(f"  {table:45} ERROR: {str(e)[:30]}")
            results.append({
                'table': table,
                'current': 0,
                'orphans': 0,
                'clean': 0,
                'error': str(e)
            })

    # 4. Check archive tables
    print("\n[4] ARCHIVE TABLES")
    print("-" * 40)

    archive_tables = [
        "outreach.outreach_archive",
        "outreach.company_target_archive",
        "outreach.people_archive",
        "people.company_slot_archive",
        "people.people_master_archive",
    ]

    for table in archive_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {table:45} {count:>10,} rows")
        except Exception as e:
            print(f"  {table:45} NOT FOUND or ERROR")

    # 5. Summary
    print("\n" + "=" * 80)
    print("ALIGNMENT SUMMARY")
    print("=" * 80)

    total_orphans = sum(r['orphans'] for r in results if 'error' not in r)

    print(f"\n  CL Authority (PASS):     {authority_count:,}")
    print(f"  Outreach Spine:          {outreach_count:,}")
    print(f"  Spine orphans:           {orphan_count:,}")
    print(f"  Total orphans detected:  {total_orphans:,}")

    if outreach_count == authority_count and total_orphans == 0:
        print("\n  STATUS: ALIGNED - Safe for paid enrichment")
    else:
        print("\n  STATUS: NEEDS CLEANUP")
        print(f"  Estimated rows to remove: {total_orphans:,}")
        print(f"  Spine delta: {outreach_count - authority_count:+,}")

    print("\n" + "=" * 80)

    conn.close()
    return authority_count, results

if __name__ == "__main__":
    run_audit()
