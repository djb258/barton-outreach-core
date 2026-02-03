#!/usr/bin/env python3
"""Analyze Hunter departments for slot filling."""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print('='*70)
print('DEPARTMENT-BASED SLOT FILLING ANALYSIS')
print('='*70)

# HR department breakdown
print('\n' + '='*70)
print('HR DEPARTMENT - For HR Slots')
print('='*70)

cur.execute("""
SELECT job_title, position_raw, COUNT(*) as cnt
FROM enrichment.hunter_contact
WHERE department = 'HR'
AND email IS NOT NULL
AND first_name IS NOT NULL
AND last_name IS NOT NULL
GROUP BY job_title, position_raw
ORDER BY COUNT(*) DESC
LIMIT 25
""")
print(f"\n{'Job Title':45} | {'Position Raw':35} | Count")
print('-'*95)
for r in cur.fetchall():
    title = (r[0] or 'NULL')[:45]
    pos = (r[1] or 'NULL')[:35]
    print(f'{title:45} | {pos:35} | {r[2]:,}')

# Finance department for CFO
print('\n' + '='*70)
print('FINANCE DEPARTMENT - For CFO Slots')
print('='*70)

cur.execute("""
SELECT job_title, position_raw, COUNT(*) as cnt
FROM enrichment.hunter_contact
WHERE department = 'Finance'
AND email IS NOT NULL
AND first_name IS NOT NULL
AND last_name IS NOT NULL
GROUP BY job_title, position_raw
ORDER BY COUNT(*) DESC
LIMIT 25
""")
print(f"\n{'Job Title':45} | {'Position Raw':35} | Count")
print('-'*95)
for r in cur.fetchall():
    title = (r[0] or 'NULL')[:45]
    pos = (r[1] or 'NULL')[:35]
    print(f'{title:45} | {pos:35} | {r[2]:,}')

# Executive department for CEO
print('\n' + '='*70)
print('EXECUTIVE DEPARTMENT - For CEO Slots')
print('='*70)

cur.execute("""
SELECT job_title, position_raw, COUNT(*) as cnt
FROM enrichment.hunter_contact
WHERE department = 'Executive'
AND email IS NOT NULL
AND first_name IS NOT NULL
AND last_name IS NOT NULL
GROUP BY job_title, position_raw
ORDER BY COUNT(*) DESC
LIMIT 30
""")
print(f"\n{'Job Title':45} | {'Position Raw':35} | Count")
print('-'*95)
for r in cur.fetchall():
    title = (r[0] or 'NULL')[:45]
    pos = (r[1] or 'NULL')[:35]
    print(f'{title:45} | {pos:35} | {r[2]:,}')

# Department totals
print('\n' + '='*70)
print('ALL DEPARTMENTS - Total Contacts')
print('='*70)
cur.execute("""
SELECT department, COUNT(*) as cnt
FROM enrichment.hunter_contact
WHERE email IS NOT NULL AND first_name IS NOT NULL AND last_name IS NOT NULL
GROUP BY department
ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    dept = r[0] or 'NULL'
    print(f'  {dept:30} | {r[1]:,}')

# Summary of what we can fill
print('\n' + '='*70)
print('SLOT FILLING POTENTIAL')
print('='*70)

# CEO from Executive dept
cur.execute("""
SELECT COUNT(DISTINCT hc.id)
FROM enrichment.hunter_contact hc
WHERE hc.department = 'Executive'
AND hc.email IS NOT NULL
AND hc.first_name IS NOT NULL
AND hc.last_name IS NOT NULL
""")
exec_count = cur.fetchone()[0]

# CFO from Finance dept
cur.execute("""
SELECT COUNT(DISTINCT hc.id)
FROM enrichment.hunter_contact hc
WHERE hc.department = 'Finance'
AND hc.email IS NOT NULL
AND hc.first_name IS NOT NULL
AND hc.last_name IS NOT NULL
""")
finance_count = cur.fetchone()[0]

# HR from HR dept
cur.execute("""
SELECT COUNT(DISTINCT hc.id)
FROM enrichment.hunter_contact hc
WHERE hc.department = 'HR'
AND hc.email IS NOT NULL
AND hc.first_name IS NOT NULL
AND hc.last_name IS NOT NULL
""")
hr_count = cur.fetchone()[0]

print(f"\nCEO candidates (Executive dept): {exec_count:,}")
print(f"CFO candidates (Finance dept):   {finance_count:,}")
print(f"HR candidates (HR dept):         {hr_count:,}")

# How many empty slots can we fill?
print('\n--- Matching to Empty Slots ---')
for slot_type, dept in [('CEO', 'Executive'), ('CFO', 'Finance'), ('HR', 'HR')]:
    cur.execute(f"""
        WITH cm_domains AS (
            SELECT 
                company_unique_id,
                LOWER(REGEXP_REPLACE(
                    REGEXP_REPLACE(website_url, '^https?://(www\\.)?', ''),
                    '/.*$', ''
                )) as domain
            FROM company.company_master
            WHERE website_url IS NOT NULL
        )
        SELECT COUNT(DISTINCT cs.slot_id)
        FROM people.company_slot cs
        JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
        JOIN outreach.outreach o ON ct.outreach_id = o.outreach_id
        JOIN cm_domains cmd ON cmd.domain = LOWER(o.domain)
        JOIN enrichment.hunter_contact hc ON LOWER(o.domain) = LOWER(hc.domain)
        WHERE cs.is_filled = false
        AND cs.slot_type = '{slot_type}'
        AND hc.department = '{dept}'
        AND hc.email IS NOT NULL
        AND hc.first_name IS NOT NULL
        AND hc.last_name IS NOT NULL
        AND cmd.company_unique_id IS NOT NULL
    """)
    cnt = cur.fetchone()[0]
    print(f"  {slot_type} slots fillable from {dept} dept: {cnt:,}")

conn.close()
