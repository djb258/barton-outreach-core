"""Check the 800 DOL-linked companies that STILL have no ZIP after repair.
If they have a DOL bridge (EIN), the filing MUST have a ZIP somewhere."""
import os, sys, psycopg2
if sys.platform == "win32": sys.stdout.reconfigure(encoding="utf-8")

conn = psycopg2.connect(
    host=os.environ["NEON_HOST"], dbname=os.environ["NEON_DATABASE"],
    user=os.environ["NEON_USER"], password=os.environ["NEON_PASSWORD"],
    sslmode="require",
)
cur = conn.cursor()

# The 800 DOL-linked companies with no CT ZIP
# Check if their EIN actually matches ANY form_5500 row
cur.execute("""
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE f.ack_id IS NOT NULL) AS has_f5500,
        COUNT(*) FILTER (WHERE sf.ack_id IS NOT NULL) AS has_sf
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    LEFT JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
    LEFT JOIN dol.form_5500_sf sf ON sf.sf_spons_ein = d.ein
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"DOL-linked, ZIP-missing: {r[0]:,}")
print(f"  Matches form_5500:     {r[1]:,}")
print(f"  Matches form_5500_sf:  {r[2]:,}")

# Check ALL ZIP columns on their filings
cur.execute("""
    SELECT
        COUNT(*) AS total_filings,
        COUNT(f.spons_dfe_mail_us_zip) FILTER (
            WHERE f.spons_dfe_mail_us_zip IS NOT NULL AND TRIM(f.spons_dfe_mail_us_zip) != ''
        ) AS has_mail_zip,
        COUNT(f.spons_dfe_loc_us_zip) FILTER (
            WHERE f.spons_dfe_loc_us_zip IS NOT NULL AND TRIM(f.spons_dfe_loc_us_zip) != ''
        ) AS has_loc_zip,
        COUNT(f.spons_dfe_mail_us_city) FILTER (
            WHERE f.spons_dfe_mail_us_city IS NOT NULL AND TRIM(f.spons_dfe_mail_us_city) != ''
        ) AS has_city,
        COUNT(f.spons_dfe_mail_us_state) FILTER (
            WHERE f.spons_dfe_mail_us_state IS NOT NULL AND TRIM(f.spons_dfe_mail_us_state) != ''
        ) AS has_state
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\nForm 5500 filings for these companies:")
print(f"  Total filings:  {r[0]:,}")
print(f"  Has mail ZIP:   {r[1]:,}")
print(f"  Has loc ZIP:    {r[2]:,}")
print(f"  Has city:       {r[3]:,}")
print(f"  Has state:      {r[4]:,}")

# Sample the mail ZIPs that exist — why didn't our view pick them up?
cur.execute("""
    SELECT d.outreach_id, d.ein,
           f.spons_dfe_mail_us_zip,
           LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) AS zip5,
           LEFT(TRIM(f.spons_dfe_mail_us_zip), 5) ~ '^\\d{5}$' AS valid_zip
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN dol.form_5500 f ON f.spons_dfe_ein = d.ein
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND f.spons_dfe_mail_us_zip IS NOT NULL
      AND TRIM(f.spons_dfe_mail_us_zip) != ''
    LIMIT 20
""")
rows = cur.fetchall()
if rows:
    print(f"\nSample mail ZIPs (why didn't they match?):")
    for r in rows:
        print(f"  oid={str(r[0])[:8]}.. ein={r[1]} raw='{r[2]}' zip5='{r[3]}' valid={r[4]}")

# Check form_5500_sf too
cur.execute("""
    SELECT
        COUNT(*) AS total_filings,
        COUNT(sf.sf_spons_us_zip) FILTER (
            WHERE sf.sf_spons_us_zip IS NOT NULL AND TRIM(sf.sf_spons_us_zip) != ''
        ) AS has_zip,
        COUNT(sf.sf_spons_us_city) FILTER (
            WHERE sf.sf_spons_us_city IS NOT NULL AND TRIM(sf.sf_spons_us_city) != ''
        ) AS has_city
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN dol.form_5500_sf sf ON sf.sf_spons_ein = d.ein
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
r = cur.fetchone()
print(f"\nForm 5500 SF filings for these companies:")
print(f"  Total filings:  {r[0]:,}")
print(f"  Has ZIP:        {r[1]:,}")
print(f"  Has city:       {r[2]:,}")

# Check the evidence view — do they appear?
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    LEFT JOIN outreach.v_dol_zip_evidence e ON e.outreach_id = ct.outreach_id
    WHERE (ct.postal_code IS NULL OR TRIM(ct.postal_code) = '')
      AND e.outreach_id IS NULL
""")
print(f"\nDOL-linked but NOT in v_dol_zip_evidence: {cur.fetchone()[0]:,}")

cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.dol d ON d.outreach_id = ct.outreach_id
    JOIN outreach.v_dol_zip_evidence e ON e.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
print(f"DOL-linked AND in v_dol_zip_evidence: {cur.fetchone()[0]:,}")

# Those in evidence but NOT repaired — what happened?
cur.execute("""
    SELECT COUNT(DISTINCT ct.outreach_id)
    FROM outreach.company_target ct
    JOIN outreach.v_ct_zip_repair_candidates rc ON rc.outreach_id = ct.outreach_id
    WHERE ct.postal_code IS NULL OR TRIM(ct.postal_code) = ''
""")
print(f"In repair candidates view right now: {cur.fetchone()[0]:,}")

conn.close()
