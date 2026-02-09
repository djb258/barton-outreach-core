#!/usr/bin/env python3
"""
Backfill LinkedIn URLs from Hunter Contact Table
=================================================
Updates people.people_master with LinkedIn URLs from enrichment.hunter_contact
for slotted people who have email but no LinkedIn URL.

Impact: ~33,603 people get LinkedIn URLs (biggest quality win)

Match logic: LOWER(people_master.email) = LOWER(hunter_contact.email)
Only updates linkedin_url — does not touch any other columns.

Usage:
    doppler run -- python backfill_linkedin_from_hunter.py [--dry-run]

Created: 2026-02-09
"""

import os
import sys
from datetime import datetime

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


BATCH_SIZE = 1000


def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[FAIL] DATABASE_URL not set. Use: doppler run -- python backfill_linkedin_from_hunter.py")
        sys.exit(1)

    import psycopg2
    return psycopg2.connect(database_url)


def count_candidates(conn):
    """Count how many slotted people have email but no LinkedIn."""
    cursor = conn.cursor()

    # Total slotted people missing LinkedIn
    cursor.execute("""
        SELECT COUNT(*)
        FROM people.people_master pm
        WHERE (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
          AND pm.email IS NOT NULL AND pm.email != ''
          AND pm.unique_id IN (
              SELECT person_unique_id FROM people.company_slot WHERE is_filled = TRUE
          )
    """)
    missing_linkedin = cursor.fetchone()[0]

    # How many of those have a Hunter match
    cursor.execute("""
        SELECT COUNT(DISTINCT pm.unique_id)
        FROM people.people_master pm
        JOIN enrichment.hunter_contact hc ON LOWER(pm.email) = LOWER(hc.email)
        WHERE (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
          AND pm.email IS NOT NULL AND pm.email != ''
          AND hc.linkedin_url IS NOT NULL AND hc.linkedin_url != ''
          AND pm.unique_id IN (
              SELECT person_unique_id FROM people.company_slot WHERE is_filled = TRUE
          )
    """)
    matchable = cursor.fetchone()[0]

    cursor.close()
    return missing_linkedin, matchable


def get_update_batch(conn, offset, limit):
    """Get a batch of (people_master unique_id, hunter linkedin_url) pairs."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ON (pm.unique_id)
            pm.unique_id,
            hc.linkedin_url
        FROM people.people_master pm
        JOIN enrichment.hunter_contact hc ON LOWER(pm.email) = LOWER(hc.email)
        WHERE (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
          AND pm.email IS NOT NULL AND pm.email != ''
          AND hc.linkedin_url IS NOT NULL AND hc.linkedin_url != ''
          AND pm.unique_id IN (
              SELECT person_unique_id FROM people.company_slot WHERE is_filled = TRUE
          )
        ORDER BY pm.unique_id, hc.confidence_score DESC NULLS LAST
        LIMIT %s OFFSET %s
    """, (limit, offset))
    rows = cursor.fetchall()
    cursor.close()
    return rows


def run_backfill(conn, dry_run=False):
    """Execute the backfill in batches."""
    missing_linkedin, matchable = count_candidates(conn)

    print(f"\n  Slotted people missing LinkedIn: {missing_linkedin:,}")
    print(f"  Matchable via Hunter email:      {matchable:,}")

    if matchable == 0:
        print("\n  No candidates to update. Done.")
        return 0

    # Breakdown by slot type
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cs.slot_type, COUNT(DISTINCT pm.unique_id)
        FROM people.people_master pm
        JOIN enrichment.hunter_contact hc ON LOWER(pm.email) = LOWER(hc.email)
        JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id AND cs.is_filled = TRUE
        WHERE (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
          AND pm.email IS NOT NULL AND pm.email != ''
          AND hc.linkedin_url IS NOT NULL AND hc.linkedin_url != ''
        GROUP BY cs.slot_type
        ORDER BY cs.slot_type
    """)
    print("\n  Breakdown by slot type:")
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]:,}")
    cursor.close()

    if dry_run:
        print(f"\n[DRY RUN] Would update {matchable:,} people_master records with LinkedIn URLs.")
        return matchable

    # Execute in batches
    total_updated = 0
    offset = 0

    while True:
        batch = get_update_batch(conn, offset, BATCH_SIZE)
        if not batch:
            break

        cursor = conn.cursor()
        for unique_id, linkedin_url in batch:
            cursor.execute("""
                UPDATE people.people_master
                SET linkedin_url = %s
                WHERE unique_id = %s
                  AND (linkedin_url IS NULL OR linkedin_url = '')
            """, (linkedin_url, unique_id))
            total_updated += cursor.rowcount

        conn.commit()
        cursor.close()

        print(f"  Batch complete: {total_updated:,} updated so far...")
        offset += BATCH_SIZE

    return total_updated


def main():
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("BACKFILL LINKEDIN FROM HUNTER CONTACT")
    print("=" * 60)
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"Started: {datetime.now().isoformat()}")

    conn = get_connection()
    print("Connected to database.")

    total_updated = run_backfill(conn, dry_run)

    conn.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  LinkedIn URLs {'would be ' if dry_run else ''}backfilled: {total_updated:,}")
    print(f"  Source: enrichment.hunter_contact")
    print(f"  Target: people.people_master.linkedin_url")
    print(f"Completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
