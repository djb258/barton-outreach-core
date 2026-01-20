#!/usr/bin/env python3
"""Check Neon schema."""

import os
import sys

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

import psycopg2
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

# List all schemas
print("=== SCHEMAS ===")
cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
for row in cursor.fetchall():
    print(f"  {row[0]}")

# List tables in marketing schema
print("\n=== TABLES IN marketing SCHEMA ===")
cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'marketing'
    ORDER BY table_name
""")
tables = cursor.fetchall()
if tables:
    for row in tables:
        print(f"  {row[0]}")
else:
    print("  (no tables)")

# List tables in svg_marketing schema
print("\n=== TABLES IN svg_marketing SCHEMA ===")
cursor.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'svg_marketing'
    ORDER BY table_name
""")
tables = cursor.fetchall()
if tables:
    for row in tables:
        print(f"  {row[0]}")
else:
    print("  (no tables)")

# Check if company_slot exists anywhere
print("\n=== SEARCHING FOR company_slot TABLE ===")
cursor.execute("""
    SELECT table_schema, table_name FROM information_schema.tables
    WHERE table_name LIKE '%slot%' OR table_name LIKE '%company%'
    ORDER BY table_schema, table_name
""")
tables = cursor.fetchall()
if tables:
    for row in tables:
        print(f"  {row[0]}.{row[1]}")
else:
    print("  (no matching tables)")

cursor.close()
conn.close()
