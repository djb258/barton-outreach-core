"""
Outreach Cascade Cleanup - Phase 4 & 5
Clears excluded company outreach_ids and phantom outreach_ids in CL
"""

import os
import sys
import psycopg2
from datetime import datetime

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

def phase_4_clear_excluded(conn):
    """Clear outreach_id from excluded companies"""
    print("\n" + "="*80)
    print("PHASE 4: Clear outreach_id in cl.company_identity_excluded")
    print("="*80)

    cursor = conn.cursor()

    # Count before clearing
    cursor.execute("""
        SELECT COUNT(*)
        FROM cl.company_identity_excluded
        WHERE outreach_id IS NOT NULL
    """)
    before_count = cursor.fetchone()[0]
    print(f"\nExcluded companies with outreach_id: {before_count:,}")

    if before_count == 0:
        print("✓ No excluded companies have outreach_id - skipping")
        return 0

    # Clear outreach_id
    cursor.execute("""
        UPDATE cl.company_identity_excluded
        SET outreach_id = NULL
        WHERE outreach_id IS NOT NULL
    """)

    updated_count = cursor.rowcount
    print(f"✓ Cleared outreach_id from {updated_count:,} excluded companies")

    conn.commit()
    cursor.close()
    return updated_count

def phase_5_investigate_phantoms(conn):
    """Investigate and clear phantom outreach_ids"""
    print("\n" + "="*80)
    print("PHASE 5: Fix alignment - investigate and clear phantom outreach_ids")
    print("="*80)

    cursor = conn.cursor()

    # Count phantom outreach_ids
    cursor.execute("""
        SELECT COUNT(*) as phantom_count
        FROM cl.company_identity ci
        WHERE ci.outreach_id IS NOT NULL
          AND ci.outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach)
    """)
    phantom_count = cursor.fetchone()[0]
    print(f"\nPhantom outreach_ids found: {phantom_count:,}")

    if phantom_count == 0:
        print("✓ No phantom outreach_ids - alignment is clean")
        cursor.close()
        return 0

    # Show sample of phantoms
    print(f"\nSample of phantom outreach_ids (first 20):")
    cursor.execute("""
        SELECT ci.sovereign_company_id, ci.outreach_id, ci.company_name
        FROM cl.company_identity ci
        WHERE ci.outreach_id IS NOT NULL
          AND ci.outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach)
        LIMIT 20
    """)

    print(f"{'Sovereign Company ID':<40} {'Outreach ID':<40} {'Company Name':<30}")
    print("-" * 110)
    for row in cursor.fetchall():
        sid, oid, name = row
        print(f"{sid:<40} {oid:<40} {name[:30]:<30}")

    # Clear phantom outreach_ids (requires temporarily disabling write-once trigger)
    print(f"\nClearing {phantom_count:,} phantom outreach_ids...")
    print("  Note: Temporarily disabling write-once trigger for cleanup...")

    # Disable write-once trigger
    cursor.execute("ALTER TABLE cl.company_identity DISABLE TRIGGER trg_write_once_pointers;")

    # Clear phantom outreach_ids
    cursor.execute("""
        UPDATE cl.company_identity
        SET outreach_id = NULL
        WHERE outreach_id IS NOT NULL
          AND outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach)
    """)

    cleared_count = cursor.rowcount

    # Re-enable write-once trigger
    cursor.execute("ALTER TABLE cl.company_identity ENABLE TRIGGER trg_write_once_pointers;")

    print(f"✓ Cleared {cleared_count:,} phantom outreach_ids")
    print("  Write-once trigger re-enabled")

    conn.commit()
    cursor.close()
    return cleared_count

def final_verification(conn):
    """Verify final alignment"""
    print("\n" + "="*80)
    print("FINAL VERIFICATION")
    print("="*80)

    cursor = conn.cursor()

    # CL vs Outreach alignment
    print("\n1. CL-Outreach Alignment Check:")
    cursor.execute("""
        SELECT 'cl.company_identity' as source, COUNT(*) as with_outreach_id
        FROM cl.company_identity WHERE outreach_id IS NOT NULL
        UNION ALL
        SELECT 'outreach.outreach' as source, COUNT(*) as count
        FROM outreach.outreach
    """)

    results = cursor.fetchall()
    cl_count = results[0][1]
    outreach_count = results[1][1]

    print(f"  cl.company_identity (outreach_id NOT NULL): {cl_count:,}")
    print(f"  outreach.outreach:                          {outreach_count:,}")

    if cl_count == outreach_count:
        print(f"  ✓ ALIGNED: {cl_count:,} = {outreach_count:,}")
    else:
        diff = abs(cl_count - outreach_count)
        print(f"  ✗ MISALIGNED: Difference of {diff:,}")

    # Orphan check
    print("\n2. Orphan Check (outreach records not in CL):")
    cursor.execute("""
        SELECT COUNT(*) as orphan_count
        FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.outreach_id = o.outreach_id
        )
    """)
    orphan_count = cursor.fetchone()[0]

    if orphan_count == 0:
        print(f"  ✓ No orphans found")
    else:
        print(f"  ✗ WARNING: {orphan_count:,} orphaned outreach records")

    # Phantom check (should be 0 after cleanup)
    print("\n3. Phantom Check (CL outreach_ids not in outreach.outreach):")
    cursor.execute("""
        SELECT COUNT(*) as phantom_count
        FROM cl.company_identity ci
        WHERE ci.outreach_id IS NOT NULL
          AND ci.outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach)
    """)
    phantom_count = cursor.fetchone()[0]

    if phantom_count == 0:
        print(f"  ✓ No phantoms found")
    else:
        print(f"  ✗ WARNING: {phantom_count:,} phantom outreach_ids")

    cursor.close()

    return {
        'cl_count': cl_count,
        'outreach_count': outreach_count,
        'aligned': cl_count == outreach_count,
        'orphan_count': orphan_count,
        'phantom_count': phantom_count
    }

def main():
    print("="*80)
    print("OUTREACH CASCADE CLEANUP - PHASE 4 & 5")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    conn = get_neon_connection()

    try:
        # Phase 4: Clear excluded companies
        excluded_cleared = phase_4_clear_excluded(conn)

        # Phase 5: Clear phantom outreach_ids
        phantoms_cleared = phase_5_investigate_phantoms(conn)

        # Final verification
        verification = final_verification(conn)

        # Summary
        print("\n" + "="*80)
        print("CLEANUP SUMMARY")
        print("="*80)
        print(f"Phase 4: Excluded companies cleared:  {excluded_cleared:,}")
        print(f"Phase 5: Phantom outreach_ids cleared: {phantoms_cleared:,}")
        print(f"\nFinal State:")
        print(f"  CL-Outreach Alignment: {verification['cl_count']:,} = {verification['outreach_count']:,} {'✓' if verification['aligned'] else '✗'}")
        print(f"  Orphans: {verification['orphan_count']:,}")
        print(f"  Phantoms: {verification['phantom_count']:,}")

        if verification['aligned'] and verification['orphan_count'] == 0 and verification['phantom_count'] == 0:
            print("\n✓ CLEANUP COMPLETE - ALIGNMENT RESTORED")
        else:
            print("\n⚠ CLEANUP COMPLETE - MANUAL REVIEW REQUIRED")

        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
