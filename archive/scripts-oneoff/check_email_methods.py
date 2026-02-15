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

# Check email_method distribution
cur.execute("""
    SELECT
        ct.email_method,
        COUNT(*) as person_count,
        COUNT(DISTINCT ct.company_unique_id) as company_count
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    GROUP BY ct.email_method
    ORDER BY COUNT(*) DESC;
""")

print('Email Method Distribution for People Missing Emails:')
print('=' * 80)
print(f"{'Email Method':<20} {'People':<15} {'Companies':<15}")
print('-' * 80)
for row in cur.fetchall():
    method = row[0] or 'NULL'
    print(f"{method:<20} {row[1]:<15} {row[2]:<15}")

print('\n')

# Check a sample of each method
cur.execute("""
    SELECT
        pm.first_name,
        pm.last_name,
        pm.company_unique_id,
        ct.email_method,
        ci.company_domain,
        hc.email_pattern
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    LEFT JOIN cl.company_identity ci ON ct.company_unique_id::uuid = ci.sovereign_company_id
    LEFT JOIN enrichment.hunter_company hc ON ct.company_unique_id::uuid = hc.company_unique_id::uuid
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    LIMIT 20;
""")

print('Sample People Missing Emails:')
print('=' * 120)
for row in cur.fetchall():
    print(f"Person: {row[0]} {row[1]}")
    print(f"  Company ID: {row[2]}")
    print(f"  Email Method: {row[3]}")
    print(f"  Domain: {row[4]}")
    print(f"  Hunter Pattern: {row[5]}")
    print()

conn.close()
