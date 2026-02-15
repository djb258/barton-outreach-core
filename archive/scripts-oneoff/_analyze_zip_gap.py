"""Analyze the remaining CT postal_code gap after DOL repair."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Hunter postal_code fill rate
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(postal_code) FILTER (WHERE postal_code IS NOT NULL AND TRIM(postal_code) != '') AS has_zip,
        COUNT(city) FILTER (WHERE city IS NOT NULL AND TRIM(city) != '') AS has_city,
        COUNT(state) FILTER (WHERE state IS NOT NULL AND TRIM(state) != '') AS has_state
    FROM enrichment.hunter_company
""")
r = cur.fetchone()
print(f"Hunter company totals:")
print(f"  Total:  {r[0]:,}")
print(f"  ZIP:    {r[1]:,} ({100*r[1]/r[0]:.1f}%)")
print(f"  City:   {r[2]:,} ({100*r[2]/r[0]:.1f}%)")
print(f"  State:  {r[3]:,} ({100*r[3]/r[0]:.1f}%)")

# Sample hunter postal codes
cur.execute("""
    SELECT postal_code, city, state, COUNT(*)
    FROM enrichment.hunter_company
    WHERE postal_code IS NOT NULL AND TRIM(postal_code) != ''
    GROUP BY postal_code, city, state
    ORDER BY COUNT(*) DESC LIMIT 5
""")
print(f"\nSample hunter ZIPs:")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | {r[2]} | {r[3]:,}")

# CT-missing matched to Hunter by domain
cur.execute("""
    SELECT
        COUNT(*) AS matchable,
        COUNT(hc.postal_code) FILTER (WHERE hc.postal_code IS NOT NULL AND TRIM(hc.postal_code) != '') AS hunter_has_zip,
        COUNT(hc.city) FILTER (WHERE hc.city IS NOT NULL AND TRIM(hc.city) != '') AS hunter_has_city,
        COUNT(hc.state) FILTER (WHERE hc.state IS NOT NULL AND TRIM(hc.state) != '') AS hunter_has_state
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\nCT-missing matched to Hunter by domain:")
print(f"  Matchable:    {r[0]:,}")
print(f"  Hunter ZIP:   {r[1]:,}")
print(f"  Hunter city:  {r[2]:,}")
print(f"  Hunter state: {r[3]:,}")

# CT-missing with NO domain match in Hunter at all
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND hc.domain IS NULL
""")
print(f"\nCT-missing with NO Hunter domain match: {cur.fetchone()[0]:,}")

# CT own city+state availability
cur.execute("""
    SELECT
        COUNT(*) AS total_missing,
        COUNT(*) FILTER (WHERE ct.city IS NOT NULL AND TRIM(ct.city) != ''
                         AND ct.state IS NOT NULL AND TRIM(ct.state) != '') AS has_city_state,
        COUNT(*) FILTER (WHERE ct.state IS NOT NULL AND TRIM(ct.state) != ''
                         AND (ct.city IS NULL OR TRIM(ct.city) = '')) AS state_only,
        COUNT(*) FILTER (WHERE (ct.city IS NULL OR TRIM(ct.city) = '')
                         AND (ct.state IS NULL OR TRIM(ct.state) = '')) AS neither
    FROM outreach.company_target ct
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\nCT-missing own location data:")
print(f"  Total missing ZIP:  {r[0]:,}")
print(f"  Has city+state:     {r[1]:,}  (could geocode to ZIP)")
print(f"  State only:         {r[2]:,}")
print(f"  No location at all: {r[3]:,}")

# Source breakdown
cur.execute("""
    SELECT ct.source, COUNT(*)
    FROM outreach.company_target ct
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
    GROUP BY ct.source
    ORDER BY COUNT(*) DESC
""")
print(f"\nCT-missing by source:")
for row in cur.fetchall():
    print(f"  {row[0] or 'NULL'}: {row[1]:,}")

# Could Hunter city+state fill CT city+state for those missing both?
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND (ct.city IS NULL OR TRIM(ct.city) = '')
      AND hc.city IS NOT NULL AND TRIM(hc.city) != ''
""")
print(f"\nHunter city could backfill CT city (where CT has none): {cur.fetchone()[0]:,}")

# What about Clay/intake data?
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(city) FILTER (WHERE city IS NOT NULL AND TRIM(city) != '') AS has_city,
        COUNT(state) FILTER (WHERE state IS NOT NULL AND TRIM(state) != '') AS has_state
    FROM intake.people_raw_intake
""")
r = cur.fetchone()
print(f"\nClay intake location data:")
print(f"  Total:  {r[0]:,}")
print(f"  City:   {r[1]:,}")
print(f"  State:  {r[2]:,}")

conn.close()
print("\nDone.")
