"""
Investigate orphaned outreach records (exist in outreach.outreach but not in CL)
"""

import os
import sys
import psycopg2

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_neon_connection():
    """Establish Neon database connection"""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=os.environ.get('NEON_PORT', '5432'),
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def investigate_orphans():
    """Investigate orphaned outreach records"""
    print("="*80)
    print("INVESTIGATING ORPHANED OUTREACH RECORDS")
    print("="*80)

    conn = get_neon_connection()
    cursor = conn.cursor()

    # Count orphans
    cursor.execute("""
        SELECT COUNT(*) as orphan_count
        FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.outreach_id = o.outreach_id
        )
    """)
    orphan_count = cursor.fetchone()[0]
    print(f"\nTotal orphaned outreach records: {orphan_count:,}")

    # Sample orphans
    print(f"\nSample orphaned records (first 20):")
    cursor.execute("""
        SELECT o.outreach_id, o.sovereign_id, o.created_at
        FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.outreach_id = o.outreach_id
        )
        LIMIT 20
    """)

    print(f"{'Outreach ID':<40} {'Sovereign ID':<40} {'Created At':<30}")
    print("-" * 110)
    for row in cursor.fetchall():
        oid, sid, created_at = row
        print(f"{oid:<40} {sid:<40} {str(created_at):<30}")

    # Check if sovereign_ids exist in CL
    print(f"\n\nChecking if sovereign_ids exist in cl.company_identity...")
    cursor.execute("""
        SELECT
            COUNT(*) as total_orphans,
            COUNT(CASE WHEN ci.sovereign_company_id IS NOT NULL THEN 1 END) as sid_exists_in_cl,
            COUNT(CASE WHEN ci.sovereign_company_id IS NULL THEN 1 END) as sid_not_in_cl
        FROM outreach.outreach o
        LEFT JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci2
            WHERE ci2.outreach_id = o.outreach_id
        )
    """)

    total, sid_exists, sid_not_exists = cursor.fetchone()
    print(f"  Total orphans: {total:,}")
    print(f"  Sovereign_id exists in CL: {sid_exists:,} ({sid_exists/total*100:.1f}%)")
    print(f"  Sovereign_id NOT in CL: {sid_not_exists:,} ({sid_not_exists/total*100:.1f}%)")

    # If SIDs exist in CL but outreach_id is not registered, we can fix this
    if sid_exists > 0:
        print(f"\n  -> FIXABLE: {sid_exists:,} orphans have valid SIDs in CL")
        print(f"     We can register their outreach_ids in CL")

    if sid_not_exists > 0:
        print(f"\n  -> UNFIXABLE: {sid_not_exists:,} orphans have invalid SIDs")
        print(f"     These should be archived")

    # Sample of fixable orphans
    if sid_exists > 0:
        print(f"\n\nSample FIXABLE orphans (SID exists in CL, outreach_id not registered):")
        cursor.execute("""
            SELECT
                o.outreach_id,
                o.sovereign_id,
                ci.company_name,
                ci.outreach_id as current_cl_outreach_id
            FROM outreach.outreach o
            JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.outreach_id = o.outreach_id
            )
            LIMIT 10
        """)

        print(f"{'Outreach ID':<40} {'Sovereign ID':<40} {'Company Name':<30} {'CL Outreach ID':<40}")
        print("-" * 150)
        for row in cursor.fetchall():
            oid, sid, name, cl_oid = row
            cl_oid_str = cl_oid if cl_oid else "NULL"
            print(f"{oid:<40} {sid:<40} {name[:30]:<30} {cl_oid_str:<40}")

    # Sample of unfixable orphans
    if sid_not_exists > 0:
        print(f"\n\nSample UNFIXABLE orphans (SID doesn't exist in CL):")
        cursor.execute("""
            SELECT o.outreach_id, o.sovereign_id, o.domain
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
            LIMIT 10
        """)

        print(f"{'Outreach ID':<40} {'Sovereign ID (INVALID)':<40} {'Domain':<30}")
        print("-" * 110)
        for row in cursor.fetchall():
            oid, sid, domain = row
            domain_str = domain if domain else ""
            print(f"{oid:<40} {sid:<40} {domain_str:<30}")

    cursor.close()
    conn.close()

    print("\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    investigate_orphans()
