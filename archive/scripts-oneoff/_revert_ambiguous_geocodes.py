"""Revert CITY_STATE_GEOCODE repairs where city has 6+ ZIPs (ambiguous)."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Count before
cur.execute("""
    SELECT COUNT(*) FROM outreach.company_target
    WHERE postal_code IS NOT NULL AND TRIM(postal_code) != ''
""")
before = cur.fetchone()[0]

# Revert: NULL out postal_code where source=CITY_STATE_GEOCODE and city has 6+ ZIPs
cur.execute("""
    WITH zip_counts AS (
        SELECT
            UPPER(city) AS ref_city,
            UPPER(state_id) AS ref_state,
            COUNT(*) AS zip_count
        FROM reference.us_zip_codes
        GROUP BY UPPER(city), UPPER(state_id)
    )
    UPDATE outreach.company_target ct
    SET postal_code = NULL,
        postal_code_source = NULL,
        postal_code_updated_at = NULL
    FROM zip_counts zc
    WHERE ct.postal_code_source = 'CITY_STATE_GEOCODE'
      AND UPPER(TRIM(ct.city)) = zc.ref_city
      AND UPPER(TRIM(ct.state)) = zc.ref_state
      AND zc.zip_count >= 6
""")
reverted = cur.rowcount
conn.commit()

# Count after
cur.execute("""
    SELECT COUNT(*) FROM outreach.company_target
    WHERE postal_code IS NOT NULL AND TRIM(postal_code) != ''
""")
after = cur.fetchone()[0]

# Remaining geocode source
cur.execute("""
    SELECT postal_code_source, COUNT(*)
    FROM outreach.company_target
    WHERE postal_code_source IS NOT NULL
    GROUP BY postal_code_source
    ORDER BY COUNT(*) DESC
""")

total = 95837
print(f"Reverted {reverted:,} ambiguous geocodes (city has 6+ ZIPs)")
print(f"  Before: {before:,} ({100*before/total:.1f}%)")
print(f"  After:  {after:,} ({100*after/total:.1f}%)")
print(f"\nBy source:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]:,}")

# Remaining gap
remaining = total - after
print(f"\nStill missing: {remaining:,} ({100*remaining/total:.1f}%)")

conn.close()
