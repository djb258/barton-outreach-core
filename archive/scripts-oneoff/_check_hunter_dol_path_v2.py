"""Check Hunter org name + state/city matching to DOL sponsors."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

print(f"{'='*75}")
print(f"  Hunter Org Name -> DOL Sponsor Matching")
print(f"{'='*75}")

# Build temp tables
cur.execute("""
    CREATE TEMP TABLE tmp_hunter_no_dol AS
    SELECT DISTINCT ON (o.domain)
        ct.outreach_id, o.domain,
        hc.organization AS hunter_org,
        UPPER(REGEXP_REPLACE(
            REGEXP_REPLACE(
                TRIM(hc.organization),
                E'\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                '', 'i'
            ),
            '[^A-Za-z0-9 ]', '', 'g'
        )) AS hunter_name_norm,
        UPPER(TRIM(hc.state)) AS hunter_state,
        UPPER(TRIM(hc.city)) AS hunter_city,
        LEFT(TRIM(hc.postal_code), 5) AS hunter_zip,
        -- Also keep CT geography for fallback
        UPPER(TRIM(ct.state)) AS ct_state,
        UPPER(TRIM(ct.city)) AS ct_city,
        LEFT(TRIM(ct.postal_code), 5) AS ct_zip
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
    ORDER BY o.domain, hc.data_quality_score DESC NULLS LAST
""")
cur.execute("SELECT COUNT(*) FROM tmp_hunter_no_dol")
print(f"\n  Hunter no-DOL companies with org name: {cur.fetchone()[0]:,}")

# Build DOL sponsor table (including 5500-SF)
cur.execute("""
    CREATE TEMP TABLE tmp_dol_sponsors AS
    WITH all_sponsors AS (
        SELECT DISTINCT
            f.spons_dfe_ein AS ein,
            UPPER(TRIM(f.spons_dfe_pn)) AS sponsor_name,
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(f.spons_dfe_pn),
                    E'\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                    '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS name_normalized,
            LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) AS zip5,
            UPPER(TRIM(f.spons_dfe_mail_us_city)) AS city,
            UPPER(TRIM(f.spons_dfe_mail_us_state)) AS state
        FROM dol.form_5500 f
        WHERE f.spons_dfe_ein IS NOT NULL AND f.spons_dfe_pn IS NOT NULL
          AND f.spons_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)

        UNION

        SELECT DISTINCT
            sf.sf_spons_ein AS ein,
            UPPER(TRIM(sf.sf_sponsor_name)) AS sponsor_name,
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(sf.sf_sponsor_name),
                    E'\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                    '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS name_normalized,
            LEFT(TRIM(sf.sf_spons_us_zip), 5) AS zip5,
            UPPER(TRIM(sf.sf_spons_us_city)) AS city,
            UPPER(TRIM(sf.sf_spons_us_state)) AS state
        FROM dol.form_5500_sf sf
        WHERE sf.sf_spons_ein IS NOT NULL AND sf.sf_sponsor_name IS NOT NULL
          AND sf.sf_spons_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
    )
    SELECT DISTINCT ON (ein)
        ein, sponsor_name, name_normalized, zip5, city, state
    FROM all_sponsors
    ORDER BY ein, sponsor_name
""")
cur.execute("SELECT COUNT(*) FROM tmp_dol_sponsors")
print(f"  Unmatched DOL sponsors: {cur.fetchone()[0]:,}")

# Index
cur.execute("CREATE INDEX idx_hnd_state ON tmp_hunter_no_dol(hunter_state)")
cur.execute("CREATE INDEX idx_hnd_city ON tmp_hunter_no_dol(hunter_city)")
cur.execute("CREATE INDEX idx_ds_state ON tmp_dol_sponsors(state)")
cur.execute("CREATE INDEX idx_ds_city ON tmp_dol_sponsors(city)")
cur.execute("CREATE INDEX idx_ds_trgm ON tmp_dol_sponsors USING gin(name_normalized gin_trgm_ops)")
cur.execute("CREATE INDEX idx_hnd_trgm ON tmp_hunter_no_dol USING gin(hunter_name_norm gin_trgm_ops)")

# ================================================================
# MATCH 1: Exact Hunter org name + state (using Hunter state or CT state)
# ================================================================
print(f"\n  {'='*65}")
print(f"  MATCH 1: Exact Hunter org name + state")
cur.execute("""
    SELECT COUNT(DISTINCT h.outreach_id)
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON h.hunter_name_norm = ds.name_normalized
       AND (h.hunter_state = ds.state OR h.ct_state = ds.state)
    WHERE LENGTH(h.hunter_name_norm) >= 3
""")
m1 = cur.fetchone()[0]
print(f"    Matches: {m1:,}")

cur.execute("""
    SELECT h.domain, h.hunter_org, h.hunter_state, ds.sponsor_name, ds.ein
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON h.hunter_name_norm = ds.name_normalized
       AND (h.hunter_state = ds.state OR h.ct_state = ds.state)
    WHERE LENGTH(h.hunter_name_norm) >= 3
    LIMIT 15
""")
for r in cur.fetchall():
    print(f"    {r[0]:28s} Hunter: {(r[1] or '')[:25]:25s} {r[2]} -> DOL: {(r[3] or '')[:28]:28s} EIN={r[4]}")

# ================================================================
# MATCH 2: Trigram >= 0.5 + state (high confidence fuzzy)
# ================================================================
print(f"\n  {'='*65}")
print(f"  MATCH 2: Trigram (>=0.5) Hunter org + state")
cur.execute("""
    SELECT COUNT(DISTINCT h.outreach_id)
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON (h.hunter_state = ds.state OR h.ct_state = ds.state)
       AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.5
    WHERE LENGTH(h.hunter_name_norm) >= 3
      AND LENGTH(ds.name_normalized) >= 3
      AND h.outreach_id NOT IN (
          SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
          JOIN tmp_dol_sponsors ds2 ON h2.hunter_name_norm = ds2.name_normalized
              AND (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
          WHERE LENGTH(h2.hunter_name_norm) >= 3
      )
""")
m2 = cur.fetchone()[0]
print(f"    Matches (net new): {m2:,}")

cur.execute("""
    WITH already AS (
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON h2.hunter_name_norm = ds2.name_normalized
            AND (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
        WHERE LENGTH(h2.hunter_name_norm) >= 3
    )
    SELECT h.domain, h.hunter_org, h.hunter_state,
           ds.sponsor_name, ds.ein,
           similarity(h.hunter_name_norm, ds.name_normalized) AS sim
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON (h.hunter_state = ds.state OR h.ct_state = ds.state)
       AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.5
    WHERE LENGTH(h.hunter_name_norm) >= 3
      AND LENGTH(ds.name_normalized) >= 3
      AND h.outreach_id NOT IN (SELECT outreach_id FROM already)
    ORDER BY sim DESC
    LIMIT 15
""")
for r in cur.fetchall():
    print(f"    {r[0]:28s} Hunter: {(r[1] or '')[:22]:22s} {r[2]} -> DOL: {(r[3] or '')[:22]:22s} EIN={r[4]} sim={r[5]:.2f}")

# ================================================================
# MATCH 3: Trigram >= 0.4 + state + city (tighter geography)
# ================================================================
print(f"\n  {'='*65}")
print(f"  MATCH 3: Trigram (>=0.4) Hunter org + state + city")
cur.execute("""
    WITH already AS (
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON h2.hunter_name_norm = ds2.name_normalized
            AND (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
        WHERE LENGTH(h2.hunter_name_norm) >= 3
        UNION
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
            AND similarity(h2.hunter_name_norm, ds2.name_normalized) >= 0.5
        WHERE LENGTH(h2.hunter_name_norm) >= 3 AND LENGTH(ds2.name_normalized) >= 3
    )
    SELECT COUNT(DISTINCT h.outreach_id)
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON (h.hunter_state = ds.state OR h.ct_state = ds.state)
       AND (h.hunter_city = ds.city OR h.ct_city = ds.city)
       AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.4
    WHERE LENGTH(h.hunter_name_norm) >= 3
      AND LENGTH(ds.name_normalized) >= 3
      AND h.outreach_id NOT IN (SELECT outreach_id FROM already)
""")
m3 = cur.fetchone()[0]
print(f"    Matches (net new): {m3:,}")

cur.execute("""
    WITH already AS (
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON h2.hunter_name_norm = ds2.name_normalized
            AND (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
        WHERE LENGTH(h2.hunter_name_norm) >= 3
        UNION
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
            AND similarity(h2.hunter_name_norm, ds2.name_normalized) >= 0.5
        WHERE LENGTH(h2.hunter_name_norm) >= 3 AND LENGTH(ds2.name_normalized) >= 3
    )
    SELECT h.domain, h.hunter_org, h.hunter_city, h.hunter_state,
           ds.sponsor_name, ds.ein,
           similarity(h.hunter_name_norm, ds.name_normalized) AS sim
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON (h.hunter_state = ds.state OR h.ct_state = ds.state)
       AND (h.hunter_city = ds.city OR h.ct_city = ds.city)
       AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.4
    WHERE LENGTH(h.hunter_name_norm) >= 3
      AND LENGTH(ds.name_normalized) >= 3
      AND h.outreach_id NOT IN (SELECT outreach_id FROM already)
    ORDER BY sim DESC
    LIMIT 15
""")
for r in cur.fetchall():
    print(f"    {r[0]:28s} Hunter: {(r[1] or '')[:20]:20s} {(r[2] or ''):12s} {r[3]} -> DOL: {(r[4] or '')[:22]:22s} EIN={r[5]} sim={r[6]:.2f}")

# ================================================================
# MATCH 4: Trigram >= 0.3 + state + city (lowest tier)
# ================================================================
print(f"\n  {'='*65}")
print(f"  MATCH 4: Trigram (>=0.3) Hunter org + state + city")
cur.execute("""
    WITH already AS (
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON h2.hunter_name_norm = ds2.name_normalized
            AND (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
        WHERE LENGTH(h2.hunter_name_norm) >= 3
        UNION
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
            AND similarity(h2.hunter_name_norm, ds2.name_normalized) >= 0.5
        WHERE LENGTH(h2.hunter_name_norm) >= 3 AND LENGTH(ds2.name_normalized) >= 3
        UNION
        SELECT h2.outreach_id FROM tmp_hunter_no_dol h2
        JOIN tmp_dol_sponsors ds2 ON (h2.hunter_state = ds2.state OR h2.ct_state = ds2.state)
            AND (h2.hunter_city = ds2.city OR h2.ct_city = ds2.city)
            AND similarity(h2.hunter_name_norm, ds2.name_normalized) >= 0.4
        WHERE LENGTH(h2.hunter_name_norm) >= 3 AND LENGTH(ds2.name_normalized) >= 3
    )
    SELECT COUNT(DISTINCT h.outreach_id)
    FROM tmp_hunter_no_dol h
    JOIN tmp_dol_sponsors ds
        ON (h.hunter_state = ds.state OR h.ct_state = ds.state)
       AND (h.hunter_city = ds.city OR h.ct_city = ds.city)
       AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.3
    WHERE LENGTH(h.hunter_name_norm) >= 3
      AND LENGTH(ds.name_normalized) >= 3
      AND h.outreach_id NOT IN (SELECT outreach_id FROM already)
""")
m4 = cur.fetchone()[0]
print(f"    Matches (net new): {m4:,}")

# ================================================================
# COMBINED: What if we use BOTH Hunter name AND CT name?
# Some companies have better names in CT (from CL) vs Hunter
# ================================================================
print(f"\n  {'='*65}")
print(f"  BONUS: CT name (CL) matches not found via Hunter name")
cur.execute("""
    WITH hunter_matched AS (
        SELECT h.outreach_id FROM tmp_hunter_no_dol h
        JOIN tmp_dol_sponsors ds ON h.hunter_name_norm = ds.name_normalized
            AND (h.hunter_state = ds.state OR h.ct_state = ds.state)
        WHERE LENGTH(h.hunter_name_norm) >= 3
        UNION
        SELECT h.outreach_id FROM tmp_hunter_no_dol h
        JOIN tmp_dol_sponsors ds ON (h.hunter_state = ds.state OR h.ct_state = ds.state)
            AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.4
        WHERE LENGTH(h.hunter_name_norm) >= 3 AND LENGTH(ds.name_normalized) >= 3
    ),
    ct_names AS (
        SELECT ct.outreach_id,
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(ci.company_name),
                    E'\\s*(,?\\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\\.))+\\s*$',
                    '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS ct_name_norm,
            UPPER(TRIM(ct.state)) AS ct_state
        FROM outreach.company_target ct
        JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        WHERE d.outreach_id IS NULL
    )
    SELECT COUNT(DISTINCT cn.outreach_id)
    FROM ct_names cn
    JOIN tmp_dol_sponsors ds
        ON cn.ct_name_norm = ds.name_normalized
       AND cn.ct_state = ds.state
    WHERE LENGTH(cn.ct_name_norm) >= 3
      AND cn.outreach_id NOT IN (SELECT outreach_id FROM hunter_matched)
""")
bonus = cur.fetchone()[0]
print(f"    CT-name exact matches not in Hunter matches: {bonus:,}")

# ================================================================
# Summary
# ================================================================
total = m1 + m2 + m3 + m4 + bonus
print(f"\n  {'='*75}")
print(f"  SUMMARY — Hunter URL-Assisted DOL Matching")
print(f"  {'='*75}")
print(f"    No-DOL with Hunter data:  18,102")
print(f"    No-DOL without Hunter:     {25092 - 18102:,}")
print(f"")
print(f"    M1 (exact Hunter name+state):        {m1:>6,}")
print(f"    M2 (fuzzy>=0.5 Hunter name+state):   {m2:>6,}")
print(f"    M3 (fuzzy>=0.4 Hunter name+city+st): {m3:>6,}")
print(f"    M4 (fuzzy>=0.3 Hunter name+city+st): {m4:>6,}")
print(f"    Bonus (CT name exact, not in Hunter): {bonus:>6,}")
print(f"    ─────────────────────────────────────────")
print(f"    Total matchable:                     {total:>6,}")
print(f"")
print(f"    Current DOL: 69,949 / 94,129 (74.3%)")
print(f"    Projected:   {69949 + total:,} / 94,129 ({100*(69949+total)/94129:.1f}%)")

conn.close()
print(f"\n{'='*75}")
print(f"  Done.")
print(f"{'='*75}")
