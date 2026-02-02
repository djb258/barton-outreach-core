#!/usr/bin/env python3
"""
Schema Drift Checker: Compare ERD documentation against actual Neon database schema
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json

def get_neon_connection():
    """Get Neon database connection"""
    return psycopg2.connect(
        host=os.getenv('NEON_HOST'),
        database=os.getenv('NEON_DATABASE'),
        user=os.getenv('NEON_USER'),
        password=os.getenv('NEON_PASSWORD'),
        sslmode='require'
    )

def get_all_tables(conn):
    """Get all tables in relevant schemas"""
    query = """
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_schema IN ('outreach', 'cl', 'people', 'dol', 'company', 'bit')
      AND table_type = 'BASE TABLE'
    ORDER BY table_schema, table_name;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def get_all_views(conn):
    """Get all views in relevant schemas"""
    query = """
    SELECT table_schema, table_name
    FROM information_schema.views
    WHERE table_schema IN ('outreach', 'cl', 'people', 'dol', 'company', 'bit')
    ORDER BY table_schema, table_name;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def get_table_columns(conn, schema, table):
    """Get columns for a specific table"""
    query = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = %s AND table_name = %s
    ORDER BY ordinal_position;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (schema, table))
        return cur.fetchall()

def get_foreign_keys(conn):
    """Get all foreign key relationships"""
    query = """
    SELECT
        tc.table_schema,
        tc.table_name,
        kcu.column_name,
        ccu.table_schema AS foreign_table_schema,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema IN ('outreach', 'cl', 'people', 'dol', 'company', 'bit')
    ORDER BY tc.table_schema, tc.table_name;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def get_primary_keys(conn):
    """Get all primary key constraints"""
    query = """
    SELECT
        tc.table_schema,
        tc.table_name,
        kcu.column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
    WHERE tc.constraint_type = 'PRIMARY KEY'
      AND tc.table_schema IN ('outreach', 'cl', 'people', 'dol', 'company', 'bit')
    ORDER BY tc.table_schema, tc.table_name, kcu.ordinal_position;
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query)
        return cur.fetchall()

def main():
    """Main execution"""
    print("Connecting to Neon database...")
    conn = get_neon_connection()

    try:
        # Get all tables
        print("\n=== TABLES ===")
        tables = get_all_tables(conn)
        for table in tables:
            print(f"{table['table_schema']}.{table['table_name']}")

        # Get all views
        print("\n=== VIEWS ===")
        views = get_all_views(conn)
        for view in views:
            print(f"{view['table_schema']}.{view['table_name']}")

        # Get detailed schema for core tables
        print("\n=== TABLE SCHEMAS ===")
        core_tables = [
            ('outreach', 'outreach'),
            ('outreach', 'company_target'),
            ('outreach', 'dol'),
            ('outreach', 'blog'),
            ('outreach', 'bit_scores'),
            ('outreach', 'people'),
            ('cl', 'company_identity'),
            ('cl', 'company_domains'),
            ('people', 'people_master'),
            ('people', 'company_slot'),
            ('dol', 'form_5500'),
            ('dol', 'form_5500_sf'),
            ('dol', 'ein_urls'),
            ('company', 'company_master'),
            ('company', 'company_source_urls'),
        ]

        schema_details = {}
        for schema, table in core_tables:
            full_name = f"{schema}.{table}"
            print(f"\n{full_name}:")
            columns = get_table_columns(conn, schema, table)
            schema_details[full_name] = columns
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"  {col['column_name']:<30} {col['data_type']:<20} {nullable:<10} {default}")

        # Get foreign keys
        print("\n=== FOREIGN KEYS ===")
        fks = get_foreign_keys(conn)
        for fk in fks:
            print(f"{fk['table_schema']}.{fk['table_name']}.{fk['column_name']} -> "
                  f"{fk['foreign_table_schema']}.{fk['foreign_table_name']}.{fk['foreign_column_name']}")

        # Get primary keys
        print("\n=== PRIMARY KEYS ===")
        pks = get_primary_keys(conn)
        pk_dict = {}
        for pk in pks:
            key = f"{pk['table_schema']}.{pk['table_name']}"
            if key not in pk_dict:
                pk_dict[key] = []
            pk_dict[key].append(pk['column_name'])

        for table, columns in pk_dict.items():
            print(f"{table}: {', '.join(columns)}")

        # Save to JSON for further processing
        output = {
            'tables': [dict(t) for t in tables],
            'views': [dict(v) for v in views],
            'schema_details': {k: [dict(c) for c in v] for k, v in schema_details.items()},
            'foreign_keys': [dict(fk) for fk in fks],
            'primary_keys': pk_dict
        }

        with open('neon_schema_snapshot.json', 'w') as f:
            json.dump(output, f, indent=2, default=str)

        print("\n\nSchema snapshot saved to neon_schema_snapshot.json")

    finally:
        conn.close()

if __name__ == '__main__':
    main()
