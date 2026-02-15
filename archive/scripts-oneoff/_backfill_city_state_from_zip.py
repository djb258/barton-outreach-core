"""Backfill city+state from reference.us_zip_codes where CT has ZIP but missing city/state."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# How many have ZIP but missing city or state?
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE (city IS NULL OR TRIM(city) = '')
                         AND postal_code IS NOT NULL AND TRIM(postal_code) != '') AS need_city,
        COUNT(*) FILTER (WHERE (state IS NULL OR TRIM(state) = '')
                         AND postal_code IS NOT NULL AND TRIM(postal_code) != '') AS need_state
    FROM outreach.company_target
""")
r = cur.fetchone()
print(f"Have ZIP but missing city:  {r[0]:,}")
print(f"Have ZIP but missing state: {r[1]:,}")

# Backfill city from reference
cur.execute("""
    UPDATE outreach.company_target ct
    SET city = z.city
    FROM reference.us_zip_codes z
    WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
      AND ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
      AND (ct.city IS NULL OR TRIM(ct.city) = '')
""")
print(f"\nCity backfilled:  {cur.rowcount:,}")

# Backfill state from reference
cur.execute("""
    UPDATE outreach.company_target ct
    SET state = z.state_id
    FROM reference.us_zip_codes z
    WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
      AND ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
      AND (ct.state IS NULL OR TRIM(ct.state) = '')
""")
print(f"State backfilled: {cur.rowcount:,}")

# Backfill country for anything that now has state but no country
cur.execute("""
    UPDATE outreach.company_target
    SET country = 'US'
    WHERE (country IS NULL OR TRIM(country) = '')
      AND state IS NOT NULL AND TRIM(state) != ''
""")
print(f"Country backfilled: {cur.rowcount:,}")

conn.commit()

# Final geography state
total = 95837
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE postal_code IS NOT NULL AND TRIM(postal_code) != '') AS has_zip,
        COUNT(*) FILTER (WHERE city IS NOT NULL AND TRIM(city) != '') AS has_city,
        COUNT(*) FILTER (WHERE state IS NOT NULL AND TRIM(state) != '') AS has_state,
        COUNT(*) FILTER (WHERE country IS NOT NULL AND TRIM(country) != '') AS has_country
    FROM outreach.company_target
""")
r = cur.fetchone()
print(f"\nGeography after backfill:")
print(f"  postal_code: {r[0]:,} ({100*r[0]/total:.1f}%)  gap: {total-r[0]:,}")
print(f"  city:        {r[1]:,} ({100*r[1]/total:.1f}%)  gap: {total-r[1]:,}")
print(f"  state:       {r[2]:,} ({100*r[2]/total:.1f}%)  gap: {total-r[2]:,}")
print(f"  country:     {r[3]:,} ({100*r[3]/total:.1f}%)  gap: {total-r[3]:,}")

conn.close()
