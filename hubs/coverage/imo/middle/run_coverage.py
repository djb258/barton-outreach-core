"""
Run Coverage — The repeatable process for working a market.

One command, three stages:
  1. SCOUT   — Pick a market (ZIP + radius), get a coverage_id
  2. REPORT  — See what's complete, what's missing
  3. ACTIVATE — Route gaps to enrichment work queues (when ready)

Every market gets a coverage_id. That ID is the key to everything.

Usage:
    # List all active markets
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py --list

    # Scout a new market (creates coverage_id + shows report)
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
        --anchor-zip 26739 --radius-miles 100

    # Check an existing market
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
        --coverage-id 126b7fc9-4a2c-49bd-97ef-4c769312a576

    # Activate a market — push gaps to enrichment queues
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
        --coverage-id 126b7fc9-4a2c-49bd-97ef-4c769312a576 --activate

    # Retire a market
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py \
        --coverage-id 126b7fc9-4a2c-49bd-97ef-4c769312a576 --retire
"""

import argparse
import csv
import os
import re
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

ZIP_PATTERN = re.compile(r"^\d{5}$")


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def next_agent_number(cur):
    """Get the next SA-NNN number."""
    cur.execute("SELECT agent_number FROM coverage.service_agent ORDER BY agent_number DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        return "SA-001"
    num = int(row[0].split("-")[1]) + 1
    return f"SA-{num:03d}"


def create_agent(cur, agent_name):
    """Create a new service agent with the next sequential number."""
    num = next_agent_number(cur)
    parts = agent_name.strip().split(None, 1)
    first_name = parts[0] if parts else agent_name
    last_name = parts[1] if len(parts) > 1 else ""
    cur.execute("""
        INSERT INTO coverage.service_agent (agent_number, agent_name, first_name, last_name, status)
        VALUES (%s, %s, %s, %s, 'active')
        RETURNING agent_number, agent_name
    """, (num, agent_name, first_name, last_name))
    return cur.fetchone()


def list_agents(cur):
    """Show all service agents."""
    cur.execute("""
        SELECT sa.agent_number, sa.first_name, sa.last_name, sa.status,
               COUNT(sac.coverage_id) FILTER (WHERE sac.status = 'active') AS active_markets
        FROM coverage.service_agent sa
        LEFT JOIN coverage.service_agent_coverage sac ON sac.service_agent_id = sa.service_agent_id
        GROUP BY sa.agent_number, sa.first_name, sa.last_name, sa.status
        ORDER BY sa.agent_number
    """)
    rows = cur.fetchall()
    if not rows:
        print("  No agents found.")
        return

    print(f"{'='*72}")
    print(f"  SERVICE AGENTS")
    print(f"{'='*72}")
    print(f"  {'NUMBER':8s} {'FIRST':14s} {'LAST':14s} {'STATUS':10s} {'MARKETS':>8s}")
    print(f"  {'-'*66}")
    for num, first, last, status, markets in rows:
        print(f"  {num:8s} {first or '':14s} {last or '':14s} {status:10s} {markets:>8,}")
    print(f"{'='*72}")


def resolve_agent(cur, agent_number):
    """Look up agent by number. Returns (service_agent_id, agent_number, agent_name) or exits."""
    cur.execute("""
        SELECT service_agent_id, agent_number, agent_name
        FROM coverage.service_agent WHERE agent_number = %s AND status = 'active'
    """, (agent_number.upper(),))
    row = cur.fetchone()
    if not row:
        print(f"  ERROR: Agent {agent_number} not found or inactive")
        sys.exit(1)
    return row


def list_markets(cur):
    """Show all coverage runs with agent info."""
    cur.execute("""
        SELECT sac.coverage_id, sac.anchor_zip, sac.radius_miles, sac.status,
               sac.created_at::date, sac.notes,
               ref.city, ref.state_id,
               sa.agent_number, sa.agent_name
        FROM coverage.service_agent_coverage sac
        JOIN reference.us_zip_codes ref ON ref.zip = sac.anchor_zip
        JOIN coverage.service_agent sa ON sa.service_agent_id = sac.service_agent_id
        ORDER BY sa.agent_number, sac.status DESC, sac.created_at DESC
    """)
    rows = cur.fetchall()
    if not rows:
        print("  No coverage runs found.")
        return

    print(f"{'='*100}")
    print(f"  COVERAGE MARKETS")
    print(f"{'='*100}")
    print(f"  {'AGENT':8s} {'STATUS':8s} {'MARKET':28s} {'RADIUS':8s} {'DATE':12s} {'COVERAGE ID'}")
    print(f"  {'-'*96}")
    for r in rows:
        cid, anchor, radius, status, dt, notes, city, state, anum, aname = r
        label = f"{anchor} ({city}, {state})"
        print(f"  {anum:8s} {status:8s} {label:28s} {str(radius)+'mi':8s} {str(dt):12s} {cid}")
        if notes:
            print(f"           {notes}")
    print(f"{'='*100}")


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


def main():
    parser = argparse.ArgumentParser(
        description="The repeatable process for working a market",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  --agents                                        List all service agents
  --create-agent "Dave Allan"                     Create a new agent (SA-002, SA-003...)
  --list                                          Show all markets
  --agent SA-001 --anchor-zip 26739 --radius 100  Scout a new market for an agent
  --coverage-id <uuid>                            Check a market
  --coverage-id <uuid> --export                   Export CSV
  --coverage-id <uuid> --activate                 Activate enrichment
  --coverage-id <uuid> --retire                   Retire a market
  --agent-dashboard SA-003                        Agent portfolio dashboard
  --agent-dashboard SA-003 --detail               Dashboard with company-level rows
        """,
    )

    # Agent management
    parser.add_argument("--agents", action="store_true", help="List all service agents")
    parser.add_argument("--create-agent", metavar="NAME", help="Create a new agent (e.g. 'Dave Allan')")
    parser.add_argument("--agent", metavar="SA-NNN", help="Agent number for new market assignment")
    parser.add_argument("--agent-dashboard", metavar="SA-NNN",
                        help="Show portfolio dashboard for an agent (e.g. SA-003)")
    parser.add_argument("--detail", action="store_true",
                        help="Show company-level rows (with --agent-dashboard)")

    # What to do
    parser.add_argument("--list", action="store_true", help="List all coverage markets")
    parser.add_argument("--coverage-id", help="Work with an existing coverage_id")
    parser.add_argument("--anchor-zip", help="5-digit anchor ZIP (scout new market)")
    parser.add_argument("--radius-miles", type=float, help="Radius in miles")
    parser.add_argument("--created-by", default="owner", help="Creator (default: owner)")
    parser.add_argument("--notes", default=None, help="Optional notes")

    # Actions
    parser.add_argument("--activate", action="store_true",
                        help="Route gaps to enrichment work queues")
    parser.add_argument("--export", action="store_true",
                        help="Export per-company CSV (outreach_id + details + sub-hub status)")
    parser.add_argument("--retire", action="store_true",
                        help="Retire this coverage run")
    parser.add_argument("--skip-dol", action="store_true",
                        help="Skip DOL gaps (expected for small employers)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview only, no DB writes")

    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    # ---- AGENTS ----
    if args.agents:
        list_agents(cur)
        conn.close()
        return

    # ---- CREATE AGENT ----
    if args.create_agent:
        num, name = create_agent(cur, args.create_agent)
        conn.commit()
        print(f"  Created agent: {num} — {name}")
        conn.close()
        return

    # ---- LIST ----
    if args.list:
        list_markets(cur)
        conn.close()
        return

    # ---- AGENT DASHBOARD ----
    if args.agent_dashboard:
        agent_id, agent_num, agent_name = resolve_agent(cur, args.agent_dashboard)
        from agent_dashboard import run_agent_dashboard
        run_agent_dashboard(cur, agent_id, agent_num, agent_name, detail=args.detail)
        conn.close()
        return

    # ---- RETIRE ----
    if args.retire:
        if not args.coverage_id:
            parser.error("--retire requires --coverage-id")
        if args.dry_run:
            print(f"  [DRY RUN] Would retire coverage_id {args.coverage_id}")
        else:
            cur.execute("""
                UPDATE coverage.service_agent_coverage
                SET status = 'retired', retired_at = NOW(), retired_by = %s
                WHERE coverage_id = %s AND status = 'active'
            """, (args.created_by, args.coverage_id))
            if cur.rowcount == 1:
                conn.commit()
                print(f"  Retired coverage_id {args.coverage_id}")
            else:
                print(f"  Nothing to retire (already retired or not found)")
        conn.close()
        return

    # ---- Determine mode ----
    new_market = bool(args.anchor_zip and args.radius_miles)
    existing = bool(args.coverage_id)

    if not new_market and not existing:
        parser.error("Provide --coverage-id OR (--anchor-zip + --radius-miles)")
    if new_market and existing:
        parser.error("Cannot provide both --coverage-id and --anchor-zip")

    start = time.time()

    # ---- STEP 1: SCOUT or REUSE ----
    print(f"{'='*75}")
    if args.dry_run:
        print(f"  COVERAGE RUN — DRY RUN")
    elif args.activate:
        print(f"  COVERAGE RUN — ACTIVATE")
    else:
        print(f"  COVERAGE RUN")
    print(f"{'='*75}")

    if new_market:
        if not ZIP_PATTERN.match(args.anchor_zip):
            print(f"  ERROR: anchor_zip must be exactly 5 digits")
            sys.exit(1)

        # Check if this exact market already exists (active)
        cur.execute("""
            SELECT sac.coverage_id, sa.agent_number, sa.agent_name
            FROM coverage.service_agent_coverage sac
            JOIN coverage.service_agent sa ON sa.service_agent_id = sac.service_agent_id
            WHERE sac.anchor_zip = %s AND sac.radius_miles = %s AND sac.status = 'active'
            LIMIT 1
        """, (args.anchor_zip, args.radius_miles))
        existing_row = cur.fetchone()

        if existing_row and not args.dry_run:
            coverage_id = existing_row[0]
            print(f"\n  Market already exists — reusing coverage_id")
            print(f"  Coverage ID: {coverage_id}")
            print(f"  Agent:       {existing_row[1]} ({existing_row[2]})")
        elif not args.dry_run:
            if not args.agent:
                parser.error("New market requires --agent SA-NNN")
            agent_id, agent_num, agent_name = resolve_agent(cur, args.agent)
            cur.execute("""
                INSERT INTO coverage.service_agent_coverage
                    (service_agent_id, anchor_zip, radius_miles, created_by, notes)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING coverage_id
            """, (agent_id, args.anchor_zip, args.radius_miles, args.created_by, args.notes))
            coverage_id = cur.fetchone()[0]
            conn.commit()
            print(f"\n  New market created")
            print(f"  Coverage ID: {coverage_id}")
            print(f"  Agent:       {agent_num} ({agent_name})")
        else:
            coverage_id = None
            print(f"\n  [DRY RUN] Would create market: {args.anchor_zip} / {args.radius_miles}mi")
    else:
        coverage_id = args.coverage_id
        cur.execute("""
            SELECT sac.anchor_zip, sac.radius_miles, sac.status,
                   sa.agent_number, sa.agent_name
            FROM coverage.service_agent_coverage sac
            JOIN coverage.service_agent sa ON sa.service_agent_id = sac.service_agent_id
            WHERE sac.coverage_id = %s
        """, (coverage_id,))
        row = cur.fetchone()
        if not row:
            print(f"  ERROR: coverage_id {coverage_id} not found")
            conn.close()
            sys.exit(1)
        print(f"\n  Coverage ID: {coverage_id}")
        print(f"  Market: {row[0]} / {row[1]}mi  Status: {row[2]}")
        print(f"  Agent:  {row[3]} ({row[4]})")

    # ---- Resolve ZIPs ----
    if coverage_id:
        radius_zips, allowed_states, anchor_zip, radius_miles, a_city, a_state = \
            resolve_from_coverage_id(cur, coverage_id)
    else:
        radius_zips, allowed_states, anchor_zip, radius_miles, a_city, a_state = \
            resolve_from_zip_radius(cur, args.anchor_zip, args.radius_miles)

    # ---- STEP 2: REPORT ----
    from coverage_report import run_report
    report = run_report(cur, radius_zips, allowed_states, anchor_zip, radius_miles,
                        a_city, a_state, coverage_id=coverage_id)

    # ---- STEP 3: EXPORT (with --export) ----
    export_path = None
    if args.export:
        print(f"\n  EXPORT")
        # Column indices:
        #  0  outreach_id      6  has_dol         11 ceo_linkedin
        #  1  company_name     7  has_blog        12 cfo_linkedin
        #  2  domain           8  ceo_filled      13 hr_linkedin
        #  3  city             9  cfo_filled      14 company_linkedin
        #  4  state           10  hr_filled
        #  5  zip
        cur.execute("""
            SELECT
                ct.outreach_id,
                ci.company_name,
                o.domain,
                TRIM(ct.city) AS city,
                TRIM(ct.state) AS state,
                LEFT(TRIM(ct.postal_code), 5) AS zip,
                CASE WHEN EXISTS (SELECT 1 FROM outreach.dol d WHERE d.outreach_id = ct.outreach_id)
                     THEN 'YES' ELSE '' END AS has_dol,
                CASE WHEN EXISTS (SELECT 1 FROM outreach.blog b WHERE b.outreach_id = ct.outreach_id)
                     THEN 'YES' ELSE '' END AS has_blog,
                CASE WHEN EXISTS (SELECT 1 FROM people.company_slot s
                     WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CEO' AND s.is_filled)
                     THEN 'YES' ELSE '' END AS ceo_filled,
                CASE WHEN EXISTS (SELECT 1 FROM people.company_slot s
                     WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CFO' AND s.is_filled)
                     THEN 'YES' ELSE '' END AS cfo_filled,
                CASE WHEN EXISTS (SELECT 1 FROM people.company_slot s
                     WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'HR' AND s.is_filled)
                     THEN 'YES' ELSE '' END AS hr_filled,
                (SELECT pm.linkedin_url FROM people.company_slot s
                     JOIN people.people_master pm ON pm.unique_id = s.person_unique_id
                     WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CEO' AND s.is_filled
                       AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != ''
                     LIMIT 1) AS ceo_linkedin,
                (SELECT pm.linkedin_url FROM people.company_slot s
                     JOIN people.people_master pm ON pm.unique_id = s.person_unique_id
                     WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'CFO' AND s.is_filled
                       AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != ''
                     LIMIT 1) AS cfo_linkedin,
                (SELECT pm.linkedin_url FROM people.company_slot s
                     JOIN people.people_master pm ON pm.unique_id = s.person_unique_id
                     WHERE s.outreach_id = ct.outreach_id AND s.slot_type = 'HR' AND s.is_filled
                       AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != ''
                     LIMIT 1) AS hr_linkedin,
                ci.linkedin_company_url AS company_linkedin
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
            JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
            WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
              AND UPPER(TRIM(ct.state)) = ANY(%s)
            ORDER BY ct.state, ct.city, ci.company_name
        """, (radius_zips, allowed_states))
        rows = cur.fetchall()

        # Write to project-level exports/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        export_dir = os.path.join(project_root, "exports")
        os.makedirs(export_dir, exist_ok=True)
        safe_zip = anchor_zip.replace(" ", "")
        safe_radius = str(int(radius_miles))
        export_path = os.path.join(export_dir, f"coverage_{safe_zip}_{safe_radius}mi.csv")

        with open(export_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "outreach_id", "company_name", "domain",
                "city", "state", "zip",
                "company_linkedin",
                "has_dol", "has_blog",
                "ceo_filled", "ceo_linkedin",
                "cfo_filled", "cfo_linkedin",
                "hr_filled", "hr_linkedin",
            ])
            for r in rows:
                writer.writerow([
                    r[0], r[1], r[2], r[3], r[4], r[5],   # company info
                    r[14] or "",                             # company linkedin
                    r[6], r[7],                              # dol, blog
                    r[8], r[11] or "",                       # ceo filled, ceo linkedin
                    r[9], r[12] or "",                       # cfo filled, cfo linkedin
                    r[10], r[13] or "",                      # hr filled, hr linkedin
                ])

        # Count completeness from market-scoped rows
        total = len(rows)
        has_dol = sum(1 for r in rows if r[6] == "YES")
        has_blog = sum(1 for r in rows if r[7] == "YES")
        has_ceo = sum(1 for r in rows if r[8] == "YES")
        has_cfo = sum(1 for r in rows if r[9] == "YES")
        has_hr = sum(1 for r in rows if r[10] == "YES")
        ceo_li = sum(1 for r in rows if r[11])
        cfo_li = sum(1 for r in rows if r[12])
        hr_li = sum(1 for r in rows if r[13])
        co_li = sum(1 for r in rows if r[14])
        all_complete = sum(1 for r in rows if r[6] == "YES" and r[7] == "YES"
                          and r[8] == "YES" and r[9] == "YES" and r[10] == "YES")

        print(f"\n  {'='*75}")
        print(f"  SUB-HUB COMPLETENESS — {anchor_zip} / {radius_miles}mi ({total:,} companies)")
        print(f"  {'='*75}")
        print(f"  {'':12s}   ── Filled ──────────    ── LinkedIn ────────")
        print(f"  {'Sub-Hub':12s} {'Have':>7s} {'Need':>7s} {'%':>5s}    {'Have':>7s} {'Need':>7s} {'%':>5s}")
        print(f"  {'-'*62}")

        table_rows = [
            ("Company",  None,     None,     co_li,  total - co_li),
            ("DOL",      has_dol,  total - has_dol,  None,   None),
            ("Blog",     has_blog, total - has_blog,  None,   None),
            ("CEO",      has_ceo,  total - has_ceo,  ceo_li, has_ceo - ceo_li),
            ("CFO",      has_cfo,  total - has_cfo,  cfo_li, has_cfo - cfo_li),
            ("HR",       has_hr,   total - has_hr,   hr_li,  has_hr - hr_li),
        ]
        for label, f_have, f_need, l_have, l_need in table_rows:
            # Filled columns
            if f_have is not None:
                f_pct = 100 * f_have / total if total > 0 else 0
                filled_str = f"{f_have:>7,} {f_need:>7,} {f_pct:>4.0f}%"
            else:
                filled_str = f"{'':>7s} {'':>7s} {'':>5s}"
            # LinkedIn columns
            if l_have is not None:
                l_base = total if f_have is None else f_have  # company vs person
                l_pct = 100 * l_have / l_base if l_base > 0 else 0
                li_str = f"{l_have:>7,} {l_need:>7,} {l_pct:>4.0f}%"
            else:
                li_str = ""
            print(f"  {label:12s} {filled_str}    {li_str}")

        print(f"  {'-'*62}")
        pct_all = 100 * all_complete / total if total > 0 else 0
        print(f"  {'ALL FILLED':12s} {all_complete:>7,} {total - all_complete:>7,} {pct_all:>4.0f}%")
        print(f"  {'='*62}")
        print(f"\n  Exported {total:,} rows -> {export_path}")

    # ---- STEP 4: ROUTE (only with --activate) ----
    gaps = None
    if args.activate:
        from route_gaps import route_gaps
        apply = not args.dry_run
        gaps = route_gaps(cur, radius_zips, allowed_states, anchor_zip, radius_miles,
                          a_city, a_state, apply=apply, skip_dol=args.skip_dol,
                          coverage_id=coverage_id)
        if apply:
            conn.commit()

    elapsed = time.time() - start

    # ---- SUMMARY ----
    # Look up agent for this coverage
    agent_label = ""
    if coverage_id:
        cur.execute("""
            SELECT sa.agent_number, sa.agent_name
            FROM coverage.service_agent_coverage sac
            JOIN coverage.service_agent sa ON sa.service_agent_id = sac.service_agent_id
            WHERE sac.coverage_id = %s
        """, (coverage_id,))
        arow = cur.fetchone()
        if arow:
            agent_label = f"{arow[0]} ({arow[1]})"

    print(f"\n  {'='*75}")
    print(f"  COVERAGE RUN COMPLETE")
    print(f"  {'='*75}")
    if coverage_id:
        print(f"    Coverage ID:    {coverage_id}")
    if agent_label:
        print(f"    Agent:          {agent_label}")
    print(f"    Market:         {anchor_zip} ({a_city}, {a_state}) / {radius_miles}mi")
    print(f"    Companies:      {report['ct_total']:,}")
    print(f"    DOL linked:     {report['dol_linked']:,}")
    print(f"    Slots filled:   {report['total_filled']:,} / {report['total_slots']:,}")
    print(f"    Work queue:     {report['unfilled']:,} slot fills")
    if gaps and not args.dry_run:
        print(f"    Gaps routed:    {gaps.get('routed', 0):,} work items")
    if export_path:
        print(f"    Export:         {export_path}")
    if not args.activate:
        print(f"    Next step:      --activate to route gaps to enrichment")
    print(f"    Time:           {elapsed:.1f}s")

    conn.close()
    print(f"\n{'='*75}")


if __name__ == "__main__":
    main()
