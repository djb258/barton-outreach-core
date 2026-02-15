"""Debug why Hunter org names aren't matching DOL sponsors."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# 1. Sample Hunter org names for no-DOL companies
print("Hunter org samples (no-DOL companies):")
cur.execute("""
    SELECT hc.organization, UPPER(TRIM(hc.state))
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
      AND hc.state IS NOT NULL
    LIMIT 15
""")
hunter_samples = cur.fetchall()
for r in hunter_samples:
    print(f"  {(r[0] or '')[:45]:45s} state={r[1]}")

# 2. Sample DOL sponsor names
print("\nDOL sponsor samples:")
cur.execute("""
    SELECT spons_dfe_pn, UPPER(TRIM(spons_dfe_mail_us_state))
    FROM dol.form_5500
    WHERE spons_dfe_pn IS NOT NULL AND spons_dfe_mail_us_state IS NOT NULL
    LIMIT 15
""")
for r in cur.fetchall():
    print(f"  {(r[0] or '')[:45]:45s} state={r[1]}")

# 3. Try a manual match - pick a specific company and look for it
print("\n\nManual match test:")
cur.execute("""
    SELECT hc.organization, UPPER(TRIM(hc.state)), o.domain
    FROM outreach.company_target ct
    JOIN outreach.outreach o ON o.outreach_id = ct.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND hc.organization IS NOT NULL AND TRIM(hc.organization) <> ''
      AND hc.state IS NOT NULL
      AND LENGTH(TRIM(hc.organization)) > 5
    LIMIT 5
""")
test_rows = cur.fetchall()
for org, state, domain in test_rows:
    print(f"\n  Looking for Hunter org: '{org}' in state {state} (domain: {domain})")
    # Search DOL
    cur.execute("""
        SELECT spons_dfe_pn, spons_dfe_ein, UPPER(TRIM(spons_dfe_mail_us_state))
        FROM dol.form_5500
        WHERE UPPER(TRIM(spons_dfe_mail_us_state)) = %s
          AND UPPER(spons_dfe_pn) LIKE '%%' || UPPER(SUBSTRING(%s FROM 1 FOR 5)) || '%%'
        LIMIT 5
    """, (state, org))
    matches = cur.fetchall()
    if matches:
        for m in matches:
            print(f"    FOUND: {m[0]:40s} EIN={m[1]} state={m[2]}")
    else:
        print(f"    No partial match found in DOL for state {state}")

# 4. Check if the EIN exclusion is too aggressive
print("\n\nEIN exclusion check:")
cur.execute("SELECT COUNT(DISTINCT ein) FROM outreach.dol WHERE ein IS NOT NULL")
existing_eins = cur.fetchone()[0]
print(f"  EINs already in outreach.dol: {existing_eins:,}")

cur.execute("SELECT COUNT(DISTINCT spons_dfe_ein) FROM dol.form_5500 WHERE spons_dfe_ein IS NOT NULL")
total_eins = cur.fetchone()[0]
print(f"  Total unique EINs in form_5500: {total_eins:,}")

cur.execute("""
    SELECT COUNT(DISTINCT spons_dfe_ein)
    FROM dol.form_5500
    WHERE spons_dfe_ein IS NOT NULL
      AND spons_dfe_ein NOT IN (SELECT ein FROM outreach.dol WHERE ein IS NOT NULL)
""")
available_eins = cur.fetchone()[0]
print(f"  Available (unmatched) EINs: {available_eins:,}")

# 5. Check if hunter_company.outreach_id links to no-DOL companies
print("\n\nHunter outreach_id linkage check:")
cur.execute("""
    SELECT COUNT(*)
    FROM enrichment.hunter_company hc
    WHERE hc.outreach_id IS NOT NULL
""")
print(f"  hunter_company with outreach_id: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT COUNT(DISTINCT hc.outreach_id)
    FROM enrichment.hunter_company hc
    LEFT JOIN outreach.dol d ON d.outreach_id = hc.outreach_id
    WHERE hc.outreach_id IS NOT NULL AND d.outreach_id IS NULL
""")
print(f"  hunter_company with outreach_id but no DOL: {cur.fetchone()[0]:,}")

# 6. Are we joining correctly? Check domain match overlap
print("\n\nDomain join diagnostics:")
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    LEFT JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    WHERE d.outreach_id IS NULL
      AND hc.domain IS NOT NULL
""")
print(f"  No-DOL outreach_ids with hunter_company domain match: {cur.fetchone()[0]:,}")

# 7. Try the simplest possible exact match
print("\n\nSimplest possible match (raw UPPER name + state):")
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    JOIN outreach.company_target ct ON ct.outreach_id = o.outreach_id
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    JOIN dol.form_5500 f
        ON UPPER(TRIM(hc.organization)) = UPPER(TRIM(f.spons_dfe_pn))
       AND UPPER(TRIM(hc.state)) = UPPER(TRIM(f.spons_dfe_mail_us_state))
    WHERE d.outreach_id IS NULL
      AND hc.organization IS NOT NULL
      AND f.spons_dfe_pn IS NOT NULL
""")
raw_match = cur.fetchone()[0]
print(f"  Raw exact match (Hunter org = DOL sponsor, same state): {raw_match:,}")

# If that's also 0, try without EIN exclusion
cur.execute("""
    SELECT COUNT(DISTINCT o.outreach_id)
    FROM outreach.outreach o
    LEFT JOIN outreach.dol d ON d.outreach_id = o.outreach_id
    JOIN enrichment.hunter_company hc ON LOWER(hc.domain) = LOWER(o.domain)
    JOIN dol.form_5500 f
        ON UPPER(TRIM(hc.organization)) = UPPER(TRIM(f.spons_dfe_pn))
    WHERE d.outreach_id IS NULL
      AND hc.organization IS NOT NULL
      AND f.spons_dfe_pn IS NOT NULL
""")
raw_match_no_state = cur.fetchone()[0]
print(f"  Raw exact match (Hunter org = DOL sponsor, any state): {raw_match_no_state:,}")

conn.close()
print(f"\n{'='*75}")
print("  Done.")
print(f"{'='*75}")
