import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

cur.execute("""
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema = 'company' AND table_name = 'company_master'
    ORDER BY ordinal_position
""")
print("Columns in company.company_master:")
for row in cur.fetchall():
    print(f"  {row[0]}")
