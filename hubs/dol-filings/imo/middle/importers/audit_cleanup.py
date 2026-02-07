#!/usr/bin/env python3
"""
Audit Cleanup Script
====================
Fixes 8 data quality issues identified in the full numbers audit.
Run with: doppler run -- python hubs/dol-filings/imo/middle/importers/audit_cleanup.py

Issues addressed:
1. NULL domains on spine → backfill from CL
2. Duplicate domains → log for manual merge
3. NULL outreach_id on appointments → domain match (N/A - table doesn't exist)
4. Duplicate emails in appointments → dedupe (N/A - table doesn't exist)
5. Orphan people → email domain match
6. Duplicate emails in people → dedupe + slot reassign
7. Orphan slots → remove
8. Missing sovereign IDs → export for CL minting
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_connection():
    """Get database connection from environment variables."""
    return psycopg2.connect(
        host=os.environ.get('NEON_HOST'),
        database=os.environ.get('NEON_DATABASE'),
        user=os.environ.get('NEON_USER'),
        password=os.environ.get('NEON_PASSWORD'),
        sslmode='require'
    )

def log(msg):
    """Print with timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def fix_null_domains(cur, dry_run=True):
    """Fix NULL domains on spine by backfilling from CL."""
    log("Checking NULL domains on spine...")

    cur.execute("""
        SELECT COUNT(*) as count
        FROM outreach.outreach
        WHERE domain IS NULL OR domain = ''
    """)
    count = cur.fetchone()['count']

    if count == 0:
        log(f"  No NULL domains found. SKIP")
        return 0

    log(f"  Found {count:,} NULL domains")

    if not dry_run:
        # Attempt to backfill from company_target
        cur.execute("""
            UPDATE outreach.outreach o
            SET domain = ct.domain
            FROM outreach.company_target ct
            WHERE o.outreach_id = ct.outreach_id
              AND (o.domain IS NULL OR o.domain = '')
              AND ct.domain IS NOT NULL AND ct.domain != ''
        """)
        fixed = cur.rowcount
        log(f"  Fixed {fixed:,} via company_target backfill")
        return fixed
    else:
        log(f"  DRY RUN - would attempt backfill from company_target")
        return 0

def log_duplicate_domains(cur):
    """Log duplicate domains for manual review."""
    log("Checking duplicate domains...")

    cur.execute("""
        SELECT domain, COUNT(*) as cnt, array_agg(outreach_id) as outreach_ids
        FROM outreach.outreach
        WHERE domain IS NOT NULL AND domain != ''
        GROUP BY domain
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 50
    """)
    dupes = cur.fetchall()

    if not dupes:
        log("  No duplicate domains found. SKIP")
        return

    log(f"  Found {len(dupes)} duplicate domain sets (showing top 50)")

    # Export to file for manual review
    export_path = "exports/duplicate_domains_audit.csv"
    os.makedirs("exports", exist_ok=True)

    with open(export_path, 'w') as f:
        f.write("domain,count,outreach_ids\n")
        for row in dupes:
            ids = ";".join(str(x) for x in row['outreach_ids'][:10])  # First 10 IDs
            f.write(f"{row['domain']},{row['cnt']},{ids}\n")

    log(f"  Exported to {export_path} for manual merge review")

def fix_orphan_people(cur, dry_run=True):
    """Fix orphan people records with no slot assignment."""
    log("Checking orphan people (no slot)...")

    # First check if barton_id column exists
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'people' AND table_name = 'company_slot'
        AND column_name = 'barton_id'
    """)
    has_barton_id = cur.fetchone() is not None

    if has_barton_id:
        cur.execute("""
            SELECT COUNT(*) as count
            FROM people.people_master pm
            WHERE NOT EXISTS (
                SELECT 1 FROM people.company_slot cs
                WHERE cs.barton_id = pm.barton_id
            )
        """)
    else:
        log("  Cannot check - company_slot has no barton_id or person_id column")
        return 0

    count = cur.fetchone()['count']

    if count == 0:
        log(f"  No orphan people found. SKIP")
        return 0

    log(f"  Found {count:,} orphan people")
    log(f"  Recommendation: Email domain match to link to slots")
    return count

def log_duplicate_emails(cur):
    """Log duplicate emails in people_master."""
    log("Checking duplicate emails in people_master...")

    cur.execute("""
        SELECT email, COUNT(*) as cnt
        FROM people.people_master
        WHERE email IS NOT NULL AND email != ''
        GROUP BY email
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 100
    """)
    dupes = cur.fetchall()

    total_dupe_count = 0
    cur.execute("""
        SELECT COUNT(*) as count FROM (
            SELECT email
            FROM people.people_master
            WHERE email IS NOT NULL AND email != ''
            GROUP BY email
            HAVING COUNT(*) > 1
        ) d
    """)
    total_dupe_count = cur.fetchone()['count']

    if total_dupe_count == 0:
        log("  No duplicate emails found. SKIP")
        return

    log(f"  Found {total_dupe_count:,} duplicate email addresses")

    # Export for review
    export_path = "exports/duplicate_emails_audit.csv"
    os.makedirs("exports", exist_ok=True)

    with open(export_path, 'w') as f:
        f.write("email,count\n")
        for row in dupes:
            f.write(f"{row['email']},{row['cnt']}\n")

    log(f"  Exported top 100 to {export_path}")

def check_orphan_slots(cur, dry_run=True):
    """Check for orphan slots with no spine match."""
    log("Checking orphan slots...")

    cur.execute("""
        SELECT COUNT(*) as count
        FROM people.company_slot cs
        WHERE NOT EXISTS (
            SELECT 1 FROM outreach.outreach o
            WHERE o.outreach_id = cs.outreach_id
        )
    """)
    count = cur.fetchone()['count']

    if count == 0:
        log(f"  No orphan slots found. SKIP")
        return 0

    log(f"  Found {count:,} orphan slots")

    if not dry_run:
        # Archive then delete
        cur.execute("""
            INSERT INTO people.company_slot_archive
            SELECT cs.*, NOW() as archived_at, 'orphan_cleanup' as archive_reason
            FROM people.company_slot cs
            WHERE NOT EXISTS (
                SELECT 1 FROM outreach.outreach o
                WHERE o.outreach_id = cs.outreach_id
            )
        """)
        cur.execute("""
            DELETE FROM people.company_slot cs
            WHERE NOT EXISTS (
                SELECT 1 FROM outreach.outreach o
                WHERE o.outreach_id = cs.outreach_id
            )
        """)
        deleted = cur.rowcount
        log(f"  Archived and deleted {deleted:,} orphan slots")
        return deleted
    else:
        log(f"  DRY RUN - would archive and delete {count:,} orphan slots")
        return 0

def run_cleanup(dry_run=True):
    """Run all cleanup operations."""
    conn = get_connection()
    conn.autocommit = False
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print(f"AUDIT CLEANUP - {'DRY RUN' if dry_run else 'LIVE RUN'}")
    print("=" * 80)
    print()

    try:
        # Issue 1: NULL domains
        fix_null_domains(cur, dry_run)
        print()

        # Issue 2: Duplicate domains (log only)
        log_duplicate_domains(cur)
        print()

        # Issue 5: Orphan people
        fix_orphan_people(cur, dry_run)
        print()

        # Issue 6: Duplicate emails (log only)
        log_duplicate_emails(cur)
        print()

        # Issue 7: Orphan slots
        check_orphan_slots(cur, dry_run)
        print()

        if not dry_run:
            conn.commit()
            log("Changes committed.")
        else:
            conn.rollback()
            log("DRY RUN complete. No changes made.")

    except Exception as e:
        conn.rollback()
        log(f"ERROR: {e}")
        raise
    finally:
        cur.close()
        conn.close()

    print()
    print("=" * 80)

if __name__ == "__main__":
    dry_run = "--live" not in sys.argv

    if not dry_run:
        confirm = input("WARNING: Running in LIVE mode. Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(1)

    run_cleanup(dry_run=dry_run)
