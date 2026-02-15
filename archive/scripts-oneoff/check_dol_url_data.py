#!/usr/bin/env python3
"""Check ALL columns in form_5500 and form_5500_sf for any URL-like data"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("Checking form_5500 for URL-like columns...")
print("=" * 70)

# Get all columns
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol' AND table_name = 'form_5500'
    ORDER BY ordinal_position
""")
cols = [r[0] for r in cur.fetchall()]

# Sample a row and look for URL patterns
cur.execute("SELECT * FROM dol.form_5500 LIMIT 1")
row = cur.fetchone()

print("Columns that might contain URLs (checking for http, .com, .org, www):")
for i, col in enumerate(cols):
    val = row[i] if row else None
    if val and isinstance(val, str):
        val_lower = val.lower()
        if 'http' in val_lower or '.com' in val_lower or '.org' in val_lower or 'www' in val_lower:
            print(f"  {col}: {val[:100]}")

print()
print("=" * 70)
print("Checking form_5500_sf for URL-like columns...")
print("=" * 70)

cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'dol' AND table_name = 'form_5500_sf'
    ORDER BY ordinal_position
""")
sf_cols = [r[0] for r in cur.fetchall()]

cur.execute("SELECT * FROM dol.form_5500_sf LIMIT 1")
sf_row = cur.fetchone()

print("Columns that might contain URLs:")
for i, col in enumerate(sf_cols):
    val = sf_row[i] if sf_row else None
    if val and isinstance(val, str):
        val_lower = val.lower()
        if 'http' in val_lower or '.com' in val_lower or '.org' in val_lower or 'www' in val_lower:
            print(f"  {col}: {val[:100]}")

print()
print("=" * 70)
print("All form_5500_sf columns:")
print("-" * 70)
for col in sf_cols:
    print(f"  {col}")

cur.close()
conn.close()
