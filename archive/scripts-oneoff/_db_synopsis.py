import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    dbname=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require'
)
cur = conn.cursor()

# CT total
cur.execute("SELECT COUNT(*) FROM outreach.company_target")
ct_total = cur.fetchone()[0]
print("=== FULL DATABASE SYNOPSIS ===")
print(f"CT (Company Target) Total: {ct_total:,}")
print()

# DOL sub-hub
print("--- DOL SUB-HUB ---")
cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol")
dol_count = cur.fetchone()[0]
print(f"DOL Linked: {dol_count:,} / {ct_total:,} ({100.0*dol_count/ct_total:.1f}%)")

cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol WHERE filing_present = TRUE")
dol_filing = cur.fetchone()[0]
print(f"DOL with Filing: {dol_filing:,} / {ct_total:,} ({100.0*dol_filing/ct_total:.1f}%)")

cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol WHERE renewal_month IS NOT NULL")
dol_renewal = cur.fetchone()[0]
print(f"DOL with Renewal Month: {dol_renewal:,} / {ct_total:,} ({100.0*dol_renewal/ct_total:.1f}%)")

cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol WHERE carrier IS NOT NULL AND carrier <> ''")
dol_carrier = cur.fetchone()[0]
print(f"DOL with Carrier: {dol_carrier:,} / {ct_total:,} ({100.0*dol_carrier/ct_total:.1f}%)")

cur.execute("SELECT COUNT(DISTINCT outreach_id) FROM outreach.dol WHERE broker_or_advisor IS NOT NULL AND broker_or_advisor <> ''")
dol_broker = cur.fetchone()[0]
print(f"DOL with Broker/Advisor: {dol_broker:,} / {ct_total:,} ({100.0*dol_broker/ct_total:.1f}%)")

# Funding type breakdown
cur.execute("""
    SELECT funding_type, COUNT(DISTINCT outreach_id)
    FROM outreach.dol
    WHERE funding_type IS NOT NULL
    GROUP BY funding_type
    ORDER BY COUNT(DISTINCT outreach_id) DESC
""")
print("\nDOL Funding Type Breakdown:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,} ({100.0*row[1]/ct_total:.1f}%)")
print()

# People sub-hub with LinkedIn
print("--- PEOPLE SUB-HUB ---")
cur.execute("SELECT COUNT(*) FROM people.people_master")
people_total = cur.fetchone()[0]
print(f"Total People Records: {people_total:,}")

# Slots by type WITH LinkedIn
cur.execute("""
    SELECT
        cs.slot_type,
        COUNT(*) as total_slots,
        SUM(CASE WHEN cs.is_filled THEN 1 ELSE 0 END) as filled,
        SUM(CASE WHEN cs.is_filled AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url <> '' THEN 1 ELSE 0 END) as with_linkedin
    FROM people.company_slot cs
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    WHERE cs.slot_type IN ('CEO', 'CFO', 'HR')
    GROUP BY cs.slot_type
    ORDER BY cs.slot_type
""")
slot_rows = cur.fetchall()
print("\nSlot Breakdown (with LinkedIn):")
for row in slot_rows:
    stype, total, filled, li = row
    li_of_filled = 100.0*li/filled if filled > 0 else 0
    print(f"  {stype}: {filled:,}/{total:,} filled ({100.0*filled/total:.1f}%) | LinkedIn: {li:,}/{filled:,} ({li_of_filled:.1f}% of filled) — {100.0*li/ct_total:.1f}% of CT")
print()

# Company LinkedIn
print("--- COMPANY LINKEDIN ---")
cur.execute("""
    SELECT COUNT(*)
    FROM cl.company_identity ci
    WHERE ci.outreach_id IS NOT NULL
      AND ci.linkedin_company_url IS NOT NULL
      AND ci.linkedin_company_url <> ''
""")
company_li = cur.fetchone()[0]
print(f"Companies with LinkedIn: {company_li:,} / {ct_total:,} ({100.0*company_li/ct_total:.1f}%)")
print()

# Email stats
print("--- EMAIL VERIFICATION ---")
cur.execute("""
    SELECT
        COUNT(*) as total_with_email,
        SUM(CASE WHEN email_verified = TRUE THEN 1 ELSE 0 END) as verified,
        SUM(CASE WHEN outreach_ready = TRUE THEN 1 ELSE 0 END) as outreach_ready
    FROM people.people_master
    WHERE email IS NOT NULL AND email <> ''
""")
email_row = cur.fetchone()
print(f"People with Email: {email_row[0]:,}")
print(f"Email Verified: {email_row[1]:,} ({100.0*email_row[1]/email_row[0]:.1f}% of emails)")
print(f"Outreach Ready: {email_row[2]:,} ({100.0*email_row[2]/email_row[0]:.1f}% of emails)")

cur.execute("""
    SELECT COUNT(DISTINCT cs.outreach_id)
    FROM people.company_slot cs
    JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    WHERE cs.is_filled = TRUE AND pm.outreach_ready = TRUE
""")
companies_ready = cur.fetchone()[0]
print(f"Companies with 1+ Outreach-Ready Email: {companies_ready:,} / {ct_total:,} ({100.0*companies_ready/ct_total:.1f}%)")
print()

# Blog sub-hub
print("--- BLOG SUB-HUB ---")
cur.execute("SELECT COUNT(*) FROM outreach.blog")
blog_total = cur.fetchone()[0]
print(f"Blog Records: {blog_total:,} / {ct_total:,} ({100.0*blog_total/ct_total:.1f}%)")

cur.execute("""
    SELECT source_type, COUNT(*)
    FROM company.company_source_urls
    GROUP BY source_type
    ORDER BY COUNT(*) DESC
""")
print("\nCompany Source URLs:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,}")

cur.execute("SELECT COUNT(DISTINCT company_unique_id) FROM company.company_source_urls")
companies_with_urls = cur.fetchone()[0]
print(f"Companies with Any URL: {companies_with_urls:,}")
print()

# Three messaging lanes
print("--- THREE MESSAGING LANES ---")
print(f"Cold Outreach: {ct_total:,}")
cur.execute("SELECT COUNT(*) FROM sales.appointments_already_had")
appts = cur.fetchone()[0]
print(f"Appointments Already Had: {appts:,}")
cur.execute("SELECT COUNT(*) FROM partners.fractional_cfo_master")
cfo_partners = cur.fetchone()[0]
print(f"Fractional CFO Partners: {cfo_partners:,}")

conn.close()
