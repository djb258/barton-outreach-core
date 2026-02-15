"""Export domains for CT companies still missing postal_code."""
import os, sys, csv, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

cur.execute("""
    SELECT ct.outreach_id, o.domain, ct.city, ct.state, ct.country
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND o.domain IS NOT NULL AND TRIM(o.domain) != ''
    ORDER BY o.domain
""")
rows = cur.fetchall()

outpath = "exports/ct_zip_gap_domains.csv"
os.makedirs("exports", exist_ok=True)
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["outreach_id", "domain", "city", "state", "country"])
    w.writerows(rows)

print(f"Exported {len(rows):,} domains to {outpath}")
conn.close()
