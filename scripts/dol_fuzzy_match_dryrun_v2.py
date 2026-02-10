"""
DOL EIN Fuzzy Match v2 — Dry Run

Uses CORRECT columns:
  form_5500:    sponsor_dfe_name + sponsor_dfe_ein (432K rows)
  form_5500_sf: sf_sponsor_name  + sf_spons_ein    (1.5M rows)

Matching strategy uses BOTH Hunter org name and CL company name
against DOL sponsor names, with geographic confirmation.

Tiers (highest confidence first):
  T1: Exact normalized name + state
  T2: Trigram (>=0.5) + state + ZIP
  T3: Trigram (>=0.4) + state + city
  T4: Trigram (>=0.3) + state + city (low confidence)

Usage:
    doppler run -- python scripts/dol_fuzzy_match_dryrun_v2.py
"""

import os
import sys
import time

import psycopg2

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")


SUFFIX_REGEX = r"""\s*(,?\s*(LLC|INC|INCORPORATED|CORP|CORPORATION|COMPANY|CO|LTD|LIMITED|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$"""


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
    print(f"  DOL EIN Fuzzy Match v2 — Dry Run (Correct Columns)")
    print(f"{'='*75}")

    # Ensure pg_trgm
    cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
    if not cur.fetchone():
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        conn.commit()
    print("\n  pg_trgm: available")

    start = time.time()

    # ================================================================
    # Build no-DOL company set with BOTH Hunter and CL names
    # ================================================================
    cur.execute(f"""
        CREATE TEMP TABLE tmp_no_dol AS
        SELECT
            ct.outreach_id,
            o.domain,
            -- CL company name (normalized)
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(ci.company_name),
                    E'{SUFFIX_REGEX}', '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS cl_name_norm,
            -- Hunter org name (normalized) — may be NULL
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(COALESCE(hc.organization, '')),
                    E'{SUFFIX_REGEX}', '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS hunter_name_norm,
            -- Best available geography (CT is authoritative for geo)
            LEFT(TRIM(ct.postal_code), 5) AS zip5,
            UPPER(TRIM(ct.city)) AS city,
            UPPER(TRIM(ct.state)) AS state,
            ct.employees
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        LEFT JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
        WHERE d.outreach_id IS NULL
    """)

    cur.execute("SELECT COUNT(*) FROM tmp_no_dol")
    no_dol = cur.fetchone()[0]
    print(f"\n  No-DOL CT companies: {no_dol:,}")

    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE hunter_name_norm IS NOT NULL AND hunter_name_norm <> '') AS has_hunter,
            COUNT(*) FILTER (WHERE hunter_name_norm IS NULL OR hunter_name_norm = '') AS no_hunter
        FROM tmp_no_dol
    """)
    r = cur.fetchone()
    print(f"    With Hunter org name: {r[0]:,}")
    print(f"    Without Hunter data:  {r[1]:,}")

    # ================================================================
    # Build DOL sponsor set (CORRECT columns)
    # ================================================================
    cur.execute(f"""
        CREATE TEMP TABLE tmp_dol_sponsors AS
        WITH all_sponsors AS (
            -- Form 5500 (sponsor_dfe_name + sponsor_dfe_ein)
            SELECT DISTINCT
                f.sponsor_dfe_ein AS ein,
                UPPER(TRIM(f.sponsor_dfe_name)) AS sponsor_name,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(f.sponsor_dfe_name),
                        E'{SUFFIX_REGEX}', '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS name_normalized,
                LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) AS zip5,
                UPPER(TRIM(f.spons_dfe_mail_us_city)) AS city,
                UPPER(TRIM(f.spons_dfe_mail_us_state)) AS state
            FROM dol.form_5500 f
            WHERE f.sponsor_dfe_ein IS NOT NULL
              AND f.sponsor_dfe_name IS NOT NULL
              AND TRIM(f.sponsor_dfe_name) <> ''

            UNION

            -- Form 5500-SF (sf_sponsor_name + sf_spons_ein)
            SELECT DISTINCT
                sf.sf_spons_ein AS ein,
                UPPER(TRIM(sf.sf_sponsor_name)) AS sponsor_name,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(sf.sf_sponsor_name),
                        E'{SUFFIX_REGEX}', '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS name_normalized,
                LEFT(TRIM(sf.sf_spons_us_zip), 5) AS zip5,
                UPPER(TRIM(sf.sf_spons_us_city)) AS city,
                UPPER(TRIM(sf.sf_spons_us_state)) AS state
            FROM dol.form_5500_sf sf
            WHERE sf.sf_spons_ein IS NOT NULL
              AND sf.sf_sponsor_name IS NOT NULL
              AND TRIM(sf.sf_sponsor_name) <> ''
        )
        SELECT DISTINCT ON (ein)
            ein, sponsor_name, name_normalized, zip5, city, state
        FROM all_sponsors
        WHERE name_normalized IS NOT NULL AND LENGTH(name_normalized) >= 2
        ORDER BY ein, sponsor_name
    """)

    cur.execute("SELECT COUNT(*) FROM tmp_dol_sponsors")
    sponsor_count = cur.fetchone()[0]
    print(f"\n  DOL sponsors (unique EINs): {sponsor_count:,}")

    # Exclude EINs already in outreach.dol
    cur.execute("""
        DELETE FROM tmp_dol_sponsors
        WHERE ein IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
    """)
    deleted = cur.rowcount
    cur.execute("SELECT COUNT(*) FROM tmp_dol_sponsors")
    remaining = cur.fetchone()[0]
    print(f"  After excluding existing DOL bridge EINs: {remaining:,} (removed {deleted:,})")

    # Indexes
    cur.execute("CREATE INDEX idx_ds2_state ON tmp_dol_sponsors(state)")
    cur.execute("CREATE INDEX idx_ds2_zip ON tmp_dol_sponsors(zip5)")
    cur.execute("CREATE INDEX idx_ds2_city ON tmp_dol_sponsors(city)")
    cur.execute("CREATE INDEX idx_ds2_name ON tmp_dol_sponsors(name_normalized)")
    cur.execute("CREATE INDEX idx_ds2_trgm ON tmp_dol_sponsors USING gin(name_normalized gin_trgm_ops)")
    cur.execute("CREATE INDEX idx_nd2_state ON tmp_no_dol(state)")
    cur.execute("CREATE INDEX idx_nd2_zip ON tmp_no_dol(zip5)")
    cur.execute("CREATE INDEX idx_nd2_city ON tmp_no_dol(city)")
    cur.execute("CREATE INDEX idx_nd2_cl ON tmp_no_dol USING gin(cl_name_norm gin_trgm_ops)")
    cur.execute("CREATE INDEX idx_nd2_hunter ON tmp_no_dol USING gin(hunter_name_norm gin_trgm_ops)")

    build_time = time.time() - start
    print(f"  Setup time: {build_time:.1f}s")

    # ================================================================
    # TIER 1: Exact normalized name + state
    # Match using EITHER CL name OR Hunter name
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 1: Exact name match + state")

    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds ON nd.state = ds.state
        WHERE LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND nd.cl_name_norm = ds.name_normalized)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND nd.hunter_name_norm = ds.name_normalized)
          )
    """)
    t1 = cur.fetchone()[0]
    print(f"    Matches: {t1:,}")

    cur.execute("""
        SELECT nd.domain, nd.cl_name_norm, nd.hunter_name_norm, nd.state,
               ds.sponsor_name, ds.ein
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds ON nd.state = ds.state
        WHERE LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND nd.cl_name_norm = ds.name_normalized)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND nd.hunter_name_norm = ds.name_normalized)
          )
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:28s} CL:{(r[1] or '')[:18]:18s} Hn:{(r[2] or '')[:18]:18s} {r[3]} -> {(r[4] or '')[:28]:28s} EIN={r[5]}")

    # Save T1 matches
    cur.execute("""
        CREATE TEMP TABLE tmp_matched AS
        SELECT DISTINCT nd.outreach_id
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds ON nd.state = ds.state
        WHERE LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND nd.cl_name_norm = ds.name_normalized)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND nd.hunter_name_norm = ds.name_normalized)
          )
    """)

    # ================================================================
    # TIER 2: Trigram >= 0.5 + state + ZIP
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 2: Trigram (>=0.5) + state + ZIP")

    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.zip5 = ds.zip5
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.5)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.5)
          )
    """)
    t2 = cur.fetchone()[0]
    print(f"    Matches (net new): {t2:,}")

    cur.execute("""
        SELECT nd.domain, nd.cl_name_norm, nd.hunter_name_norm, nd.zip5, nd.state,
               ds.sponsor_name, ds.ein,
               GREATEST(
                   CASE WHEN LENGTH(nd.cl_name_norm) >= 3 THEN similarity(nd.cl_name_norm, ds.name_normalized) ELSE 0 END,
                   CASE WHEN LENGTH(nd.hunter_name_norm) >= 3 THEN similarity(nd.hunter_name_norm, ds.name_normalized) ELSE 0 END
               ) AS best_sim
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.zip5 = ds.zip5
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.5)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.5)
          )
        ORDER BY best_sim DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:26s} CL:{(r[1] or '')[:16]:16s} Hn:{(r[2] or '')[:16]:16s} {r[4]} {r[3]} -> {(r[5] or '')[:24]:24s} EIN={r[6]} sim={r[7]:.2f}")

    # Add to matched
    cur.execute("""
        INSERT INTO tmp_matched
        SELECT DISTINCT nd.outreach_id
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.zip5 = ds.zip5
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.5)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.5)
          )
    """)

    # ================================================================
    # TIER 3: Trigram >= 0.4 + state + city
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 3: Trigram (>=0.4) + state + city")

    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.4)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.4)
          )
    """)
    t3 = cur.fetchone()[0]
    print(f"    Matches (net new): {t3:,}")

    cur.execute("""
        SELECT nd.domain, nd.cl_name_norm, nd.hunter_name_norm, nd.city, nd.state,
               ds.sponsor_name, ds.ein,
               GREATEST(
                   CASE WHEN LENGTH(nd.cl_name_norm) >= 3 THEN similarity(nd.cl_name_norm, ds.name_normalized) ELSE 0 END,
                   CASE WHEN LENGTH(nd.hunter_name_norm) >= 3 THEN similarity(nd.hunter_name_norm, ds.name_normalized) ELSE 0 END
               ) AS best_sim
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.4)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.4)
          )
        ORDER BY best_sim DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:26s} CL:{(r[1] or '')[:14]:14s} Hn:{(r[2] or '')[:14]:14s} {r[3]:12s} {r[4]} -> {(r[5] or '')[:24]:24s} sim={r[7]:.2f}")

    # Add to matched
    cur.execute("""
        INSERT INTO tmp_matched
        SELECT DISTINCT nd.outreach_id
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.4)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.4)
          )
    """)

    # ================================================================
    # TIER 4: Trigram >= 0.3 + state + city (low confidence)
    # ================================================================
    print(f"\n  {'='*65}")
    print(f"  TIER 4: Trigram (>=0.3) + state + city")

    cur.execute("""
        SELECT COUNT(DISTINCT nd.outreach_id)
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.3)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.3)
          )
    """)
    t4 = cur.fetchone()[0]
    print(f"    Matches (net new): {t4:,}")

    cur.execute("""
        SELECT nd.domain, nd.cl_name_norm, nd.hunter_name_norm, nd.city, nd.state,
               ds.sponsor_name, ds.ein,
               GREATEST(
                   CASE WHEN LENGTH(nd.cl_name_norm) >= 3 THEN similarity(nd.cl_name_norm, ds.name_normalized) ELSE 0 END,
                   CASE WHEN LENGTH(nd.hunter_name_norm) >= 3 THEN similarity(nd.hunter_name_norm, ds.name_normalized) ELSE 0 END
               ) AS best_sim
        FROM tmp_no_dol nd
        JOIN tmp_dol_sponsors ds
            ON nd.state = ds.state
           AND nd.city = ds.city
        WHERE nd.outreach_id NOT IN (SELECT outreach_id FROM tmp_matched)
          AND LENGTH(ds.name_normalized) >= 3
          AND (
              (LENGTH(nd.cl_name_norm) >= 3 AND similarity(nd.cl_name_norm, ds.name_normalized) >= 0.3)
              OR
              (LENGTH(nd.hunter_name_norm) >= 3 AND similarity(nd.hunter_name_norm, ds.name_normalized) >= 0.3)
          )
        ORDER BY best_sim DESC
        LIMIT 15
    """)
    for r in cur.fetchall():
        print(f"    {r[0]:26s} CL:{(r[1] or '')[:14]:14s} Hn:{(r[2] or '')[:14]:14s} {r[3]:12s} {r[4]} -> {(r[5] or '')[:24]:24s} sim={r[7]:.2f}")

    # ================================================================
    # Summary
    # ================================================================
    total = t1 + t2 + t3 + t4
    elapsed = time.time() - start

    # Get current DOL count
    cur.execute("SELECT COUNT(*) FROM outreach.dol")
    current_dol = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM outreach.company_target")
    ct_total = cur.fetchone()[0]

    print(f"\n  {'='*75}")
    print(f"  SUMMARY (v2 — Correct Columns)")
    print(f"  {'='*75}")
    print(f"    No-DOL companies:     {no_dol:,}")
    print(f"    DOL sponsors pool:    {remaining:,}")
    print(f"")
    print(f"    T1 (exact name+state):        {t1:>6,}  HIGH confidence")
    print(f"    T2 (fuzzy>=0.5 + state+zip):  {t2:>6,}  HIGH confidence")
    print(f"    T3 (fuzzy>=0.4 + state+city): {t3:>6,}  MEDIUM confidence")
    print(f"    T4 (fuzzy>=0.3 + state+city): {t4:>6,}  LOW confidence")
    print(f"    ──────────────────────────────────────")
    print(f"    Total matchable:              {total:>6,}")
    print(f"    Remaining unmatched:          {no_dol - total:>6,}")
    print(f"")
    print(f"    Current DOL coverage:  {current_dol:,} / {ct_total:,} ({100*current_dol/ct_total:.1f}%)")
    print(f"    Projected (T1+T2):     {current_dol + t1 + t2:,} / {ct_total:,} ({100*(current_dol+t1+t2)/ct_total:.1f}%)")
    print(f"    Projected (T1-T3):     {current_dol + t1 + t2 + t3:,} / {ct_total:,} ({100*(current_dol+t1+t2+t3)/ct_total:.1f}%)")
    print(f"    Projected (all):       {current_dol + total:,} / {ct_total:,} ({100*(current_dol+total)/ct_total:.1f}%)")
    print(f"    Time: {elapsed:.1f}s")

    conn.close()
    print(f"\n{'='*75}")
    print(f"  Done.")
    print(f"{'='*75}")


if __name__ == "__main__":
    main()
