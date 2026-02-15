"""
Check if Clay no-DOL company domains match Hunter-enriched DOL sponsor domains.

Path: Clay domain → hunter_company domain → DOL EIN
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
print(f"  Domain-Based DOL Bridge Analysis")
print(f"{'='*75}")

# 1. How was the existing DOL bridge built? Check outreach.dol for domain/EIN linkage
cur.execute("""SELECT column_name FROM information_schema.columns
    WHERE table_schema='outreach' AND table_name='dol' ORDER BY ordinal_position""")
dol_cols = [r[0] for r in cur.fetchall()]
print(f"\n  outreach.dol columns: {', '.join(dol_cols)}")

# 2. No-DOL Clay companies
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
      AND ci.source_system IN ('clay_import', 'clay')
""")
clay_no_dol = cur.fetchone()[0]
print(f"\n  Clay companies without DOL bridge: {clay_no_dol:,}")

# 3. Get their domains
cur.execute("""
    SELECT COUNT(DISTINCT o.domain)
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    WHERE d.outreach_id IS NULL
      AND ci.source_system IN ('clay_import', 'clay')
      AND o.domain IS NOT NULL
""")
print(f"  Unique domains: {cur.fetchone()[0]:,}")

# 4. Check if outreach.dol has EIN + what data it carries
cur.execute("SELECT COUNT(*), COUNT(DISTINCT ein) FROM outreach.dol WHERE ein IS NOT NULL")
r = cur.fetchone()
print(f"\n  outreach.dol: {r[0]:,} records, {r[1]:,} unique EINs")

# 5. For companies WITH DOL bridge, check if their domains are in hunter_company
# This tells us the enrichment path
cur.execute("""
    SELECT COUNT(DISTINCT o.domain)
    FROM outreach.outreach o
    JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
""")
print(f"  DOL-bridged companies found in hunter_company: {cur.fetchone()[0]:,}")

# 6. KEY QUESTION: Do Clay no-DOL domains match domains of DOL-bridged companies?
# (Same domain exists twice - once from Clay, once from DOL intake)
cur.execute("""
    SELECT COUNT(DISTINCT clay_o.outreach_id)
    FROM outreach.outreach clay_o
    JOIN outreach.company_target clay_ct ON clay_ct.outreach_id = clay_o.outreach_id
    JOIN cl.company_identity clay_ci ON clay_ci.outreach_id = clay_o.outreach_id
    LEFT JOIN outreach.dol clay_d ON clay_d.outreach_id = clay_o.outreach_id
    -- Find if this domain has ANOTHER outreach_id that HAS a DOL bridge
    JOIN outreach.outreach dol_o ON LOWER(dol_o.domain) = LOWER(clay_o.domain)
        AND dol_o.outreach_id <> clay_o.outreach_id
    JOIN outreach.dol dol_d ON dol_d.outreach_id = dol_o.outreach_id
    WHERE clay_d.outreach_id IS NULL
      AND clay_ci.source_system IN ('clay_import', 'clay')
""")
dup_domain = cur.fetchone()[0]
print(f"\n  Clay no-DOL domains that match a DOL-bridged domain: {dup_domain:,}")

# 7. Do Clay no-DOL domains appear in hunter_company with an outreach_id that HAS DOL?
cur.execute("""
    SELECT COUNT(DISTINCT clay_o.outreach_id)
    FROM outreach.outreach clay_o
    JOIN cl.company_identity clay_ci ON clay_ci.outreach_id = clay_o.outreach_id
    LEFT JOIN outreach.dol clay_d ON clay_d.outreach_id = clay_o.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(clay_o.domain)
    WHERE clay_d.outreach_id IS NULL
      AND clay_ci.source_system IN ('clay_import', 'clay')
      AND hc.outreach_id IS NOT NULL
      AND hc.outreach_id IN (SELECT outreach_id FROM outreach.dol)
""")
hc_dol_link = cur.fetchone()[0]
print(f"  Clay domains in hunter_company linked to DOL outreach_id: {hc_dol_link:,}")

# 8. What about the hunter_dol_enrichment source? Check how those were built
print(f"\n  CL source_system breakdown (all companies):")
cur.execute("""
    SELECT ci.source_system, COUNT(*),
        COUNT(CASE WHEN d.outreach_id IS NOT NULL THEN 1 END) AS has_dol,
        COUNT(CASE WHEN d.outreach_id IS NULL THEN 1 END) AS no_dol
    FROM cl.company_identity ci
    JOIN outreach.outreach o ON o.outreach_id = ci.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = ci.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ci.outreach_id
    WHERE ci.outreach_id IS NOT NULL
    GROUP BY ci.source_system ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    pct_dol = 100 * r[2] / r[1] if r[1] > 0 else 0
    print(f"    {(r[0] or 'NULL'):30s}: {r[1]:>6,} total  |  {r[2]:>6,} DOL ({pct_dol:.0f}%)  |  {r[3]:>6,} no DOL")

# 9. For the hunter_dol_enrichment source, check if their domains overlap with Clay no-DOL
print(f"\n  hunter_dol_enrichment companies:")
cur.execute("""
    SELECT COUNT(*) FROM cl.company_identity WHERE source_system = 'hunter_dol_enrichment'
""")
print(f"    Total: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT COUNT(DISTINCT hde_o.domain)
    FROM cl.company_identity hde_ci
    JOIN outreach.outreach hde_o ON hde_o.outreach_id = hde_ci.outreach_id
    WHERE hde_ci.source_system = 'hunter_dol_enrichment'
      AND hde_o.domain IS NOT NULL
""")
print(f"    Unique domains: {cur.fetchone()[0]:,}")

# 10. Domain overlap: Clay no-DOL domains that exist in hunter_dol_enrichment
cur.execute("""
    SELECT COUNT(DISTINCT clay_o.domain)
    FROM outreach.outreach clay_o
    JOIN cl.company_identity clay_ci ON clay_ci.outreach_id = clay_o.outreach_id
    LEFT JOIN outreach.dol clay_d ON clay_d.outreach_id = clay_o.outreach_id
    WHERE clay_d.outreach_id IS NULL
      AND clay_ci.source_system IN ('clay_import', 'clay')
      AND LOWER(clay_o.domain) IN (
          SELECT LOWER(hde_o.domain)
          FROM cl.company_identity hde_ci
          JOIN outreach.outreach hde_o ON hde_o.outreach_id = hde_ci.outreach_id
          WHERE hde_ci.source_system = 'hunter_dol_enrichment'
      )
""")
overlap = cur.fetchone()[0]
print(f"\n  Clay no-DOL domains also in hunter_dol_enrichment: {overlap:,}")

# 11. For those overlapping domains, the DOL bridge should already exist
# under the hunter_dol_enrichment outreach_id. We just need to copy it.
if overlap > 0:
    cur.execute("""
        SELECT clay_o.domain, clay_o.outreach_id AS clay_oid,
               hde_o.outreach_id AS dol_oid, d.ein
        FROM outreach.outreach clay_o
        JOIN cl.company_identity clay_ci ON clay_ci.outreach_id = clay_o.outreach_id
        LEFT JOIN outreach.dol clay_d ON clay_d.outreach_id = clay_o.outreach_id
        JOIN outreach.outreach hde_o ON LOWER(hde_o.domain) = LOWER(clay_o.domain)
            AND hde_o.outreach_id <> clay_o.outreach_id
        JOIN cl.company_identity hde_ci ON hde_ci.outreach_id = hde_o.outreach_id
            AND hde_ci.source_system = 'hunter_dol_enrichment'
        JOIN outreach.dol d ON d.outreach_id = hde_o.outreach_id
        WHERE clay_d.outreach_id IS NULL
          AND clay_ci.source_system IN ('clay_import', 'clay')
        LIMIT 10
    """)
    print(f"\n  Sample overlaps (Clay domain = DOL-enriched domain):")
    for r in cur.fetchall():
        print(f"    {r[0]:30s} Clay OID={str(r[1])[:8]}... DOL OID={str(r[2])[:8]}... EIN={r[3]}")

# 12. For Clay domains NOT in hunter_dol_enrichment, can we match via hunter_company?
# hunter_company has 88K domains — some of those are DOL sponsors enriched by Hunter
print(f"\n  Alternative: Match Clay domain -> hunter_company -> form_5500 via name+geography")
cur.execute("""
    SELECT COUNT(DISTINCT clay_o.outreach_id)
    FROM outreach.outreach clay_o
    JOIN cl.company_identity clay_ci ON clay_ci.outreach_id = clay_o.outreach_id
    JOIN outreach.company_target ct ON ct.outreach_id = clay_o.outreach_id
    LEFT JOIN outreach.dol clay_d ON clay_d.outreach_id = clay_o.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(clay_o.domain)
    WHERE clay_d.outreach_id IS NULL
      AND clay_ci.source_system IN ('clay_import', 'clay')
      AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
""")
print(f"  Clay no-DOL with Hunter org name: {cur.fetchone()[0]:,}")

conn.close()
print(f"\n{'='*75}")
print(f"  Done.")
print(f"{'='*75}")
