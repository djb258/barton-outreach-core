#!/usr/bin/env python3
"""Check company_master current state"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

# Find all company/master tables
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_name LIKE '%master%' OR table_name LIKE '%company%'
    ORDER BY table_schema, table_name
""")
print("Tables containing 'master' or 'company':")
for r in cur.fetchall():
    print(f"  {r[0]}.{r[1]}")

print()

# Count company_master
cur.execute('SELECT COUNT(*) FROM company.company_master')
print(f"company.company_master: {cur.fetchone()[0]:,}")

# Check if there's filtering happening
cur.execute("SELECT COUNT(*) FROM company.company_master WHERE is_active = true")
active = cur.fetchone()[0]
print(f"  is_active = true: {active:,}")

cur.execute("SELECT COUNT(*) FROM company.company_master WHERE is_active = false")
inactive = cur.fetchone()[0]
print(f"  is_active = false: {inactive:,}")

cur.execute("SELECT COUNT(*) FROM company.company_master WHERE is_active IS NULL")
null_active = cur.fetchone()[0]
print(f"  is_active IS NULL: {null_active:,}")

cur.close()
conn.close()
