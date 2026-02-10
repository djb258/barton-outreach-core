"""
Create a service agent coverage: persist intent (agent + anchor ZIP + radius).

ZIP membership is derived via coverage.v_service_agent_coverage_zips — nothing
is materialized. This script inserts one row into service_agent_coverage and
returns the coverage_id. Dry-run queries the view to preview derived membership.

Usage:
    doppler run -- python hubs/coverage/imo/middle/create_service_agent_coverage.py \
        --agent-id <uuid> --anchor-zip 75201 --radius-miles 50 --created-by "owner"

    doppler run -- python hubs/coverage/imo/middle/create_service_agent_coverage.py \
        --agent-id <uuid> --anchor-zip 75201 --radius-miles 50 --created-by "owner" --dry-run
"""

import argparse
import os
import re
import sys
import time

import psycopg2

# Windows UTF-8 stdout
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ZIP_PATTERN = re.compile(r"^\d{5}$")

# Preview query: same haversine as the view, used for dry-run and post-insert verification
PREVIEW_HAVERSINE = """
WITH distances AS (
    SELECT
        zip, city, state_id, population,
        ROUND((3959 * acos(
            LEAST(1.0, GREATEST(-1.0,
                cos(radians(%(anchor_lat)s)) * cos(radians(lat)) *
                cos(radians(lng) - radians(%(anchor_lng)s)) +
                sin(radians(%(anchor_lat)s)) * sin(radians(lat))
            ))
        ))::numeric, 2) AS distance_miles
    FROM reference.us_zip_codes
    WHERE lat BETWEEN %(anchor_lat)s - (%(radius)s / 69.0)
                  AND %(anchor_lat)s + (%(radius)s / 69.0)
      AND lng BETWEEN %(anchor_lng)s - (%(radius)s / (69.0 * cos(radians(%(anchor_lat)s))))
                  AND %(anchor_lng)s + (%(radius)s / (69.0 * cos(radians(%(anchor_lat)s))))
)
SELECT zip, city, state_id, population, distance_miles
FROM distances
WHERE distance_miles <= %(radius)s
ORDER BY distance_miles
"""


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def validate_anchor_zip(cur, anchor_zip):
    """Look up anchor ZIP in reference table. Returns (lat, lng, city, state_id) or exits."""
    cur.execute(
        "SELECT lat, lng, city, state_id FROM reference.us_zip_codes WHERE zip = %s",
        (anchor_zip,),
    )
    row = cur.fetchone()
    if not row:
        print(f"HARD FAIL: anchor_zip {anchor_zip} not found in reference.us_zip_codes")
        sys.exit(1)
    return row


def preview_zips(cur, anchor_lat, anchor_lng, radius_miles):
    """Preview derived ZIP membership using haversine CTE."""
    cur.execute(PREVIEW_HAVERSINE, {
        "anchor_lat": float(anchor_lat),
        "anchor_lng": float(anchor_lng),
        "radius": float(radius_miles),
    })
    return cur.fetchall()


def print_summary(anchor_zip, anchor_city, anchor_state, radius_miles, zips,
                  coverage_id=None):
    """Print coverage summary."""
    total_pop = sum(r[3] or 0 for r in zips)

    states = {}
    for r in zips:
        st = r[2] or "UNKNOWN"
        states[st] = states.get(st, 0) + 1

    print(f"\n{'='*60}")
    print(f"  Coverage Summary")
    print(f"{'='*60}")
    if coverage_id:
        print(f"  coverage_id:   {coverage_id}")
    print(f"  Anchor ZIP:    {anchor_zip} ({anchor_city}, {anchor_state})")
    print(f"  Radius:        {radius_miles} miles")
    print(f"  ZIPs derived:  {len(zips):,}")
    print(f"  Population:    {total_pop:,}")
    print(f"  States:        {len(states)}")

    if zips:
        print(f"\n  Nearest 5:")
        for r in zips[:5]:
            print(f"    {r[0]} | {r[1]}, {r[2]} | pop={r[3] or 0:,} | {r[4]} mi")

        print(f"\n  Farthest 5:")
        for r in zips[-5:]:
            print(f"    {r[0]} | {r[1]}, {r[2]} | pop={r[3] or 0:,} | {r[4]} mi")

    print(f"\n  State breakdown:")
    for st, cnt in sorted(states.items(), key=lambda x: -x[1]):
        print(f"    {st}: {cnt:,} ZIPs")

    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description="Create service agent coverage (intent + derived ZIP view)"
    )
    parser.add_argument("--agent-id", required=True, help="Service agent UUID")
    parser.add_argument("--anchor-zip", required=True, help="5-digit anchor ZIP code")
    parser.add_argument("--radius-miles", required=True, type=float, help="Radius in miles")
    parser.add_argument("--created-by", required=True, help="Who is creating this coverage")
    parser.add_argument("--notes", default=None, help="Optional notes")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview derived ZIP membership without persisting intent")
    args = parser.parse_args()

    if not ZIP_PATTERN.match(args.anchor_zip):
        print(f"HARD FAIL: anchor_zip must be exactly 5 digits, got: {args.anchor_zip!r}")
        sys.exit(1)

    if args.radius_miles <= 0:
        print(f"HARD FAIL: radius_miles must be > 0, got: {args.radius_miles}")
        sys.exit(1)

    conn = get_connection()
    cur = conn.cursor()

    # Step 1: Validate anchor ZIP
    print(f"Validating anchor ZIP {args.anchor_zip}...")
    anchor_lat, anchor_lng, anchor_city, anchor_state = validate_anchor_zip(
        cur, args.anchor_zip
    )
    print(f"  Found: {anchor_city}, {anchor_state} (lat={anchor_lat}, lng={anchor_lng})")

    # Step 2: Validate service agent
    print(f"Validating service agent {args.agent_id}...")
    cur.execute(
        "SELECT agent_name, status FROM coverage.service_agent WHERE service_agent_id = %s",
        (args.agent_id,),
    )
    agent_row = cur.fetchone()
    if not agent_row:
        print(f"HARD FAIL: service_agent_id {args.agent_id} not found")
        conn.close()
        sys.exit(1)
    if agent_row[1] != "active":
        print(f"HARD FAIL: service agent {agent_row[0]!r} is {agent_row[1]}, must be active")
        conn.close()
        sys.exit(1)
    print(f"  Agent: {agent_row[0]} (status={agent_row[1]})")

    # Step 3: Preview derived ZIP membership
    print(f"\nDeriving ZIPs within {args.radius_miles} miles of {args.anchor_zip}...")
    start = time.time()
    zips = preview_zips(cur, anchor_lat, anchor_lng, args.radius_miles)
    elapsed = time.time() - start
    print(f"  Derived {len(zips):,} ZIPs in {elapsed:.2f}s")

    if args.dry_run:
        print_summary(args.anchor_zip, anchor_city, anchor_state, args.radius_miles, zips)
        print("\n[DRY RUN] No intent persisted. ZIP membership shown above is derived, not stored.")
        conn.close()
        return

    # Step 4: Persist intent (one row — no ZIP rows)
    print("\nPersisting coverage intent...")
    cur.execute(
        """
        INSERT INTO coverage.service_agent_coverage
            (service_agent_id, anchor_zip, radius_miles, created_by, notes)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING coverage_id
        """,
        (args.agent_id, args.anchor_zip, args.radius_miles, args.created_by, args.notes),
    )
    coverage_id = cur.fetchone()[0]
    conn.commit()

    # Step 5: Verify via view
    cur.execute(
        "SELECT COUNT(*) FROM coverage.v_service_agent_coverage_zips WHERE coverage_id = %s",
        (coverage_id,),
    )
    view_count = cur.fetchone()[0]

    print_summary(args.anchor_zip, anchor_city, anchor_state, args.radius_miles, zips,
                  coverage_id=coverage_id)

    print(f"\nView verification: {view_count:,} ZIPs derived for coverage_id {coverage_id}")
    print(f"\ncoverage_id = {coverage_id}")
    print("Done.")

    conn.close()


if __name__ == "__main__":
    main()
