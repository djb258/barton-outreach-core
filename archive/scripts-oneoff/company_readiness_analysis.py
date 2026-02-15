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
print(f"=== COMPANY READINESS ANALYSIS ===")
print(f"Total Companies (CT): {ct_total}")
print()

# Build per-company stats
# For each company, count: slots_filled, slots_with_email, slots_with_linkedin
cur.execute("""
WITH company_slots AS (
    SELECT
        ct.outreach_id,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) as slots_filled,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.outreach_ready = TRUE THEN 1 END) as slots_with_email,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '' THEN 1 END) as slots_with_linkedin,
        -- Can we reach at least one person (email OR linkedin)?
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND (pm.outreach_ready = TRUE OR (pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '')) THEN 1 END) as slots_reachable
    FROM outreach.company_target ct
    LEFT JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    GROUP BY ct.outreach_id
)
SELECT
    slots_filled,
    COUNT(*) as companies,
    -- Email coverage at this depth
    SUM(CASE WHEN slots_with_email >= slots_filled AND slots_filled > 0 THEN 1 ELSE 0 END) as all_have_email,
    SUM(CASE WHEN slots_with_email >= 1 THEN 1 ELSE 0 END) as at_least_one_email,
    -- LinkedIn coverage at this depth
    SUM(CASE WHEN slots_with_linkedin >= slots_filled AND slots_filled > 0 THEN 1 ELSE 0 END) as all_have_linkedin,
    SUM(CASE WHEN slots_with_linkedin >= 1 THEN 1 ELSE 0 END) as at_least_one_linkedin,
    -- Reachable (email OR linkedin)
    SUM(CASE WHEN slots_reachable >= 1 THEN 1 ELSE 0 END) as at_least_one_reachable,
    SUM(CASE WHEN slots_reachable >= slots_filled AND slots_filled > 0 THEN 1 ELSE 0 END) as all_reachable
FROM company_slots
GROUP BY slots_filled
ORDER BY slots_filled
""")

rows = cur.fetchall()
print(f"--- COVERAGE DEPTH ---")
print(f"{'Slots Filled':>14} {'Companies':>10} {'All Email':>10} {'1+ Email':>10} {'All LI':>10} {'1+ LI':>10} {'1+ Reach':>10} {'All Reach':>10}")
print("-" * 95)

total_companies = 0
total_at_least_one_filled = 0
total_at_least_one_email = 0
total_at_least_one_li = 0
total_at_least_one_reach = 0
total_all_email = 0
total_all_li = 0
total_all_reach = 0

for row in rows:
    sf, cos, all_em, one_em, all_li, one_li, one_reach, all_reach = row
    total_companies += cos
    if sf > 0:
        total_at_least_one_filled += cos
        total_at_least_one_email += one_em
        total_at_least_one_li += one_li
        total_at_least_one_reach += one_reach
        total_all_email += all_em
        total_all_li += all_li
        total_all_reach += all_reach
    label = f"{sf} of 3" if sf < 3 else "ALL 3"
    if sf == 0:
        label = "0 (none)"
    print(f"{label:>14} {cos:>10,} {all_em:>10,} {one_em:>10,} {all_li:>10,} {one_li:>10,} {one_reach:>10,} {all_reach:>10,}")

print("-" * 95)
print()

# Summary funnel
print(f"=== READINESS FUNNEL ===")
print(f"1. Total Companies:                    {ct_total:>10,}")
print(f"2. At Least 1 Slot Filled:             {total_at_least_one_filled:>10,}  ({100.0*total_at_least_one_filled/ct_total:.1f}%)")
print(f"3. At Least 1 Person Reachable:        {total_at_least_one_reach:>10,}  ({100.0*total_at_least_one_reach/ct_total:.1f}%)")
print(f"   - via Email:                        {total_at_least_one_email:>10,}  ({100.0*total_at_least_one_email/ct_total:.1f}%)")
print(f"   - via LinkedIn:                     {total_at_least_one_li:>10,}  ({100.0*total_at_least_one_li/ct_total:.1f}%)")
print()

# Now break down the 3-slot companies specifically
print(f"=== DEPTH ANALYSIS: COMPANIES WITH ALL 3 SLOTS FILLED ===")
cur.execute("""
WITH company_slots AS (
    SELECT
        ct.outreach_id,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) as slots_filled,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.outreach_ready = TRUE THEN 1 END) as slots_with_email,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '' THEN 1 END) as slots_with_linkedin
    FROM outreach.company_target ct
    LEFT JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    GROUP BY ct.outreach_id
    HAVING COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) = 3
)
SELECT
    COUNT(*) as total_3slot,
    SUM(CASE WHEN slots_with_email = 3 THEN 1 ELSE 0 END) as all_3_email,
    SUM(CASE WHEN slots_with_email >= 2 THEN 1 ELSE 0 END) as at_least_2_email,
    SUM(CASE WHEN slots_with_email >= 1 THEN 1 ELSE 0 END) as at_least_1_email,
    SUM(CASE WHEN slots_with_linkedin = 3 THEN 1 ELSE 0 END) as all_3_li,
    SUM(CASE WHEN slots_with_linkedin >= 2 THEN 1 ELSE 0 END) as at_least_2_li,
    SUM(CASE WHEN slots_with_linkedin >= 1 THEN 1 ELSE 0 END) as at_least_1_li,
    SUM(CASE WHEN slots_with_email = 3 AND slots_with_linkedin = 3 THEN 1 ELSE 0 END) as full_coverage
FROM company_slots
""")
r = cur.fetchone()
t3 = r[0]
print(f"Companies with all 3 slots filled: {t3:,}")
print(f"  All 3 have verified email:       {r[1]:>8,}  ({100.0*r[1]/t3:.1f}%)")
print(f"  At least 2 have email:           {r[2]:>8,}  ({100.0*r[2]/t3:.1f}%)")
print(f"  At least 1 has email:            {r[3]:>8,}  ({100.0*r[3]/t3:.1f}%)")
print(f"  All 3 have LinkedIn:             {r[4]:>8,}  ({100.0*r[4]/t3:.1f}%)")
print(f"  At least 2 have LinkedIn:        {r[5]:>8,}  ({100.0*r[5]/t3:.1f}%)")
print(f"  At least 1 has LinkedIn:         {r[6]:>8,}  ({100.0*r[6]/t3:.1f}%)")
print(f"  FULL COVERAGE (3 email + 3 LI):  {r[7]:>8,}  ({100.0*r[7]/t3:.1f}%)")
print()

# Same for 2-slot companies
print(f"=== DEPTH ANALYSIS: COMPANIES WITH 2 OF 3 SLOTS FILLED ===")
cur.execute("""
WITH company_slots AS (
    SELECT
        ct.outreach_id,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) as slots_filled,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.outreach_ready = TRUE THEN 1 END) as slots_with_email,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '' THEN 1 END) as slots_with_linkedin
    FROM outreach.company_target ct
    LEFT JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    GROUP BY ct.outreach_id
    HAVING COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) = 2
)
SELECT
    COUNT(*) as total_2slot,
    SUM(CASE WHEN slots_with_email = 2 THEN 1 ELSE 0 END) as both_email,
    SUM(CASE WHEN slots_with_email >= 1 THEN 1 ELSE 0 END) as at_least_1_email,
    SUM(CASE WHEN slots_with_linkedin = 2 THEN 1 ELSE 0 END) as both_li,
    SUM(CASE WHEN slots_with_linkedin >= 1 THEN 1 ELSE 0 END) as at_least_1_li,
    SUM(CASE WHEN slots_with_email = 2 AND slots_with_linkedin = 2 THEN 1 ELSE 0 END) as full_coverage
FROM company_slots
""")
r2 = cur.fetchone()
t2 = r2[0]
print(f"Companies with 2 of 3 slots filled: {t2:,}")
print(f"  Both have verified email:         {r2[1]:>8,}  ({100.0*r2[1]/t2:.1f}%)")
print(f"  At least 1 has email:             {r2[2]:>8,}  ({100.0*r2[2]/t2:.1f}%)")
print(f"  Both have LinkedIn:               {r2[3]:>8,}  ({100.0*r2[3]/t2:.1f}%)")
print(f"  At least 1 has LinkedIn:          {r2[4]:>8,}  ({100.0*r2[4]/t2:.1f}%)")
print(f"  FULL COVERAGE (2 email + 2 LI):   {r2[5]:>8,}  ({100.0*r2[5]/t2:.1f}%)")
print()

# Same for 1-slot companies
print(f"=== DEPTH ANALYSIS: COMPANIES WITH 1 OF 3 SLOTS FILLED ===")
cur.execute("""
WITH company_slots AS (
    SELECT
        ct.outreach_id,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) as slots_filled,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.outreach_ready = TRUE THEN 1 END) as slots_with_email,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
                    AND pm.linkedin_url IS NOT NULL AND pm.linkedin_url != '' THEN 1 END) as slots_with_linkedin
    FROM outreach.company_target ct
    LEFT JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
    LEFT JOIN people.people_master pm ON pm.unique_id = cs.person_unique_id
    GROUP BY ct.outreach_id
    HAVING COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) = 1
)
SELECT
    COUNT(*) as total_1slot,
    SUM(CASE WHEN slots_with_email = 1 THEN 1 ELSE 0 END) as has_email,
    SUM(CASE WHEN slots_with_linkedin = 1 THEN 1 ELSE 0 END) as has_li,
    SUM(CASE WHEN slots_with_email = 1 AND slots_with_linkedin = 1 THEN 1 ELSE 0 END) as full_coverage
FROM company_slots
""")
r1 = cur.fetchone()
t1 = r1[0]
print(f"Companies with 1 of 3 slots filled: {t1:,}")
print(f"  Has verified email:               {r1[1]:>8,}  ({100.0*r1[1]/t1:.1f}%)")
print(f"  Has LinkedIn:                     {r1[2]:>8,}  ({100.0*r1[2]/t1:.1f}%)")
print(f"  FULL COVERAGE (email + LI):       {r1[3]:>8,}  ({100.0*r1[3]/t1:.1f}%)")
print()

# Zero slots
cur.execute("""
WITH company_slots AS (
    SELECT
        ct.outreach_id,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) as slots_filled
    FROM outreach.company_target ct
    LEFT JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
    GROUP BY ct.outreach_id
    HAVING COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) = 0
)
SELECT COUNT(*) FROM company_slots
""")
zero = cur.fetchone()[0]
print(f"Companies with 0 slots filled: {zero:,} ({100.0*zero/ct_total:.1f}% of CT)")
print()

# WHICH slots are most commonly the one filled in 1-slot companies?
print(f"=== WHICH SLOT IS FILLED (1-slot companies) ===")
cur.execute("""
WITH company_slots AS (
    SELECT
        ct.outreach_id,
        COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) as slots_filled
    FROM outreach.company_target ct
    LEFT JOIN people.company_slot cs ON cs.outreach_id = ct.outreach_id
    GROUP BY ct.outreach_id
    HAVING COUNT(CASE WHEN cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR') THEN 1 END) = 1
),
filled_slot AS (
    SELECT cs.outreach_id, cs.slot_type
    FROM people.company_slot cs
    WHERE cs.is_filled = TRUE AND cs.slot_type IN ('CEO','CFO','HR')
      AND cs.outreach_id IN (SELECT outreach_id FROM company_slots)
)
SELECT slot_type, COUNT(*) as cnt
FROM filled_slot
GROUP BY slot_type
ORDER BY cnt DESC
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,}")

conn.close()
