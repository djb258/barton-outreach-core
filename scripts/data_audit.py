#!/usr/bin/env python3
"""Full data audit across all production tables."""
import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

def q1(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

def fmt(n):
    return "{:,}".format(n)

def pct(n, d):
    return "{:.1f}%".format(n / d * 100) if d else "0%"

print("=" * 70)
print("FULL DATA AUDIT - 2026-02-09")
print("=" * 70)

# ── SPINE ──
print("\n-- SPINE --")
spine = q1("SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL")
outreach = q1("SELECT COUNT(*) FROM outreach.outreach")
ct = q1("SELECT COUNT(*) FROM outreach.company_target")
print("  CL sovereign eligible:       " + fmt(spine))
print("  Outreach spine:              " + fmt(outreach))
print("  Company target:              " + fmt(ct))

# ── SLOTS ──
print("\n-- SLOTS (people.company_slot) --")
total_slots = q1("SELECT COUNT(*) FROM people.company_slot")
filled = q1("SELECT COUNT(*) FROM people.company_slot WHERE is_filled = TRUE")
empty = total_slots - filled
print("  Total slots:                 " + fmt(total_slots))
print("  Filled:                      {} ({})".format(fmt(filled), pct(filled, total_slots)))
print("  Empty:                       {} ({})".format(fmt(empty), pct(empty, total_slots)))

cur.execute("""
    SELECT slot_type,
           COUNT(*) as total,
           COUNT(CASE WHEN is_filled THEN 1 END) as filled
    FROM people.company_slot
    GROUP BY slot_type ORDER BY slot_type
""")
print("")
print("  {:<6} {:>8} {:>8} {:>8} {:>6}".format("Type", "Total", "Filled", "Empty", "Fill"))
print("  {:<6} {:>8} {:>8} {:>8} {:>6}".format("------", "--------", "--------", "--------", "------"))
for stype, total, f in cur.fetchall():
    e = total - f
    print("  {:<6} {:>8} {:>8} {:>8} {:>5}".format(
        stype, fmt(total), fmt(f), fmt(e), pct(f, total)))

# ── PEOPLE ──
print("\n-- PEOPLE (people.people_master) --")
total_people = q1("SELECT COUNT(*) FROM people.people_master")
has_email = q1("SELECT COUNT(*) FROM people.people_master WHERE email IS NOT NULL AND email != ''")
has_linkedin = q1("SELECT COUNT(*) FROM people.people_master WHERE linkedin_url IS NOT NULL AND linkedin_url != ''")
has_phone = q1("SELECT COUNT(*) FROM people.people_master WHERE work_phone_e164 IS NOT NULL AND work_phone_e164 != ''")

print("  Total people:                " + fmt(total_people))
print("  With email:                  {} ({})".format(fmt(has_email), pct(has_email, total_people)))
print("  With LinkedIn:               {} ({})".format(fmt(has_linkedin), pct(has_linkedin, total_people)))
print("  With phone:                  {} ({})".format(fmt(has_phone), pct(has_phone, total_people)))

# Slotted people quality
cur.execute("""
    SELECT COUNT(DISTINCT pm.unique_id),
           COUNT(DISTINCT CASE WHEN pm.email IS NOT NULL AND pm.email != '' THEN pm.unique_id END),
           COUNT(DISTINCT CASE WHEN pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '' THEN pm.unique_id END),
           COUNT(DISTINCT CASE WHEN pm.email IS NOT NULL AND pm.email != ''
                                AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '' THEN pm.unique_id END)
    FROM people.people_master pm
    JOIN people.company_slot cs ON cs.person_unique_id = pm.unique_id AND cs.is_filled = TRUE
""")
slotted, sl_email, sl_li, sl_both = cur.fetchone()
print("\n  SLOTTED PEOPLE QUALITY:")
print("  Slotted people:              " + fmt(slotted))
print("    With email:                {} ({})".format(fmt(sl_email), pct(sl_email, slotted)))
print("    With LinkedIn:             {} ({})".format(fmt(sl_li), pct(sl_li, slotted)))
print("    With BOTH email+LinkedIn:  {} ({})".format(fmt(sl_both), pct(sl_both, slotted)))
print("    Email but NO LinkedIn:     " + fmt(sl_email - sl_both))
print("    LinkedIn but NO email:     " + fmt(sl_li - sl_both))

# ── DOL ──
print("\n-- DOL --")
dol = q1("SELECT COUNT(*) FROM outreach.dol")
print("  DOL bridge records:          {} / 95,004 ({})".format(fmt(dol), pct(dol, 95004)))

# ── COMPANY LINKEDIN ──
print("\n-- COMPANY LINKEDIN --")
cl_li = q1("SELECT COUNT(*) FROM cl.company_identity WHERE linkedin_company_url IS NOT NULL AND linkedin_company_url != '' AND outreach_id IS NOT NULL")
print("  With company LinkedIn:       {} / 95,004 ({})".format(fmt(cl_li), pct(cl_li, 95004)))

# ── EMAIL METHOD ──
print("\n-- EMAIL METHOD (company_target) --")
has_method = q1("SELECT COUNT(*) FROM outreach.company_target WHERE email_method IS NOT NULL")
print("  With email_method:           {} / 95,004 ({})".format(fmt(has_method), pct(has_method, 95004)))

cur.execute("""
    SELECT method_type, COUNT(*)
    FROM outreach.company_target
    WHERE email_method IS NOT NULL
    GROUP BY method_type ORDER BY COUNT(*) DESC
""")
rows = cur.fetchall()
if rows:
    print("  By method_type:")
    for mt, cnt in rows:
        print("    {:<20} {:>8}".format(str(mt), fmt(cnt)))

# ── EMAIL VERIFICATION ──
print("\n-- EMAIL VERIFICATION STATUS --")
cur.execute("""
    SELECT execution_status, COUNT(*)
    FROM outreach.company_target
    GROUP BY execution_status ORDER BY COUNT(*) DESC
""")
print("  By execution_status:")
for status, cnt in cur.fetchall():
    print("    {:<25} {:>8}".format(str(status), fmt(cnt)))

# ── SOURCE DATA ──
print("\n-- SOURCE DATA (unpromoted) --")
ht = q1("SELECT COUNT(*) FROM enrichment.hunter_contact")
hl = q1("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE outreach_id IS NOT NULL")
h_li = q1("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE linkedin_url IS NOT NULL AND linkedin_url != ''")
h_title = q1("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE job_title IS NOT NULL AND job_title != ''")
print("  Hunter contacts total:       " + fmt(ht))
print("    Linked to outreach:        {} ({})".format(fmt(hl), pct(hl, ht)))
print("    Unlinked:                  " + fmt(ht - hl))
print("    With LinkedIn URL:         {} ({})".format(fmt(h_li), pct(h_li, ht)))
print("    With job title:            {} ({})".format(fmt(h_title), pct(h_title, ht)))
print("    NULL/empty job title:      {} ({})".format(fmt(ht - h_title), pct(ht - h_title, ht)))

clay = q1("SELECT COUNT(*) FROM intake.people_raw_intake")
clay_li = q1("SELECT COUNT(*) FROM intake.people_raw_intake WHERE linkedin_url IS NOT NULL AND linkedin_url != ''")
print("  Clay intake people:          " + fmt(clay))
print("    With LinkedIn:             " + fmt(clay_li))

# ── MESSAGING LANE TABLES ──
print("\n-- MESSAGING LANE TABLES --")
aah = q1("SELECT COUNT(*) FROM sales.appointments_already_had")
fcm = q1("SELECT COUNT(*) FROM partners.fractional_cfo_master")
pa = q1("SELECT COUNT(*) FROM partners.partner_appointments")
print("  sales.appointments_already_had:  " + fmt(aah))
print("  partners.fractional_cfo_master:  " + fmt(fcm))
print("  partners.partner_appointments:   " + fmt(pa))

# Check legacy appointments
try:
    legacy = q1("SELECT COUNT(*) FROM outreach.appointments")
    print("  outreach.appointments (legacy):  " + fmt(legacy))
except:
    conn.rollback()
    print("  outreach.appointments:           (table not found)")

# ── DOMAIN HEALTH ──
print("\n-- DOMAIN HEALTH --")
try:
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='outreach' AND table_name='blog' AND column_name LIKE '%status%'")
    status_cols = [r[0] for r in cur.fetchall()]
    if status_cols:
        col = status_cols[0]
        cur.execute("SELECT {}, COUNT(*) FROM outreach.blog GROUP BY {} ORDER BY COUNT(*) DESC".format(col, col))
        for val, cnt in cur.fetchall():
            print("  {:<25} {:>8}".format(str(val), fmt(cnt)))
    else:
        blog_total = q1("SELECT COUNT(*) FROM outreach.blog")
        print("  Blog records total:          " + fmt(blog_total))
except Exception as e:
    conn.rollback()
    print("  (error reading blog: {})".format(str(e)[:60]))

# ── BLOG URLs ──
print("\n-- BLOG/ABOUT URLs --")
cur.execute("SELECT source_type, COUNT(*) FROM company.company_source_urls GROUP BY source_type ORDER BY COUNT(*) DESC")
total_urls = 0
for stype, cnt in cur.fetchall():
    print("  {:<20} {:>8}".format(stype, fmt(cnt)))
    total_urls += cnt
print("  {:<20} {:>8}".format("TOTAL", fmt(total_urls)))
companies_with_urls = q1("SELECT COUNT(DISTINCT company_unique_id) FROM company.company_source_urls")
print("  Unique companies:            " + fmt(companies_with_urls))

conn.close()
print("\n" + "=" * 70)
