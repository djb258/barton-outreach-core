import os
import psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol' AND table_name = 'form_5500_sf' 
    AND (column_name LIKE '%name%' OR column_name LIKE '%state%')
    ORDER BY ordinal_position
""")
print("form_5500_sf name/state cols:", [r[0] for r in cur.fetchall()])
