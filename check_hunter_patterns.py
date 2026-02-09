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
    SELECT email_pattern, COUNT(*) as cnt
    FROM enrichment.hunter_company
    WHERE email_pattern IS NOT NULL
    GROUP BY email_pattern
    ORDER BY COUNT(*) DESC
    LIMIT 15;
""")

print('Top Hunter Email Patterns:')
print('=' * 60)
for row in cur.fetchall():
    print(f'{row[0]}: {row[1]} companies')

conn.close()
