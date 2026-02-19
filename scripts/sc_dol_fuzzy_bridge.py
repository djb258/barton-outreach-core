#!/usr/bin/env python3
"""
SC DOL Fuzzy Bridge — Match remaining SC companies to DOL filings.

Uses PostgreSQL pg_trgm for name similarity, confirmed by geography + domain.

Tiers (cumulative, each excludes prior matches):
  T1: Domain bridge (ein_urls domain match)                    HIGHEST
  T2: Fuzzy name (>=0.5) + same state + same ZIP              HIGH
  T3: Fuzzy name (>=0.4) + same state + same city             MEDIUM
  T4: Fuzzy name (>=0.3) + same state + same ZIP              LOWER

Signals used: ZIP, city, domain, fuzzy name.
NOT used: street address (one number off = false negative).

Usage:
    doppler run -- python scripts/sc_dol_fuzzy_bridge.py
    doppler run -- python scripts/sc_dol_fuzzy_bridge.py --apply
    doppler run -- python scripts/sc_dol_fuzzy_bridge.py --apply --max-tier 2
"""
import argparse
import os
import sys
import io
import time
import uuid

import psycopg2

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def norm_name_sql(col):
    """SQL expression to normalize a company name: uppercase, strip suffixes, remove punctuation."""
    return (
        f"UPPER(REGEXP_REPLACE(REGEXP_REPLACE(TRIM({col}), "
        r"E'\\s*(,?\\s*(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO|LTD|LIMITED|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$', '', 'i'), "
        "'[^A-Za-z0-9 ]', '', 'g'))"
    )


def get_conn():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def derive_funding_type(pension_code, welfare_code, fund_ins, fund_trust):
    """Derive funding_type from form_5500 fields."""
    if pension_code and not welfare_code:
        return 'pension_only'
    if fund_trust == '1':
        return 'self_funded'
    if fund_ins == '1' and (not fund_trust or fund_trust == '0'):
        return 'fully_insured'
    return 'unknown'


def main():
    parser = argparse.ArgumentParser(description="SC DOL fuzzy bridge")
    parser.add_argument("--apply", action="store_true", help="Apply matches to outreach.dol")
    parser.add_argument("--max-tier", type=int, default=3,
                        help="Max tier to apply (1-4, default=3)")
    args = parser.parse_args()

    conn = get_conn()
    cur = conn.cursor()

    print(f"{'=' * 70}")
    print(f"  SC DOL FUZZY BRIDGE {'— APPLY MODE' if args.apply else '— DRY RUN'}")
    print(f"  Max tier: {args.max_tier}")
    print(f"  Signals: ZIP + city + domain + fuzzy name")
    print(f"  NOT using: street address")
    print(f"{'=' * 70}")

    # Ensure pg_trgm
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
    if not cur.fetchone():
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        conn.commit()

    start = time.time()

    # ================================================================
    # Build SC no-DOL set
    # ================================================================
    cl_norm = norm_name_sql("ci.company_name")
    cur.execute(f"""
        CREATE TEMP TABLE tmp_sc_no_dol AS
        SELECT
            ct.outreach_id,
            ci.company_domain AS domain,
            {cl_norm} AS company_name_norm,
            UPPER(TRIM(ci.company_name)) AS company_name_raw,
            LEFT(TRIM(ct.postal_code), 5) AS zip5,
            UPPER(TRIM(ct.city)) AS city,
            UPPER(TRIM(ct.state)) AS state
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        WHERE ci.state_code = 'SC'
          AND d.outreach_id IS NULL
    """)
    cur.execute("SELECT COUNT(*) FROM tmp_sc_no_dol")
    no_dol = cur.fetchone()[0]
    print(f"\n  SC companies without DOL: {no_dol:,}")

    cur.execute("SELECT COUNT(*) FROM tmp_sc_no_dol WHERE zip5 IS NOT NULL AND zip5 <> ''")
    with_zip = cur.fetchone()[0]
    print(f"  With ZIP:                 {with_zip:,}")

    cur.execute("SELECT COUNT(*) FROM tmp_sc_no_dol WHERE city IS NOT NULL AND city <> ''")
    with_city = cur.fetchone()[0]
    print(f"  With city:                {with_city:,}")

    cur.execute("SELECT COUNT(*) FROM tmp_sc_no_dol WHERE domain IS NOT NULL AND domain <> ''")
    with_domain = cur.fetchone()[0]
    print(f"  With domain:              {with_domain:,}")

    # ================================================================
    # Build DOL sponsor set (SC + neighboring states for edge cases)
    # ================================================================
    f5500_norm = norm_name_sql("sponsor_dfe_name")
    sf_norm = norm_name_sql("sf_sponsor_name")
    cur.execute(f"""
        CREATE TEMP TABLE tmp_sponsors AS
        WITH all_sponsors AS (
            SELECT sponsor_dfe_ein AS ein,
                UPPER(TRIM(sponsor_dfe_name)) AS sponsor_name,
                {f5500_norm} AS name_norm,
                LEFT(TRIM(spons_dfe_mail_us_zip), 5) AS zip5,
                UPPER(TRIM(spons_dfe_mail_us_city)) AS city,
                UPPER(TRIM(spons_dfe_mail_us_state)) AS state,
                form_plan_year_begin_date::date AS plan_begin,
                type_pension_bnft_code AS pension_code,
                type_welfare_bnft_code AS welfare_code,
                funding_insurance_ind AS fund_ins,
                funding_trust_ind AS fund_trust
            FROM dol.form_5500
            WHERE UPPER(TRIM(spons_dfe_mail_us_state)) IN ('SC', 'NC', 'GA')
              AND sponsor_dfe_ein IS NOT NULL
              AND sponsor_dfe_name IS NOT NULL

            UNION ALL

            SELECT sf_spons_ein AS ein,
                UPPER(TRIM(sf_sponsor_name)) AS sponsor_name,
                {sf_norm} AS name_norm,
                LEFT(TRIM(sf_spons_us_zip), 5) AS zip5,
                UPPER(TRIM(sf_spons_us_city)) AS city,
                UPPER(TRIM(sf_spons_us_state)) AS state,
                sf_plan_year_begin_date::date AS plan_begin,
                sf_type_pension_bnft_code AS pension_code,
                sf_type_welfare_bnft_code AS welfare_code,
                NULL AS fund_ins,
                NULL AS fund_trust
            FROM dol.form_5500_sf
            WHERE UPPER(TRIM(sf_spons_us_state)) IN ('SC', 'NC', 'GA')
              AND sf_spons_ein IS NOT NULL
              AND sf_sponsor_name IS NOT NULL
        )
        SELECT DISTINCT ON (ein)
            ein, sponsor_name, name_norm, zip5, city, state,
            plan_begin, pension_code, welfare_code, fund_ins, fund_trust
        FROM all_sponsors
        WHERE LENGTH(name_norm) >= 2
        ORDER BY ein, plan_begin DESC NULLS LAST
    """)

    # Remove EINs already in outreach.dol (from the exact match pass)
    cur.execute("""
        DELETE FROM tmp_sponsors
        WHERE ein IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
    """)
    cur.execute("SELECT COUNT(*) FROM tmp_sponsors")
    sponsors = cur.fetchone()[0]
    print(f"\n  Available DOL sponsors (SC/NC/GA): {sponsors:,}")

    # Indexes for performance
    for stmt in [
        "CREATE INDEX idx_s_state ON tmp_sponsors(state)",
        "CREATE INDEX idx_s_zip ON tmp_sponsors(zip5)",
        "CREATE INDEX idx_s_city ON tmp_sponsors(city)",
        "CREATE INDEX idx_s_name ON tmp_sponsors(name_norm)",
        "CREATE INDEX idx_s_trgm ON tmp_sponsors USING gin(name_norm gin_trgm_ops)",
        "CREATE INDEX idx_n_zip ON tmp_sc_no_dol(zip5)",
        "CREATE INDEX idx_n_city ON tmp_sc_no_dol(city)",
        "CREATE INDEX idx_n_domain ON tmp_sc_no_dol(LOWER(domain))",
    ]:
        cur.execute(stmt)

    print(f"  Setup: {time.time()-start:.1f}s")

    # ================================================================
    # Match results table
    # ================================================================
    cur.execute("""
        CREATE TEMP TABLE tmp_matches (
            outreach_id UUID,
            ein TEXT,
            sponsor_name TEXT,
            tier INT,
            similarity NUMERIC(4,2),
            match_method TEXT,
            plan_begin DATE,
            pension_code TEXT,
            welfare_code TEXT,
            fund_ins TEXT,
            fund_trust TEXT
        )
    """)

    def name_sim(threshold):
        return f"(LENGTH(nd.company_name_norm) >= 3 AND similarity(nd.company_name_norm, s.name_norm) >= {threshold})"

    def best_sim():
        return "CASE WHEN LENGTH(nd.company_name_norm) >= 3 THEN similarity(nd.company_name_norm, s.name_norm) ELSE 0 END"

    # ── T1: Domain bridge via ein_urls ──
    print(f"\n  T1: Domain bridge (ein_urls) ...", end=" ", flush=True)
    cur.execute("""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, eu.ein, s.sponsor_name, 1, 1.00::numeric(4,2), 'domain_bridge',
            s.plan_begin::date, s.pension_code, s.welfare_code, s.fund_ins, s.fund_trust
        FROM tmp_sc_no_dol nd
        JOIN dol.ein_urls eu ON LOWER(nd.domain) = LOWER(eu.domain)
        LEFT JOIN tmp_sponsors s ON s.ein = eu.ein
        WHERE nd.domain IS NOT NULL AND nd.domain <> ''
        ORDER BY nd.outreach_id, eu.ein
    """)
    t1 = cur.rowcount
    print(f"{t1:,}")

    # ── T2: Fuzzy name (>=0.5) + same ZIP ──
    print(f"  T2: Fuzzy (>=0.5) + ZIP ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 2, {best_sim()}, 'fuzzy_zip',
            s.plan_begin, s.pension_code, s.welfare_code, s.fund_ins, s.fund_trust
        FROM tmp_sc_no_dol nd
        JOIN tmp_sponsors s ON nd.zip5 = s.zip5 AND {name_sim(0.5)}
        WHERE nd.zip5 IS NOT NULL AND nd.zip5 <> ''
          AND LENGTH(s.name_norm) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matches)
        ORDER BY nd.outreach_id, {best_sim()} DESC
    """)
    t2 = cur.rowcount
    print(f"{t2:,}")

    # ── T3: Fuzzy name (>=0.4) + same city + same state ──
    print(f"  T3: Fuzzy (>=0.4) + city + state ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 3, {best_sim()}, 'fuzzy_city',
            s.plan_begin, s.pension_code, s.welfare_code, s.fund_ins, s.fund_trust
        FROM tmp_sc_no_dol nd
        JOIN tmp_sponsors s ON nd.city = s.city AND nd.state = s.state AND {name_sim(0.4)}
        WHERE nd.city IS NOT NULL AND nd.city <> ''
          AND LENGTH(s.name_norm) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matches)
        ORDER BY nd.outreach_id, {best_sim()} DESC
    """)
    t3 = cur.rowcount
    print(f"{t3:,}")

    # ── T4: Fuzzy name (>=0.3) + same ZIP (looser name, tight geography) ──
    print(f"  T4: Fuzzy (>=0.3) + ZIP ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 4, {best_sim()}, 'fuzzy_zip_loose',
            s.plan_begin, s.pension_code, s.welfare_code, s.fund_ins, s.fund_trust
        FROM tmp_sc_no_dol nd
        JOIN tmp_sponsors s ON nd.zip5 = s.zip5 AND {name_sim(0.3)}
        WHERE nd.zip5 IS NOT NULL AND nd.zip5 <> ''
          AND LENGTH(s.name_norm) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matches)
        ORDER BY nd.outreach_id, {best_sim()} DESC
    """)
    t4 = cur.rowcount
    print(f"{t4:,}")

    total = t1 + t2 + t3 + t4
    elapsed = time.time() - start

    # ── Samples per tier ──
    for tier, label in [(1, "Domain bridge"), (2, "Fuzzy+ZIP"), (3, "Fuzzy+city"), (4, "Fuzzy+ZIP loose")]:
        cur.execute("""
            SELECT nd.company_name_raw, m.sponsor_name, m.ein, m.similarity,
                   nd.zip5, nd.city
            FROM tmp_matches m
            JOIN tmp_sc_no_dol nd ON nd.outreach_id = m.outreach_id
            WHERE m.tier = %s
            ORDER BY m.similarity DESC
            LIMIT 10
        """, (tier,))
        rows = cur.fetchall()
        if rows:
            print(f"\n  T{tier} samples ({label}):")
            for company, sponsor, ein, sim, zip5, city in rows:
                print(f"    {(company or '')[:35]:<37s} -> {(sponsor or '')[:35]:<37s} sim={float(sim):.2f} {zip5 or ''} {city or ''}")

    # ── Summary ──
    cur.execute("SELECT COUNT(*) FROM outreach.dol")
    current_dol = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tmp_matches WHERE tier <= %s", (args.max_tier,))
    apply_count = cur.fetchone()[0]

    print(f"\n  {'=' * 65}")
    print(f"  SUMMARY")
    print(f"  {'=' * 65}")
    print(f"    T1 domain bridge:               {t1:>6,}")
    print(f"    T2 fuzzy(>=0.5) + ZIP:          {t2:>6,}")
    print(f"    T3 fuzzy(>=0.4) + city + state: {t3:>6,}")
    print(f"    T4 fuzzy(>=0.3) + ZIP:          {t4:>6,}")
    print(f"    {'─' * 40}")
    print(f"    Total found:                    {total:>6,}")
    print(f"    Applying (tier <= {args.max_tier}):           {apply_count:>6,}")
    print(f"")
    print(f"    Current SC DOL:  {current_dol:,}")
    print(f"    + new matches:   {apply_count:,}")
    print(f"    Time: {elapsed:.1f}s")

    # ================================================================
    # APPLY
    # ================================================================
    if not args.apply:
        print(f"\n  [DRY RUN] Add --apply to insert into outreach.dol")
        conn.close()
        return

    print(f"\n  Inserting {apply_count:,} DOL records (tier <= {args.max_tier})...")

    # Load carrier data
    cur.execute("""
        SELECT DISTINCT ON (sch_a_ein)
               sch_a_ein, ins_carrier_name
        FROM dol.schedule_a
        WHERE ins_carrier_name IS NOT NULL AND ins_carrier_name <> ''
        ORDER BY sch_a_ein, ack_id DESC
    """)
    carriers = {ein: carrier for ein, carrier in cur.fetchall()}

    cur.execute("""
        SELECT m.outreach_id, m.ein, m.plan_begin,
               m.pension_code, m.welfare_code, m.fund_ins, m.fund_trust
        FROM tmp_matches m
        WHERE m.tier <= %s
    """, (args.max_tier,))
    rows = cur.fetchall()

    inserted = 0
    errors = 0
    for oid, ein, plan_begin, pension, welfare, fund_ins, fund_trust in rows:
        funding_type = derive_funding_type(pension, welfare, fund_ins, fund_trust)

        renewal_month = None
        outreach_start_month = None
        if plan_begin:
            try:
                renewal_month = plan_begin.month
                outreach_start_month = ((renewal_month - 5 - 1) % 12) + 1
            except Exception:
                pass

        carrier = carriers.get(ein)

        try:
            dol_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO outreach.dol
                    (dol_id, outreach_id, ein, filing_present, funding_type,
                     carrier, renewal_month, outreach_start_month,
                     created_at, updated_at)
                SELECT %s, %s, %s, TRUE, %s, %s, %s, %s, NOW(), NOW()
                WHERE NOT EXISTS (
                    SELECT 1 FROM outreach.dol WHERE outreach_id = %s
                )
            """, (
                dol_id, oid, ein, funding_type, carrier,
                renewal_month, outreach_start_month, oid,
            ))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"    ERROR for {oid}: {e}")
            conn.rollback()
            errors += 1

    conn.commit()
    print(f"\n  APPLIED: {inserted:,} new DOL bridge records")
    print(f"  Errors:  {errors:,}")

    # Final status
    try:
        conn.close()
    except Exception:
        pass
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*),
               COUNT(CASE WHEN EXISTS (
                   SELECT 1 FROM outreach.dol d WHERE d.outreach_id = o.outreach_id
               ) THEN 1 END)
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON ci.company_unique_id = o.sovereign_id
        WHERE ci.state_code = 'SC'
    """)
    total_sc, with_dol = cur.fetchone()

    print(f"\n  FINAL SC DOL STATUS:")
    print(f"    Total SC:       {total_sc:,}")
    print(f"    With DOL:       {with_dol:,} ({100*with_dol/max(1,total_sc):.1f}%)")
    print(f"    Without DOL:    {total_sc - with_dol:,}")
    print(f"  {'=' * 65}")

    conn.close()


if __name__ == "__main__":
    main()
