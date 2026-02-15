"""Full CT data audit — every column, every join path, every enrichment source."""
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
print(f"  CT (outreach.company_target) — FULL DATA AUDIT")
print(f"  Total: {total:,}")
print(f"{'='*75}")

# ============================================================
# SECTION 1: CT Column Fill
# ============================================================
print(f"\n  SECTION 1: CT Column Fill Rates")
print(f"  {'-'*65}")

cols = [
    ("outreach_id", "Identity"),
    ("company_unique_id", "Identity"),
    ("target_id", "Identity"),
    ("outreach_status", "Status"),
    ("execution_status", "Status"),
    ("email_method", "Enrichment"),
    ("method_type", "Enrichment"),
    ("confidence_score", "Enrichment"),
    ("is_catchall", "Enrichment"),
    ("imo_completed_at", "Enrichment"),
    ("industry", "Company Profile"),
    ("employees", "Company Profile"),
    ("country", "Geography"),
    ("state", "Geography"),
    ("city", "Geography"),
    ("postal_code", "Geography"),
    ("postal_code_source", "Geography"),
    ("bit_score_snapshot", "Scoring"),
    ("source", "Metadata"),
    ("sequence_count", "Execution"),
    ("active_sequence_id", "Execution"),
    ("first_targeted_at", "Execution"),
    ("last_targeted_at", "Execution"),
    ("data_year", "Metadata"),
]

current_group = None
for col_name, group in cols:
    if group != current_group:
        current_group = group
        print(f"\n  [{group}]")
    cur.execute(f"""
        SELECT
            COUNT(CASE WHEN "{col_name}" IS NOT NULL
                        AND TRIM("{col_name}"::text) != '' THEN 1 END)
        FROM outreach.company_target
    """)
    filled = cur.fetchone()[0]
    pct = 100 * filled / total
    gap = total - filled
    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    print(f"    {col_name:<25s} {bar} {pct:>5.1f}%  ({filled:>6,} / {total:,})  gap: {gap:,}")

# ============================================================
# SECTION 2: Spine + CL Linkage
# ============================================================
print(f"\n\n  SECTION 2: Spine & CL Linkage")
print(f"  {'-'*65}")

cur.execute("""
    SELECT
        COUNT(*) AS ct_total,
        COUNT(o.outreach_id) AS has_spine,
        COUNT(ci.outreach_id) AS has_cl
    FROM outreach.company_target ct
    LEFT JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
""")
r = cur.fetchone()
print(f"    CT -> outreach.outreach (spine):   {r[1]:,} / {r[0]:,}  ({100*r[1]/r[0]:.1f}%)")
print(f"    CT -> cl.company_identity:         {r[2]:,} / {r[0]:,}  ({100*r[2]/r[0]:.1f}%)")

# Domain from spine
cur.execute("""
    SELECT
        COUNT(o.domain) FILTER (WHERE o.domain IS NOT NULL AND TRIM(o.domain) != '')
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
""")
print(f"    Has domain (via spine):            {cur.fetchone()[0]:,} / {total:,}")

# Company name from CL
cur.execute("""
    SELECT
        COUNT(ci.company_name) FILTER (WHERE ci.company_name IS NOT NULL AND TRIM(ci.company_name) != '')
    FROM outreach.company_target ct
    JOIN cl.company_identity ci ON ci.outreach_id = ct.outreach_id
""")
print(f"    Has company_name (via CL):         {cur.fetchone()[0]:,} / {total:,}")

# ============================================================
# SECTION 3: Sub-Hub Linkage
# ============================================================
print(f"\n\n  SECTION 3: Sub-Hub Linkage")
print(f"  {'-'*65}")

cur.execute("""
    SELECT
        COUNT(d.outreach_id) AS dol,
        COUNT(d.ein) FILTER (WHERE d.ein IS NOT NULL) AS dol_ein,
        COUNT(d.filing_present) FILTER (WHERE d.filing_present = true) AS dol_filing,
        COUNT(d.renewal_month) FILTER (WHERE d.renewal_month IS NOT NULL) AS dol_renewal,
        COUNT(d.funding_type) FILTER (WHERE d.funding_type IS NOT NULL) AS dol_funding,
        COUNT(d.carrier) FILTER (WHERE d.carrier IS NOT NULL AND TRIM(d.carrier) != '') AS dol_carrier,
        COUNT(d.broker_or_advisor) FILTER (WHERE d.broker_or_advisor IS NOT NULL AND TRIM(d.broker_or_advisor) != '') AS dol_broker
    FROM outreach.company_target ct
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
""")
r = cur.fetchone()
print(f"    DOL bridge:         {r[0]:,} ({100*r[0]/total:.1f}%)")
print(f"      EIN:              {r[1]:,}")
print(f"      Filing present:   {r[2]:,}")
print(f"      Renewal month:    {r[3]:,}")
print(f"      Funding type:     {r[4]:,}")
print(f"      Carrier:          {r[5]:,}")
print(f"      Broker/advisor:   {r[6]:,}")

# People slots
cur.execute("""
    SELECT
        slot_type,
        COUNT(*) AS total_slots,
        COUNT(*) FILTER (WHERE is_filled = true) AS filled
    FROM people.company_slot
    WHERE slot_type IN ('CEO', 'CFO', 'HR')
    GROUP BY slot_type
    ORDER BY slot_type
""")
print(f"\n    People Slots:")
for r in cur.fetchall():
    print(f"      {r[0]}: {r[2]:,} filled / {r[1]:,} total ({100*r[2]/r[1]:.1f}%)")

# Blog
cur.execute("""
    SELECT COUNT(b.outreach_id)
    FROM outreach.company_target ct
    LEFT JOIN outreach.blog b ON b.outreach_id = ct.outreach_id
""")
print(f"\n    Blog linked:        {cur.fetchone()[0]:,}")

# BIT scores
cur.execute("""
    SELECT COUNT(bs.outreach_id)
    FROM outreach.company_target ct
    LEFT JOIN outreach.bit_scores bs ON bs.outreach_id = ct.outreach_id
""")
print(f"    BIT scored:         {cur.fetchone()[0]:,}")

# ============================================================
# SECTION 4: Enrichment Source Linkage
# ============================================================
print(f"\n\n  SECTION 4: Enrichment Source Linkage (via domain)")
print(f"  {'-'*65}")

cur.execute("""
    SELECT
        COUNT(DISTINCT ct.outreach_id) FILTER (WHERE hc.domain IS NOT NULL) AS hunter_match,
        COUNT(DISTINCT ct.outreach_id) FILTER (WHERE cm.company_unique_id IS NOT NULL) AS cm_match
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    LEFT JOIN company.company_master cm ON LOWER(
        REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
    ) = LOWER(o.domain)
""")
r = cur.fetchone()
print(f"    Hunter company match:     {r[0]:,} / {total:,} ({100*r[0]/total:.1f}%)")
print(f"    Company master match:     {r[1]:,} / {total:,} ({100*r[1]/total:.1f}%)")

# Blog URLs via company_master bridge
cur.execute("""
    SELECT
        COUNT(DISTINCT ct.outreach_id) FILTER (WHERE csu.source_url IS NOT NULL) AS has_any_url
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN company.company_master cm ON LOWER(
        REPLACE(REPLACE(REPLACE(cm.website_url, 'http://', ''), 'https://', ''), 'www.', '')
    ) = LOWER(o.domain)
    LEFT JOIN company.company_source_urls csu ON csu.company_unique_id = cm.company_unique_id
""")
print(f"    Has source URLs:          {cur.fetchone()[0]:,}")

# Hunter contacts
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_contact hcon ON LOWER(hcon.domain) = LOWER(o.domain)
""")
print(f"    Hunter contacts match:    {cur.fetchone()[0]:,}")

# ============================================================
# SECTION 5: Data Quality Checks
# ============================================================
print(f"\n\n  SECTION 5: Data Quality Checks")
print(f"  {'-'*65}")

# Orphan check: CT rows with no spine
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    LEFT JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE o.outreach_id IS NULL
""")
print(f"    CT orphans (no spine):        {cur.fetchone()[0]:,}")

# Spine rows with no CT
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.outreach o
    LEFT JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    WHERE ct.outreach_id IS NULL
""")
print(f"    Spine orphans (no CT):        {cur.fetchone()[0]:,}")

# CL with no spine
cur.execute("""
    SELECT COUNT(*)
    FROM cl.company_identity ci
    WHERE ci.outreach_id IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM outreach.outreach o WHERE o.outreach_id = ci.outreach_id)
""")
print(f"    CL orphans (no spine):        {cur.fetchone()[0]:,}")

# Duplicate domains
cur.execute("""
    SELECT COUNT(*) FROM (
        SELECT o.domain, COUNT(*)
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        WHERE o.domain IS NOT NULL AND TRIM(o.domain) != ''
        GROUP BY o.domain
        HAVING COUNT(*) > 1
    ) dupes
""")
print(f"    Duplicate domains:            {cur.fetchone()[0]:,}")

# Invalid postal codes (non-5-digit)
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target
    WHERE postal_code IS NOT NULL
      AND TRIM(postal_code) != ''
      AND LEFT(TRIM(postal_code), 5) !~ '^\\d{5}$'
""")
print(f"    Invalid postal codes:         {cur.fetchone()[0]:,}")

# postal_code not in reference
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    WHERE ct.postal_code IS NOT NULL AND TRIM(ct.postal_code) != ''
      AND NOT EXISTS (
          SELECT 1 FROM reference.us_zip_codes z
          WHERE z.zip = LEFT(TRIM(ct.postal_code), 5)
      )
""")
print(f"    ZIP not in reference table:   {cur.fetchone()[0]:,}")

# email_method but no domain
cur.execute("""
    SELECT COUNT(*)
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    WHERE ct.email_method IS NOT NULL AND TRIM(ct.email_method) != ''
      AND (o.domain IS NULL OR TRIM(o.domain) = '')
""")
print(f"    Has email_method, no domain:  {cur.fetchone()[0]:,}")

# ============================================================
# SECTION 6: Geography completeness matrix
# ============================================================
print(f"\n\n  SECTION 6: Geography Completeness Matrix")
print(f"  {'-'*65}")

cur.execute("""
    SELECT
        CASE WHEN postal_code IS NOT NULL AND TRIM(postal_code) != '' THEN 'Y' ELSE 'N' END AS has_zip,
        CASE WHEN city IS NOT NULL AND TRIM(city) != '' THEN 'Y' ELSE 'N' END AS has_city,
        CASE WHEN state IS NOT NULL AND TRIM(state) != '' THEN 'Y' ELSE 'N' END AS has_state,
        CASE WHEN country IS NOT NULL AND TRIM(country) != '' THEN 'Y' ELSE 'N' END AS has_country,
        COUNT(*) AS cnt
    FROM outreach.company_target
    GROUP BY 1, 2, 3, 4
    ORDER BY COUNT(*) DESC
""")
print(f"    {'ZIP':>4s} {'City':>5s} {'State':>6s} {'Country':>8s}  {'Count':>8s}  {'%':>6s}")
for r in cur.fetchall():
    print(f"    {r[0]:>4s} {r[1]:>5s} {r[2]:>6s} {r[3]:>8s}  {r[4]:>8,}  {100*r[4]/total:>5.1f}%")

# ============================================================
# SECTION 7: Enrichment gap summary
# ============================================================
print(f"\n\n  SECTION 7: Enrichment Gap Summary (what's missing)")
print(f"  {'-'*65}")

gaps = [
    ("postal_code", "Geography"),
    ("city", "Geography"),
    ("state", "Geography"),
    ("country", "Geography"),
    ("email_method", "Enrichment"),
    ("method_type", "Enrichment"),
    ("industry", "Company Profile"),
    ("employees", "Company Profile"),
]

for col, group in gaps:
    cur.execute(f"""
        SELECT
            COUNT(*) AS gap,
            COUNT(o.domain) FILTER (WHERE o.domain IS NOT NULL AND TRIM(o.domain) != '') AS has_domain
        FROM outreach.company_target ct
        JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
        WHERE ct."{col}" IS NULL OR TRIM(ct."{col}"::text) = ''
    """)
    r = cur.fetchone()
    print(f"    {col:<20s} gap: {r[0]:>6,}  (all have domain: {'YES' if r[0] == r[1] else f'{r[1]:,}/{r[0]:,}'})")

conn.close()
print(f"\n{'='*75}")
print(f"  Audit complete.")
print(f"{'='*75}")
