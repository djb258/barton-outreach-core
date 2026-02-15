"""
DOL Fuzzy Bridge — Match unlinked CT companies to Form 5500 EINs.

Uses correct columns:
  form_5500:    sponsor_dfe_name + sponsor_dfe_ein
  form_5500_sf: sf_sponsor_name  + sf_spons_ein

Multi-signal matching (CL name + Hunter org name) against DOL sponsors,
confirmed by geography (state, ZIP, city).

Tiers:
  T1: Exact normalized name + state           HIGH
  T2: Trigram (>=0.5) + state + ZIP           HIGH
  T3: Trigram (>=0.4) + state + city          MEDIUM
  T4: Trigram (>=0.3) + state + city          LOW

Usage:
    doppler run -- python scripts/dol_fuzzy_bridge.py
    doppler run -- python scripts/dol_fuzzy_bridge.py --apply
    doppler run -- python scripts/dol_fuzzy_bridge.py --apply --min-tier 2  # T1+T2 only
"""

import argparse
import os
import sys
import time

import psycopg2
from psycopg2.extras import execute_values

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

SUFFIX_SQL = r"\s*(,?\s*(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO|LTD|LIMITED|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$"


def norm_name_sql(col):
    """Return SQL expression that normalizes a company name column."""
    return f"UPPER(REGEXP_REPLACE(REGEXP_REPLACE(TRIM({col}), E'\\\\s*(,?\\\\s*(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO|LTD|LIMITED|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\\\.))+\\\\s*$', '', 'i'), '[^A-Za-z0-9 ]', '', 'g'))"


def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        dbname=os.environ["NEON_DATABASE"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
    )


def main():
    parser = argparse.ArgumentParser(description="DOL fuzzy bridge")
    parser.add_argument("--apply", action="store_true", help="Apply matches to outreach.dol")
    parser.add_argument("--min-tier", type=int, default=4, help="Max tier to apply (1-4, default=4)")
    args = parser.parse_args()

    conn = get_connection()
    cur = conn.cursor()

    print(f"{'='*75}")
    print(f"  DOL Fuzzy Bridge {'— APPLY MODE' if args.apply else '— DRY RUN'}")
    print(f"  Max tier: {args.min_tier}")
    print(f"{'='*75}")

    # Ensure pg_trgm
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
    if not cur.fetchone():
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        conn.commit()

    start = time.time()

    # ================================================================
    # Build no-DOL set (CL name + Hunter org name)
    # ================================================================
    cl_norm = norm_name_sql("ci.company_name")
    hunter_norm = norm_name_sql("COALESCE(hc.organization, '')")
    cur.execute(f"""
        CREATE TEMP TABLE tmp_no_dol AS
        SELECT DISTINCT ON (ct.outreach_id)
            ct.outreach_id,
            o.domain,
            {cl_norm} AS cl_name,
            {hunter_norm} AS hunter_name,
            LEFT(TRIM(ct.postal_code), 5) AS zip5,
            UPPER(TRIM(ct.city)) AS city,
            UPPER(TRIM(ct.state)) AS state
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        LEFT JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
        WHERE d.outreach_id IS NULL
        ORDER BY ct.outreach_id, hc.data_quality_score DESC NULLS LAST
    """)
    cur.execute("SELECT COUNT(*) FROM tmp_no_dol")
    no_dol = cur.fetchone()[0]
    print(f"\n  No-DOL companies: {no_dol:,}")

    # ================================================================
    # Build DOL sponsor set (CORRECT columns)
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
                UPPER(TRIM(spons_dfe_mail_us_state)) AS state
            FROM dol.form_5500
            WHERE sponsor_dfe_ein IS NOT NULL AND sponsor_dfe_name IS NOT NULL

            UNION

            SELECT sf_spons_ein AS ein,
                UPPER(TRIM(sf_sponsor_name)) AS sponsor_name,
                {sf_norm} AS name_norm,
                LEFT(TRIM(sf_spons_us_zip), 5) AS zip5,
                UPPER(TRIM(sf_spons_us_city)) AS city,
                UPPER(TRIM(sf_spons_us_state)) AS state
            FROM dol.form_5500_sf
            WHERE sf_spons_ein IS NOT NULL AND sf_sponsor_name IS NOT NULL
        )
        SELECT DISTINCT ON (ein)
            ein, sponsor_name, name_norm, zip5, city, state
        FROM all_sponsors
        WHERE LENGTH(name_norm) >= 2
        ORDER BY ein, sponsor_name
    """)

    # Remove EINs already bridged
    cur.execute("""
        DELETE FROM tmp_sponsors
        WHERE ein IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
    """)
    cur.execute("SELECT COUNT(*) FROM tmp_sponsors")
    sponsors = cur.fetchone()[0]
    print(f"  Available DOL sponsors: {sponsors:,}")

    # Indexes
    for stmt in [
        "CREATE INDEX idx_s_state ON tmp_sponsors(state)",
        "CREATE INDEX idx_s_zip ON tmp_sponsors(zip5)",
        "CREATE INDEX idx_s_city ON tmp_sponsors(city)",
        "CREATE INDEX idx_s_name ON tmp_sponsors(name_norm)",
        "CREATE INDEX idx_s_trgm ON tmp_sponsors USING gin(name_norm gin_trgm_ops)",
        "CREATE INDEX idx_n_state ON tmp_no_dol(state)",
        "CREATE INDEX idx_n_zip ON tmp_no_dol(zip5)",
        "CREATE INDEX idx_n_city ON tmp_no_dol(city)",
    ]:
        cur.execute(stmt)

    print(f"  Setup: {time.time()-start:.1f}s")

    # ================================================================
    # Collect matches into a results table
    # ================================================================
    cur.execute("""
        CREATE TEMP TABLE tmp_matches (
            outreach_id UUID,
            ein TEXT,
            sponsor_name TEXT,
            tier INT,
            similarity NUMERIC(4,2),
            match_source TEXT
        )
    """)

    # Helper: name match condition (either CL or Hunter name)
    def name_exact():
        return """(
            (LENGTH(nd.cl_name) >= 3 AND nd.cl_name = s.name_norm)
            OR (LENGTH(nd.hunter_name) >= 3 AND nd.hunter_name = s.name_norm)
        )"""

    def name_sim(threshold):
        return f"""(
            (LENGTH(nd.cl_name) >= 3 AND similarity(nd.cl_name, s.name_norm) >= {threshold})
            OR (LENGTH(nd.hunter_name) >= 3 AND similarity(nd.hunter_name, s.name_norm) >= {threshold})
        )"""

    def best_sim():
        return """GREATEST(
            CASE WHEN LENGTH(nd.cl_name) >= 3 THEN similarity(nd.cl_name, s.name_norm) ELSE 0 END,
            CASE WHEN LENGTH(nd.hunter_name) >= 3 THEN similarity(nd.hunter_name, s.name_norm) ELSE 0 END
        )"""

    # T1: Exact name + state
    print(f"\n  T1: Exact name + state ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 1, 1.00,
            CASE WHEN LENGTH(nd.cl_name) >= 3 AND nd.cl_name = s.name_norm THEN 'CL' ELSE 'HUNTER' END
        FROM tmp_no_dol nd
        JOIN tmp_sponsors s ON nd.state = s.state AND {name_exact()}
        WHERE LENGTH(s.name_norm) >= 3
        ORDER BY nd.outreach_id, s.ein
    """)
    t1 = cur.rowcount
    print(f"{t1:,}")

    # T2: Trigram >= 0.5 + state + ZIP
    print(f"  T2: Fuzzy (>=0.5) + state + ZIP ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 2, {best_sim()},
            CASE WHEN LENGTH(nd.cl_name) >= 3 AND similarity(nd.cl_name, s.name_norm) >= 0.5 THEN 'CL' ELSE 'HUNTER' END
        FROM tmp_no_dol nd
        JOIN tmp_sponsors s ON nd.state = s.state AND nd.zip5 = s.zip5 AND {name_sim(0.5)}
        WHERE LENGTH(s.name_norm) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matches)
        ORDER BY nd.outreach_id, {best_sim()} DESC
    """)
    t2 = cur.rowcount
    print(f"{t2:,}")

    # T3: Trigram >= 0.4 + state + city
    print(f"  T3: Fuzzy (>=0.4) + state + city ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 3, {best_sim()},
            CASE WHEN LENGTH(nd.cl_name) >= 3 AND similarity(nd.cl_name, s.name_norm) >= 0.4 THEN 'CL' ELSE 'HUNTER' END
        FROM tmp_no_dol nd
        JOIN tmp_sponsors s ON nd.state = s.state AND nd.city = s.city AND {name_sim(0.4)}
        WHERE LENGTH(s.name_norm) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matches)
        ORDER BY nd.outreach_id, {best_sim()} DESC
    """)
    t3 = cur.rowcount
    print(f"{t3:,}")

    # T4: Trigram >= 0.3 + state + city
    print(f"  T4: Fuzzy (>=0.3) + state + city ...", end=" ", flush=True)
    cur.execute(f"""
        INSERT INTO tmp_matches
        SELECT DISTINCT ON (nd.outreach_id)
            nd.outreach_id, s.ein, s.sponsor_name, 4, {best_sim()},
            CASE WHEN LENGTH(nd.cl_name) >= 3 AND similarity(nd.cl_name, s.name_norm) >= 0.3 THEN 'CL' ELSE 'HUNTER' END
        FROM tmp_no_dol nd
        JOIN tmp_sponsors s ON nd.state = s.state AND nd.city = s.city AND {name_sim(0.3)}
        WHERE LENGTH(s.name_norm) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matches)
        ORDER BY nd.outreach_id, {best_sim()} DESC
    """)
    t4 = cur.rowcount
    print(f"{t4:,}")

    total = t1 + t2 + t3 + t4
    elapsed = time.time() - start

    # Samples per tier
    for tier in range(1, 5):
        cur.execute("""
            SELECT nd.domain, m.sponsor_name, m.ein, m.similarity, m.match_source, nd.state
            FROM tmp_matches m
            JOIN tmp_no_dol nd ON nd.outreach_id = m.outreach_id
            WHERE m.tier = %s
            ORDER BY m.similarity DESC
            LIMIT 8
        """, (tier,))
        rows = cur.fetchall()
        if rows:
            print(f"\n  T{tier} samples:")
            for r in rows:
                print(f"    {r[0]:28s} -> {(r[1] or '')[:28]:28s} EIN={r[2]} sim={r[3]:.2f} via={r[4]} {r[5]}")

    # Current state
    cur.execute("SELECT COUNT(*) FROM outreach.dol")
    current_dol = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM outreach.company_target")
    ct_total = cur.fetchone()[0]

    # How many match up to min_tier
    cur.execute("SELECT COUNT(*) FROM tmp_matches WHERE tier <= %s", (args.min_tier,))
    apply_count = cur.fetchone()[0]

    print(f"\n  {'='*75}")
    print(f"  SUMMARY")
    print(f"  {'='*75}")
    print(f"    T1 exact name+state:        {t1:>6,}")
    print(f"    T2 fuzzy(>=0.5)+state+zip:  {t2:>6,}")
    print(f"    T3 fuzzy(>=0.4)+state+city: {t3:>6,}")
    print(f"    T4 fuzzy(>=0.3)+state+city: {t4:>6,}")
    print(f"    ─────────────────────────────────")
    print(f"    Total:                      {total:>6,}")
    print(f"    Applying (tier <= {args.min_tier}):       {apply_count:>6,}")
    print(f"")
    print(f"    Current DOL:  {current_dol:,} / {ct_total:,} ({100*current_dol/ct_total:.1f}%)")
    print(f"    Projected:    {current_dol + apply_count:,} / {ct_total:,} ({100*(current_dol+apply_count)/ct_total:.1f}%)")
    print(f"    Time: {elapsed:.1f}s")

    # ================================================================
    # APPLY
    # ================================================================
    if not args.apply:
        print(f"\n  [DRY RUN] Add --apply to insert into outreach.dol")
        conn.close()
        return

    # Insert into outreach.dol
    cur.execute("""
        SELECT m.outreach_id, m.ein, m.tier, m.similarity
        FROM tmp_matches m
        WHERE m.tier <= %s
    """, (args.min_tier,))
    rows = cur.fetchall()

    inserted = 0
    for oid, ein, tier, sim in rows:
        cur.execute("""
            INSERT INTO outreach.dol (outreach_id, ein, filing_present, funding_type, created_at)
            SELECT %s, %s,
                CASE WHEN EXISTS (
                    SELECT 1 FROM dol.form_5500 WHERE sponsor_dfe_ein = %s
                    UNION ALL
                    SELECT 1 FROM dol.form_5500_sf WHERE sf_spons_ein = %s
                ) THEN TRUE ELSE FALSE END,
                'unknown',
                NOW()
            WHERE NOT EXISTS (SELECT 1 FROM outreach.dol WHERE outreach_id = %s)
        """, (oid, ein, ein, ein, oid))
        inserted += cur.rowcount

    conn.commit()
    print(f"\n  APPLIED: {inserted:,} new DOL bridge records")

    # Verify
    cur.execute("SELECT COUNT(*) FROM outreach.dol")
    new_dol = cur.fetchone()[0]
    print(f"  DOL total now: {new_dol:,} / {ct_total:,} ({100*new_dol/ct_total:.1f}%)")

    conn.close()
    print(f"\n{'='*75}")
    print(f"  Done.")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
