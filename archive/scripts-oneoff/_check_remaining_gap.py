"""Check what's left in the 1,708 ZIP gap."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Country breakdown
cur.execute("""
    SELECT ct.country, COUNT(*)
    FROM outreach.company_target ct
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
    GROUP BY ct.country
    ORDER BY COUNT(*) DESC
""")
print(f"Missing ZIP by country:")
for r in cur.fetchall():
    print(f"  {r[0] or 'NULL':15s}: {r[1]:,}")

# Do they have city+state?
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE city IS NOT NULL AND TRIM(city) != ''
                         AND state IS NOT NULL AND TRIM(state) != '') AS has_city_state,
        COUNT(*) FILTER (WHERE city IS NOT NULL AND TRIM(city) != '') AS has_city,
        COUNT(*) FILTER (WHERE state IS NOT NULL AND TRIM(state) != '') AS has_state,
        COUNT(*) FILTER (WHERE (city IS NULL OR TRIM(city) = '')
                         AND (state IS NULL OR TRIM(state) = '')) AS no_location
    FROM outreach.company_target
    WHERE postal_code IS NULL OR TRIM(postal_code) = ''
""")
r = cur.fetchone()
print(f"\nLocation data on remaining {r[0]:,}:")
print(f"  Has city+state: {r[1]:,}")
print(f"  Has city only:  {r[2] - r[1]:,}")
print(f"  Has state only: {r[3] - r[1]:,}")
print(f"  No location:    {r[4]:,}")

# TLD breakdown
cur.execute("""
    SELECT
        CASE
            WHEN o.domain LIKE '%%.com' THEN '.com'
            WHEN o.domain LIKE '%%.net' THEN '.net'
            WHEN o.domain LIKE '%%.org' THEN '.org'
            WHEN o.domain LIKE '%%.co.uk' OR o.domain LIKE '%%.uk' THEN '.uk'
            WHEN o.domain LIKE '%%.ca' THEN '.ca'
            WHEN o.domain LIKE '%%.au' THEN '.au'
            WHEN o.domain LIKE '%%.de' THEN '.de'
            WHEN o.domain LIKE '%%.io' THEN '.io'
            WHEN o.domain LIKE '%%.fr' THEN '.fr'
            ELSE SUBSTRING(o.domain FROM '\.[^.]+$')
        END AS tld,
        COUNT(*)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
    GROUP BY 1
    ORDER BY COUNT(*) DESC
    LIMIT 20
""")
print(f"\nBy TLD:")
for r in cur.fetchall():
    print(f"  {r[0]:10s}: {r[1]:,}")

# DOL bridge?
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(d.outreach_id) AS has_dol
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\nDOL bridge: {r[1]:,} / {r[0]:,}")

# Were they in the Clay export but Clay returned no ZIP?
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE ct.country IS NOT NULL AND UPPER(TRIM(ct.country)) NOT IN ('US', 'UNITED STATES', 'USA')) AS intl,
        COUNT(*) FILTER (WHERE ct.country IS NULL OR TRIM(ct.country) = '') AS no_country,
        COUNT(*) FILTER (WHERE ct.country IS NOT NULL AND UPPER(TRIM(ct.country)) IN ('US', 'UNITED STATES', 'USA')) AS us
    FROM outreach.company_target ct
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\nUS vs International:")
print(f"  US:            {r[2]:,}")
print(f"  International: {r[0]:,}")
print(f"  No country:    {r[1]:,}")

# Sample the US ones — why no ZIP?
cur.execute("""
    SELECT o.domain, ci.company_name, ct.city, ct.state, ct.country
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.country IS NOT NULL AND UPPER(TRIM(ct.country)) IN ('US', 'UNITED STATES', 'USA')
    LIMIT 20
""")
rows = cur.fetchall()
if rows:
    print(f"\nSample US companies still missing ZIP:")
    for r in rows:
        print(f"  {r[0]:35s} {(r[1] or '')[:30]:30s} {r[2] or '-':15s} {r[3] or '-':5s} {r[4]}")

# Sample international
cur.execute("""
    SELECT o.domain, ci.company_name, ct.city, ct.state, ct.country
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.country IS NOT NULL AND UPPER(TRIM(ct.country)) NOT IN ('US', 'UNITED STATES', 'USA')
    LIMIT 20
""")
rows = cur.fetchall()
if rows:
    print(f"\nSample international companies (no US ZIP possible):")
    for r in rows:
        print(f"  {r[0]:35s} {(r[1] or '')[:30]:30s} {r[4] or '-'}")

conn.close()
