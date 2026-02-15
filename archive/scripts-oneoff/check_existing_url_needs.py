#!/usr/bin/env python3
"""
Check existing company_master records that have EIN but may need URL enrichment
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("Existing Company Master - URL Enrichment Opportunity")
print("=" * 70)

# Companies with EIN but no domain in company_master
cur.execute("""
    SELECT COUNT(*) 
    FROM company.company_master 
    WHERE ein IS NOT NULL
""")
with_ein = cur.fetchone()[0]
print(f"company_master with EIN: {with_ein:,}")

# Check cl.company_identity for domain status
cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(company_domain) as has_domain,
        COUNT(*) - COUNT(company_domain) as missing_domain
    FROM cl.company_identity
    WHERE outreach_id IS NOT NULL
""")
r = cur.fetchone()
print(f"\ncl.company_identity with outreach_id: {r[0]:,}")
print(f"  Has domain: {r[1]:,}")
print(f"  Missing domain: {r[2]:,}")

# Check outreach.blog for URL status
cur.execute("""
    SELECT 
        COUNT(DISTINCT o.outreach_id) as total_outreach,
        COUNT(DISTINCT b.outreach_id) as has_blog
    FROM outreach.outreach o
    LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
""")
r = cur.fetchone()
print(f"\noutreach.outreach total: {r[0]:,}")
print(f"  Has blog entry: {r[1]:,}")
print(f"  Missing blog: {r[0] - r[1]:,}")

# Check if any existing companies have EIN that matches DOL
cur.execute("""
    WITH dol_eins AS (
        SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500
        UNION
        SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf
    )
    SELECT 
        COUNT(*) as cm_with_dol_ein,
        COUNT(CASE WHEN ci.company_domain IS NULL THEN 1 END) as missing_domain
    FROM company.company_master cm
    JOIN dol_eins d ON cm.ein = d.ein
    LEFT JOIN cl.company_identity ci ON cm.company_unique_id::text = ci.company_unique_id
""")
r = cur.fetchone()
print(f"\ncompany_master with DOL EIN match: {r[0]:,}")
print(f"  Missing domain in CL: {r[1]:,}")

# Get sample of these for domain lookup
cur.execute("""
    WITH dol_eins AS (
        SELECT DISTINCT sponsor_dfe_ein as ein FROM dol.form_5500
        UNION
        SELECT DISTINCT sf_spons_ein as ein FROM dol.form_5500_sf
    )
    SELECT cm.ein, cm.company_name, cm.address_city, cm.address_state,
           ci.company_domain, ci.outreach_id
    FROM company.company_master cm
    JOIN dol_eins d ON cm.ein = d.ein
    LEFT JOIN cl.company_identity ci ON cm.company_unique_id::text = ci.company_unique_id
    WHERE ci.company_domain IS NULL
    AND ci.outreach_id IS NOT NULL
    LIMIT 20
""")
rows = cur.fetchall()
print(f"\nSample companies with EIN match but missing domain:")
print("-" * 70)
for r in rows:
    print(f"  EIN: {r[0]} | {r[1][:40]:<40} | {r[2]}, {r[3]}")

cur.close()
conn.close()
