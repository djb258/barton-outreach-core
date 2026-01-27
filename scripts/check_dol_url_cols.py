#!/usr/bin/env python3
"""Check DOL form_5500 columns for any URL/website fields"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("DOL form_5500 columns containing 'url', 'web', 'site', 'http':")
print("=" * 60)
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol' AND table_name = 'form_5500'
    AND (column_name ILIKE '%url%' OR column_name ILIKE '%web%' 
         OR column_name ILIKE '%site%' OR column_name ILIKE '%http%')
    ORDER BY column_name
""")
url_cols = cur.fetchall()
if url_cols:
    for r in url_cols:
        print(f"  {r[0]}")
else:
    print("  (none found)")

print()
print("All DOL form_5500 columns:")
print("-" * 60)
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol' AND table_name = 'form_5500'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r[0]}")

print()
print("=" * 60)
print("DOL form_5500_sf columns containing 'url', 'web', 'site', 'http':")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol' AND table_name = 'form_5500_sf'
    AND (column_name ILIKE '%url%' OR column_name ILIKE '%web%' 
         OR column_name ILIKE '%site%' OR column_name ILIKE '%http%')
    ORDER BY column_name
""")
url_cols = cur.fetchall()
if url_cols:
    for r in url_cols:
        print(f"  {r[0]}")
else:
    print("  (none found)")

cur.close()
conn.close()
