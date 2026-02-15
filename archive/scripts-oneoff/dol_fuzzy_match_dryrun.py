"""
DOL EIN Fuzzy Match — Dry Run

Multi-signal matching to find DOL Form 5500 EINs for CT companies
that don't have a DOL bridge yet.

Matching tiers (highest confidence first):
  T1: Exact normalized name + state
  T2: Domain keyword in sponsor name + state + ZIP
  T3: Trigram similarity (>=0.4) + ZIP match
  T4: Trigram similarity (>=0.3) + state match + city match

Usage:
    doppler run -- python scripts/dol_fuzzy_match_dryrun.py
"""

import os
import re
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
    conn = get_connection()
    cur = conn.cursor()

    print(f"{'='*75}")
    print(f"  DOL EIN Fuzzy Match — Dry Run")
    print(f"{'='*75}")

    # ================================================================
    # Check if pg_trgm extension is available
    # ================================================================
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
    has_trgm = cur.fetchone() is not None
    if not has_trgm:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        conn.commit()
        print("\n  Enabled pg_trgm extension")
    else:
        print("\n  pg_trgm extension: available")

    # ================================================================
    # Build the no-DOL CT company set
    # ================================================================
    start = time.time()

    cur.execute("""
        CREATE TEMP TABLE tmp_no_dol AS
        SELECT
            ct.outreach_id,
            ci.company_name,
            -- Normalize: uppercase, strip suffixes
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(ci.company_name),
                    '\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                    '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS name_normalized,
            o.domain,
            -- Extract meaningful domain keyword (strip TLD and common words)
            UPPER(REGEXP_REPLACE(
                SPLIT_PART(o.domain, '.', 1),
                '(group|inc|corp|llc|co|the|my|get|go|try|use|app)', '', 'gi'
            )) AS domain_keyword,
            LEFT(TRIM(ct.postal_code), 5) AS zip5,
            UPPER(TRIM(ct.city)) AS city,
            UPPER(TRIM(ct.state)) AS state,
            ct.employees
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        WHERE d.outreach_id IS NULL
    """)

    cur.execute("SELECT COUNT(*) FROM tmp_no_dol")
    no_dol_count = cur.fetchone()[0]
    print(f"\n  No-DOL CT companies: {no_dol_count:,}")

    # Employee breakdown
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE employees >= 100) AS large,
            COUNT(*) FILTER (WHERE employees BETWEEN 25 AND 99) AS mid,
            COUNT(*) FILTER (WHERE employees < 25) AS small,
            COUNT(*) FILTER (WHERE employees IS NULL) AS unknown
        FROM tmp_no_dol
    """)
    r = cur.fetchone()
    print(f"    100+ employees:  {r[0]:,}")
    print(f"    25-99:           {r[1]:,}")
    print(f"    <25:             {r[2]:,}")
    print(f"    Unknown:         {r[3]:,}")

    # ================================================================
    # Build the DOL sponsor set (EINs not already in outreach.dol)
    # ================================================================
    cur.execute("""
        CREATE TEMP TABLE tmp_dol_sponsors AS
        WITH all_sponsors AS (
            -- Form 5500 sponsors
            SELECT DISTINCT
                f.spons_dfe_ein AS ein,
                UPPER(TRIM(f.spons_dfe_pn)) AS sponsor_name,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(f.spons_dfe_pn),
                        '\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                        '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS name_normalized,
                LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) AS zip5,
                UPPER(TRIM(f.spons_dfe_mail_us_city)) AS city,
                UPPER(TRIM(f.spons_dfe_mail_us_state)) AS state
            FROM dol.form_5500 f
            WHERE f.spons_dfe_ein IS NOT NULL
              AND f.spons_dfe_pn IS NOT NULL
              AND f.spons_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)

            UNION

            -- Form 5500-SF sponsors
            SELECT DISTINCT
                sf.sf_spons_ein AS ein,
                UPPER(TRIM(sf.sf_sponsor_name)) AS sponsor_name,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(sf.sf_sponsor_name),
                        '\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                        '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS name_normalized,
                LEFT(TRIM(sf.sf_spons_us_zip), 5) AS zip5,
                UPPER(TRIM(sf.sf_spons_us_city)) AS city,
                UPPER(TRIM(sf.sf_spons_us_state)) AS state
            FROM dol.form_5500_sf sf
            WHERE sf.sf_spons_ein IS NOT NULL
              AND sf.sf_sponsor_name IS NOT NULL
              AND sf.sf_spons_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
        )
        SELECT DISTINCT ON (ein)
            ein, sponsor_name, name_normalized, zip5, city, state
        FROM all_sponsors
        WHERE zip5 IS NOT NULL AND zip5 ~ '^\\d{5}$'
        ORDER BY ein, sponsor_name
    """)

    cur.execute("SELECT COUNT(*) FROM tmp_dol_sponsors")
    sponsor_count = cur.fetchone()[0]
    print(f"\n  Unmatched DOL sponsors (with ZIP): {sponsor_count:,}")

    # Index for performance
    cur.execute("CREATE INDEX idx_tmp_sponsors_state ON tmp_dol_sponsors(state)")
    cur.execute("CREATE INDEX idx_tmp_sponsors_zip ON tmp_dol_sponsors(zip5)")
    cur.execute("CREATE INDEX idx_tmp_sponsors_name ON tmp_dol_sponsors USING gin(name_normalized gin_trgm_ops)")
    cur.execute("CREATE INDEX idx_tmp_nodol_state ON tmp_no_dol(state)")
    cur.execute("CREATE INDEX idx_tmp_nodol_zip ON tmp_no_dol(zip5)")

    # ================================================================
    # TIER 1: Exact normalized name + state
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 1: Exact name + state")
    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.name_normalized = ds.name_normalized
           AND nd.state = ds.state
        WHERE LENGTH(nd.name_normalized) >= 3
    """)
    t1 = cur.fetchone()[0]
    print(f"    Matches: {t1:,}")

    # Sample
    cur.execute("""
        SELECT nd.company_name, nd.domain, nd.state, ds.sponsor_name, ds.ein
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.name_normalized = ds.name_normalized
           AND nd.state = ds.state
        WHERE LENGTH(nd.name_normalized) >= 3
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"      CT: {(r[0] or '')[:30]:30s} ({r[1]:25s} {r[2]}) -> DOL: {(r[3] or '')[:30]:30s} EIN={r[4]}")

    # ================================================================
    # TIER 2: Domain keyword in sponsor name + state + ZIP
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 2: Domain keyword in sponsor name + state + ZIP")
    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.zip5 = ds.zip5
        WHERE LENGTH(nd.domain_keyword) >= 4
          AND ds.name_normalized LIKE '%%' || nd.domain_keyword || '%%'
          AND nd.outreach_id NOT IN (
              SELECT nd2.outreach_id FROM tmp_no_dol nd2
              JOIN tmp_dol_sponsors ds2 ON nd2.name_normalized = ds2.name_normalized AND nd2.state = ds2.state
              WHERE LENGTH(nd2.name_normalized) >= 3
          )
    """)
    t2 = cur.fetchone()[0]
    print(f"    Matches (net new): {t2:,}")

    cur.execute("""
        SELECT nd.company_name, nd.domain, nd.domain_keyword, ds.sponsor_name, ds.ein
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.zip5 = ds.zip5
        WHERE LENGTH(nd.domain_keyword) >= 4
          AND ds.name_normalized LIKE '%%' || nd.domain_keyword || '%%'
          AND nd.outreach_id NOT IN (
              SELECT nd2.outreach_id FROM tmp_no_dol nd2
              JOIN tmp_dol_sponsors ds2 ON nd2.name_normalized = ds2.name_normalized AND nd2.state = ds2.state
              WHERE LENGTH(nd2.name_normalized) >= 3
          )
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"      CT: {(r[0] or '')[:25]:25s} dom={r[2]:15s} -> DOL: {(r[3] or '')[:30]:30s} EIN={r[4]}")

    # ================================================================
    # TIER 3: Trigram similarity >= 0.4 + ZIP match
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 3: Trigram similarity (>=0.4) + ZIP match")

    # Set threshold
    cur.execute("SET pg_trgm.similarity_threshold = 0.4")

    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.zip5 = ds.zip5
           AND similarity(nd.name_normalized, ds.name_normalized) >= 0.4
        WHERE LENGTH(nd.name_normalized) >= 3
          AND LENGTH(ds.name_normalized) >= 3
    """)
    t3_raw = cur.fetchone()[0]

    # Subtract T1 and T2
    cur.execute("""
        WITH t1_t2 AS (
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.name_normalized = ds.name_normalized AND nd.state = ds.state
            WHERE LENGTH(nd.name_normalized) >= 3
            UNION
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.state = ds.state AND nd.zip5 = ds.zip5
            WHERE LENGTH(nd.domain_keyword) >= 4
              AND ds.name_normalized LIKE '%%' || nd.domain_keyword || '%%'
        )
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.zip5 = ds.zip5
           AND similarity(nd.name_normalized, ds.name_normalized) >= 0.4
        WHERE LENGTH(nd.name_normalized) >= 3
          AND LENGTH(ds.name_normalized) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM t1_t2)
    """)
    t3 = cur.fetchone()[0]
    print(f"    Matches (net new): {t3:,}")

    cur.execute("""
        WITH t1_t2 AS (
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.name_normalized = ds.name_normalized AND nd.state = ds.state
            WHERE LENGTH(nd.name_normalized) >= 3
            UNION
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.state = ds.state AND nd.zip5 = ds.zip5
            WHERE LENGTH(nd.domain_keyword) >= 4
              AND ds.name_normalized LIKE '%%' || nd.domain_keyword || '%%'
        )
        SELECT nd.company_name, nd.domain, nd.zip5,
               ds.sponsor_name, ds.ein,
               similarity(nd.name_normalized, ds.name_normalized) AS sim
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.zip5 = ds.zip5
           AND similarity(nd.name_normalized, ds.name_normalized) >= 0.4
        WHERE LENGTH(nd.name_normalized) >= 3
          AND LENGTH(ds.name_normalized) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM t1_t2)
        ORDER BY similarity(nd.name_normalized, ds.name_normalized) DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"      CT: {(r[0] or '')[:25]:25s} {r[2]} -> DOL: {(r[3] or '')[:25]:25s} EIN={r[4]} sim={r[5]:.2f}")

    # ================================================================
    # TIER 4: Trigram similarity >= 0.3 + state + city
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 4: Trigram similarity (>=0.3) + state + city")

    cur.execute("SET pg_trgm.similarity_threshold = 0.3")

    cur.execute("""
        WITH already_matched AS (
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.name_normalized = ds.name_normalized AND nd.state = ds.state
            WHERE LENGTH(nd.name_normalized) >= 3
            UNION
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.state = ds.state AND nd.zip5 = ds.zip5
            WHERE LENGTH(nd.domain_keyword) >= 4
              AND ds.name_normalized LIKE '%%' || nd.domain_keyword || '%%'
            UNION
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.zip5 = ds.zip5 AND similarity(nd.name_normalized, ds.name_normalized) >= 0.4
            WHERE LENGTH(nd.name_normalized) >= 3 AND LENGTH(ds.name_normalized) >= 3
        )
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
           AND similarity(nd.name_normalized, ds.name_normalized) >= 0.3
        WHERE LENGTH(nd.name_normalized) >= 3
          AND LENGTH(ds.name_normalized) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM already_matched)
    """)
    t4 = cur.fetchone()[0]
    print(f"    Matches (net new): {t4:,}")

    cur.execute("""
        WITH already_matched AS (
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.name_normalized = ds.name_normalized AND nd.state = ds.state
            WHERE LENGTH(nd.name_normalized) >= 3
            UNION
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.state = ds.state AND nd.zip5 = ds.zip5
            WHERE LENGTH(nd.domain_keyword) >= 4
              AND ds.name_normalized LIKE '%%' || nd.domain_keyword || '%%'
            UNION
            SELECT nd.outreach_id FROM tmp_no_dol nd
            JOIN tmp_dol_sponsors ds ON nd.zip5 = ds.zip5 AND similarity(nd.name_normalized, ds.name_normalized) >= 0.4
            WHERE LENGTH(nd.name_normalized) >= 3 AND LENGTH(ds.name_normalized) >= 3
        )
        SELECT nd.company_name, nd.domain, nd.city, nd.state,
               ds.sponsor_name, ds.ein,
               similarity(nd.name_normalized, ds.name_normalized) AS sim
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
           AND similarity(nd.name_normalized, ds.name_normalized) >= 0.3
        WHERE LENGTH(nd.name_normalized) >= 3
          AND LENGTH(ds.name_normalized) >= 3
          AND nd.outreach_id NOT IN (SELECT outreach_id FROM already_matched)
        ORDER BY similarity(nd.name_normalized, ds.name_normalized) DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"      CT: {(r[0] or '')[:25]:25s} {r[2] or '':15s} {r[3]} -> DOL: {(r[4] or '')[:25]:25s} sim={r[6]:.2f}")

    # ================================================================
    # Summary
    # ================================================================
    total_matched = t1 + t2 + t3 + t4
    elapsed = time.time() - start

    print(f"\n  {'='*75}")
    print(f"  SUMMARY")
    print(f"  {'='*75}")
    print(f"    No-DOL companies:     {no_dol_count:,}")
    print(f"    Unmatched sponsors:   {sponsor_count:,}")
    print(f"")
    print(f"    T1 (exact name+state):     {t1:>6,}")
    print(f"    T2 (domain+state+zip):     {t2:>6,}")
    print(f"    T3 (fuzzy name+zip):       {t3:>6,}")
    print(f"    T4 (fuzzy name+state+city):{t4:>6,}")
    print(f"    ────────────────────────────────")
    print(f"    Total matchable:           {total_matched:>6,}")
    print(f"    Remaining unmatched:       {no_dol_count - total_matched:>6,}")
    print(f"")
    print(f"    Current DOL coverage:  69,949 / 94,129 (74.3%)")
    print(f"    Projected DOL coverage: {69949 + total_matched:,} / 94,129 ({100*(69949+total_matched)/94129:.1f}%)")
    print(f"    Time: {elapsed:.1f}s")

    conn.close()
    print(f"\n{'='*75}")
    print(f"  Done.")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
