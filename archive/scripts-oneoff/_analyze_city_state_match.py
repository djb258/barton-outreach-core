"""Test city+state → ZIP match quality before building repair."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# How many distinct city+state combos in CT-missing?
cur.execute("""
    SELECT COUNT(DISTINCT (UPPER(TRIM(city)), UPPER(TRIM(state))))
    FROM outreach.company_target
    WHERE (postal_code IS NULL OR TRIM(postal_code) = '')
      AND city IS NOT NULL AND TRIM(city) != ''
      AND state IS NOT NULL AND TRIM(state) != ''
""")
print(f"Distinct city+state combos in CT-missing: {cur.fetchone()[0]:,}")

# CT state uses abbreviation or full name?
cur.execute("""
    SELECT state, COUNT(*)
    FROM outreach.company_target
    WHERE (postal_code IS NULL OR TRIM(postal_code) = '')
      AND state IS NOT NULL AND TRIM(state) != ''
    GROUP BY state ORDER BY COUNT(*) DESC LIMIT 15
""")
print(f"\nCT state values (top 15):")
for r in cur.fetchall():
    print(f"  '{r[0]}': {r[1]:,}")

# reference.us_zip_codes state format
cur.execute("""
    SELECT state_id, state_name, COUNT(*)
    FROM reference.us_zip_codes
    GROUP BY state_id, state_name ORDER BY COUNT(*) DESC LIMIT 10
""")
print(f"\nReference state format (top 10):")
for r in cur.fetchall():
    print(f"  {r[0]:>2s} / {r[1]:25s} : {r[2]:,} ZIPs")

# Test: how many CT city+state pairs match reference by city+state_id?
cur.execute("""
    WITH ct_missing AS (
        SELECT DISTINCT
            UPPER(TRIM(city)) AS ct_city,
            UPPER(TRIM(state)) AS ct_state
        FROM outreach.company_target
        WHERE (postal_code IS NULL OR TRIM(postal_code) = '')
          AND city IS NOT NULL AND TRIM(city) != ''
          AND state IS NOT NULL AND TRIM(state) != ''
    )
    SELECT
        COUNT(*) AS total_combos,
        COUNT(z.zip) AS matched_combos
    FROM ct_missing cm
    LEFT JOIN LATERAL (
        SELECT zip FROM reference.us_zip_codes
        WHERE UPPER(city) = cm.ct_city AND UPPER(state_id) = cm.ct_state
        LIMIT 1
    ) z ON true
""")
r = cur.fetchone()
print(f"\nCity+state_id match test:")
print(f"  Total combos:   {r[0]:,}")
print(f"  Matched:        {r[1]:,} ({100*r[1]/r[0]:.1f}%)")
print(f"  Unmatched:      {r[0]-r[1]:,}")

# Count companies (not combos) that would match
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
      AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
      AND EXISTS (
          SELECT 1 FROM reference.us_zip_codes z
          WHERE UPPER(z.city) = UPPER(TRIM(ct.city))
            AND UPPER(z.state_id) = UPPER(TRIM(ct.state))
      )
""")
print(f"\nCompanies matchable by city+state_id: {cur.fetchone()[0]:,}")

# What about state_name match for longer state values?
cur.execute("""
    SELECT ct.state, COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
      AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
      AND LENGTH(TRIM(ct.state)) > 2
    GROUP BY ct.state ORDER BY COUNT(*) DESC LIMIT 10
""")
print(f"\nCT state values longer than 2 chars:")
for r in cur.fetchall():
    print(f"  '{r[0]}': {r[1]:,}")

# Cities with multiple ZIPs — how ambiguous is this?
cur.execute("""
    WITH ct_cities AS (
        SELECT DISTINCT
            UPPER(TRIM(ct.city)) AS ct_city,
            UPPER(TRIM(ct.state)) AS ct_state
        FROM outreach.company_target ct
        WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
          AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
          AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
    )
    SELECT
        cm.ct_city, cm.ct_state, COUNT(z.zip) AS zip_count
    FROM ct_cities cm
    JOIN reference.us_zip_codes z
        ON UPPER(z.city) = cm.ct_city AND UPPER(z.state_id) = cm.ct_state
    GROUP BY cm.ct_city, cm.ct_state
    ORDER BY COUNT(z.zip) DESC
    LIMIT 15
""")
print(f"\nMost ambiguous cities (most ZIPs per city+state):")
for r in cur.fetchall():
    print(f"  {r[0]:25s} {r[1]:2s}: {r[2]:,} ZIPs")

# Single-ZIP cities
cur.execute("""
    WITH ct_cities AS (
        SELECT DISTINCT
            UPPER(TRIM(ct.city)) AS ct_city,
            UPPER(TRIM(ct.state)) AS ct_state
        FROM outreach.company_target ct
        WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
          AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
          AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
    ),
    zip_counts AS (
        SELECT cm.ct_city, cm.ct_state, COUNT(z.zip) AS zip_count
        FROM ct_cities cm
        JOIN reference.us_zip_codes z
            ON UPPER(z.city) = cm.ct_city AND UPPER(z.state_id) = cm.ct_state
        GROUP BY cm.ct_city, cm.ct_state
    )
    SELECT
        COUNT(*) FILTER (WHERE zip_count = 1) AS single_zip,
        COUNT(*) FILTER (WHERE zip_count BETWEEN 2 AND 5) AS few_zips,
        COUNT(*) FILTER (WHERE zip_count BETWEEN 6 AND 20) AS medium_zips,
        COUNT(*) FILTER (WHERE zip_count > 20) AS many_zips,
        COUNT(*) AS total
    FROM zip_counts
""")
r = cur.fetchone()
print(f"\nCity ambiguity distribution:")
print(f"  1 ZIP (exact):    {r[0]:,} cities")
print(f"  2-5 ZIPs:        {r[1]:,} cities")
print(f"  6-20 ZIPs:       {r[2]:,} cities")
print(f"  20+ ZIPs:        {r[3]:,} cities")
print(f"  Total matchable: {r[4]:,} cities")

conn.close()
print("\nDone.")
