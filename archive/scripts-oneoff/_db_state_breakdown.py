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

cur.execute("""
WITH ct AS (
    SELECT ct.outreach_id, ct.state
    FROM outreach.company_target ct
    WHERE ct.state NOT IN ('CA', 'NY')
),
dol_ids AS (
    SELECT DISTINCT outreach_id FROM outreach.dol
),
blog_ids AS (
    SELECT DISTINCT outreach_id FROM outreach.blog
),
company_li AS (
    SELECT outreach_id
    FROM cl.company_identity
    WHERE outreach_id IS NOT NULL
      AND linkedin_company_url IS NOT NULL
      AND linkedin_company_url <> ''
),
ceo_data AS (
    SELECT cs.outreach_id,
           CASE WHEN pm.linkedin_url IS NOT NULL AND pm.linkedin_url <> '' THEN 1 ELSE 0 END as has_li
    FROM people.company_slot cs
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    WHERE cs.slot_type = 'CEO' AND cs.is_filled = TRUE
),
cfo_data AS (
    SELECT cs.outreach_id,
           CASE WHEN pm.linkedin_url IS NOT NULL AND pm.linkedin_url <> '' THEN 1 ELSE 0 END as has_li
    FROM people.company_slot cs
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    WHERE cs.slot_type = 'CFO' AND cs.is_filled = TRUE
),
hr_data AS (
    SELECT cs.outreach_id,
           CASE WHEN pm.linkedin_url IS NOT NULL AND pm.linkedin_url <> '' THEN 1 ELSE 0 END as has_li
    FROM people.company_slot cs
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    WHERE cs.slot_type = 'HR' AND cs.is_filled = TRUE
)
SELECT
    ct.state,
    COUNT(DISTINCT ct.outreach_id) as companies,
    -- DOL
    COUNT(DISTINCT CASE WHEN d.outreach_id IS NOT NULL THEN ct.outreach_id END) as dol,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN d.outreach_id IS NOT NULL THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as dol_pct,
    -- Blog
    COUNT(DISTINCT CASE WHEN b.outreach_id IS NOT NULL THEN ct.outreach_id END) as blog,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN b.outreach_id IS NOT NULL THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as blog_pct,
    -- Company LinkedIn
    COUNT(DISTINCT CASE WHEN cli.outreach_id IS NOT NULL THEN ct.outreach_id END) as co_li,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN cli.outreach_id IS NOT NULL THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as co_li_pct,
    -- CEO filled
    COUNT(DISTINCT CASE WHEN ceo.outreach_id IS NOT NULL THEN ct.outreach_id END) as ceo,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN ceo.outreach_id IS NOT NULL THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as ceo_pct,
    -- CEO LinkedIn
    COUNT(DISTINCT CASE WHEN ceo.outreach_id IS NOT NULL AND ceo.has_li = 1 THEN ct.outreach_id END) as ceo_li,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN ceo.outreach_id IS NOT NULL AND ceo.has_li = 1 THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as ceo_li_pct,
    -- CFO filled
    COUNT(DISTINCT CASE WHEN cfo.outreach_id IS NOT NULL THEN ct.outreach_id END) as cfo,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN cfo.outreach_id IS NOT NULL THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as cfo_pct,
    -- CFO LinkedIn
    COUNT(DISTINCT CASE WHEN cfo.outreach_id IS NOT NULL AND cfo.has_li = 1 THEN ct.outreach_id END) as cfo_li,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN cfo.outreach_id IS NOT NULL AND cfo.has_li = 1 THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as cfo_li_pct,
    -- HR filled
    COUNT(DISTINCT CASE WHEN hr.outreach_id IS NOT NULL THEN ct.outreach_id END) as hr,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN hr.outreach_id IS NOT NULL THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as hr_pct,
    -- HR LinkedIn
    COUNT(DISTINCT CASE WHEN hr.outreach_id IS NOT NULL AND hr.has_li = 1 THEN ct.outreach_id END) as hr_li,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN hr.outreach_id IS NOT NULL AND hr.has_li = 1 THEN ct.outreach_id END) / NULLIF(COUNT(DISTINCT ct.outreach_id), 0), 1) as hr_li_pct
FROM ct
LEFT JOIN dol_ids d ON d.outreach_id = ct.outreach_id
LEFT JOIN blog_ids b ON b.outreach_id = ct.outreach_id
LEFT JOIN company_li cli ON cli.outreach_id = ct.outreach_id
LEFT JOIN ceo_data ceo ON ceo.outreach_id = ct.outreach_id
LEFT JOIN cfo_data cfo ON cfo.outreach_id = ct.outreach_id
LEFT JOIN hr_data hr ON hr.outreach_id = ct.outreach_id
GROUP BY ct.state
ORDER BY companies DESC
""")

rows = cur.fetchall()

# Print header
print(f"{'State':<6} {'Cos':>7} {'DOL%':>6} {'Blog%':>6} {'CoLI%':>6} {'CEO%':>6} {'CEO_LI%':>8} {'CFO%':>6} {'CFO_LI%':>8} {'HR%':>6} {'HR_LI%':>7}")
print("-" * 95)

total_cos = 0
total_dol = 0
total_blog = 0
total_cli = 0
total_ceo = 0
total_ceo_li = 0
total_cfo = 0
total_cfo_li = 0
total_hr = 0
total_hr_li = 0

for row in rows:
    state = row[0] or 'NULL'
    cos = row[1]
    total_cos += cos
    total_dol += row[2]
    total_blog += row[4]
    total_cli += row[6]
    total_ceo += row[8]
    total_ceo_li += row[10]
    total_cfo += row[12]
    total_cfo_li += row[14]
    total_hr += row[16]
    total_hr_li += row[18]

    print(f"{state:<6} {cos:>7,} {row[3]:>5.1f}% {row[5]:>5.1f}% {row[7]:>5.1f}% {row[9]:>5.1f}% {row[11]:>7.1f}% {row[13]:>5.1f}% {row[15]:>7.1f}% {row[17]:>5.1f}% {row[19]:>6.1f}%")

print("-" * 95)
print(f"{'TOTAL':<6} {total_cos:>7,} {100.0*total_dol/total_cos:>5.1f}% {100.0*total_blog/total_cos:>5.1f}% {100.0*total_cli/total_cos:>5.1f}% {100.0*total_ceo/total_cos:>5.1f}% {100.0*total_ceo_li/total_cos:>7.1f}% {100.0*total_cfo/total_cos:>5.1f}% {100.0*total_cfo_li/total_cos:>7.1f}% {100.0*total_hr/total_cos:>5.1f}% {100.0*total_hr_li/total_cos:>6.1f}%")

conn.close()
