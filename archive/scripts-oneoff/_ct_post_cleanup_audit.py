"""Post-cleanup CT data audit + DOL bridge opportunity."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM outreach.company_target")
total = cur.fetchone()[0]

print(f"{'='*75}")
print(f"  CT DATA AUDIT — POST CLEANUP")
print(f"  Total: {total:,}")
print(f"{'='*75}")

# ============================================================
# SECTION 1: Geography (should be ~100%)
# ============================================================
print(f"\n  GEOGRAPHY")
for col in ["postal_code", "city", "state", "country"]:
    cur.execute(f"""
        SELECT COUNT(CASE WHEN "{col}" IS NOT NULL AND TRIM("{col}"::text) != '' THEN 1 END)
        FROM outreach.company_target
    """)
    filled = cur.fetchone()[0]
    pct = 100 * filled / total
    gap = total - filled
    print(f"    {col:<20s} {filled:>6,} / {total:,}  ({pct:>5.1f}%)  gap: {gap:,}")

# ============================================================
# SECTION 2: Enrichment columns
# ============================================================
print(f"\n  ENRICHMENT")
for col in ["email_method", "method_type", "confidence_score", "is_catchall", "industry", "employees"]:
    cur.execute(f"""
        SELECT COUNT(CASE WHEN "{col}" IS NOT NULL AND TRIM("{col}"::text) != '' THEN 1 END)
        FROM outreach.company_target
    """)
    filled = cur.fetchone()[0]
    pct = 100 * filled / total
    gap = total - filled
    print(f"    {col:<20s} {filled:>6,} / {total:,}  ({pct:>5.1f}%)  gap: {gap:,}")

# ============================================================
# SECTION 3: Sub-Hub linkage
# ============================================================
print(f"\n  SUB-HUB LINKAGE")

cur.execute("""SELECT COUNT(*) FROM outreach.dol d JOIN outreach.company_target ct ON ct.outreach_id = d.outreach_id""")
dol = cur.fetchone()[0]
print(f"    DOL bridge:      {dol:,} / {total:,} ({100*dol/total:.1f}%)  gap: {total-dol:,}")

cur.execute("""SELECT COUNT(*) FROM outreach.blog b JOIN outreach.company_target ct ON ct.outreach_id = b.outreach_id""")
blog = cur.fetchone()[0]
print(f"    Blog:            {blog:,} / {total:,} ({100*blog/total:.1f}%)  gap: {total-blog:,}")

cur.execute("""SELECT COUNT(*) FROM outreach.bit_scores bs JOIN outreach.company_target ct ON ct.outreach_id = bs.outreach_id""")
bit = cur.fetchone()[0]
print(f"    BIT scored:      {bit:,} / {total:,} ({100*bit/total:.1f}%)  gap: {total-bit:,}")

# Slots
cur.execute("""
    SELECT slot_type, COUNT(*) FILTER (WHERE is_filled), COUNT(*)
    FROM people.company_slot
    GROUP BY slot_type ORDER BY slot_type
""")
print(f"\n    People Slots:")
total_slots = 0
total_filled = 0
for r in cur.fetchall():
    print(f"      {r[0]}: {r[1]:,} filled / {r[2]:,} ({100*r[1]/r[2]:.1f}%)")
    total_slots += r[2]
    total_filled += r[1]
print(f"      TOTAL: {total_filled:,} / {total_slots:,} ({100*total_filled/total_slots:.1f}%)")

# ============================================================
# SECTION 4: DOL Bridge Opportunity
# ============================================================
print(f"\n{'='*75}")
print(f"  DOL BRIDGE OPPORTUNITY")
print(f"{'='*75}")

no_dol = total - dol
print(f"\n  Companies WITHOUT DOL bridge: {no_dol:,}")

# Can we match more via Hunter EIN?
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
""")
hunter_match_no_dol = cur.fetchone()[0]
print(f"  Matched to Hunter company (no DOL): {hunter_match_no_dol:,}")

# How many of the no-DOL companies have a ZIP that matches a form_5500 sponsor ZIP?
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
      AND ct.postal_code IS NOT NULL
""")
no_dol_has_zip = cur.fetchone()[0]
print(f"  No-DOL with ZIP:                    {no_dol_has_zip:,}")

# Check if company names match form_5500 sponsor names
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
      AND ci.company_name IS NOT NULL
""")
no_dol_has_name = cur.fetchone()[0]
print(f"  No-DOL with company name:           {no_dol_has_name:,}")

# State breakdown of no-DOL companies
cur.execute("""
    SELECT ct.state, COUNT(*)
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
    GROUP BY ct.state ORDER BY COUNT(*) DESC LIMIT 15
""")
print(f"\n  No-DOL by state (top 15):")
for r in cur.fetchall():
    print(f"    {r[0] or 'NULL':5s}: {r[1]:,}")

# Industry breakdown of no-DOL
cur.execute("""
    SELECT ct.industry, COUNT(*)
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
      AND ct.industry IS NOT NULL AND TRIM(ct.industry) != ''
    GROUP BY ct.industry ORDER BY COUNT(*) DESC LIMIT 10
""")
print(f"\n  No-DOL by industry (top 10):")
for r in cur.fetchall():
    print(f"    {(r[0] or '')[:40]:40s}: {r[1]:,}")

# Employee size of no-DOL
cur.execute("""
    SELECT
        COUNT(*) FILTER (WHERE ct.employees < 25) AS tiny,
        COUNT(*) FILTER (WHERE ct.employees BETWEEN 25 AND 99) AS small,
        COUNT(*) FILTER (WHERE ct.employees BETWEEN 100 AND 499) AS mid,
        COUNT(*) FILTER (WHERE ct.employees >= 500) AS large,
        COUNT(*) FILTER (WHERE ct.employees IS NULL) AS unknown
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    WHERE d.outreach_id IS NULL
""")
r = cur.fetchone()
print(f"\n  No-DOL by company size:")
print(f"    <25 employees:   {r[0]:,}")
print(f"    25-99:           {r[1]:,}")
print(f"    100-499:         {r[2]:,}")
print(f"    500+:            {r[3]:,}")
print(f"    Unknown:         {r[4]:,}")

# ============================================================
# SECTION 5: Postal code source breakdown
# ============================================================
print(f"\n{'='*75}")
print(f"  POSTAL CODE SOURCE BREAKDOWN")
print(f"{'='*75}")

cur.execute("""
    SELECT COALESCE(postal_code_source, 'ORIGINAL_LOAD'), COUNT(*)
    FROM outreach.company_target
    GROUP BY postal_code_source
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"    {r[0]:25s}: {r[1]:>6,} ({100*r[1]/total:.1f}%)")

conn.close()
print(f"\n{'='*75}")
print(f"  Audit complete.")
print(f"{'='*75}")
