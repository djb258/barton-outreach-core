"""
Agent Dashboard — Portfolio view across all markets for a service agent.

Shows:
  1. Portfolio Summary — aggregate stats across all active markets
  2. Per-Market Breakdown — one row per market with sub-hub completion
  3. Company Detail (--detail) — per-company rows within each market

Usage (via run_coverage.py):
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py --agent-dashboard SA-003
    doppler run -- python hubs/coverage/imo/middle/run_coverage.py --agent-dashboard SA-003 --detail
"""

import sys


def get_agent_markets(cur, service_agent_id):
    """Fetch all active markets for an agent. Returns list of dicts."""
    cur.execute("""
        SELECT sac.coverage_id, sac.anchor_zip, sac.radius_miles,
               ref.city, ref.state_id
        FROM coverage.service_agent_coverage sac
        JOIN reference.us_zip_codes ref ON ref.zip = sac.anchor_zip
        WHERE sac.service_agent_id = %s AND sac.status = 'active'
        ORDER BY sac.created_at
    """, (service_agent_id,))
    rows = cur.fetchall()
    markets = []
    for cid, anchor_zip, radius, city, state in rows:
        markets.append({
            "coverage_id": cid,
            "anchor_zip": anchor_zip,
            "radius_miles": float(radius),
            "city": city,
            "state": state,
        })
    return markets


def resolve_market_zips(cur, coverage_id):
    """Resolve ZIPs and allowed states for a coverage_id."""
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
    return radius_zips, sorted(radius_states)


def get_market_stats(cur, radius_zips, allowed_states):
    """Per-market sub-hub stats. Returns dict with counts."""
    # CT count
    cur.execute("""
        SELECT COUNT(*)
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
    """, (radius_zips, allowed_states))
    ct_total = cur.fetchone()[0]

    # DOL linked
    cur.execute("""
        SELECT COUNT(DISTINCT ct.outreach_id)
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
          AND EXISTS (SELECT 1 FROM outreach.dol d WHERE d.outreach_id = ct.outreach_id)
    """, (radius_zips, allowed_states))
    dol_linked = cur.fetchone()[0]

    # People slots (grouped by slot_type)
    cur.execute("""
        SELECT ps.slot_type,
            COUNT(*) AS total,
            COUNT(CASE WHEN ps.is_filled THEN 1 END) AS filled
        FROM people.company_slot ps
        JOIN outreach.company_target ct ON ct.outreach_id = ps.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
        GROUP BY ps.slot_type
    """, (radius_zips, allowed_states))
    slots = {}
    for slot_type, total, filled in cur.fetchall():
        slots[slot_type] = {"total": total, "filled": filled}

    # Blog coverage (row exists in outreach.blog)
    cur.execute("""
        SELECT COUNT(DISTINCT ct.outreach_id)
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
          AND EXISTS (SELECT 1 FROM outreach.blog b WHERE b.outreach_id = ct.outreach_id)
    """, (radius_zips, allowed_states))
    blog_count = cur.fetchone()[0]

    # Blog URLs — about_url or news_url filled (OSAM: outreach.blog is CANONICAL)
    cur.execute("""
        SELECT COUNT(DISTINCT ct.outreach_id)
        FROM outreach.company_target ct
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
          AND EXISTS (
              SELECT 1 FROM outreach.blog b
              WHERE b.outreach_id = ct.outreach_id
                AND (b.about_url IS NOT NULL OR b.news_url IS NOT NULL)
          )
    """, (radius_zips, allowed_states))
    blog_url_count = cur.fetchone()[0]

    return {
        "ct_total": ct_total,
        "dol_linked": dol_linked,
        "slots": slots,
        "blog_count": blog_count,
        "blog_url_count": blog_url_count,
    }


def get_company_detail(cur, radius_zips, allowed_states):
    """Company-level rows for --detail. Uses EXISTS to avoid fan-out."""
    cur.execute("""
        SELECT ct.outreach_id, ci.company_name, o.domain,
               LEFT(TRIM(ct.postal_code), 5) AS zip,
               UPPER(TRIM(ct.state)) AS state,
               EXISTS(SELECT 1 FROM outreach.dol d WHERE d.outreach_id = ct.outreach_id) AS has_dol,
               EXISTS(SELECT 1 FROM people.company_slot cs
                      WHERE cs.outreach_id = ct.outreach_id AND cs.slot_type = 'CEO' AND cs.is_filled) AS ceo_filled,
               EXISTS(SELECT 1 FROM people.company_slot cs
                      WHERE cs.outreach_id = ct.outreach_id AND cs.slot_type = 'CFO' AND cs.is_filled) AS cfo_filled,
               EXISTS(SELECT 1 FROM people.company_slot cs
                      WHERE cs.outreach_id = ct.outreach_id AND cs.slot_type = 'HR' AND cs.is_filled) AS hr_filled,
               EXISTS(SELECT 1 FROM outreach.blog b WHERE b.outreach_id = ct.outreach_id) AS has_blog,
               EXISTS(SELECT 1 FROM outreach.blog b WHERE b.outreach_id = ct.outreach_id
                      AND (b.about_url IS NOT NULL OR b.news_url IS NOT NULL)) AS has_blog_urls
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        WHERE LEFT(TRIM(ct.postal_code), 5) = ANY(%s)
          AND UPPER(TRIM(ct.state)) = ANY(%s)
        ORDER BY ci.company_name
    """, (radius_zips, allowed_states))
    return cur.fetchall()


def _pct(num, denom):
    """Format percentage, returning '--' if denom is 0."""
    if denom == 0:
        return "--"
    return f"{100 * num / denom:.0f}%"


def _slot_filled(slots, slot_type):
    """Get filled count for a slot type, defaulting to 0."""
    return slots.get(slot_type, {}).get("filled", 0)


def print_dashboard(agent_num, agent_name, markets_data, detail_data=None):
    """Print the formatted agent dashboard."""
    W = 90

    print(f"\n{'=' * W}")
    print(f"  AGENT DASHBOARD -- {agent_num} {agent_name}")
    print(f"{'=' * W}")

    # ---- Aggregate portfolio summary ----
    total_cos = 0
    total_dol = 0
    total_ceo = 0
    total_cfo = 0
    total_hr = 0
    total_blog = 0
    total_blog_urls = 0

    for m in markets_data:
        s = m["stats"]
        total_cos += s["ct_total"]
        total_dol += s["dol_linked"]
        total_ceo += _slot_filled(s["slots"], "CEO")
        total_cfo += _slot_filled(s["slots"], "CFO")
        total_hr += _slot_filled(s["slots"], "HR")
        total_blog += s["blog_count"]
        total_blog_urls += s["blog_url_count"]

    active_markets = len(markets_data)

    print(f"\n  PORTFOLIO SUMMARY (all markets)")
    print(f"  {'_' * (W - 4)}")
    print(f"  Markets:      {active_markets} active")
    print(f"  Companies:    {total_cos:,}")
    print(f"  DOL:          {total_dol:,} / {total_cos:,}  ({_pct(total_dol, total_cos)})")
    print(f"  CEO:          {total_ceo:,} / {total_cos:,}  ({_pct(total_ceo, total_cos)})")
    print(f"  CFO:          {total_cfo:,} / {total_cos:,}  ({_pct(total_cfo, total_cos)})")
    print(f"  HR:           {total_hr:,} / {total_cos:,}  ({_pct(total_hr, total_cos)})")
    print(f"  Blog:         {total_blog:,} / {total_cos:,}  ({_pct(total_blog, total_cos)})")
    print(f"  Blog URLs:    {total_blog_urls:,} / {total_cos:,}  ({_pct(total_blog_urls, total_cos)})")

    # ---- Per-market breakdown ----
    print(f"\n  PER-MARKET BREAKDOWN")
    hdr = (f"  {'MARKET':<24s} {'COS':>6s}  {'DOL%':>5s}  {'CEO%':>5s}  "
           f"{'CFO%':>5s}  {'HR%':>5s}  {'BLOG':>5s}  {'URLs':>5s}  COVERAGE ID")
    print(f"  {'-' * (W - 4)}")
    print(hdr)
    print(f"  {'-' * (W - 4)}")

    for m in markets_data:
        s = m["stats"]
        ct = s["ct_total"]
        label = f"{m['anchor_zip']}/{int(m['radius_miles'])}mi ({m['city'][:8]}, {m['state']})"
        ceo_f = _slot_filled(s["slots"], "CEO")
        cfo_f = _slot_filled(s["slots"], "CFO")
        hr_f = _slot_filled(s["slots"], "HR")

        row = (f"  {label:<24s} {ct:>6,}  {_pct(s['dol_linked'], ct):>5s}  "
               f"{_pct(ceo_f, ct):>5s}  {_pct(cfo_f, ct):>5s}  "
               f"{_pct(hr_f, ct):>5s}  {_pct(s['blog_count'], ct):>5s}  "
               f"{_pct(s['blog_url_count'], ct):>5s}  {m['coverage_id']}")
        print(row)

    print(f"  {'-' * (W - 4)}")
    print(f"{'=' * W}")

    # ---- Company detail (optional) ----
    if detail_data:
        for m in markets_data:
            rows = detail_data.get(str(m["coverage_id"]), [])
            if not rows:
                continue
            label = f"{m['anchor_zip']}/{int(m['radius_miles'])}mi"
            print(f"\n  COMPANY DETAIL -- {label} ({len(rows):,} companies)")
            dhdr = (f"  {'COMPANY':<38s} {'DOMAIN':<24s} "
                    f"{'DOL':>4s} {'CEO':>4s} {'CFO':>4s} {'HR':>4s} {'BLOG':>5s} {'URLs':>5s}")
            print(f"  {'-' * (W - 4)}")
            print(dhdr)
            print(f"  {'-' * (W - 4)}")

            yn = {True: "Y", False: "N"}
            for r in rows:
                # r: outreach_id, company_name, domain, zip, state, has_dol, ceo, cfo, hr, blog, blog_urls
                name = (r[1] or "")[:36]
                domain = (r[2] or "")[:22]
                print(f"  {name:<38s} {domain:<24s} "
                      f"{yn[r[5]]:>4s} {yn[r[6]]:>4s} {yn[r[7]]:>4s} "
                      f"{yn[r[8]]:>4s} {yn[r[9]]:>5s} {yn[r[10]]:>5s}")

            print(f"  {'-' * (W - 4)}")
        print(f"{'=' * W}")


def run_agent_dashboard(cur, service_agent_id, agent_num, agent_name, detail=False):
    """Main entry point — fetch markets, compute stats, print dashboard."""
    markets = get_agent_markets(cur, service_agent_id)
    if not markets:
        print(f"\n  {agent_num} {agent_name} has no active markets.")
        return

    markets_data = []
    detail_data = {}

    for m in markets:
        zips, states = resolve_market_zips(cur, m["coverage_id"])
        if not zips:
            # Empty market (no ZIPs resolved) — skip with zero stats
            m["stats"] = {
                "ct_total": 0, "dol_linked": 0, "slots": {},
                "blog_count": 0, "blog_url_count": 0,
            }
            markets_data.append(m)
            continue

        stats = get_market_stats(cur, zips, states)
        m["stats"] = stats
        markets_data.append(m)

        if detail:
            rows = get_company_detail(cur, zips, states)
            detail_data[str(m["coverage_id"])] = rows

    print_dashboard(agent_num, agent_name, markets_data,
                    detail_data=detail_data if detail else None)
