"""
Match Clay no-DOL company domains against dol.ein_urls.
This is the direct bridge: Clay domain -> ein_urls domain -> EIN.
Also try fuzzy domain matching.
"""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

print(f"{'='*75}")
print(f"  Clay Domain -> dol.ein_urls Bridge Analysis")
print(f"{'='*75}")

# ein_urls stats
cur.execute("SELECT COUNT(*), COUNT(DISTINCT ein), COUNT(DISTINCT domain) FROM dol.ein_urls")
r = cur.fetchone()
print(f"\n  dol.ein_urls: {r[0]:,} rows, {r[1]:,} unique EINs, {r[2]:,} unique domains")

# How many ein_urls EINs are NOT already in outreach.dol?
cur.execute("""
    SELECT COUNT(DISTINCT eu.ein)
    FROM dol.ein_urls eu
    WHERE eu.ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
""")
print(f"  EINs NOT yet in outreach.dol: {cur.fetchone()[0]:,}")

# ================================================================
# EXACT domain match: Clay domain = ein_urls domain
# ================================================================
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN dol.ein_urls eu ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND ci.source_system IN ('clay_import', 'clay')
""")
exact = cur.fetchone()[0]
print(f"\n  EXACT domain match (Clay domain = ein_urls domain): {exact:,}")

# Including EINs already in outreach.dol
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN dol.ein_urls eu ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND ci.source_system IN ('clay_import', 'clay')
      AND eu.ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
""")
exact_new_ein = cur.fetchone()[0]
print(f"  (with new EINs only): {exact_new_ein:,}")

# Sample
cur.execute("""
    SELECT o.domain, eu.company_name, eu.ein, eu.state, ct.state AS ct_state
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN dol.ein_urls eu ON LOWER(eu.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND ci.source_system IN ('clay_import', 'clay')
    LIMIT 15
""")
print(f"\n  Sample exact matches:")
for r in cur.fetchall():
    state_match = "YES" if (r[3] or '').upper() == (r[4] or '').upper() else "NO"
    print(f"    {r[0]:30s} -> {(r[1] or '')[:30]:30s} EIN={r[2]} DOL:{r[3]} CT:{r[4]} state_match={state_match}")

# ================================================================
# FUZZY domain match with pg_trgm
# ================================================================
print(f"\n  {'='*65}")
print(f"  FUZZY DOMAIN MATCHING (pg_trgm)")

# Create temp tables for performance
cur.execute("""
    CREATE TEMP TABLE tmp_clay_domains AS
    SELECT DISTINCT
        o.outreach_id,
        LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')) AS domain_clean,
        SPLIT_PART(LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')), '.', 1) AS domain_word,
        UPPER(TRIM(ct.state)) AS ct_state,
        LEFT(TRIM(ct.postal_code), 5) AS ct_zip
    FROM outreach.outreach o
    JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    WHERE d.outreach_id IS NULL
      AND ci.source_system IN ('clay_import', 'clay')
      AND o.domain IS NOT NULL
""")

cur.execute("""
    CREATE TEMP TABLE tmp_ein_domains AS
    SELECT DISTINCT
        eu.ein,
        LOWER(REGEXP_REPLACE(eu.domain, '^www\\.', '')) AS domain_clean,
        SPLIT_PART(LOWER(REGEXP_REPLACE(eu.domain, '^www\\.', '')), '.', 1) AS domain_word,
        eu.company_name,
        UPPER(TRIM(eu.state)) AS dol_state
    FROM dol.ein_urls eu
    WHERE eu.domain IS NOT NULL AND eu.ein IS NOT NULL
""")

cur.execute("CREATE INDEX idx_cd_word ON tmp_clay_domains(domain_word)")
cur.execute("CREATE INDEX idx_ed_word ON tmp_ein_domains(domain_word)")
cur.execute("CREATE INDEX idx_cd_trgm ON tmp_clay_domains USING gin(domain_clean gin_trgm_ops)")
cur.execute("CREATE INDEX idx_ed_trgm ON tmp_ein_domains USING gin(domain_clean gin_trgm_ops)")

cur.execute("SELECT COUNT(*) FROM tmp_clay_domains")
print(f"\n  Clay domains: {cur.fetchone()[0]:,}")
cur.execute("SELECT COUNT(*) FROM tmp_ein_domains")
print(f"  ein_urls domains: {cur.fetchone()[0]:,}")

# Fuzzy match >= 0.6 with state confirmation
cur.execute("""
    SELECT COUNT(DISTINCT cd.outreach_id)
    FROM tmp_clay_domains cd
    JOIN tmp_ein_domains ed
        ON similarity(cd.domain_clean, ed.domain_clean) >= 0.6
       AND cd.ct_state = ed.dol_state
    WHERE cd.domain_clean <> ed.domain_clean
""")
fuzzy_06_state = cur.fetchone()[0]
print(f"\n  Fuzzy domain (>=0.6) + same state: {fuzzy_06_state:,}")

# Fuzzy >= 0.5 with state
cur.execute("""
    SELECT COUNT(DISTINCT cd.outreach_id)
    FROM tmp_clay_domains cd
    JOIN tmp_ein_domains ed
        ON similarity(cd.domain_clean, ed.domain_clean) >= 0.5
       AND cd.ct_state = ed.dol_state
    WHERE cd.domain_clean <> ed.domain_clean
""")
fuzzy_05_state = cur.fetchone()[0]
print(f"  Fuzzy domain (>=0.5) + same state: {fuzzy_05_state:,}")

# Domain word match + state (same first word, different TLD or suffix)
cur.execute("""
    SELECT COUNT(DISTINCT cd.outreach_id)
    FROM tmp_clay_domains cd
    JOIN tmp_ein_domains ed
        ON cd.domain_word = ed.domain_word
       AND cd.ct_state = ed.dol_state
    WHERE cd.domain_clean <> ed.domain_clean
      AND LENGTH(cd.domain_word) >= 4
""")
word_state = cur.fetchone()[0]
print(f"  Domain keyword match + same state: {word_state:,}")

# Sample fuzzy matches
cur.execute("""
    SELECT cd.domain_clean, ed.domain_clean, ed.company_name, ed.ein,
           cd.ct_state, ed.dol_state,
           similarity(cd.domain_clean, ed.domain_clean) AS sim
    FROM tmp_clay_domains cd
    JOIN tmp_ein_domains ed
        ON similarity(cd.domain_clean, ed.domain_clean) >= 0.5
       AND cd.ct_state = ed.dol_state
    WHERE cd.domain_clean <> ed.domain_clean
    ORDER BY sim DESC
    LIMIT 20
""")
print(f"\n  Fuzzy domain match samples (>=0.5 + state):")
for r in cur.fetchall():
    print(f"    Clay: {r[0]:32s} -> DOL: {r[1]:32s} {(r[2] or '')[:25]:25s} EIN={r[3]} {r[4]} sim={r[6]:.2f}")

# ================================================================
# Summary
# ================================================================
print(f"\n  {'='*75}")
print(f"  SUMMARY")
print(f"  {'='*75}")
print(f"    Clay no-DOL companies: 24,451")
print(f"")
print(f"    Exact domain match:            {exact:>6,}  HIGHEST confidence")
print(f"    Fuzzy domain (>=0.6) + state:  {fuzzy_06_state:>6,}  HIGH confidence")
print(f"    Fuzzy domain (>=0.5) + state:  {fuzzy_05_state:>6,}  MEDIUM confidence")
print(f"    Domain keyword + state:        {word_state:>6,}  NEEDS REVIEW")
total = exact + fuzzy_05_state  # fuzzy_06 is subset of fuzzy_05
print(f"")
print(f"    Current DOL: 69,949 / 94,129 (74.3%)")
print(f"    + exact domain:     {69949 + exact:,} ({100*(69949+exact)/94129:.1f}%)")
print(f"    + fuzzy(>=0.5)+st:  {69949 + exact + fuzzy_05_state:,} ({100*(69949+exact+fuzzy_05_state)/94129:.1f}%)")

conn.close()
print(f"\n{'='*75}")
print(f"  Done.")
print(f"{'='*75}")
