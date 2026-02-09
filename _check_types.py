import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Check form_5500 NUMERIC columns
cur.execute("""
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500' AND data_type='numeric'
ORDER BY ordinal_position
""")
print("=== form_5500 NUMERIC columns ===")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Check form_5500_sf NUMERIC columns
cur.execute("""
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500_sf' AND data_type='numeric'
ORDER BY ordinal_position
""")
print("\n=== form_5500_sf NUMERIC columns ===")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Check schedule_a NUMERIC columns
cur.execute("""
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='schedule_a' AND data_type='numeric'
ORDER BY ordinal_position
""")
print("\n=== schedule_a NUMERIC columns ===")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Check NOT NULL on form_5500
cur.execute("""
SELECT column_name, is_nullable FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500' AND is_nullable='NO'
ORDER BY ordinal_position
""")
print("\n=== form_5500 NOT NULL columns ===")
for r in cur.fetchall():
    print(f"  {r[0]}")

conn.close()
