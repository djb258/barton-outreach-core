import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()
cur.execute("""
SELECT column_name FROM information_schema.columns 
WHERE table_schema='dol' AND table_name='form_5500' 
AND column_name IN ('sponsor_dfe_ein','sponsor_dfe_name','plan_number','spons_dfe_ein','spons_dfe_pn')
ORDER BY ordinal_position
""")
print("form_5500 alias columns:")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Check what the CSV header has
import csv
with open("data/5500/2024/form_5500/f_5500_2024_latest.csv", "r") as f:
    hdr = [c.strip().lower() for c in next(csv.reader(f))]
print("\nCSV columns with 'ein', 'name', 'pn':")
for h in hdr:
    if 'ein' in h or 'name' in h or '_pn' in h:
        print(f"  {h}")

conn.close()
