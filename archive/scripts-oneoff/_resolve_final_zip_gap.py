"""
Resolve the final 1,708 ZIP gap:
1. Identify international companies (non-US) for exclusion
2. Check blog/DOL/Hunter for ZIP evidence on remaining US/unknown
3. Report what's truly unreachable
"""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

cur.execute("""
    SELECT COUNT(*) FROM outreach.company_target
    WHERE postal_code IS NULL OR TRIM(postal_code) = ''
""")
total_gap = cur.fetchone()[0]
print(f"{'='*70}")
print(f"  Final ZIP Gap Resolution — {total_gap:,} companies")
print(f"{'='*70}")

# ============================================================
# STEP 1: Tag international vs US vs unknown
# ============================================================
# International = country is set AND not US
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.country IS NOT NULL AND TRIM(ct.country) != ''
      AND UPPER(TRIM(ct.country)) NOT IN ('US', 'USA', 'UNITED STATES')
""")
intl = cur.fetchone()[0]

# US = country is US
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.country IS NOT NULL
      AND UPPER(TRIM(ct.country)) IN ('US', 'USA', 'UNITED STATES')
""")
us = cur.fetchone()[0]

# Unknown country but has US state abbreviation
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND (ct.country IS NULL OR TRIM(ct.country) = '')
      AND ct.state IS NOT NULL AND LENGTH(TRIM(ct.state)) = 2
      AND EXISTS (
          SELECT 1 FROM reference.us_zip_codes z
          WHERE UPPER(z.state_id) = UPPER(TRIM(ct.state))
      )
""")
unknown_us_state = cur.fetchone()[0]

# Unknown country, no US state clue
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND (ct.country IS NULL OR TRIM(ct.country) = '')
      AND NOT (
          ct.state IS NOT NULL AND LENGTH(TRIM(ct.state)) = 2
          AND EXISTS (
              SELECT 1 FROM reference.us_zip_codes z
              WHERE UPPER(z.state_id) = UPPER(TRIM(ct.state))
          )
      )
""")
unknown_no_clue = cur.fetchone()[0]

print(f"\n  Classification:")
print(f"    International (non-US country):  {intl:,}")
print(f"    US (country=US):                 {us:,}")
print(f"    Unknown but has US state:        {unknown_us_state:,}")
print(f"    Unknown, no US clue:             {unknown_no_clue:,}")
print(f"    Total:                           {intl + us + unknown_us_state + unknown_no_clue:,}")

# ============================================================
# STEP 2: For US + unknown-with-US-state, check all data sources
# ============================================================
actionable_us = us + unknown_us_state
print(f"\n{'='*70}")
print(f"  Checking data sources for {actionable_us:,} US companies + {unknown_no_clue:,} unknowns")
print(f"{'='*70}")

# Blog URLs
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN company.company_master cm ON LOWER(
        REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
    ) = LOWER(o.domain)
    JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND csu.source_type IN ('about_page', 'contact_page')
""")
blog_urls = cur.fetchone()[0]
print(f"\n  Blog about/contact URLs:  {blog_urls:,}")

# Hunter company (city+state we haven't used yet)
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND hc.city IS NOT NULL AND TRIM(hc.city) != ''
      AND hc.state IS NOT NULL AND TRIM(hc.state) != ''
""")
hunter_city = cur.fetchone()[0]
print(f"  Hunter city+state:        {hunter_city:,}")

# Can we geocode those Hunter city+state to ZIP via reference?
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND hc.city IS NOT NULL AND TRIM(hc.city) != ''
      AND hc.state IS NOT NULL AND TRIM(hc.state) != ''
      AND EXISTS (
          SELECT 1 FROM reference.us_zip_codes z
          WHERE UPPER(z.city) = UPPER(TRIM(hc.city))
            AND UPPER(z.state_id) = UPPER(TRIM(hc.state))
      )
""")
hunter_geocodable = cur.fetchone()[0]
print(f"  Hunter geocodable to ZIP: {hunter_geocodable:,}")

# CT already has city+state that might match reference with fuzzy
cur.execute("""
    SELECT ct.city, ct.state, COUNT(*)
    FROM outreach.company_target ct
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND ct.city IS NOT NULL AND TRIM(ct.city) != ''
      AND ct.state IS NOT NULL AND TRIM(ct.state) != ''
      AND NOT EXISTS (
          SELECT 1 FROM reference.us_zip_codes z
          WHERE UPPER(z.city) = UPPER(TRIM(ct.city))
            AND UPPER(z.state_id) = UPPER(TRIM(ct.state))
      )
    GROUP BY ct.city, ct.state
    ORDER BY COUNT(*) DESC
""")
fuzzy_rows = cur.fetchall()
fuzzy_total = sum(r[2] for r in fuzzy_rows)
print(f"\n  CT has city+state but no exact reference match: {fuzzy_total:,}")
if fuzzy_rows:
    print(f"  Fuzzy candidates:")
    for r in fuzzy_rows[:20]:
        print(f"    '{r[0]}', '{r[1]}': {r[2]:,}")

# DOL bridge without filing
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
dol_linked = cur.fetchone()[0]
print(f"\n  DOL bridge (no filing ZIP): {dol_linked:,}")

# ============================================================
# STEP 3: Domain health check on unknowns
# ============================================================
print(f"\n{'='*70}")
print(f"  Domain check on {unknown_no_clue:,} unknown-country companies")
print(f"{'='*70}")

# Do they have .com TLD? (likely US)
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE o.domain LIKE '%%.com') AS dot_com,
        COUNT(*) FILTER (WHERE o.domain LIKE '%%.net') AS dot_net,
        COUNT(*) FILTER (WHERE o.domain LIKE '%%.org') AS dot_org,
        COUNT(*) FILTER (WHERE o.domain LIKE '%%.io' OR o.domain LIKE '%%.ai'
                         OR o.domain LIKE '%%.co') AS tech_tld,
        COUNT(*) FILTER (WHERE o.domain NOT LIKE '%%.com' AND o.domain NOT LIKE '%%.net'
                         AND o.domain NOT LIKE '%%.org' AND o.domain NOT LIKE '%%.io'
                         AND o.domain NOT LIKE '%%.ai' AND o.domain NOT LIKE '%%.co') AS other_tld,
        COUNT(*) AS total
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND (ct.country IS NULL OR TRIM(ct.country) = '')
      AND NOT (
          ct.state IS NOT NULL AND LENGTH(TRIM(ct.state)) = 2
          AND EXISTS (
              SELECT 1 FROM reference.us_zip_codes z
              WHERE UPPER(z.state_id) = UPPER(TRIM(ct.state))
          )
      )
""")
r = cur.fetchone()
print(f"  .com:     {r[0]:,}")
print(f"  .net:     {r[1]:,}")
print(f"  .org:     {r[2]:,}")
print(f"  .io/.ai/.co: {r[3]:,}")
print(f"  Other:    {r[4]:,}")

# Sample the unknowns
cur.execute("""
    SELECT o.domain, ci.company_name, ct.city, ct.state
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND (ct.country IS NULL OR TRIM(ct.country) = '')
      AND NOT (
          ct.state IS NOT NULL AND LENGTH(TRIM(ct.state)) = 2
          AND EXISTS (
              SELECT 1 FROM reference.us_zip_codes z
              WHERE UPPER(z.state_id) = UPPER(TRIM(ct.state))
          )
      )
    ORDER BY random()
    LIMIT 30
""")
print(f"\n  Random sample of unknowns:")
for r in cur.fetchall():
    city = r[2] or '-'
    state = r[3] or '-'
    print(f"    {r[0]:35s} {(r[1] or '')[:35]:35s} {city:20s} {state}")

conn.close()
print(f"\n{'='*70}")
print(f"  Done.")
print(f"{'='*70}")
