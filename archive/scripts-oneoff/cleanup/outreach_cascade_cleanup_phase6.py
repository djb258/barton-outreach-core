"""
Outreach Cascade Cleanup - Phase 6
Fix orphaned outreach records and restore alignment
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

def phase_6a_register_fixable_orphans(conn):
    """Register fixable orphans (valid SIDs) in CL"""
    print("\n" + "="*80)
    print("PHASE 6A: Register fixable orphans in CL")
    print("="*80)

    cursor = conn.cursor()

    # Count fixable orphans
    cursor.execute("""
        SELECT COUNT(*)
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON o.sovereign_id = ci.sovereign_company_id
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci2
            WHERE ci2.outreach_id = o.outreach_id
        )
    """)
    fixable_count = cursor.fetchone()[0]
    print(f"\nFixable orphans (valid SIDs in CL): {fixable_count:,}")

    if fixable_count == 0:
        print("  No fixable orphans - skipping")
        cursor.close()
        return 0

    # Disable write-once trigger
    print("  Temporarily disabling write-once trigger...")
    cursor.execute("ALTER TABLE cl.company_identity DISABLE TRIGGER trg_write_once_pointers;")

    # Register outreach_ids in CL
    print(f"  Registering {fixable_count:,} outreach_ids in CL...")
    cursor.execute("""
        UPDATE cl.company_identity ci
        SET outreach_id = o.outreach_id
        FROM outreach.outreach o
        WHERE o.sovereign_id = ci.sovereign_company_id
          AND ci.outreach_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM cl.company_identity ci2
              WHERE ci2.outreach_id = o.outreach_id
          )
    """)

    registered_count = cursor.rowcount

    # Re-enable write-once trigger
    cursor.execute("ALTER TABLE cl.company_identity ENABLE TRIGGER trg_write_once_pointers;")
    print("  Write-once trigger re-enabled")

    print(f"  Registered {registered_count:,} outreach_ids in CL")

    conn.commit()
    cursor.close()
    return registered_count

def phase_6b_archive_unfixable_orphans(conn):
    """Archive unfixable orphans (invalid SIDs)"""
    print("\n" + "="*80)
    print("PHASE 6B: Archive unfixable orphans")
    print("="*80)

    cursor = conn.cursor()

    # Count unfixable orphans
    cursor.execute("""
        SELECT COUNT(*)
        FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.outreach_id = o.outreach_id
        )
        AND NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci2
            WHERE ci2.sovereign_company_id = o.sovereign_id
        )
    """)
    unfixable_count = cursor.fetchone()[0]
    print(f"\nUnfixable orphans (invalid SIDs): {unfixable_count:,}")

    if unfixable_count == 0:
        print("  No unfixable orphans - skipping")
        cursor.close()
        return 0

    # Create archive table if needed (reuse existing from Phase 1)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS outreach.outreach_orphan_archive (
            outreach_id UUID PRIMARY KEY,
            sovereign_id UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            domain VARCHAR,
            archived_at TIMESTAMPTZ DEFAULT NOW(),
            archive_reason VARCHAR DEFAULT 'PHASE6_INVALID_SOVEREIGN_ID'
        )
    """)

    # Archive unfixable orphans
    print(f"  Archiving {unfixable_count:,} unfixable orphans...")
    cursor.execute("""
        INSERT INTO outreach.outreach_orphan_archive (outreach_id, sovereign_id, created_at, updated_at, domain)
        SELECT o.outreach_id, o.sovereign_id, o.created_at, o.updated_at, o.domain
        FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.outreach_id = o.outreach_id
        )
        AND NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci2
            WHERE ci2.sovereign_company_id = o.sovereign_id
        )
    """)

    archived_count = cursor.rowcount

    # Cascade cleanup - Delete from dependent tables first
    print(f"  Cascading cleanup to dependent tables...")

    # 1. Delete from people.company_slot
    cursor.execute("""
        DELETE FROM people.company_slot cs
        WHERE cs.outreach_id IN (
            SELECT o.outreach_id
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
        )
    """)
    slot_deleted = cursor.rowcount
    print(f"    people.company_slot: {slot_deleted:,} records deleted")

    # 2. Delete from outreach.company_target
    cursor.execute("""
        DELETE FROM outreach.company_target ct
        WHERE ct.outreach_id IN (
            SELECT o.outreach_id
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
        )
    """)
    ct_deleted = cursor.rowcount
    print(f"    outreach.company_target: {ct_deleted:,} records deleted")

    # 3. Delete from outreach.people
    cursor.execute("""
        DELETE FROM outreach.people p
        WHERE p.outreach_id IN (
            SELECT o.outreach_id
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
        )
    """)
    people_deleted = cursor.rowcount
    print(f"    outreach.people: {people_deleted:,} records deleted")

    # 4. Delete from outreach.blog
    cursor.execute("""
        DELETE FROM outreach.blog b
        WHERE b.outreach_id IN (
            SELECT o.outreach_id
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
        )
    """)
    blog_deleted = cursor.rowcount
    print(f"    outreach.blog: {blog_deleted:,} records deleted")

    # 5. Delete from outreach.bit_scores
    cursor.execute("""
        DELETE FROM outreach.bit_scores bs
        WHERE bs.outreach_id IN (
            SELECT o.outreach_id
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
        )
    """)
    bit_deleted = cursor.rowcount
    print(f"    outreach.bit_scores: {bit_deleted:,} records deleted")

    # 6. Delete from outreach.dol
    cursor.execute("""
        DELETE FROM outreach.dol d
        WHERE d.outreach_id IN (
            SELECT o.outreach_id
            FROM outreach.outreach o
            WHERE NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci
                WHERE ci.outreach_id = o.outreach_id
            )
            AND NOT EXISTS (
                SELECT 1 FROM cl.company_identity ci2
                WHERE ci2.sovereign_company_id = o.sovereign_id
            )
        )
    """)
    dol_deleted = cursor.rowcount
    print(f"    outreach.dol: {dol_deleted:,} records deleted")

    # 7. Finally, delete from outreach.outreach
    cursor.execute("""
        DELETE FROM outreach.outreach o
        WHERE NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci
            WHERE ci.outreach_id = o.outreach_id
        )
        AND NOT EXISTS (
            SELECT 1 FROM cl.company_identity ci2
            WHERE ci2.sovereign_company_id = o.sovereign_id
        )
    """)

    deleted_count = cursor.rowcount

    print(f"  Archived {archived_count:,} records to outreach.outreach_orphan_archive")
    print(f"  Deleted {deleted_count:,} unfixable orphans from outreach.outreach")
    print(f"  Total cascade deletions: {slot_deleted + ct_deleted + people_deleted + blog_deleted + bit_deleted + dol_deleted + deleted_count:,}")

    conn.commit()
    cursor.close()
    return deleted_count

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
        print(f"  ALIGNED: {cl_count:,} = {outreach_count:,}")
    else:
        diff = abs(cl_count - outreach_count)
        print(f"  MISALIGNED: Difference of {diff:,}")

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
        print(f"  No orphans found")
    else:
        print(f"  WARNING: {orphan_count:,} orphaned outreach records")

    # Phantom check
    print("\n3. Phantom Check (CL outreach_ids not in outreach.outreach):")
    cursor.execute("""
        SELECT COUNT(*) as phantom_count
        FROM cl.company_identity ci
        WHERE ci.outreach_id IS NOT NULL
          AND ci.outreach_id NOT IN (SELECT outreach_id FROM outreach.outreach)
    """)
    phantom_count = cursor.fetchone()[0]

    if phantom_count == 0:
        print(f"  No phantoms found")
    else:
        print(f"  WARNING: {phantom_count:,} phantom outreach_ids")

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
    print("OUTREACH CASCADE CLEANUP - PHASE 6")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    conn = get_neon_connection()

    try:
        # Phase 6A: Register fixable orphans
        registered = phase_6a_register_fixable_orphans(conn)

        # Phase 6B: Archive unfixable orphans
        archived = phase_6b_archive_unfixable_orphans(conn)

        # Final verification
        verification = final_verification(conn)

        # Summary
        print("\n" + "="*80)
        print("CLEANUP SUMMARY")
        print("="*80)
        print(f"Phase 6A: Fixable orphans registered:  {registered:,}")
        print(f"Phase 6B: Unfixable orphans archived:  {archived:,}")
        print(f"\nFinal State:")
        print(f"  CL-Outreach Alignment: {verification['cl_count']:,} = {verification['outreach_count']:,} {'[ALIGNED]' if verification['aligned'] else '[MISALIGNED]'}")
        print(f"  Orphans: {verification['orphan_count']:,}")
        print(f"  Phantoms: {verification['phantom_count']:,}")

        if verification['aligned'] and verification['orphan_count'] == 0 and verification['phantom_count'] == 0:
            print("\nCLEANUP COMPLETE - ALIGNMENT RESTORED")
        else:
            print("\nCLEANUP COMPLETE - MANUAL REVIEW REQUIRED")

        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)

    except Exception as e:
        print(f"\nERROR: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
