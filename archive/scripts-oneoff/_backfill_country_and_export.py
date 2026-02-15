"""
1. Backfill country='US' where we have state or postal_code
2. Export domains that still need geography (ZIP, city, state)
"""
import os, sys, csv, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

total = 95837

# ============================================================
# Step 1: Backfill country = 'US' where state or ZIP exists
# ============================================================
cur.execute("""
    SELECT COUNT(*) FROM outreach.company_target
    WHERE (country IS NULL OR TRIM(country) = '')
      AND (
          (state IS NOT NULL AND TRIM(state) != '')
          OR (postal_code IS NOT NULL AND TRIM(postal_code) != '')
      )
""")
backfillable = cur.fetchone()[0]
print(f"Country backfill: {backfillable:,} companies have state/ZIP but no country")

cur.execute("""
    UPDATE outreach.company_target
    SET country = 'US'
    WHERE (country IS NULL OR TRIM(country) = '')
      AND (
          (state IS NOT NULL AND TRIM(state) != '')
          OR (postal_code IS NOT NULL AND TRIM(postal_code) != '')
      )
""")
print(f"  Applied: {cur.rowcount:,}")
conn.commit()

# Verify country fill
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE country IS NOT NULL AND TRIM(country) != '') AS has_country,
        COUNT(*) FILTER (WHERE country IS NULL OR TRIM(country) = '') AS no_country
    FROM outreach.company_target
""")
r = cur.fetchone()
print(f"  Country now: {r[0]:,} ({100*r[0]/total:.1f}%) filled, {r[1]:,} missing")

# ============================================================
# Step 2: Normalize existing country values to 'US'
# ============================================================
cur.execute("""
    SELECT country, COUNT(*)
    FROM outreach.company_target
    WHERE country IS NOT NULL AND TRIM(country) != ''
    GROUP BY country ORDER BY COUNT(*) DESC LIMIT 10
""")
print(f"\n  Country values:")
for r in cur.fetchall():
    print(f"    '{r[0]}': {r[1]:,}")

# Normalize variants to 'US'
cur.execute("""
    UPDATE outreach.company_target
    SET country = 'US'
    WHERE country IS NOT NULL
      AND UPPER(TRIM(country)) IN ('UNITED STATES', 'USA', 'U.S.', 'U.S.A.', 'UNITED STATES OF AMERICA')
      AND country != 'US'
""")
if cur.rowcount > 0:
    print(f"  Normalized {cur.rowcount:,} country values to 'US'")
    conn.commit()

# ============================================================
# Step 3: Current geography state
# ============================================================
print(f"\n{'='*65}")
print(f"  Geography State After Country Backfill")
print(f"{'='*65}")

cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE postal_code IS NOT NULL AND TRIM(postal_code) != '') AS has_zip,
        COUNT(*) FILTER (WHERE city IS NOT NULL AND TRIM(city) != '') AS has_city,
        COUNT(*) FILTER (WHERE state IS NOT NULL AND TRIM(state) != '') AS has_state,
        COUNT(*) FILTER (WHERE country IS NOT NULL AND TRIM(country) != '') AS has_country
    FROM outreach.company_target
""")
r = cur.fetchone()
print(f"  postal_code: {r[0]:,} ({100*r[0]/total:.1f}%)  gap: {total-r[0]:,}")
print(f"  city:        {r[1]:,} ({100*r[1]/total:.1f}%)  gap: {total-r[1]:,}")
print(f"  state:       {r[2]:,} ({100*r[2]/total:.1f}%)  gap: {total-r[2]:,}")
print(f"  country:     {r[3]:,} ({100*r[3]/total:.1f}%)  gap: {total-r[3]:,}")

# ============================================================
# Step 4: Export — companies missing ANY geography column
# ============================================================
cur.execute("""
    SELECT
        ct.outreach_id,
        o.domain,
        ct.postal_code,
        ct.city,
        ct.state,
        ct.country,
        CASE WHEN ct.postal_code IS NULL OR TRIM(ct.postal_code) = '' THEN 'NEED' ELSE 'OK' END AS zip_status,
        CASE WHEN ct.city IS NULL OR TRIM(ct.city) = '' THEN 'NEED' ELSE 'OK' END AS city_status,
        CASE WHEN ct.state IS NULL OR TRIM(ct.state) = '' THEN 'NEED' ELSE 'OK' END AS state_status
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
       OR (ct.city IS NULL OR TRIM(ct.city) = '')
       OR (ct.state IS NULL OR TRIM(ct.state) = '')
    ORDER BY o.domain
""")
rows = cur.fetchall()

outpath = "exports/ct_geography_gaps.csv"
os.makedirs("exports", exist_ok=True)
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["outreach_id", "domain", "postal_code", "city", "state", "country",
                "zip_status", "city_status", "state_status"])
    w.writerows(rows)

print(f"\n  Exported {len(rows):,} companies to {outpath}")

# Breakdown of what's needed
need_zip = sum(1 for r in rows if r[6] == 'NEED')
need_city = sum(1 for r in rows if r[7] == 'NEED')
need_state = sum(1 for r in rows if r[8] == 'NEED')
need_all = sum(1 for r in rows if r[6] == 'NEED' and r[7] == 'NEED' and r[8] == 'NEED')

print(f"    Need ZIP:       {need_zip:,}")
print(f"    Need city:      {need_city:,}")
print(f"    Need state:     {need_state:,}")
print(f"    Need all three: {need_all:,}")

# Unique domains
domains = set(r[1] for r in rows)
print(f"    Unique domains: {len(domains):,}")

conn.close()
print(f"\n  Done.")
