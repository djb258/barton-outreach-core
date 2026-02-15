#!/usr/bin/env python3
"""
Schema Audit Script - READ ONLY
Inventories all schemas, tables, and views in the Neon database.
"""
import psycopg2
import os
from collections import defaultdict

def main():
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()

    # Get all schemas
    cur.execute("""
    SELECT schema_name
    FROM information_schema.schemata
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    ORDER BY schema_name
    """)
    schemas = [r[0] for r in cur.fetchall()]

    print("=" * 80)
    print("SCHEMA AUDIT REPORT - READ ONLY")
    print("=" * 80)

    print("\n=== SCHEMAS ===")
    for s in schemas:
        print(f"  {s}")

    # Get all tables with row counts
    print("\n=== TABLES BY SCHEMA (with row estimates) ===")
    for schema in schemas:
        cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """, (schema,))
        tables = [r[0] for r in cur.fetchall()]

        if tables:
            print(f"\n[{schema}] - {len(tables)} tables")
            for table in tables:
                # Get row count estimate
                try:
                    cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
                    count = cur.fetchone()[0]
                    print(f"  {table}: {count:,} rows")
                except Exception as e:
                    print(f"  {table}: ERROR - {e}")

    # Get all views
    print("\n=== VIEWS BY SCHEMA ===")
    for schema in schemas:
        cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'VIEW'
        ORDER BY table_name
        """, (schema,))
        views = [r[0] for r in cur.fetchall()]

        if views:
            print(f"\n[{schema}] - {len(views)} views")
            for view in views:
                print(f"  {view}")

    # Get materialized views
    print("\n=== MATERIALIZED VIEWS ===")
    cur.execute("""
    SELECT schemaname, matviewname
    FROM pg_matviews
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    ORDER BY schemaname, matviewname
    """)
    matviews = cur.fetchall()
    if matviews:
        for schema, mv in matviews:
            print(f"  {schema}.{mv}")
    else:
        print("  (none)")

    conn.close()

if __name__ == "__main__":
    main()
