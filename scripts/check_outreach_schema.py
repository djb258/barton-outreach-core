#!/usr/bin/env python3
"""
Check outreach tables structure and find the matching path
"""
import psycopg2
import os

conn = psycopg2.connect(os.environ['DATABASE_URL'])
cur = conn.cursor()

print("Outreach Schema Tables")
print("=" * 70)

# List all outreach tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'outreach'
    ORDER BY table_name
""")
print("outreach.* tables:")
for r in cur.fetchall():
    print(f"  {r[0]}")

# Check outreach.outreach columns
print()
print("outreach.outreach columns:")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'outreach'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check outreach.company_target columns
print()
print("outreach.company_target columns:")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'company_target'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check outreach.blog columns
print()
print("outreach.blog columns:")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'blog'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Check outreach.dol columns
print()
print("outreach.dol columns:")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns 
    WHERE table_schema = 'outreach' AND table_name = 'dol'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# Sample from outreach.outreach
print()
print("Sample outreach.outreach (5 rows):")
cur.execute("SELECT * FROM outreach.outreach LIMIT 5")
cols = [desc[0] for desc in cur.description]
print(f"  Columns: {cols}")
for row in cur.fetchall():
    print(f"  {row}")

cur.close()
conn.close()
