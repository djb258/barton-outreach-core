"""
Route Coverage Gaps — Push incomplete sub-hub records to error tables.

Given a coverage_id (or anchor ZIP + radius), identifies per-company sub-hub
gaps and routes them to the appropriate error table as work queue items.

Error tables are named per sub-hub:
  - Missing people slots  -> people.people_errors
  - Missing DOL           -> outreach.dol_errors
  - Missing blog          -> outreach.blog_errors

No errors on the spine (outreach.outreach). Each sub-hub owns its gaps.

Usage:
    doppler run -- python hubs/coverage/imo/middle/route_gaps.py --coverage-id <uuid>
    doppler run -- python hubs/coverage/imo/middle/route_gaps.py --coverage-id <uuid> --apply
    doppler run -- python hubs/coverage/imo/middle/route_gaps.py --anchor-zip 26739 --radius-miles 100 --apply --skip-dol
"""

import argparse
import os
import sys
import uuid

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

    return radius_zips, sorted(radius_states), anchor_zip, float(radius_miles), a_city, a_state


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


def route_gaps(cur, radius_zips, allowed_states, anchor_zip, radius_miles,
               a_city, a_state, apply=False, skip_dol=False, coverage_id=None):
    """Identify and route gaps. Returns summary dict."""
    print(f"{'='*75}")
    print(f"  ROUTE COVERAGE GAPS {'— APPLY' if apply else '— DRY RUN'}")
    if coverage_id:
        print(f"  Coverage ID: {coverage_id}")
    print(f"  Anchor: {anchor_zip} ({a_city}, {a_state})")
    print(f"  Radius: {radius_miles} miles | ZIPs: {len(radius_zips):,}")
    print(f"  States: {', '.join(allowed_states)}")
    print(f"{'='*75}")

    # Identify per-company gaps
    cur.execute("""
        SELECT
            ct.outreach_id,
            (d.outreach_id IS NULL) AS missing_dol,
            (b.outreach_id IS NULL) AS missing_blog,
            (ceo.outreach_id IS NULL OR NOT COALESCE(ceo.is_filled, FALSE)) AS missing_ceo,
            (cfo.outreach_id IS NULL OR NOT COALESCE(cfo.is_filled, FALSE)) AS missing_cfo,
            (hr.outreach_id IS NULL OR NOT COALESCE(hr.is_filled, FALSE)) AS missing_hr
        FROM outreach.company_target ct
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
        LEFT JOIN people.company_slot ceo ON ceo.outreach_id = ct.outreach_id AND ceo.slot_type = 'CEO'
        LEFT JOIN people.company_slot cfo ON cfo.outreach_id = ct.outreach_id AND cfo.slot_type = 'CFO'
        LEFT JOIN people.company_slot hr ON hr.outreach_id = ct.outreach_id AND hr.slot_type = 'HR'
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
    """, (radius_zips, allowed_states))
    rows = cur.fetchall()

    gap_dol = []
    gap_blog = []
    gap_people = []

    for oid, m_dol, m_blog, m_ceo, m_cfo, m_hr in rows:
        if m_dol:
            gap_dol.append(oid)
        if m_blog:
            gap_blog.append(oid)
        missing_slots = []
        if m_ceo:
            missing_slots.append("CEO")
        if m_cfo:
            missing_slots.append("CFO")
        if m_hr:
            missing_slots.append("HR")
        if missing_slots:
            gap_people.append((oid, missing_slots))

    total_companies = len(rows)
    total_slot_gaps = sum(len(slots) for _, slots in gap_people)

    print(f"\n  Companies in market: {total_companies:,}")
    print(f"\n  Sub-hub gaps found:")
    print(f"    DOL:    {len(gap_dol):,} companies {'(skipping — expected for small employers)' if skip_dol else ''}")
    print(f"    Blog:   {len(gap_blog):,} companies")
    print(f"    People: {len(gap_people):,} companies ({total_slot_gaps:,} unfilled slots)")

    ceo_gap = sum(1 for _, slots in gap_people if "CEO" in slots)
    cfo_gap = sum(1 for _, slots in gap_people if "CFO" in slots)
    hr_gap = sum(1 for _, slots in gap_people if "HR" in slots)
    print(f"      CEO: {ceo_gap:,}  CFO: {cfo_gap:,}  HR: {hr_gap:,}")

    if not apply:
        print(f"\n  [DRY RUN] Add --apply to write to error tables")
        return {"total_companies": total_companies, "routed": 0}

    run_id = str(uuid.uuid4())[:8]

    # ---- Bulk INSERT per sub-hub (single query each, no row-by-row) ----

    # --- People gaps -> people.people_errors ---
    # CHECK constraints: error_type IN (validation,ambiguity,conflict,missing_data,stale_data,external_fail)
    #   error_stage IN (slot_creation,slot_fill,...), retry_strategy IN (manual_fix,auto_retry,discard)
    cur.execute("""
        INSERT INTO people.people_errors (
            outreach_id, error_stage, error_type, error_code,
            error_message, raw_payload, retry_strategy, status
        )
        SELECT
            gaps.outreach_id, 'slot_fill', 'missing_data',
            'MISSING_' || gaps.slot_type,
            gaps.slot_type || ' slot unfilled - needs enrichment',
            jsonb_build_object('slot_type', gaps.slot_type, 'batch', %s),
            'auto_retry', 'open'
        FROM (
            SELECT ct.outreach_id, s.slot_type
            FROM outreach.company_target ct
            CROSS JOIN (VALUES ('CEO'),('CFO'),('HR')) AS s(slot_type)
            LEFT JOIN people.company_slot cs
                ON cs.outreach_id = ct.outreach_id AND cs.slot_type = s.slot_type
            WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
              AND UPPER(TRIM(ct.state)) = ANY(%s)
              AND (cs.outreach_id IS NULL OR NOT COALESCE(cs.is_filled, FALSE))
        ) gaps
        WHERE NOT EXISTS (
            SELECT 1 FROM people.people_errors pe
            WHERE pe.outreach_id = gaps.outreach_id
              AND pe.error_type = 'missing_data'
              AND pe.error_code = 'MISSING_' || gaps.slot_type
              AND pe.status = 'open'
        )
    """, (run_id, radius_zips, allowed_states))
    people_inserted = cur.rowcount

    print(f"\n  people.people_errors:  {people_inserted:,} new work items (skipped existing)")

    # --- Blog gaps -> outreach.blog_errors ---
    cur.execute("""
        INSERT INTO outreach.blog_errors (
            outreach_id, error_type, pipeline_stage, failure_code,
            blocking_reason, severity, retry_allowed
        )
        SELECT ct.outreach_id, 'BLOG_MISSING', 'blog_discovery', 'NO_BLOG_RECORD',
            'Company has no blog sub-hub record', 'non_blocking', TRUE
        FROM outreach.company_target ct
        LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
          AND b.outreach_id IS NULL
          AND NOT EXISTS (
              SELECT 1 FROM outreach.blog_errors be
              WHERE be.outreach_id = ct.outreach_id
                AND be.error_type = 'BLOG_MISSING'
                AND be.resolved_at IS NULL
          )
    """, (radius_zips, allowed_states))
    blog_inserted = cur.rowcount

    print(f"  outreach.blog_errors: {blog_inserted:,} new work items (skipped existing)")

    # --- DOL gaps -> outreach.dol_errors (optional) ---
    dol_inserted = 0
    if not skip_dol:
        cur.execute("""
            INSERT INTO outreach.dol_errors (
                outreach_id, error_type, pipeline_stage, failure_code,
                blocking_reason, severity, retry_allowed
            )
            SELECT ct.outreach_id, 'DOL_UNLINKED', 'ein_resolution', 'NO_DOL_BRIDGE',
                'No DOL bridge record - may be small employer without Form 5500',
                'non_blocking', TRUE
            FROM outreach.company_target ct
            LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
            WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
              AND UPPER(TRIM(ct.state)) = ANY(%s)
              AND d.outreach_id IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM outreach.dol_errors de
                  WHERE de.outreach_id = ct.outreach_id
                    AND de.error_type = 'DOL_UNLINKED'
                    AND de.resolved_at IS NULL
              )
        """, (radius_zips, allowed_states))
        dol_inserted = cur.rowcount
        print(f"  outreach.dol_errors:  {dol_inserted:,} new work items (skipped existing)")
    else:
        print(f"  outreach.dol_errors:  skipped (--skip-dol)")

    total_routed = people_inserted + blog_inserted + dol_inserted

    print(f"\n  {'='*65}")
    print(f"  ROUTING SUMMARY")
    print(f"  {'='*65}")
    print(f"    Batch:          {run_id}")
    print(f"    Market:         {anchor_zip} / {radius_miles}mi")
    print(f"    Companies:      {total_companies:,}")
    print(f"    Total routed:   {total_routed:,} work items")
    print(f"    People slots:   {people_inserted:,}")
    print(f"    Blog:           {blog_inserted:,}")
    print(f"    DOL:            {dol_inserted:,}")

    return {
        "total_companies": total_companies,
        "routed": total_routed,
        "people": people_inserted,
        "blog": blog_inserted,
        "dol": dol_inserted,
        "batch": run_id,
    }


def main():
    parser = argparse.ArgumentParser(description="Route coverage gaps to sub-hub error tables")
    parser.add_argument("--coverage-id", help="Coverage ID (from service_agent_coverage)")
    parser.add_argument("--anchor-zip", help="5-digit anchor ZIP (if no coverage-id)")
    parser.add_argument("--radius-miles", type=float, help="Radius in miles (if no coverage-id)")
    parser.add_argument("--apply", action="store_true", help="Write to error tables (default: dry run)")
    parser.add_argument("--skip-dol", action="store_true", help="Skip DOL gaps (expected for small employers)")
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

    route_gaps(cur, radius_zips, allowed_states, anchor_zip, radius_miles,
               a_city, a_state, apply=args.apply, skip_dol=args.skip_dol,
               coverage_id=args.coverage_id)

    if args.apply:
        conn.commit()

    conn.close()
    print(f"\n{'='*75}")
    print(f"  Done.")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
