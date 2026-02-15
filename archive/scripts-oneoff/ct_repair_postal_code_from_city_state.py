"""
CT Postal Code Repair via City+State Geocode.

For CT companies still missing postal_code after DOL repair, looks up the
best-match ZIP from reference.us_zip_codes using city+state.

For cities with multiple ZIPs, picks the most populous ZIP (best proxy for
the city's "primary" ZIP code).

Doctrine: CT is the sole ZIP authority. This is a second repair pass.
ADR: docs/adr/ADR-CT-ZIP-REPAIR-VIA-DOL-EVIDENCE.md (same principle)

Usage:
    doppler run -- python scripts/ct_repair_postal_code_from_city_state.py
    doppler run -- python scripts/ct_repair_postal_code_from_city_state.py --apply
"""

import argparse
import os
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def main():
    parser = argparse.ArgumentParser(
        description="CT postal_code repair from city+state geocode"
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Apply repairs (default: dry-run only)"
    )
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    # ================================================================
    # Baseline
    # ================================================================
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL
                        AND TRIM(postal_code) != '' THEN 1 END) AS has_zip,
            COUNT(CASE WHEN postal_code IS NULL
                        OR TRIM(postal_code) = '' THEN 1 END) AS missing
        FROM outreach.company_target
    """)
    total, has_zip, missing = cur.fetchone()

    print(f"{'='*60}")
    print(f"  CT Postal Code Repair — City+State Geocode")
    print(f"{'='*60}")
    print(f"\n  BEFORE:")
    print(f"    CT total:         {total:,}")
    print(f"    With postal_code: {has_zip:,} ({100*has_zip/total:.1f}%)")
    print(f"    Missing:          {missing:,} ({100*missing/total:.1f}%)")

    # ================================================================
    # Preview: how many are repairable?
    # For each CT company missing ZIP but having city+state,
    # find the best ZIP from reference.us_zip_codes (most populous).
    # ================================================================
    cur.execute("""
        WITH candidates AS (
            SELECT
                ct.outreach_id,
                UPPER(TRIM(ct.city)) AS ct_city,
                UPPER(TRIM(ct.state)) AS ct_state
            FROM outreach.company_target ct
            WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
              AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
              AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
        ),
        best_zip AS (
            SELECT DISTINCT ON (c.outreach_id)
                c.outreach_id,
                z.zip,
                z.city AS ref_city,
                z.state_id AS ref_state,
                z.population
            FROM candidates c
            JOIN reference.us_zip_codes z
                ON UPPER(z.city) = c.ct_city
               AND UPPER(z.state_id) = c.ct_state
            ORDER BY c.outreach_id, z.population DESC NULLS LAST
        )
        SELECT COUNT(*), ref_state, COUNT(DISTINCT ref_state)
        FROM best_zip
        GROUP BY ref_state
        ORDER BY COUNT(*) DESC
    """)
    state_rows = cur.fetchall()
    candidate_count = sum(r[0] for r in state_rows)

    print(f"\n  Repair candidates: {candidate_count:,}")

    if not state_rows:
        print("\n  No candidates found.")
        conn.close()
        return

    print(f"\n  By state:")
    for r in state_rows[:15]:
        print(f"    {r[1]}: {r[0]:,}")
    if len(state_rows) > 15:
        print(f"    ... and {len(state_rows) - 15} more states")

    # Sample
    cur.execute("""
        WITH candidates AS (
            SELECT
                ct.outreach_id,
                ct.city AS ct_city_raw,
                ct.state AS ct_state_raw,
                UPPER(TRIM(ct.city)) AS ct_city,
                UPPER(TRIM(ct.state)) AS ct_state
            FROM outreach.company_target ct
            WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
              AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
              AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
        ),
        best_zip AS (
            SELECT DISTINCT ON (c.outreach_id)
                c.outreach_id,
                c.ct_city_raw,
                c.ct_state_raw,
                z.zip,
                z.city AS ref_city,
                z.population
            FROM candidates c
            JOIN reference.us_zip_codes z
                ON UPPER(z.city) = c.ct_city
               AND UPPER(z.state_id) = c.ct_state
            ORDER BY c.outreach_id, z.population DESC NULLS LAST
        )
        SELECT outreach_id, ct_city_raw, ct_state_raw, zip, ref_city, population
        FROM best_zip
        ORDER BY population DESC NULLS LAST
        LIMIT 10
    """)
    print(f"\n  Sample (highest population ZIPs):")
    for r in cur.fetchall():
        pop = f"{r[5]:,}" if r[5] else "?"
        print(f"    {r[1]:25s} {r[2]:>2s} -> {r[3]} (pop {pop})")

    # ================================================================
    # Dry run vs apply
    # ================================================================
    if not args.apply:
        proj = has_zip + candidate_count
        print(f"\n  [DRY RUN] Would repair {candidate_count:,} companies.")
        print(f"  Post-repair projection: {proj:,} / {total:,} ({100*proj/total:.1f}%)")
        print(f"\n  To apply: add --apply flag")
        conn.close()
        return

    # ================================================================
    # Apply: single bulk UPDATE
    # ================================================================
    print(f"\n  Applying repairs (bulk UPDATE)...")
    start = time.time()

    cur.execute("""
        WITH best_zip AS (
            SELECT DISTINCT ON (ct.outreach_id)
                ct.outreach_id,
                z.zip
            FROM outreach.company_target ct
            JOIN reference.us_zip_codes z
                ON UPPER(z.city) = UPPER(TRIM(ct.city))
               AND UPPER(z.state_id) = UPPER(TRIM(ct.state))
            WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
              AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
              AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
            ORDER BY ct.outreach_id, z.population DESC NULLS LAST
        )
        UPDATE outreach.company_target ct
        SET postal_code = bz.zip,
            postal_code_source = 'CITY_STATE_GEOCODE',
            postal_code_updated_at = NOW()
        FROM best_zip bz
        WHERE bz.outreach_id = ct.outreach_id
          AND (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
    """)

    applied = cur.rowcount
    conn.commit()
    elapsed = time.time() - start

    # ================================================================
    # Post-repair verification
    # ================================================================
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            COUNT(CASE WHEN postal_code IS NOT NULL
                        AND TRIM(postal_code) != '' THEN 1 END) AS has_zip
        FROM outreach.company_target
    """)
    post_total, post_has_zip = cur.fetchone()

    print(f"\n  AFTER:")
    print(f"    Applied:          {applied:,}")
    print(f"    With postal_code: {post_has_zip:,} ({100*post_has_zip/post_total:.1f}%)")
    print(f"    Improvement:      +{post_has_zip - has_zip:,} companies")
    print(f"    Time:             {elapsed:.1f}s")

    # Source breakdown
    cur.execute("""
        SELECT postal_code_source, COUNT(*)
        FROM outreach.company_target
        WHERE postal_code_source IS NOT NULL
        GROUP BY postal_code_source
        ORDER BY COUNT(*) DESC
    """)
    print(f"\n  By source:")
    for r in cur.fetchall():
        print(f"    {r[0]}: {r[1]:,}")

    # Remaining gap
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target
        WHERE postal_code IS NULL OR TRIM(postal_code) = ''
    """)
    remaining = cur.fetchone()[0]
    print(f"\n  Still missing: {remaining:,} ({100*remaining/post_total:.1f}%)")

    conn.close()
    print(f"\n{'='*60}")
    print(f"  Done.")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
