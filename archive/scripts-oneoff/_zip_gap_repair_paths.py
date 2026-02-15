"""Map repair paths for the 19,273 CT companies still missing postal_code."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# Total missing
cur.execute("""
    SELECT COUNT(*) FROM outreach.company_target
    WHERE postal_code IS NULL OR TRIM(postal_code) = ''
""")
total_missing = cur.fetchone()[0]
print(f"{'='*70}")
print(f"  ZIP Gap Repair Path Analysis — {total_missing:,} companies")
print(f"{'='*70}")

# ============================================================
# PATH 1: Blog URLs already scraped
# ============================================================
cur.execute("""
    SELECT
        COUNT(DISTINCT ct.outreach_id) AS has_any_url,
        COUNT(DISTINCT ct.outreach_id) FILTER (
            WHERE csu.source_type = 'about_page'
        ) AS has_about,
        COUNT(DISTINCT ct.outreach_id) FILTER (
            WHERE csu.source_type = 'contact_page'
        ) AS has_contact
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN company.company_master cm ON LOWER(
        REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
    ) = LOWER(o.domain)
    JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\n  PATH 1: Blog URLs (already scraped, FREE)")
print(f"    Has any URL:     {r[0]:,}")
print(f"    Has about page:  {r[1]:,}")
print(f"    Has contact page: {r[2]:,}")

# ============================================================
# PATH 2: Hunter company data (already in DB — city+state but no ZIP)
# ============================================================
cur.execute("""
    SELECT
        COUNT(*) AS matched,
        COUNT(hc.city) FILTER (WHERE hc.city IS NOT NULL AND TRIM(hc.city) != '') AS has_city,
        COUNT(hc.state) FILTER (WHERE hc.state IS NOT NULL AND TRIM(hc.state) != '') AS has_state,
        COUNT(hc.street) FILTER (WHERE hc.street IS NOT NULL AND TRIM(hc.street) != '') AS has_street
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\n  PATH 2: Hunter company (already in DB)")
print(f"    Domain matched:  {r[0]:,}")
print(f"    Has city:        {r[1]:,}")
print(f"    Has state:       {r[2]:,}")
print(f"    Has street:      {r[3]:,}  (street+city+state = geocodable)")

# ============================================================
# PATH 3: DOL bridge exists but no ZIP evidence
# ============================================================
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
print(f"\n  PATH 3: DOL bridge (has EIN, no ZIP evidence found)")
print(f"    Has DOL link:    {cur.fetchone()[0]:,}")

# ============================================================
# PATH 4: Domain exists (could re-enrich via Hunter API or Clay)
# ============================================================
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(o.domain) FILTER (WHERE o.domain IS NOT NULL AND TRIM(o.domain) != '') AS has_domain
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\n  PATH 4: Has domain (API re-enrichment via Hunter/Clay)")
print(f"    Has domain:      {r[1]:,} / {r[0]:,}")

# ============================================================
# What city+state data do the missing companies have?
# ============================================================
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE ct.city IS NOT NULL AND TRIM(ct.city) != ''
                         AND ct.state IS NOT NULL AND TRIM(ct.state) != '') AS has_city_state,
        COUNT(*) FILTER (WHERE ct.state IS NOT NULL AND TRIM(ct.state) != ''
                         AND (ct.city IS NULL OR TRIM(ct.city) = '')) AS state_only,
        COUNT(*) FILTER (WHERE (ct.city IS NULL OR TRIM(ct.city) = '')
                         AND (ct.state IS NULL OR TRIM(ct.state) = '')) AS no_location
    FROM outreach.company_target ct
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\n  Current location data on missing companies:")
print(f"    Has city+state:  {r[0]:,}  (multi-ZIP cities, need precise ZIP)")
print(f"    State only:      {r[1]:,}")
print(f"    No location:     {r[2]:,}")

# ============================================================
# Overlap: has domain AND no location at all (worst case)
# ============================================================
cur.execute("""
    SELECT
        COUNT(*) AS no_loc_total,
        COUNT(o.domain) FILTER (WHERE o.domain IS NOT NULL AND TRIM(o.domain) != '') AS has_domain
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND (ct.city IS NULL OR TRIM(ct.city) = '')
      AND (ct.state IS NULL OR TRIM(ct.state) = '')
""")
r = cur.fetchone()
print(f"\n  Worst case (no location + no ZIP):")
print(f"    Total:           {r[0]:,}")
print(f"    Has domain:      {r[1]:,}  (enrichable)")
print(f"    No domain:       {r[0] - r[1]:,}  (dead end)")

# ============================================================
# Cost estimate: Hunter API re-enrichment
# ============================================================
cur.execute("""
    SELECT COUNT(DISTINCT o.domain)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND o.domain IS NOT NULL AND TRIM(o.domain) != ''
""")
domains = cur.fetchone()[0]
print(f"\n  {'='*70}")
print(f"  Cost Estimates:")
print(f"  {'='*70}")
print(f"  Unique domains needing enrichment: {domains:,}")
print(f"  Hunter API ($0.008/call):  ${domains * 0.008:,.2f}")
print(f"  Clay (est $0.005/call):    ${domains * 0.005:,.2f}")

conn.close()
print(f"\n{'='*70}")
print(f"  Done.")
print(f"{'='*70}")
