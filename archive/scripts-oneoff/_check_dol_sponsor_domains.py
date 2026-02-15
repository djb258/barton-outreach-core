"""
Check if DOL sponsors (form_5500) have been enriched with domains via Hunter
that we can fuzzy-match against Clay company domains.
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
print(f"  DOL Sponsor Domain Enrichment Check")
print(f"{'='*75}")

# 1. How many unique DOL EINs exist that are NOT in outreach.dol?
cur.execute("""
    SELECT COUNT(DISTINCT sponsor_dfe_ein)
    FROM dol.form_5500
    WHERE sponsor_dfe_ein IS NOT NULL
      AND sponsor_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
""")
unmatched_eins = cur.fetchone()[0]
print(f"\n  Unmatched DOL EINs (form_5500): {unmatched_eins:,}")

cur.execute("""
    SELECT COUNT(DISTINCT sf_spons_ein)
    FROM dol.form_5500_sf
    WHERE sf_spons_ein IS NOT NULL
      AND sf_spons_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
""")
unmatched_sf = cur.fetchone()[0]
print(f"  Unmatched DOL EINs (form_5500_sf): {unmatched_sf:,}")

# 2. Check if hunter_company has domain data linked to DOL EINs
# hunter_company doesn't have EIN directly, but it has domain
# The enrichment path was: EIN -> Hunter search -> find domain
# Let's check if there's any EIN-to-domain mapping table
print(f"\n  Checking for EIN-to-domain mapping tables...")
cur.execute("""
    SELECT table_schema, table_name, column_name
    FROM information_schema.columns
    WHERE column_name ILIKE '%%ein%%'
      AND table_schema NOT IN ('information_schema', 'pg_catalog')
    ORDER BY table_schema, table_name
""")
for r in cur.fetchall():
    print(f"    {r[0]}.{r[1]}.{r[2]}")

# 3. Check enrichment.hunter_contact for EIN data
cur.execute("""SELECT column_name FROM information_schema.columns
    WHERE table_schema='enrichment' AND table_name='hunter_contact'
    AND column_name ILIKE '%%ein%%'""")
hc_ein = [r[0] for r in cur.fetchall()]
print(f"\n  hunter_contact EIN columns: {hc_ein if hc_ein else 'NONE'}")

# 4. The real enrichment path: Hunter was given DOL company names
# and returned domains. That mapping would be in hunter_company.
# Let's see if hunter_company.source shows DOL-related sources
cur.execute("""
    SELECT source, COUNT(*)
    FROM enrichment.hunter_company
    WHERE source IS NOT NULL
    GROUP BY source ORDER BY COUNT(*) DESC
""")
print(f"\n  hunter_company by source:")
for r in cur.fetchall():
    print(f"    {(r[0] or 'NULL'):40s}: {r[1]:,}")

cur.execute("""
    SELECT source_file, COUNT(*)
    FROM enrichment.hunter_company
    WHERE source_file IS NOT NULL
    GROUP BY source_file ORDER BY COUNT(*) DESC LIMIT 15
""")
print(f"\n  hunter_company by source_file (top 15):")
for r in cur.fetchall():
    print(f"    {(r[0] or 'NULL'):60s}: {r[1]:,}")

# 5. Check outreach.dol.url_enrichment_data
cur.execute("""
    SELECT COUNT(*) FROM outreach.dol
    WHERE url_enrichment_data IS NOT NULL AND TRIM(url_enrichment_data::text) <> ''
""")
print(f"\n  outreach.dol with url_enrichment_data: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT url_enrichment_data FROM outreach.dol
    WHERE url_enrichment_data IS NOT NULL AND TRIM(url_enrichment_data::text) <> ''
    LIMIT 3
""")
print(f"  Sample url_enrichment_data:")
for r in cur.fetchall():
    print(f"    {str(r[0])[:120]}")

# 6. Direct approach: match Clay domains against hunter_company domains
# where those hunter_company records are linked to DOL-source outreach_ids
print(f"\n  {'='*65}")
print(f"  DIRECT DOMAIN MATCHING")
print(f"  {'='*65}")

# The 52,629 hunter_dol_enrichment companies have domains in outreach.outreach
# Those domains were found by Hunter for DOL sponsors
# Can we fuzzy-match Clay domains against them?

# First: exact domain match (already checked = 0 overlap)
# Second: fuzzy domain match (strip www, normalize)
cur.execute("""
    WITH clay_domains AS (
        SELECT DISTINCT
            o.outreach_id,
            LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')) AS domain_clean,
            SPLIT_PART(LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')), '.', 1) AS domain_word
        FROM outreach.outreach o
        JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
        LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
        WHERE d.outreach_id IS NULL
          AND ci.source_system IN ('clay_import', 'clay')
          AND o.domain IS NOT NULL
    ),
    dol_domains AS (
        SELECT DISTINCT
            o.outreach_id,
            d.ein,
            LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')) AS domain_clean,
            SPLIT_PART(LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')), '.', 1) AS domain_word
        FROM outreach.outreach o
        JOIN outreach.dol d ON d.outreach_id = o.outreach_id
        WHERE o.domain IS NOT NULL
    )
    SELECT COUNT(DISTINCT cd.outreach_id)
    FROM clay_domains cd
    JOIN dol_domains dd ON cd.domain_word = dd.domain_word
        AND cd.domain_clean <> dd.domain_clean
""")
word_match = cur.fetchone()[0]
print(f"\n  Domain keyword match (same first word, diff full domain): {word_match:,}")

# Trigram on domain itself
cur.execute("""
    SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm'
""")
if cur.fetchone():
    cur.execute("""
        WITH clay_domains AS (
            SELECT DISTINCT
                o.outreach_id,
                LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')) AS domain_clean
            FROM outreach.outreach o
            JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
            LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
            WHERE d.outreach_id IS NULL
              AND ci.source_system IN ('clay_import', 'clay')
              AND o.domain IS NOT NULL
            LIMIT 1000
        ),
        dol_domains AS (
            SELECT DISTINCT
                d.ein,
                LOWER(REGEXP_REPLACE(o.domain, '^www\\.', '')) AS domain_clean
            FROM outreach.outreach o
            JOIN outreach.dol d ON d.outreach_id = o.outreach_id
            WHERE o.domain IS NOT NULL
        )
        SELECT cd.domain_clean, dd.domain_clean, dd.ein,
               similarity(cd.domain_clean, dd.domain_clean) AS sim
        FROM clay_domains cd
        JOIN dol_domains dd ON similarity(cd.domain_clean, dd.domain_clean) >= 0.6
        WHERE cd.domain_clean <> dd.domain_clean
        ORDER BY sim DESC
        LIMIT 20
    """)
    results = cur.fetchall()
    print(f"\n  Fuzzy domain matches (sim >= 0.6, sample of 1000 Clay domains):")
    if results:
        for r in results:
            print(f"    Clay: {r[0]:35s} -> DOL: {r[1]:35s} EIN={r[2]} sim={r[3]:.2f}")
    else:
        print(f"    None found")

conn.close()
print(f"\n{'='*75}")
print(f"  Done.")
print(f"{'='*75}")
