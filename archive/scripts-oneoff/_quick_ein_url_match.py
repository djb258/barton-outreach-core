"""Quick: exact domain match Clay -> ein_urls + sub-hub coverage for Clay no-DOL."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

print(f"{'='*75}")
print(f"  Quick EIN-URL Match + Sub-Hub Coverage")
print(f"{'='*75}")

# ein_urls stats
cur.execute("SELECT COUNT(*), COUNT(DISTINCT ein), COUNT(DISTINCT domain) FROM dol.ein_urls")
r = cur.fetchone()
print(f"\n  dol.ein_urls: {r[0]:,} rows, {r[1]:,} EINs, {r[2]:,} domains")

# EXACT domain match
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN dol.ein_urls eu ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
""")
exact = cur.fetchone()[0]
print(f"\n  Exact domain match (ALL no-DOL -> ein_urls): {exact:,}")

# Sample
cur.execute("""
    SELECT o.domain, eu.company_name, eu.ein, eu.state, ct.state
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN dol.ein_urls eu ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
    LIMIT 15
""")
print(f"\n  Sample exact matches:")
for r in cur.fetchall():
    sm = "OK" if (r[3] or '').upper().strip() == (r[4] or '').upper().strip() else "DIFF"
    print(f"    {r[0]:30s} -> {(r[1] or '')[:28]:28s} EIN={r[2]} DOL:{r[3]} CT:{r[4]} [{sm}]")

# State match rate
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(CASE WHEN UPPER(TRIM(eu.state)) = UPPER(TRIM(ct.state)) THEN 1 END) AS state_match
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN dol.ein_urls eu ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
""")
r = cur.fetchone()
print(f"\n  State confirmation: {r[1]:,} / {r[0]:,} ({100*r[1]/r[0]:.0f}%) match")

# ================================================================
# SUB-HUB COVERAGE for all no-DOL companies
# ================================================================
print(f"\n  {'='*65}")
print(f"  SUB-HUB COVERAGE — No-DOL Companies (24,451)")

cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(CASE WHEN b.outreach_id IS NOT NULL THEN 1 END) AS has_blog,
        COUNT(CASE WHEN bs.outreach_id IS NOT NULL THEN 1 END) AS has_bit
    FROM outreach.company_target ct
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
    LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
""")
r = cur.fetchone()
print(f"\n    Total no-DOL:   {r[0]:,}")
print(f"    Has Blog:       {r[1]:,} ({100*r[1]/r[0]:.0f}%)")
print(f"    Has BIT score:  {r[2]:,} ({100*r[2]/r[0]:.0f}%)")

# People slots
cur.execute("""
    SELECT
        ps.slot_type,
        COUNT(*) AS total,
        COUNT(CASE WHEN ps.is_filled THEN 1 END) AS filled
    FROM people.company_slot ps
    JOIN outreach.company_target ct ON ct.outreach_id = ps.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
    GROUP BY ps.slot_type ORDER BY ps.slot_type
""")
print(f"\n    People Slots (no-DOL companies):")
for r in cur.fetchall():
    print(f"      {r[0]}: {r[2]:,} filled / {r[1]:,} ({100*r[2]/r[1]:.0f}%)")

# Blog/About URLs
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN company.company_master cm ON LOWER(REPLACE(REPLACE(REPLACE(cm.website_url,
        'http://',''),'https://',''),'www.','')) = LOWER(o.domain)
    JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
    WHERE d.outreach_id IS NULL
""")
has_urls = cur.fetchone()[0]
print(f"\n    Has company_source_urls: {has_urls:,}")

conn.close()
print(f"\n{'='*75}")
print(f"  Done.")
print(f"{'='*75}")
