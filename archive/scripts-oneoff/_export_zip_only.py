"""Export companies missing ZIP — just outreach_id, domain, url."""
import os, sys, csv, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

cur.execute("""
    SELECT ct.outreach_id, o.domain, 'https://' || o.domain AS url
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
    ORDER BY o.domain
""")
rows = cur.fetchall()

outpath = "exports/ct_need_zip.csv"
os.makedirs("exports", exist_ok=True)
with open(outpath, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["outreach_id", "domain", "url"])
    w.writerows(rows)

print(f"Exported {len(rows):,} companies to {outpath}")
print(f"Unique domains: {len(set(r[1] for r in rows)):,}")
conn.close()
