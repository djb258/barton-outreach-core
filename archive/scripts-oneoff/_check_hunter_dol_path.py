"""Check Hunter company data availability for no-DOL CT domains."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

print(f"{'='*75}")
print(f"  Hunter Company Data for No-DOL CT Domains")
print(f"{'='*75}")

# How many no-DOL domains found in hunter_company?
cur.execute("""
    SELECT COUNT(DISTINCT o.domain)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
""")
print(f"\n  No-DOL CT domains total: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT COUNT(DISTINCT o.domain)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
""")
hunter_match = cur.fetchone()[0]
print(f"  Found in hunter_company: {hunter_match:,}")

# Data quality
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(CASE WHEN hc.organization IS NOT NULL AND TRIM(hc.organization) <> '' THEN 1 END) AS has_org,
        COUNT(CASE WHEN hc.city IS NOT NULL AND TRIM(hc.city) <> '' THEN 1 END) AS has_city,
        COUNT(CASE WHEN hc.state IS NOT NULL AND TRIM(hc.state) <> '' THEN 1 END) AS has_state,
        COUNT(CASE WHEN hc.postal_code IS NOT NULL AND TRIM(hc.postal_code) <> '' THEN 1 END) AS has_zip
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
""")
r = cur.fetchone()
print(f"\n  Hunter data quality for no-DOL matches:")
print(f"    Total rows:     {r[0]:,}")
print(f"    Has org name:   {r[1]:,}")
print(f"    Has city:       {r[2]:,}")
print(f"    Has state:      {r[3]:,}")
print(f"    Has postal_code:{r[4]:,}")

# Sample
cur.execute("""
    SELECT o.domain, hc.organization, hc.city, hc.state, hc.postal_code
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
    LIMIT 15
""")
print(f"\n  Sample (domain -> Hunter org, city, state, zip):")
for r in cur.fetchall():
    print(f"    {r[0]:30s} -> {(r[1] or '')[:35]:35s} {(r[2] or ''):15s} {(r[3] or ''):3s} {r[4] or ''}")

# Key question: can we use Hunter org name + location to match DOL sponsors?
# Quick test: exact Hunter org name + state against DOL sponsors
cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'")
has_trgm = cur.fetchone() is not None

cur.execute("""
    WITH hunter_no_dol AS (
        SELECT DISTINCT ON (o.domain)
            ct.outreach_id, o.domain,
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(hc.organization),
                    '\s*(,?\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$',
                    '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS hunter_name_norm,
            UPPER(TRIM(hc.state)) AS hunter_state,
            UPPER(TRIM(hc.city)) AS hunter_city,
            LEFT(TRIM(hc.postal_code), 5) AS hunter_zip
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
        JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
        WHERE d.outreach_id IS NULL
          AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
        ORDER BY o.domain, hc.data_quality_score DESC NULLS LAST
    )
    SELECT COUNT(DISTINCT h.outreach_id)
    FROM hunter_no_dol h
    JOIN (
        SELECT DISTINCT
            spons_dfe_ein AS ein,
            UPPER(REGEXP_REPLACE(
                REGEXP_REPLACE(
                    TRIM(spons_dfe_pn),
                    '\s*(,?\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$',
                    '', 'i'
                ),
                '[^A-Za-z0-9 ]', '', 'g'
            )) AS name_normalized,
            UPPER(TRIM(spons_dfe_mail_us_state)) AS state
        FROM dol.form_5500
        WHERE spons_dfe_ein IS NOT NULL
          AND spons_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
    ) ds ON h.hunter_name_norm = ds.name_normalized AND h.hunter_state = ds.state
    WHERE LENGTH(h.hunter_name_norm) >= 3
""")
exact_match = cur.fetchone()[0]
print(f"\n  Exact Hunter org name + state -> DOL sponsor: {exact_match:,}")

# And with trigram similarity
if has_trgm:
    cur.execute("""
        WITH hunter_no_dol AS (
            SELECT DISTINCT ON (o.domain)
                ct.outreach_id, o.domain,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(hc.organization),
                        '\s*(,?\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$',
                        '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS hunter_name_norm,
                UPPER(TRIM(hc.state)) AS hunter_state,
                LEFT(TRIM(hc.postal_code), 5) AS hunter_zip
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
            LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
            JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
            WHERE d.outreach_id IS NULL
              AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
            ORDER BY o.domain, hc.data_quality_score DESC NULLS LAST
        ),
        dol_sponsors AS (
            SELECT DISTINCT ON (spons_dfe_ein)
                spons_dfe_ein AS ein,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(spons_dfe_pn),
                        '\s*(,?\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$',
                        '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS name_normalized,
                UPPER(TRIM(spons_dfe_mail_us_state)) AS state,
                LEFT(TRIM(spons_dfe_mail_us_zip), 5) AS zip5
            FROM dol.form_5500
            WHERE spons_dfe_ein IS NOT NULL
              AND spons_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
            ORDER BY spons_dfe_ein, spons_dfe_pn
        )
        SELECT COUNT(DISTINCT h.outreach_id)
        FROM hunter_no_dol h
        JOIN dol_sponsors ds
            ON h.hunter_state = ds.state
           AND h.hunter_zip = ds.zip5
           AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.4
        WHERE LENGTH(h.hunter_name_norm) >= 3
          AND LENGTH(ds.name_normalized) >= 3
    """)
    trgm_match = cur.fetchone()[0]
    print(f"  Trigram (>=0.4) Hunter org + state + ZIP -> DOL: {trgm_match:,}")

    # Sample the matches
    cur.execute("""
        WITH hunter_no_dol AS (
            SELECT DISTINCT ON (o.domain)
                ct.outreach_id, o.domain,
                hc.organization AS hunter_org,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(hc.organization),
                        '\s*(,?\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$',
                        '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS hunter_name_norm,
                UPPER(TRIM(hc.state)) AS hunter_state,
                UPPER(TRIM(hc.city)) AS hunter_city,
                LEFT(TRIM(hc.postal_code), 5) AS hunter_zip
            FROM outreach.company_target ct
            JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
            LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
            JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
            WHERE d.outreach_id IS NULL
              AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
            ORDER BY o.domain, hc.data_quality_score DESC NULLS LAST
        ),
        dol_sponsors AS (
            SELECT DISTINCT ON (spons_dfe_ein)
                spons_dfe_ein AS ein,
                TRIM(spons_dfe_pn) AS sponsor_name,
                UPPER(REGEXP_REPLACE(
                    REGEXP_REPLACE(
                        TRIM(spons_dfe_pn),
                        '\s*(,?\s*(LLC|INC|CORP|CORPORATION|COMPANY|CO|LTD|LP|LLP|PC|PA|PLLC|GROUP|HOLDINGS|SERVICES|ENTERPRISES|ASSOCIATES|INTERNATIONAL|\.))+\s*$',
                        '', 'i'
                    ),
                    '[^A-Za-z0-9 ]', '', 'g'
                )) AS name_normalized,
                UPPER(TRIM(spons_dfe_mail_us_state)) AS state,
                LEFT(TRIM(spons_dfe_mail_us_zip), 5) AS zip5
            FROM dol.form_5500
            WHERE spons_dfe_ein IS NOT NULL
              AND spons_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
            ORDER BY spons_dfe_ein, spons_dfe_pn
        )
        SELECT h.domain, h.hunter_org, h.hunter_zip, h.hunter_state,
               ds.sponsor_name, ds.ein,
               similarity(h.hunter_name_norm, ds.name_normalized) AS sim
        FROM hunter_no_dol h
        JOIN dol_sponsors ds
            ON h.hunter_state = ds.state
           AND h.hunter_zip = ds.zip5
           AND similarity(h.hunter_name_norm, ds.name_normalized) >= 0.4
        WHERE LENGTH(h.hunter_name_norm) >= 3
          AND LENGTH(ds.name_normalized) >= 3
        ORDER BY sim DESC
        LIMIT 15
    """)
    print(f"\n  Sample Hunter->DOL matches (trigram+state+zip):")
    for r in cur.fetchall():
        print(f"    {r[0]:28s} Hunter: {(r[1] or '')[:25]:25s} {r[3]} {r[2]} -> DOL: {(r[4] or '')[:25]:25s} EIN={r[5]} sim={r[6]:.2f}")

conn.close()
print(f"\n{'='*75}")
print(f"  Done.")
print(f"{'='*75}")
