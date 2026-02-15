#!/usr/bin/env python3
"""
People Master Orphan Cleanup
============================
Archives and removes orphaned people.people_master records that have no
valid path to the outreach spine via people.company_slot.

Orphan Definition:
    A people_master record is orphaned if it has no matching entry in
    people.company_slot (via person_unique_id) that links to outreach.outreach.

Usage:
    doppler run -- python scripts/people_master_orphan_cleanup.py [--dry-run]
"""

import os
import sys
import psycopg2
from datetime import datetime

DRY_RUN = "--dry-run" in sys.argv

def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def run_cleanup():
    """Archive and delete orphaned people_master records."""
    conn = connect_db()
    cur = conn.cursor()

    print("=" * 80)
    print("PEOPLE MASTER ORPHAN CLEANUP")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Mode: {'DRY RUN' if DRY_RUN else 'LIVE EXECUTION'}")
    print("=" * 80)

    # Step 1: Count orphans
    print("\n[1] IDENTIFYING ORPHANS")
    print("-" * 40)

    cur.execute("SELECT COUNT(*) FROM people.people_master")
    total = cur.fetchone()[0]
    print(f"  Total people_master records: {total:,}")

    cur.execute("""
        SELECT COUNT(*) FROM people.people_master pm
        WHERE NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.person_unique_id = pm.unique_id
        )
    """)
    orphan_count = cur.fetchone()[0]
    print(f"  Orphaned records (no slot link): {orphan_count:,}")
    print(f"  Records to keep: {total - orphan_count:,}")

    if orphan_count == 0:
        print("\n  NO ORPHANS FOUND. Nothing to clean up.")
        conn.close()
        return

    # Step 2: Archive orphans
    print("\n[2] ARCHIVING ORPHANS")
    print("-" * 40)

    archive_sql = """
        INSERT INTO people.people_master_archive (
            unique_id, company_unique_id, company_slot_unique_id,
            first_name, last_name, full_name_stored, title, seniority, department,
            email, work_phone_e164, personal_phone_e164,
            linkedin_url, twitter_url, facebook_url, bio,
            skills, education, certifications,
            source_system, source_record_id,
            promoted_from_intake_at, promotion_audit_log_id,
            created_at, updated_at,
            email_verified, message_key_scheduled,
            email_verification_source, email_verified_at,
            validation_status_stored, last_verified_at, last_enrichment_attempt,
            archived_at, archive_reason
        )
        SELECT
            pm.unique_id, pm.company_unique_id, pm.company_slot_unique_id,
            pm.first_name, pm.last_name, pm.full_name, pm.title, pm.seniority, pm.department,
            pm.email, pm.work_phone_e164, pm.personal_phone_e164,
            pm.linkedin_url, pm.twitter_url, pm.facebook_url, pm.bio,
            array_to_string(pm.skills, ','), pm.education, array_to_string(pm.certifications, ','),
            pm.source_system, pm.source_record_id,
            pm.promoted_from_intake_at, pm.promotion_audit_log_id,
            pm.created_at, pm.updated_at,
            pm.email_verified, pm.message_key_scheduled,
            pm.email_verification_source, pm.email_verified_at,
            pm.validation_status, pm.last_verified_at, pm.last_enrichment_attempt,
            NOW(), 'orphan_cleanup_2026-01-22: no_slot_linkage'
        FROM people.people_master pm
        WHERE NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.person_unique_id = pm.unique_id
        )
    """

    if DRY_RUN:
        print("  [DRY RUN] Would archive orphaned records...")
        print(f"  [DRY RUN] Records to archive: {orphan_count:,}")
    else:
        cur.execute(archive_sql)
        archived = cur.rowcount
        print(f"  Archived: {archived:,} records")

    # Step 3: Delete orphans from source
    print("\n[3] DELETING FROM SOURCE")
    print("-" * 40)

    delete_sql = """
        DELETE FROM people.people_master pm
        WHERE NOT EXISTS (
            SELECT 1 FROM people.company_slot cs
            WHERE cs.person_unique_id = pm.unique_id
        )
    """

    if DRY_RUN:
        print("  [DRY RUN] Would delete orphaned records from people_master...")
        print(f"  [DRY RUN] Records to delete: {orphan_count:,}")
    else:
        cur.execute(delete_sql)
        deleted = cur.rowcount
        print(f"  Deleted: {deleted:,} records")

    # Step 4: Verify
    print("\n[4] POST-CLEANUP VERIFICATION")
    print("-" * 40)

    if not DRY_RUN:
        cur.execute("SELECT COUNT(*) FROM people.people_master")
        new_total = cur.fetchone()[0]
        print(f"  people_master count: {new_total:,}")

        cur.execute("SELECT COUNT(*) FROM people.people_master_archive")
        archive_total = cur.fetchone()[0]
        print(f"  people_master_archive count: {archive_total:,}")

        cur.execute("""
            SELECT COUNT(*) FROM people.people_master pm
            WHERE NOT EXISTS (
                SELECT 1 FROM people.company_slot cs
                WHERE cs.person_unique_id = pm.unique_id
            )
        """)
        remaining_orphans = cur.fetchone()[0]
        print(f"  Remaining orphans: {remaining_orphans:,}")

        if remaining_orphans == 0:
            print("\n  STATUS: CLEANUP SUCCESSFUL")
            conn.commit()
        else:
            print("\n  STATUS: CLEANUP INCOMPLETE - ROLLING BACK")
            conn.rollback()
    else:
        print("  [DRY RUN] Verification skipped")

    print("\n" + "=" * 80)
    if DRY_RUN:
        print("DRY RUN COMPLETE - No changes made")
        print("Run without --dry-run to execute cleanup")
    else:
        print("CLEANUP COMPLETE")
    print("=" * 80)

    conn.close()

if __name__ == "__main__":
    run_cleanup()
