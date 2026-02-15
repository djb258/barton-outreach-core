import os, psycopg2
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# Check dol.form_5500 columns
cur.execute("""
SELECT column_name FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500' ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print("=== dol.form_5500 columns ===")
print(", ".join(cols))
print(f"Total: {len(cols)}")

# Check dol.form_5500_sf columns
cur.execute("""
SELECT column_name FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500_sf' ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print("\n=== dol.form_5500_sf columns ===")
print(", ".join(cols))
print(f"Total: {len(cols)}")

# Check dol.schedule_a columns
cur.execute("""
SELECT column_name FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='schedule_a' ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]
print("\n=== dol.schedule_a columns ===")
print(", ".join(cols))
print(f"Total: {len(cols)}")

# Check existing row counts by form_year
for tbl in ['form_5500', 'form_5500_sf', 'schedule_a']:
    cur.execute(f"SELECT form_year, COUNT(*) FROM dol.{tbl} GROUP BY form_year ORDER BY form_year")
    rows = cur.fetchall()
    print(f"\n{tbl}: {rows}")

# Check if ack_id is UNIQUE on form_5500
cur.execute("""
SELECT conname, contype FROM pg_constraint c
JOIN pg_namespace n ON n.oid=c.connamespace
WHERE n.nspname='dol' AND conrelid='dol.form_5500'::regclass
""")
print("\nform_5500 constraints:", cur.fetchall())

conn.close()
