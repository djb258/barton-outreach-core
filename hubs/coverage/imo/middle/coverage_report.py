"""
Coverage Report — Market-scoped sub-hub completeness.

Given a coverage_id (or anchor ZIP + radius), produces a doctrine-clean report:
  - CT companies (state-filtered to radius states ONLY)
  - DOL linked %
  - People slots filled %
  - Blog (informational)
  - CLS: pending

This is a finite repair backlog for a defined market.

Scope rules:
  - CT postal_code determines membership (CT is scope authority)
  - State filter enforced: only states present in the radius ZIP set
  - DOL ZIPs may repair CT but NEVER expand scope
  - BIT is deprecated — CLS replaces it (not wired yet)

Usage:
    doppler run -- python hubs/coverage/imo/middle/coverage_report.py --coverage-id <uuid>
    doppler run -- python hubs/coverage/imo/middle/coverage_report.py --anchor-zip 26739 --radius-miles 100
"""

import argparse
import os
import sys

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


def resolve_from_coverage_id(cur, coverage_id):
    """Resolve ZIPs and metadata from a coverage_id via the view."""
    cur.execute("""
        SELECT sac.anchor_zip, sac.radius_miles, sac.status,
               ref.city, ref.state_id
        FROM coverage.service_agent_coverage sac
        JOIN reference.us_zip_codes ref ON ref.zip = sac.anchor_zip
        WHERE sac.coverage_id = %s
    """, (coverage_id,))
    row = cur.fetchone()
    if not row:
        print(f"  ERROR: coverage_id {coverage_id} not found")
        sys.exit(1)
    anchor_zip, radius_miles, status, a_city, a_state = row
    if status != "active":
        print(f"  WARNING: coverage_id {coverage_id} is {status}")

    cur.execute("""
        SELECT zip, state_id
        FROM coverage.v_service_agent_coverage_zips
        WHERE coverage_id = %s
    """, (coverage_id,))
    radius_zips = []
    radius_states = set()
    for zip_code, state in cur.fetchall():
        radius_zips.append(zip_code)
        radius_states.add(state)

    return radius_zips, sorted(radius_states), anchor_zip, radius_miles, a_city, a_state


def resolve_from_zip_radius(cur, anchor_zip, radius_miles):
    """Resolve ZIPs via haversine (ad-hoc, no persisted coverage_id)."""
    cur.execute("""
        SELECT lat, lng, city, state_id
        FROM reference.us_zip_codes WHERE zip = %s
    """, (anchor_zip,))
    anchor = cur.fetchone()
    if not anchor:
        print(f"  ERROR: ZIP {anchor_zip} not found in reference.us_zip_codes")
        sys.exit(1)
    a_lat, a_lng, a_city, a_state = anchor

    cur.execute("""
        SELECT zip, state_id,
            ROUND((3959 * acos(LEAST(1.0, GREATEST(-1.0,
                cos(radians(%s)) * cos(radians(lat)) *
                cos(radians(lng) - radians(%s)) +
                sin(radians(%s)) * sin(radians(lat))
            ))))::numeric, 2) AS distance
        FROM reference.us_zip_codes
        WHERE lat BETWEEN %s - (%s / 69.0) AND %s + (%s / 69.0)
          AND lng BETWEEN %s - (%s / (69.0 * cos(radians(%s)))) AND %s + (%s / (69.0 * cos(radians(%s))))
    """, (a_lat, a_lng, a_lat,
          a_lat, radius_miles, a_lat, radius_miles,
          a_lng, radius_miles, a_lat, a_lng, radius_miles, a_lat))
    radius_zips = []
    radius_states = set()
    for zip_code, state, dist in cur.fetchall():
        if float(dist) <= radius_miles:
            radius_zips.append(zip_code)
            radius_states.add(state)

    return radius_zips, sorted(radius_states), anchor_zip, radius_miles, a_city, a_state


def run_report(cur, radius_zips, allowed_states, anchor_zip, radius_miles, a_city, a_state, coverage_id=None):
    """Run the coverage report and print results. Returns summary dict."""
    print(f"{'='*75}")
    print(f"  COVERAGE REPORT")
    if coverage_id:
        print(f"  Coverage ID: {coverage_id}")
    print(f"  Anchor: {anchor_zip} ({a_city}, {a_state})")
    print(f"  Radius: {radius_miles} miles")
    print(f"  ZIPs:   {len(radius_zips):,}")
    print(f"  States: {', '.join(allowed_states)}")
    print(f"{'='*75}")

    # CT companies — state-filtered to radius states ONLY
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
    """, (radius_zips, allowed_states))
    ct_total = cur.fetchone()[0]

    print(f"\n  CT companies (state-filtered): {ct_total:,}")

    # DOL linked
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target ct
        JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
    """, (radius_zips, allowed_states))
    dol_linked = cur.fetchone()[0]
    dol_pct = 100 * dol_linked / ct_total if ct_total > 0 else 0

    print(f"  DOL linked:                    {dol_linked:,} ({dol_pct:.0f}%)")

    # People slots
    cur.execute("""
        SELECT ps.slot_type,
            COUNT(*) AS total,
            COUNT(CASE WHEN ps.is_filled THEN 1 END) AS filled
        FROM people.company_slot ps
        JOIN outreach.company_target ct ON ct.outreach_id = ps.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
        GROUP BY ps.slot_type ORDER BY ps.slot_type
    """, (radius_zips, allowed_states))
    slots = cur.fetchall()

    print(f"\n  People Slots:")
    total_slots = 0
    total_filled = 0
    for slot_type, total, filled in slots:
        pct = 100 * filled / total if total > 0 else 0
        gap = total - filled
        print(f"    {slot_type:5s}: {filled:,} / {total:,} ({pct:.0f}%)  gap: {gap:,}")
        total_slots += total
        total_filled += filled
    if total_slots > 0:
        overall_pct = 100 * total_filled / total_slots
        print(f"    {'TOTAL':5s}: {total_filled:,} / {total_slots:,} ({overall_pct:.0f}%)  gap: {total_slots - total_filled:,}")

    # Blog (informational only)
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target ct
        JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
    """, (radius_zips, allowed_states))
    blog_count = cur.fetchone()[0]
    blog_pct = 100 * blog_count / ct_total if ct_total > 0 else 0

    print(f"\n  Blog (informational):          {blog_count:,} ({blog_pct:.0f}%)")

    # CLS
    print(f"  CLS:                           pending")

    # State breakdown
    cur.execute("""
        SELECT UPPER(TRIM(ct.state)), COUNT(*)
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
        GROUP BY 1 ORDER BY COUNT(*) DESC
    """, (radius_zips, allowed_states))
    print(f"\n  By state:")
    for state, count in cur.fetchall():
        print(f"    {state}: {count:,}")

    # Repair backlog summary
    unfilled = total_slots - total_filled
    no_dol = ct_total - dol_linked

    print(f"\n  {'='*75}")
    print(f"  REPAIR BACKLOG")
    print(f"  {'='*75}")
    print(f"    People slots to fill:  {unfilled:,}")
    print(f"    DOL unlinked:          {no_dol:,} (expected — small employers)")
    print(f"    CLS:                   not wired yet")
    print(f"\n    Work queue = {unfilled:,} slot fills")

    return {
        "ct_total": ct_total,
        "dol_linked": dol_linked,
        "total_slots": total_slots,
        "total_filled": total_filled,
        "blog_count": blog_count,
        "unfilled": unfilled,
    }


def main():
    parser = argparse.ArgumentParser(description="Coverage report for a market radius")
    parser.add_argument("--coverage-id", help="Coverage ID (from service_agent_coverage)")
    parser.add_argument("--anchor-zip", help="5-digit anchor ZIP (if no coverage-id)")
    parser.add_argument("--radius-miles", type=float, help="Radius in miles (if no coverage-id)")
    args = parser.parse_args()

    if not args.coverage_id and not (args.anchor_zip and args.radius_miles):
        parser.error("Provide --coverage-id OR both --anchor-zip and --radius-miles")

    conn = get_connection()
    cur = conn.cursor()

    if args.coverage_id:
        radius_zips, allowed_states, anchor_zip, radius_miles, a_city, a_state = \
            resolve_from_coverage_id(cur, args.coverage_id)
    else:
        radius_zips, allowed_states, anchor_zip, radius_miles, a_city, a_state = \
            resolve_from_zip_radius(cur, args.anchor_zip, args.radius_miles)

    run_report(cur, radius_zips, allowed_states, anchor_zip, radius_miles,
               a_city, a_state, coverage_id=args.coverage_id)

    conn.close()
    print(f"\n{'='*75}")
    print(f"  Done.")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
