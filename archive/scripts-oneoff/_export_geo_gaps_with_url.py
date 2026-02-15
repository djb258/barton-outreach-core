"""Re-export geography gaps with full URL."""
import os, sys, csv, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

cur.execute("""
    SELECT
        ct.outreach_id,
        o.domain,
        'https://' || o.domain AS url,
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
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["outreach_id", "domain", "url", "postal_code", "city", "state", "country",
                "zip_status", "city_status", "state_status"])
    w.writerows(rows)

print(f"Exported {len(rows):,} companies to {outpath}")
conn.close()
