#!/usr/bin/env python3
"""
Outreach Sub-Hub Alignment Audit v2
===================================
Fixed version with proper type handling.

Usage:
    doppler run -- python scripts/outreach_alignment_audit_v2.py
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
    conn.autocommit = True  # Prevent transaction issues
    cur = conn.cursor()

    print("=" * 80)
    print("OUTREACH SUB-HUB ALIGNMENT AUDIT v2")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    # 1. Get CL authority count
    print("\n[1] CL AUTHORITY COUNT")
    print("-" * 40)

    cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE identity_status = 'PASS') as pass_count,
            COUNT(*) FILTER (WHERE identity_status = 'FAIL') as fail_count
        FROM cl.company_identity
    """)
    cl_stats = cur.fetchone()
    print(f"  Total:  {cl_stats[0]:,}")
    print(f"  PASS:   {cl_stats[1]:,}")
    print(f"  FAIL:   {cl_stats[2]:,}")

    authority_count = cl_stats[1]  # PASS count is authority
    print(f"\n  AUTHORITY COUNT (PASS): {authority_count:,}")

    # 2. Audit Outreach spine
    print("\n[2] OUTREACH SPINE")
    print("-" * 40)

    cur.execute("SELECT COUNT(*) FROM outreach.outreach")
    outreach_count = cur.fetchone()[0]
    print(f"  outreach.outreach: {outreach_count:,} rows")

    # Check alignment
    cur.execute("""
        SELECT COUNT(*) FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.company_unique_id = o.sovereign_id
            AND ci.identity_status = 'PASS'
        )
    """)
    orphan_count = cur.fetchone()[0]
    print(f"  Orphaned: {orphan_count:,}")
    print(f"  Status: {'ALIGNED' if orphan_count == 0 else 'NEEDS CLEANUP'}")

    # 3. Audit each table individually
    print("\n[3] TABLE-BY-TABLE AUDIT")
    print("-" * 80)
    print(f"  {'Table':<45} {'Count':>12} {'Orphans':>12} {'Status':>10}")
    print("-" * 80)

    results = []

    # Tables with outreach_id FK
    outreach_id_tables = [
        "outreach.company_target",
        "outreach.company_target_errors",
        "outreach.dol",
        "outreach.dol_errors",
        "outreach.people",
        "outreach.people_errors",
        "outreach.blog",
        "outreach.blog_errors",
        "outreach.bit_scores",
        "outreach.bit_signals",
        "outreach.bit_input_history",
        "outreach.blog_source_history",
    ]

    for table in outreach_id_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            current = cur.fetchone()[0]

            cur.execute(f"""
                SELECT COUNT(*) FROM {table} t
                WHERE NOT EXISTS (
                    SELECT 1 FROM outreach.outreach o
                    WHERE o.outreach_id = t.outreach_id
                )
            """)
            orphans = cur.fetchone()[0]

            status = "OK" if orphans == 0 else "CLEANUP"
            print(f"  {table:<45} {current:>12,} {orphans:>12,} {status:>10}")
            results.append({'table': table, 'count': current, 'orphans': orphans})
        except Exception as e:
            print(f"  {table:<45} {'ERROR':<12} {str(e)[:30]}")

    # People schema tables
    print("\n  People Schema:")
    print("-" * 80)

    # people.company_slot
    try:
        cur.execute("SELECT COUNT(*) FROM people.company_slot")
        cs_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM people.company_slot cs
            WHERE NOT EXISTS (
                SELECT 1 FROM outreach.outreach o
                WHERE o.outreach_id = cs.outreach_id
            )
        """)
        cs_orphans = cur.fetchone()[0]

        print(f"  {'people.company_slot':<45} {cs_count:>12,} {cs_orphans:>12,} {'OK' if cs_orphans == 0 else 'CLEANUP':>10}")
        results.append({'table': 'people.company_slot', 'count': cs_count, 'orphans': cs_orphans})
    except Exception as e:
        print(f"  {'people.company_slot':<45} ERROR: {e}")

    # people.people_master - uses company_unique_id
    try:
        cur.execute("SELECT COUNT(*) FROM people.people_master")
        pm_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM people.people_master pm
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.company_unique_id = pm.company_unique_id
                AND ci.identity_status = 'PASS'
            )
        """)
        pm_orphans = cur.fetchone()[0]

        print(f"  {'people.people_master':<45} {pm_count:>12,} {pm_orphans:>12,} {'OK' if pm_orphans == 0 else 'CLEANUP':>10}")
        results.append({'table': 'people.people_master', 'count': pm_count, 'orphans': pm_orphans})
    except Exception as e:
        print(f"  {'people.people_master':<45} ERROR: {e}")

    # company_hub_status - uses company_unique_id as TEXT
    try:
        cur.execute("SELECT COUNT(*) FROM outreach.company_hub_status")
        chs_count = cur.fetchone()[0]

        cur.execute("""
            SELECT COUNT(*) FROM outreach.company_hub_status chs
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.company_unique_id = chs.company_unique_id::text
                AND ci.identity_status = 'PASS'
            )
        """)
        chs_orphans = cur.fetchone()[0]

        print(f"  {'outreach.company_hub_status':<45} {chs_count:>12,} {chs_orphans:>12,} {'OK' if chs_orphans == 0 else 'CLEANUP':>10}")
        results.append({'table': 'outreach.company_hub_status', 'count': chs_count, 'orphans': chs_orphans})
    except Exception as e:
        print(f"  {'outreach.company_hub_status':<45} ERROR: {e}")

    # 4. Archive tables
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
            print(f"  {table:<45} {count:>12,} rows (archived)")
        except Exception as e:
            print(f"  {table:<45} (not found)")

    # 5. Summary
    print("\n" + "=" * 80)
    print("ALIGNMENT SUMMARY")
    print("=" * 80)

    total_orphans = sum(r.get('orphans', 0) for r in results)
    total_rows = sum(r.get('count', 0) for r in results)

    print(f"\n  CL Authority (PASS):     {authority_count:,}")
    print(f"  Outreach Spine:          {outreach_count:,}")
    print(f"  Spine delta:             {outreach_count - authority_count:+,}")
    print(f"  Total orphans detected:  {total_orphans:,}")
    print(f"  Total rows audited:      {total_rows:,}")

    if outreach_count == authority_count and total_orphans == 0:
        print("\n  " + "=" * 60)
        print("  STATUS: ALIGNED")
        print("  Safe for paid enrichment: YES")
        print("  " + "=" * 60)
    else:
        print("\n  " + "=" * 60)
        print("  STATUS: NEEDS CLEANUP")
        print(f"  Rows to remove: {total_orphans:,}")
        print("  Safe for paid enrichment: NO")
        print("  " + "=" * 60)

    conn.close()
    return authority_count, outreach_count, total_orphans, results

if __name__ == "__main__":
    run_audit()
