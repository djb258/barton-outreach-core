#!/usr/bin/env python3
"""List all tables in Neon database"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv('DATABASE_URL')
conn = psycopg2.connect(database_url)
cursor = conn.cursor()

print("All tables in database:\n")

cursor.execute("""
    SELECT
        table_schema,
        table_name,
        (SELECT COUNT(*)
         FROM information_schema.columns
         WHERE columns.table_schema = tables.table_schema
         AND columns.table_name = tables.table_name) as column_count
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    AND table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name
""")

tables = cursor.fetchall()

current_schema = None
for schema, table, col_count in tables:
    if schema != current_schema:
        print(f"\n{schema}:")
        current_schema = schema
    print(f"  - {table} ({col_count} columns)")

# Check for any tables with state column
print("\n\nTables with 'state' column:")
cursor.execute("""
    SELECT DISTINCT
        table_schema || '.' || table_name as full_table_name
    FROM information_schema.columns
    WHERE column_name = 'state'
    AND table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY full_table_name
""")

state_tables = cursor.fetchall()
for table in state_tables:
    print(f"  - {table[0]}")

cursor.close()
conn.close()
