import os
import psycopg2

conn = psycopg2.connect(
    host=os.environ['NEON_HOST'],
    database=os.environ['NEON_DATABASE'],
    user=os.environ['NEON_USER'],
    password=os.environ['NEON_PASSWORD'],
    sslmode='require'
)

cur = conn.cursor()
cur.execute("""
    SELECT
        pm.company_unique_id,
        ct.company_unique_id as ct_company_unique_id,
        ci.sovereign_company_id,
        ci.company_domain
    FROM people.people_master pm
    LEFT JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON ct.company_unique_id::uuid = ci.sovereign_company_id
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    LIMIT 5;
""")

print('Sample Join Results:')
print('=' * 80)
for row in cur.fetchall():
    print(f"PM company_unique_id: {row[0]}")
    print(f"CT company_unique_id: {row[1]}")
    print(f"CI sovereign_company_id: {row[2]}")
    print(f"Domain: {row[3]}")
    print()

conn.close()
