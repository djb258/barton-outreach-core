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

# Check which sources have patterns
cur.execute("""
    SELECT
        ct.source,
        COUNT(*) as companies,
        COUNT(ct.email_method) as with_pattern,
        COUNT(hc.email_pattern) as in_hunter_table
    FROM outreach.company_target ct
    LEFT JOIN enrichment.hunter_company hc ON ct.company_unique_id::uuid = hc.company_unique_id::uuid
    GROUP BY ct.source
    ORDER BY COUNT(*) DESC;
""")

print('Source Analysis:')
print('=' * 100)
print(f"{'Source':<30} {'Companies':<15} {'With Pattern':<15} {'In Hunter Table':<20}")
print('-' * 100)
for row in cur.fetchall():
    source = row[0] or 'NULL'
    print(f"{source:<30} {row[1]:<15} {row[2]:<15} {row[3]:<20}")

print('\n')

# Check overlap between people missing emails and Hunter-sourced companies
cur.execute("""
    SELECT
        ct.source,
        COUNT(*) as people_count,
        COUNT(DISTINCT ct.company_unique_id) as company_count
    FROM people.people_master pm
    INNER JOIN people.company_slot cs ON pm.unique_id = cs.person_unique_id
    LEFT JOIN outreach.company_target ct ON cs.outreach_id = ct.outreach_id
    WHERE cs.is_filled = TRUE
    AND (pm.email IS NULL OR TRIM(pm.email) = '')
    GROUP BY ct.source
    ORDER BY COUNT(*) DESC;
""")

print('People Missing Emails by Source:')
print('=' * 80)
print(f"{'Source':<30} {'People':<15} {'Companies':<15}")
print('-' * 80)
for row in cur.fetchall():
    source = row[0] or 'NULL'
    print(f"{source:<30} {row[1]:<15} {row[2]:<15}")

conn.close()
