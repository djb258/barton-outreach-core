#!/usr/bin/env python3
"""Check EIN format mismatch between outreach.dol and dol.form_5500"""

import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("=" * 70)
print("EIN FORMAT CHECK - Why join fails")
print("=" * 70)
print()

# Sample EINs from outreach.dol
cur.execute("SELECT ein FROM outreach.dol WHERE ein IS NOT NULL LIMIT 5")
print("outreach.dol EIN format:")
for r in cur.fetchall():
    print(f'  "{r[0]}"')

# Sample EINs from dol.form_5500
cur.execute("SELECT spons_dfe_ein FROM dol.form_5500 WHERE spons_dfe_ein IS NOT NULL LIMIT 5")
print()
print("dol.form_5500 EIN format:")
for r in cur.fetchall():
    print(f'  "{r[0]}"')

# Check data types
cur.execute("""
SELECT 
    c.table_schema, c.table_name, c.column_name, c.data_type
FROM information_schema.columns c
WHERE (c.table_schema = 'outreach' AND c.table_name = 'dol' AND c.column_name = 'ein')
   OR (c.table_schema = 'dol' AND c.table_name = 'form_5500' AND c.column_name = 'spons_dfe_ein')
""")
print()
print("Data types:")
for r in cur.fetchall():
    print(f"  {r[0]}.{r[1]}.{r[2]}: {r[3]}")

# Try normalized join
print()
print("=" * 70)
print("TRYING NORMALIZED JOIN")
print("=" * 70)

cur.execute("""
SELECT COUNT(*)
FROM outreach.dol d
JOIN dol.form_5500 f ON REPLACE(f.spons_dfe_ein, '-', '') = REPLACE(d.ein, '-', '')
""")
print(f"Matches with normalized EIN: {cur.fetchone()[0]:,}")

conn.close()
