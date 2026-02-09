#!/usr/bin/env python3
"""Check how much unlinked source data can be linked to production."""
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

print("=" * 70)
print("LINKABILITY ANALYSIS")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════
# 1. HUNTER UNLINKED (247,362) — can we link via domain?
# ═══════════════════════════════════════════════════════════════════
print("\n== HUNTER UNLINKED (no outreach_id) ==")

unlinked = q1("SELECT COUNT(*) FROM enrichment.hunter_contact WHERE outreach_id IS NULL")
print("  Total unlinked:              " + fmt(unlinked))

# How many have a domain?
has_domain = q1("""
    SELECT COUNT(*) FROM enrichment.hunter_contact
    WHERE outreach_id IS NULL AND domain IS NOT NULL AND domain != ''
""")
print("  With domain:                 " + fmt(has_domain))

# How many of those domains exist in outreach.outreach?
linkable_by_domain = q1("""
    SELECT COUNT(*)
    FROM enrichment.hunter_contact hc
    WHERE hc.outreach_id IS NULL
      AND hc.domain IS NOT NULL AND hc.domain != ''
      AND LOWER(hc.domain) IN (SELECT LOWER(domain) FROM outreach.outreach)
""")
print("  Domain matches outreach:     {} (linkable!)".format(fmt(linkable_by_domain)))
print("  Domain NOT in outreach:      " + fmt(has_domain - linkable_by_domain))

# Of the linkable ones, how many have useful data?
cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN hc.job_title IS NOT NULL AND hc.job_title != '' THEN 1 END) as has_title,
        COUNT(CASE WHEN hc.linkedin_url IS NOT NULL AND hc.linkedin_url != '' THEN 1 END) as has_linkedin,
        COUNT(CASE WHEN hc.email IS NOT NULL AND hc.email != '' THEN 1 END) as has_email,
        COUNT(CASE WHEN hc.phone_number IS NOT NULL AND hc.phone_number != '' THEN 1 END) as has_phone
    FROM enrichment.hunter_contact hc
    WHERE hc.outreach_id IS NULL
      AND LOWER(hc.domain) IN (SELECT LOWER(domain) FROM outreach.outreach)
""")
total, has_title, has_li, has_em, has_ph = cur.fetchone()
print("\n  Of the {} linkable:".format(fmt(total)))
print("    With email:                " + fmt(has_em))
print("    With job title:            " + fmt(has_title))
print("    With LinkedIn:             " + fmt(has_li))
print("    With phone:                " + fmt(has_ph))

# How many are CEO/CFO/HR by title?
cur.execute("""
    SELECT
        COUNT(CASE WHEN LOWER(job_title) SIMILAR TO '%%(ceo|chief executive|president|owner|founder|managing director|general manager|principal|chairman)%%' THEN 1 END) as ceo,
        COUNT(CASE WHEN LOWER(job_title) SIMILAR TO '%%(cfo|chief financial|vp finance|controller|treasurer|finance director)%%' THEN 1 END) as cfo,
        COUNT(CASE WHEN LOWER(job_title) SIMILAR TO '%%(hr|human resources|chief people|chro|people operations|talent|head of people)%%' THEN 1 END) as hr
    FROM enrichment.hunter_contact hc
    WHERE hc.outreach_id IS NULL
      AND LOWER(hc.domain) IN (SELECT LOWER(domain) FROM outreach.outreach)
      AND hc.job_title IS NOT NULL AND hc.job_title != ''
""")
ceo, cfo, hr = cur.fetchone()
print("\n    CEO/CFO/HR title breakdown:")
print("      CEO titles:              " + fmt(ceo))
print("      CFO titles:              " + fmt(cfo))
print("      HR titles:               " + fmt(hr))
print("      Total slottable:         " + fmt(ceo + cfo + hr))

# Of those, how many target EMPTY slots?
cur.execute("""
    SELECT COUNT(DISTINCT cs.slot_id)
    FROM people.company_slot cs
    JOIN outreach.outreach oo ON oo.outreach_id = cs.outreach_id
    WHERE cs.is_filled = FALSE AND cs.person_unique_id IS NULL
      AND LOWER(oo.domain) IN (
          SELECT DISTINCT LOWER(domain) FROM enrichment.hunter_contact
          WHERE outreach_id IS NULL AND job_title IS NOT NULL AND job_title != ''
      )
""")
empty_slots_reachable = cur.fetchone()[0]
print("    Empty slots on those domains: " + fmt(empty_slots_reachable))

# ═══════════════════════════════════════════════════════════════════
# 2. HUNTER NO JOB TITLE (198,363) — still useful?
# ═══════════════════════════════════════════════════════════════════
print("\n== HUNTER NO JOB TITLE ==")

no_title = q1("""
    SELECT COUNT(*) FROM enrichment.hunter_contact
    WHERE (job_title IS NULL OR job_title = '')
""")
print("  Total no title:              " + fmt(no_title))

cur.execute("""
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN hc.linkedin_url IS NOT NULL AND hc.linkedin_url != '' THEN 1 END) as has_linkedin,
        COUNT(CASE WHEN hc.email IS NOT NULL AND hc.email != '' THEN 1 END) as has_email,
        COUNT(CASE WHEN hc.outreach_id IS NOT NULL THEN 1 END) as has_oid,
        COUNT(CASE WHEN LOWER(hc.domain) IN (SELECT LOWER(domain) FROM outreach.outreach) THEN 1 END) as domain_match
    FROM enrichment.hunter_contact hc
    WHERE (hc.job_title IS NULL OR hc.job_title = '')
""")
total, li, em, oid, dm = cur.fetchone()
print("  With email:                  " + fmt(em))
print("  With LinkedIn:               " + fmt(li))
print("  Already linked (outreach_id):" + fmt(oid))
print("  Domain in outreach:          " + fmt(dm))
print("  Unlinked + linkable by domain: " + fmt(dm - oid))
print("  (These have email/LinkedIn but no title - can enrich LinkedIn or")
print("   backfill as general contacts, but cannot slot without title)")

# ═══════════════════════════════════════════════════════════════════
# 3. CLAY LINKEDIN (119,950) — match via company_name
# ═══════════════════════════════════════════════════════════════════
print("\n== CLAY INTAKE (company_name match) ==")

clay_total = q1("SELECT COUNT(*) FROM intake.people_raw_intake")
clay_li = q1("SELECT COUNT(*) FROM intake.people_raw_intake WHERE linkedin_url IS NOT NULL AND linkedin_url != ''")
print("  Total Clay people:           " + fmt(clay_total))
print("  With LinkedIn:               " + fmt(clay_li))

# How many Clay company_names match CL?
cur.execute("""
    SELECT COUNT(DISTINCT pri.id)
    FROM intake.people_raw_intake pri
    JOIN cl.company_identity ci
        ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
    WHERE ci.outreach_id IS NOT NULL
""")
name_match = cur.fetchone()[0]
print("\n  Company name exact match to CL: " + fmt(name_match))

# With LinkedIn
cur.execute("""
    SELECT COUNT(DISTINCT pri.id)
    FROM intake.people_raw_intake pri
    JOIN cl.company_identity ci
        ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
    WHERE ci.outreach_id IS NOT NULL
      AND pri.linkedin_url IS NOT NULL AND pri.linkedin_url != ''
""")
name_match_li = cur.fetchone()[0]
print("  With LinkedIn:               " + fmt(name_match_li))

# How many unique companies match?
cur.execute("""
    SELECT COUNT(DISTINCT ci.outreach_id)
    FROM intake.people_raw_intake pri
    JOIN cl.company_identity ci
        ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
    WHERE ci.outreach_id IS NOT NULL
""")
matched_companies = cur.fetchone()[0]
print("  Unique companies matched:    " + fmt(matched_companies))

# Slot type breakdown from Clay
cur.execute("""
    SELECT pri.slot_type, COUNT(*)
    FROM intake.people_raw_intake pri
    JOIN cl.company_identity ci
        ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
    WHERE ci.outreach_id IS NOT NULL
      AND pri.slot_type IS NOT NULL
    GROUP BY pri.slot_type ORDER BY COUNT(*) DESC
""")
rows = cur.fetchall()
if rows:
    print("\n  By slot_type:")
    for st, cnt in rows:
        print("    {:<10} {:>8}".format(str(st), fmt(cnt)))

# How many of those are NOT already in people_master?
cur.execute("""
    SELECT COUNT(DISTINCT pri.id)
    FROM intake.people_raw_intake pri
    JOIN cl.company_identity ci
        ON LOWER(TRIM(pri.company_name)) = LOWER(TRIM(ci.company_name))
    WHERE ci.outreach_id IS NOT NULL
      AND pri.linkedin_url IS NOT NULL AND pri.linkedin_url != ''
      AND NOT EXISTS (
          SELECT 1 FROM people.people_master pm
          WHERE LOWER(TRIM(pm.first_name)) = LOWER(TRIM(pri.first_name))
            AND LOWER(TRIM(pm.last_name)) = LOWER(TRIM(pri.last_name))
            AND pm.company_unique_id = ci.company_unique_id
      )
""")
new_people = cur.fetchone()[0]
print("\n  Clay people NOT in people_master: " + fmt(new_people))
print("  (These could be promoted as new contacts with LinkedIn)")

# ═══════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("ACTIONABLE SUMMARY")
print("=" * 70)
print("\n  1. HUNTER UNLINKED -> link via domain")
print("     {} contacts linkable, {} with CEO/CFO/HR titles".format(fmt(linkable_by_domain), fmt(ceo + cfo + hr)))
print("     Action: UPDATE hunter_contact SET outreach_id = oo.outreach_id WHERE domain match")
print("")
print("  2. HUNTER NO TITLE -> limited value without enrichment")
print("     {} have LinkedIn (could scrape title from LinkedIn profile)".format(fmt(li)))
print("     Cannot slot without title")
print("")
print("  3. CLAY -> link via company_name")
print("     {} people match CL companies, {} with LinkedIn".format(fmt(name_match), fmt(name_match_li)))
print("     {} are NEW (not in people_master)".format(fmt(new_people)))
print("     Action: Promote to people_master with outreach_id from CL match")

conn.close()
print("\n" + "=" * 70)
