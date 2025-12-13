#!/usr/bin/env python3
"""
Deduplicate Clay and Apollo Company Data
=========================================
Removes duplicates from intake.company_raw_wv (Clay) that already exist
in intake.company_raw_intake (Apollo).

Strategy:
1. Match by exact company name (case-insensitive)
2. Keep Apollo record (it has apollo_id and more fields)
3. Delete Clay duplicate from company_raw_wv
4. Also clean up internal duplicates within Clay table

Usage:
    python dedupe_clay_apollo.py [--dry-run]
"""

import psycopg2
import sys
import argparse

# Neon connection settings
NEON_CONFIG = {
    'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
    'port': 5432,
    'database': 'Marketing DB',
    'user': 'Marketing DB_owner',
    'password': 'npg_OsE4Z2oPCpiT',
    'sslmode': 'require'
}


def get_duplicate_stats(cur):
    """Get statistics on duplicates."""
    stats = {}

    # Count Apollo records
    cur.execute("SELECT COUNT(*) FROM intake.company_raw_intake;")
    stats['apollo_total'] = cur.fetchone()[0]

    # Count Clay records
    cur.execute("SELECT COUNT(*) FROM intake.company_raw_wv;")
    stats['clay_total'] = cur.fetchone()[0]

    # Count duplicates by name match (Clay records that match Apollo)
    cur.execute("""
        SELECT COUNT(DISTINCT c.company_unique_id)
        FROM intake.company_raw_wv c
        JOIN intake.company_raw_intake a
            ON LOWER(TRIM(c.company_name)) = LOWER(TRIM(a.company))
        WHERE (a.company_state ILIKE '%%west virginia%%' OR a.state_abbrev = 'WV')
          AND c.company_name IS NOT NULL
          AND a.company IS NOT NULL;
    """)
    stats['cross_duplicates'] = cur.fetchone()[0]

    # Count internal duplicates in Clay (same name appears multiple times)
    cur.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT LOWER(TRIM(company_name)))
        FROM intake.company_raw_wv
        WHERE company_name IS NOT NULL;
    """)
    stats['clay_internal_dupes'] = cur.fetchone()[0]

    return stats


def get_clay_duplicates_to_remove(cur):
    """Get list of Clay company_unique_ids that duplicate Apollo records."""
    cur.execute("""
        SELECT DISTINCT c.company_unique_id, c.company_name, a.company as apollo_name
        FROM intake.company_raw_wv c
        JOIN intake.company_raw_intake a
            ON LOWER(TRIM(c.company_name)) = LOWER(TRIM(a.company))
        WHERE (a.company_state ILIKE '%%west virginia%%' OR a.state_abbrev = 'WV')
          AND c.company_name IS NOT NULL
          AND a.company IS NOT NULL
        ORDER BY c.company_name;
    """)
    return cur.fetchall()


def get_clay_internal_duplicates(cur):
    """Get Clay records that are duplicates within the Clay table itself.
    Keep the first one (by company_unique_id), delete the rest."""
    cur.execute("""
        WITH ranked AS (
            SELECT
                company_unique_id,
                company_name,
                ROW_NUMBER() OVER (
                    PARTITION BY LOWER(TRIM(company_name))
                    ORDER BY company_unique_id
                ) as rn
            FROM intake.company_raw_wv
            WHERE company_name IS NOT NULL
        )
        SELECT company_unique_id, company_name
        FROM ranked
        WHERE rn > 1
        ORDER BY company_name;
    """)
    return cur.fetchall()


def remove_duplicates(cur, conn, dry_run=False):
    """Remove duplicate records from Clay table."""

    # Get cross-duplicates (Clay records matching Apollo)
    cross_dupes = get_clay_duplicates_to_remove(cur)
    print(f"\nCross-duplicates (Clay matching Apollo): {len(cross_dupes)}")

    if cross_dupes:
        print("Sample cross-duplicates to remove:")
        for row in cross_dupes[:10]:
            print(f"  {row[0]}: {row[1]}")

    # Get internal duplicates within Clay
    internal_dupes = get_clay_internal_duplicates(cur)
    print(f"\nInternal Clay duplicates: {len(internal_dupes)}")

    if internal_dupes:
        print("Sample internal duplicates to remove:")
        for row in internal_dupes[:10]:
            print(f"  {row[0]}: {row[1]}")

    # Combine all IDs to remove
    ids_to_remove = set()
    for row in cross_dupes:
        ids_to_remove.add(row[0])
    for row in internal_dupes:
        ids_to_remove.add(row[0])

    total_to_remove = len(ids_to_remove)
    print(f"\nTotal unique records to remove: {total_to_remove}")

    if dry_run:
        print("\n[DRY RUN] No records deleted.")
        return 0

    if total_to_remove == 0:
        print("No duplicates to remove.")
        return 0

    # Delete duplicates
    ids_list = list(ids_to_remove)

    # Delete in batches to avoid query size limits
    batch_size = 500
    deleted = 0

    for i in range(0, len(ids_list), batch_size):
        batch = ids_list[i:i+batch_size]
        placeholders = ','.join(['%s'] * len(batch))
        cur.execute(f"""
            DELETE FROM intake.company_raw_wv
            WHERE company_unique_id IN ({placeholders});
        """, batch)
        deleted += cur.rowcount

    conn.commit()
    print(f"\nDeleted {deleted} duplicate records from intake.company_raw_wv")
    return deleted


def clean_junk_records(cur, conn, dry_run=False):
    """Remove obvious junk/test records."""

    # Find junk records (test data, invalid names, etc.)
    cur.execute("""
        SELECT company_unique_id, company_name, domain
        FROM intake.company_raw_wv
        WHERE company_name IS NULL
           OR LOWER(TRIM(company_name)) IN ('n/a', 'test', 'test company', 'example', 'example inc')
           OR LENGTH(TRIM(company_name)) < 2
           OR domain IN ('test.com', 'example.com', 'invalid', 'n/a');
    """)
    junk = cur.fetchall()

    print(f"\nJunk/test records found: {len(junk)}")
    if junk:
        print("Junk records to remove:")
        for row in junk[:20]:
            print(f"  {row[0]}: {row[1]} | {row[2]}")

    if dry_run or len(junk) == 0:
        if dry_run:
            print("[DRY RUN] No junk records deleted.")
        return 0

    # Delete junk
    junk_ids = [row[0] for row in junk]
    placeholders = ','.join(['%s'] * len(junk_ids))
    cur.execute(f"""
        DELETE FROM intake.company_raw_wv
        WHERE company_unique_id IN ({placeholders});
    """, junk_ids)

    deleted = cur.rowcount
    conn.commit()
    print(f"Deleted {deleted} junk records")
    return deleted


def main():
    parser = argparse.ArgumentParser(description='Deduplicate Clay and Apollo company data')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without actually deleting')
    args = parser.parse_args()

    # Set up UTF-8 output
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    conn = psycopg2.connect(**NEON_CONFIG)
    cur = conn.cursor()

    try:
        # Get initial stats
        print("=" * 60)
        print("DEDUPLICATION ANALYSIS")
        print("=" * 60)

        stats = get_duplicate_stats(cur)
        print(f"\nInitial counts:")
        print(f"  Apollo records (company_raw_intake): {stats['apollo_total']}")
        print(f"  Clay records (company_raw_wv): {stats['clay_total']}")
        print(f"  Cross-duplicates (Clay matching Apollo): {stats['cross_duplicates']}")
        print(f"  Internal Clay duplicates: {stats['clay_internal_dupes']}")

        # Clean junk first
        print("\n" + "=" * 60)
        print("STEP 1: REMOVE JUNK/TEST RECORDS")
        print("=" * 60)
        junk_deleted = clean_junk_records(cur, conn, dry_run=args.dry_run)

        # Remove duplicates
        print("\n" + "=" * 60)
        print("STEP 2: REMOVE DUPLICATES")
        print("=" * 60)
        dupes_deleted = remove_duplicates(cur, conn, dry_run=args.dry_run)

        # Final stats
        print("\n" + "=" * 60)
        print("FINAL RESULTS")
        print("=" * 60)

        final_stats = get_duplicate_stats(cur)
        print(f"\nFinal counts:")
        print(f"  Apollo records: {final_stats['apollo_total']}")
        print(f"  Clay records: {final_stats['clay_total']}")
        print(f"  Remaining cross-duplicates: {final_stats['cross_duplicates']}")
        print(f"  Remaining internal duplicates: {final_stats['clay_internal_dupes']}")

        print(f"\nSummary:")
        print(f"  Junk records removed: {junk_deleted}")
        print(f"  Duplicate records removed: {dupes_deleted}")
        print(f"  Total removed: {junk_deleted + dupes_deleted}")

        if args.dry_run:
            print("\n[DRY RUN MODE - No changes made]")
        else:
            print("\nDeduplication complete!")

    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    main()
