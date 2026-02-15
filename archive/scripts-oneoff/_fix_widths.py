"""Fix form_5500 column size issues for 2024 import.
Widen all foreign address/province/state columns that are too narrow.
"""
import os, psycopg2

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("SET session \"dol.import_mode\" = 'active';")

# Find all VARCHAR(10) and VARCHAR(20) columns in form_5500 that contain 'foreign' or 'prov'
cur.execute("""
SELECT column_name, character_maximum_length
FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500'
AND data_type='character varying' 
AND character_maximum_length < 100
AND (column_name LIKE '%foreign%' OR column_name LIKE '%prov%' 
     OR column_name LIKE '%postal%' OR column_name LIKE '%cntry%')
ORDER BY ordinal_position
""")
cols = cur.fetchall()
print(f"Found {len(cols)} narrow foreign columns to widen:")
for name, maxlen in cols:
    new_size = 255
    print(f"  {name}: VARCHAR({maxlen}) -> VARCHAR({new_size})")
    cur.execute(f"ALTER TABLE dol.form_5500 ALTER COLUMN {name} TYPE VARCHAR({new_size});")

# Also widen any _text columns that might be VARCHAR
cur.execute("""
SELECT column_name, character_maximum_length
FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500'
AND data_type='character varying'
AND character_maximum_length < 100
AND column_name LIKE '%text%'
ORDER BY ordinal_position
""")
for name, maxlen in cur.fetchall():
    print(f"  {name}: VARCHAR({maxlen}) -> TEXT")
    cur.execute(f"ALTER TABLE dol.form_5500 ALTER COLUMN {name} TYPE TEXT;")

conn.commit()
print("\nDone.")
conn.close()
