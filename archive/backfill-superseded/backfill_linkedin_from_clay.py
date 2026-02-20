#!/usr/bin/env python3
"""
Backfill LinkedIn URLs from Clay Intake
========================================
For slotted people who STILL have no LinkedIn after Hunter backfill,
try matching to Clay intake (intake.people_raw_intake) by
first_name + last_name + company_name.

Match path:
  people_master → company_slot → outreach_id
  → outreach.outreach → domain
  → outreach.company_target.company_name
  → intake.people_raw_intake.company_name + first_name + last_name

Conservative: exact name + company match only.

Usage:
    doppler run -- python backfill_linkedin_from_clay.py [--dry-run]

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
        print("[FAIL] DATABASE_URL not set. Use: doppler run -- python backfill_linkedin_from_clay.py")
        sys.exit(1)

    import psycopg2
    return psycopg2.connect(database_url)


def count_remaining_gaps(conn):
    """Count slotted people still missing LinkedIn (after Hunter backfill)."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM people.people_master pm
        WHERE (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
          AND pm.unique_id IN (
              SELECT person_unique_id FROM people.company_slot WHERE is_filled = TRUE
          )
    """)
    count = cursor.fetchone()[0]
    cursor.close()
    return count


def find_clay_matches(conn):
    """Find matches between slotted people and Clay intake by name + company.

    Join path:
      people_master → company_slot → outreach.outreach → cl.company_identity
      Then match cl.company_identity.company_name to intake.people_raw_intake.company_name
      Plus first_name + last_name exact match.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            pm.unique_id AS people_unique_id,
            pm.first_name,
            pm.last_name,
            ci.company_name,
            pri.linkedin_url AS clay_linkedin_url
        FROM people.people_master pm
        JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id AND cs.is_filled = TRUE
        JOIN outreach.outreach oo ON oo.outreach_id = cs.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = oo.outreach_id
        JOIN intake.people_raw_intake pri
            ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
            AND LOWER(TRIM(pri.first_name)) = LOWER(TRIM(pm.first_name))
            AND LOWER(TRIM(pri.last_name)) = LOWER(TRIM(pm.last_name))
        WHERE (pm.linkedin_url IS NULL OR pm.linkedin_url = '')
          AND pri.linkedin_url IS NOT NULL AND pri.linkedin_url != ''
    """)
    matches = cursor.fetchall()
    cursor.close()
    return matches


def preview_matches(matches):
    """Show a sample of matches for review."""
    print(f"\n  Sample matches (first 10):")
    print(f"  {'People ID':<30} {'Name':<30} {'Company':<30} {'Clay LinkedIn'}")
    print(f"  {'-'*30} {'-'*30} {'-'*30} {'-'*50}")
    for row in matches[:10]:
        people_id, first_name, last_name, company, linkedin = row
        name = f"{first_name} {last_name}"
        print(f"  {people_id:<30} {name:<30} {company[:30]:<30} {linkedin[:50]}")


def run_backfill(conn, dry_run=False):
    """Execute the Clay LinkedIn backfill."""
    remaining = count_remaining_gaps(conn)
    print(f"\n  Slotted people still missing LinkedIn: {remaining:,}")

    if remaining == 0:
        print("  No gaps to fill. Done.")
        return 0

    print("\n  Finding Clay intake matches (exact name + company)...")
    matches = find_clay_matches(conn)
    print(f"  Found {len(matches):,} matches")

    if not matches:
        print("  No Clay matches found. Done.")
        return 0

    # Deduplicate — take first match per people_unique_id
    seen = set()
    unique_matches = []
    for row in matches:
        if row[0] not in seen:
            seen.add(row[0])
            unique_matches.append(row)

    print(f"  Unique people to update: {len(unique_matches):,}")
    preview_matches(unique_matches)

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(unique_matches):,} people_master records with LinkedIn URLs from Clay.")
        return len(unique_matches)

    # Execute in batches
    total_updated = 0
    cursor = conn.cursor()

    for i in range(0, len(unique_matches), BATCH_SIZE):
        batch = unique_matches[i:i + BATCH_SIZE]
        for people_id, _, _, _, linkedin_url in batch:
            cursor.execute("""
                UPDATE people.people_master
                SET linkedin_url = %s
                WHERE unique_id = %s
                  AND (linkedin_url IS NULL OR linkedin_url = '')
            """, (linkedin_url, people_id))
            total_updated += cursor.rowcount

        conn.commit()
        print(f"  Batch complete: {total_updated:,} updated so far...")

    cursor.close()
    return total_updated


def main():
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("BACKFILL LINKEDIN FROM CLAY INTAKE")
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
    print(f"  Source: intake.people_raw_intake (Clay)")
    print(f"  Target: people.people_master.linkedin_url")
    print(f"  Match method: exact first_name + last_name + company_name")
    print(f"Completed: {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
