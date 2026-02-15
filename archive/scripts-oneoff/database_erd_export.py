#!/usr/bin/env python3
"""
Database ERD Export Script
Executes comprehensive schema introspection queries for ERD generation.
Outputs results in JSON format for diagram creation.
"""

import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path


def connect_db():
    """Connect to Neon PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=os.environ['NEON_HOST'],
            database=os.environ['NEON_DATABASE'],
            user=os.environ['NEON_USER'],
            password=os.environ['NEON_PASSWORD'],
            sslmode='require'
        )
        return conn
    except KeyError as e:
        print(f"ERROR: Missing environment variable: {e}")
        print("Required: NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        sys.exit(1)


def execute_query(cur, query_name, sql):
    """Execute a query and return results."""
    print(f"\n[{query_name}] Executing...")
    try:
        cur.execute(sql)
        results = cur.fetchall()
        print(f"[{query_name}] Retrieved {len(results)} rows")
        return results
    except Exception as e:
        print(f"[{query_name}] ERROR: {e}")
        return []


def main():
    print("=" * 80)
    print("DATABASE ERD EXPORT")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)

    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    export_data = {
        'generated_at': datetime.now().isoformat(),
        'database': os.environ.get('NEON_DATABASE'),
        'host': os.environ.get('NEON_HOST'),
    }

    # =========================================================================
    # QUERY 1: List all schemas
    # =========================================================================
    query1_sql = """
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        ORDER BY schema_name;
    """
    schemas = execute_query(cur, "QUERY 1: Schemas", query1_sql)
    export_data['schemas'] = [dict(row) for row in schemas]

    # =========================================================================
    # QUERY 2: List all tables with their schemas
    # =========================================================================
    query2_sql = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name;
    """
    tables = execute_query(cur, "QUERY 2: Tables", query2_sql)
    export_data['tables'] = [dict(row) for row in tables]

    # =========================================================================
    # QUERY 3: Get all foreign key relationships
    # =========================================================================
    query3_sql = """
        SELECT
            tc.table_schema AS source_schema,
            tc.table_name AS source_table,
            kcu.column_name AS source_column,
            ccu.table_schema AS target_schema,
            ccu.table_name AS target_table,
            ccu.column_name AS target_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        ORDER BY tc.table_schema, tc.table_name;
    """
    foreign_keys = execute_query(cur, "QUERY 3: Foreign Keys", query3_sql)
    export_data['foreign_keys'] = [dict(row) for row in foreign_keys]

    # =========================================================================
    # QUERY 4: Get primary keys for all tables
    # =========================================================================
    query4_sql = """
        SELECT
            tc.table_schema,
            tc.table_name,
            kcu.column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
        ORDER BY tc.table_schema, tc.table_name;
    """
    primary_keys = execute_query(cur, "QUERY 4: Primary Keys", query4_sql)
    export_data['primary_keys'] = [dict(row) for row in primary_keys]

    # =========================================================================
    # QUERY 5: Get columns for key tables
    # =========================================================================
    query5_sql = """
        SELECT
            table_schema,
            table_name,
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            ordinal_position
        FROM information_schema.columns
        WHERE (table_schema = 'cl' AND table_name = 'company_identity')
           OR (table_schema = 'outreach' AND table_name IN ('outreach', 'company_target', 'dol', 'people', 'blog', 'bit_scores', 'bit_signals', 'manual_overrides', 'override_audit_log'))
           OR (table_schema = 'people' AND table_name IN ('company_slot', 'people_master'))
           OR (table_schema = 'dol' AND table_name IN ('form_5500', 'schedule_a', 'ein_registry'))
        ORDER BY table_schema, table_name, ordinal_position;
    """
    columns = execute_query(cur, "QUERY 5: Key Table Columns", query5_sql)
    export_data['key_table_columns'] = [dict(row) for row in columns]

    # =========================================================================
    # ADDITIONAL: Get all views
    # =========================================================================
    views_sql = """
        SELECT
            table_schema,
            table_name AS view_name
        FROM information_schema.views
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """
    views = execute_query(cur, "ADDITIONAL: Views", views_sql)
    export_data['views'] = [dict(row) for row in views]

    # =========================================================================
    # ADDITIONAL: Get indexes
    # =========================================================================
    indexes_sql = """
        SELECT
            schemaname AS schema_name,
            tablename AS table_name,
            indexname AS index_name,
            indexdef AS index_definition
        FROM pg_indexes
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename, indexname;
    """
    indexes = execute_query(cur, "ADDITIONAL: Indexes", indexes_sql)
    export_data['indexes'] = [dict(row) for row in indexes]

    # =========================================================================
    # ADDITIONAL: Get table row counts (for key tables only)
    # =========================================================================
    print("\n[ROW COUNTS] Getting row counts for key tables...")
    row_counts = {}
    key_tables = [
        ('cl', 'company_identity'),
        ('outreach', 'outreach'),
        ('outreach', 'company_target'),
        ('outreach', 'dol'),
        ('outreach', 'people'),
        ('outreach', 'blog'),
        ('outreach', 'bit_scores'),
        ('outreach', 'bit_signals'),
        ('outreach', 'manual_overrides'),
        ('outreach', 'override_audit_log'),
        ('people', 'company_slot'),
        ('people', 'people_master'),
        ('dol', 'form_5500'),
        ('dol', 'schedule_a'),
        ('dol', 'ein_registry'),
    ]

    for schema, table in key_tables:
        try:
            cur.execute(f'SELECT COUNT(*) as count FROM "{schema}"."{table}"')
            count = cur.fetchone()['count']
            row_counts[f"{schema}.{table}"] = count
            print(f"  {schema}.{table}: {count:,} rows")
        except Exception as e:
            print(f"  {schema}.{table}: ERROR - {e}")
            row_counts[f"{schema}.{table}"] = None

    export_data['row_counts'] = row_counts

    # =========================================================================
    # ADDITIONAL: Get unique constraints
    # =========================================================================
    unique_sql = """
        SELECT
            tc.table_schema,
            tc.table_name,
            tc.constraint_name,
            STRING_AGG(kcu.column_name, ', ' ORDER BY kcu.ordinal_position) as columns
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'UNIQUE'
            AND tc.table_schema NOT IN ('pg_catalog', 'information_schema')
        GROUP BY tc.table_schema, tc.table_name, tc.constraint_name
        ORDER BY tc.table_schema, tc.table_name;
    """
    unique_constraints = execute_query(cur, "ADDITIONAL: Unique Constraints", unique_sql)
    export_data['unique_constraints'] = [dict(row) for row in unique_constraints]

    # =========================================================================
    # Close connection
    # =========================================================================
    cur.close()
    conn.close()

    # =========================================================================
    # Write to JSON file
    # =========================================================================
    output_file = Path(__file__).parent.parent / 'docs' / 'database_erd_export.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("WRITING RESULTS")
    print("=" * 80)
    print(f"Output file: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"\nSUCCESS: Exported {len(export_data)} data sections to {output_file}")

    # =========================================================================
    # Print summary statistics
    # =========================================================================
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(f"Schemas: {len(export_data['schemas'])}")
    print(f"Tables: {len(export_data['tables'])}")
    print(f"Views: {len(export_data['views'])}")
    print(f"Foreign Keys: {len(export_data['foreign_keys'])}")
    print(f"Primary Keys: {len(export_data['primary_keys'])}")
    print(f"Unique Constraints: {len(export_data['unique_constraints'])}")
    print(f"Key Table Columns: {len(export_data['key_table_columns'])}")
    print(f"Indexes: {len(export_data['indexes'])}")
    print(f"Row Counts: {len(export_data['row_counts'])}")

    # Print schemas found
    print("\nSchemas found:")
    for schema in export_data['schemas']:
        print(f"  - {schema['schema_name']}")

    # Print key tables with row counts
    print("\nKey tables:")
    for table_key, count in sorted(row_counts.items()):
        if count is not None:
            print(f"  {table_key}: {count:,} rows")
        else:
            print(f"  {table_key}: (error)")

    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)


if __name__ == '__main__':
    main()
