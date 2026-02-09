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

# Get a sample of people missing emails with their company info
cur.execute("""
    SELECT
        pm.unique_id as person_id,
        pm.first_name,
        pm.last_name,
        pm.company_unique_id as pm_company_id,
        cs.outreach_id,
        ct.company_unique_id as ct_company_uuid,
        ct.email_method,
        ci.company_domain,
        hc.email_pattern,
        hc.company_unique_id as hc_company_uuid
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON ct.company_unique_id::uuid = ci.sovereign_company_id
    LEFT JOIN enrichment.hunter_company hc ON ct.company_unique_id::uuid = hc.company_unique_id::uuid
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    AND ct.email_method = 'hunter'
    LIMIT 10;
""")

print('People with email_method=hunter but missing emails:')
print('=' * 120)
for row in cur.fetchall():
    print(f"Person: {row[1]} {row[2]}")
    print(f"  PM Company ID: {row[3]}")
    print(f"  CT Company UUID: {row[5]}")
    print(f"  Email Method: {row[6]}")
    print(f"  Domain: {row[7]}")
    print(f"  Hunter Pattern: {row[8]}")
    print(f"  Hunter Company UUID: {row[9]}")
    print()

# Check how many have hunter method but no pattern
cur.execute("""
    SELECT COUNT(DISTINCT ct.company_unique_id)
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    AND ct.email_method = 'hunter';
""")

print(f"Companies with email_method='hunter': {cur.fetchone()[0]}")

# Check if any have patterns in hunter_company
cur.execute("""
    SELECT COUNT(DISTINCT hc.company_unique_id)
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    LEFT JOIN enrichment.hunter_company hc ON ct.company_unique_id::uuid = hc.company_unique_id::uuid
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    AND ct.email_method = 'hunter'
    AND hc.email_pattern IS NOT NULL;
""")

print(f"Companies with email_method='hunter' AND hunter_company pattern: {cur.fetchone()[0]}")

conn.close()
