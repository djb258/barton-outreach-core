"""Check how many city+state geocodes were ambiguous (multi-ZIP cities)."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# How many of the CITY_STATE_GEOCODE repairs came from multi-ZIP cities?
cur.execute("""
    WITH geocoded AS (
        SELECT
            ct.outreach_id,
            UPPER(TRIM(ct.city)) AS ct_city,
            UPPER(TRIM(ct.state)) AS ct_state,
            ct.postal_code
        FROM outreach.company_target ct
        WHERE ct.postal_code_source = 'CITY_STATE_GEOCODE'
    ),
    zip_counts AS (
        SELECT
            UPPER(z.city) AS ref_city,
            UPPER(z.state_id) AS ref_state,
            COUNT(*) AS zip_count
        FROM reference.us_zip_codes z
        GROUP BY UPPER(z.city), UPPER(z.state_id)
    )
    SELECT
        COUNT(*) AS total_geocoded,
        COUNT(*) FILTER (WHERE zc.zip_count = 1) AS exact_match,
        COUNT(*) FILTER (WHERE zc.zip_count BETWEEN 2 AND 5) AS few_zips,
        COUNT(*) FILTER (WHERE zc.zip_count BETWEEN 6 AND 20) AS medium_zips,
        COUNT(*) FILTER (WHERE zc.zip_count > 20) AS many_zips
    FROM geocoded g
    JOIN zip_counts zc ON zc.ref_city = g.ct_city AND zc.ref_state = g.ct_state
""")
r = cur.fetchone()
print(f"CITY_STATE_GEOCODE breakdown:")
print(f"  Total geocoded:        {r[0]:,}")
print(f"  Exact (1 ZIP):         {r[1]:,}  <- confident")
print(f"  Low ambiguity (2-5):   {r[2]:,}  <- probably fine")
print(f"  Medium ambiguity (6-20): {r[3]:,}  <- questionable")
print(f"  High ambiguity (20+):  {r[4]:,}  <- should revert")

# What cities are in the 20+ bucket?
cur.execute("""
    WITH geocoded AS (
        SELECT
            ct.outreach_id,
            UPPER(TRIM(ct.city)) AS ct_city,
            UPPER(TRIM(ct.state)) AS ct_state
        FROM outreach.company_target ct
        WHERE ct.postal_code_source = 'CITY_STATE_GEOCODE'
    ),
    zip_counts AS (
        SELECT
            UPPER(z.city) AS ref_city,
            UPPER(z.state_id) AS ref_state,
            COUNT(*) AS zip_count
        FROM reference.us_zip_codes z
        GROUP BY UPPER(z.city), UPPER(z.state_id)
    )
    SELECT g.ct_city, g.ct_state, zc.zip_count, COUNT(*) AS companies
    FROM geocoded g
    JOIN zip_counts zc ON zc.ref_city = g.ct_city AND zc.ref_state = g.ct_state
    WHERE zc.zip_count > 20
    GROUP BY g.ct_city, g.ct_state, zc.zip_count
    ORDER BY COUNT(*) DESC
""")
print(f"\nHigh-ambiguity cities (20+ ZIPs):")
for r in cur.fetchall():
    print(f"  {r[0]:25s} {r[1]:>2s}: {r[2]:>3d} ZIPs, {r[3]:>4,} companies")

# Also check 6-20 range
cur.execute("""
    WITH geocoded AS (
        SELECT
            ct.outreach_id,
            UPPER(TRIM(ct.city)) AS ct_city,
            UPPER(TRIM(ct.state)) AS ct_state
        FROM outreach.company_target ct
        WHERE ct.postal_code_source = 'CITY_STATE_GEOCODE'
    ),
    zip_counts AS (
        SELECT
            UPPER(z.city) AS ref_city,
            UPPER(z.state_id) AS ref_state,
            COUNT(*) AS zip_count
        FROM reference.us_zip_codes z
        GROUP BY UPPER(z.city), UPPER(z.state_id)
    )
    SELECT g.ct_city, g.ct_state, zc.zip_count, COUNT(*) AS companies
    FROM geocoded g
    JOIN zip_counts zc ON zc.ref_city = g.ct_city AND zc.ref_state = g.ct_state
    WHERE zc.zip_count BETWEEN 6 AND 20
    GROUP BY g.ct_city, g.ct_state, zc.zip_count
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")
print(f"\nMedium-ambiguity cities (6-20 ZIPs, top 20):")
for r in cur.fetchall():
    print(f"  {r[0]:25s} {r[1]:>2s}: {r[2]:>3d} ZIPs, {r[3]:>4,} companies")

conn.close()
