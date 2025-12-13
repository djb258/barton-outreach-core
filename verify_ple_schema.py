#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLE Schema Verification Script
Connects to Neon PostgreSQL and verifies current schema against PLE specification.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

# PLE Specification
PLE_TABLES = {
    "companies": [
        "id", "company_uid", "name", "linkedin_url", "employee_count",
        "state", "city", "industry", "source", "created_at", "updated_at"
    ],
    "company_slots": [
        "id", "slot_uid", "company_id", "slot_type", "person_id",
        "assigned_at", "vacated_at"
    ],
    "people": [
        "id", "person_uid", "company_id", "linkedin_url", "email",
        "first_name", "last_name", "title", "validation_status",
        "last_verified_at", "last_enrichment_attempt", "created_at", "updated_at"
    ],
    "person_movement_history": [
        "id", "person_id", "linkedin_url", "company_id_from", "company_id_to",
        "title_from", "title_to", "movement_type", "detected_at", "raw_payload"
    ],
    "person_scores": [
        "id", "person_id", "bit_score", "confidence_score", "calculated_at",
        "score_factors"
    ],
    "company_events": [
        "id", "company_id", "event_type", "event_date", "source_url",
        "summary", "detected_at", "impacts_bit"
    ]
}

def get_db_connection():
    """Establish database connection."""
    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")

    if not connection_string:
        raise ValueError("DATABASE_URL or NEON_CONNECTION_STRING not found in .env file")

    return psycopg2.connect(connection_string)

def list_schemas(conn):
    """List all schemas in the database."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast', '_timescaledb_cache', '_timescaledb_catalog', '_timescaledb_config', '_timescaledb_internal', 'timescaledb_information', 'timescaledb_experimental')
            ORDER BY schema_name;
        """)
        return [row['schema_name'] for row in cur.fetchall()]

def list_tables_in_schema(conn, schema_name):
    """List all tables in a specific schema."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """, (schema_name,))
        return [row['table_name'] for row in cur.fetchall()]

def get_table_columns(conn, schema_name, table_name):
    """Get column definitions for a specific table."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """, (schema_name, table_name))
        return cur.fetchall()

def get_table_constraints(conn, schema_name, table_name):
    """Get constraints for a specific table."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name,
                ccu.table_schema AS foreign_table_schema,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            LEFT JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            LEFT JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.table_schema = %s AND tc.table_name = %s
            ORDER BY tc.constraint_type, tc.constraint_name;
        """, (schema_name, table_name))
        return cur.fetchall()

def main():
    """Main execution function."""
    print("=" * 80)
    print("PLE SCHEMA VERIFICATION REPORT")
    print("=" * 80)
    print()

    try:
        # Connect to database
        conn = get_db_connection()
        print("✓ Connected to Neon PostgreSQL database")
        print()

        # List all schemas
        print("-" * 80)
        print("1. ALL SCHEMAS IN DATABASE")
        print("-" * 80)
        schemas = list_schemas(conn)
        for schema in schemas:
            print(f"  • {schema}")
        print()

        # List all tables in each schema
        print("-" * 80)
        print("2. TABLES BY SCHEMA")
        print("-" * 80)
        all_tables = {}
        for schema in schemas:
            tables = list_tables_in_schema(conn, schema)
            all_tables[schema] = tables
            print(f"\n{schema} schema ({len(tables)} tables):")
            for table in tables:
                print(f"  • {table}")
        print()

        # Check for PLE-related tables
        print("-" * 80)
        print("3. PLE TABLE ANALYSIS")
        print("-" * 80)

        ple_matches = {}
        similar_tables = {
            "companies": ["company_master", "companies", "company"],
            "company_slots": ["company_slot", "company_slots", "slots"],
            "people": ["people_master", "people", "person", "persons"],
            "person_movement_history": ["movement_history", "person_movement", "movement"],
            "person_scores": ["scores", "person_scores", "bit_scores"],
            "company_events": ["events", "company_events", "bit_events"]
        }

        for ple_table, search_patterns in similar_tables.items():
            print(f"\nSearching for '{ple_table}' (or similar):")
            found = False

            for schema, tables in all_tables.items():
                for table in tables:
                    if table in search_patterns or ple_table == table:
                        found = True
                        full_name = f"{schema}.{table}"
                        print(f"  ✓ FOUND: {full_name}")

                        # Store match
                        if ple_table not in ple_matches:
                            ple_matches[ple_table] = []
                        ple_matches[ple_table].append(full_name)

                        # Get columns
                        columns = get_table_columns(conn, schema, table)
                        print(f"    Columns ({len(columns)}):")
                        for col in columns:
                            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                            print(f"      - {col['column_name']}: {col['data_type']} {nullable}{default}")

                        # Get constraints
                        constraints = get_table_constraints(conn, schema, table)
                        if constraints:
                            print(f"    Constraints:")
                            for const in constraints:
                                if const['constraint_type'] == 'PRIMARY KEY':
                                    print(f"      - PK: {const['column_name']}")
                                elif const['constraint_type'] == 'FOREIGN KEY':
                                    print(f"      - FK: {const['column_name']} → {const['foreign_table_schema']}.{const['foreign_table_name']}.{const['foreign_column_name']}")
                                elif const['constraint_type'] == 'UNIQUE':
                                    print(f"      - UNIQUE: {const['column_name']}")

            if not found:
                print(f"  ✗ NOT FOUND")

        print()

        # Summary
        print("-" * 80)
        print("4. PLE SPECIFICATION COMPARISON")
        print("-" * 80)
        print()

        for ple_table, expected_columns in PLE_TABLES.items():
            print(f"\n{ple_table}:")
            print(f"  Expected columns: {', '.join(expected_columns)}")

            if ple_table in ple_matches:
                for full_table_name in ple_matches[ple_table]:
                    schema, table = full_table_name.split('.')
                    actual_columns = [col['column_name'] for col in get_table_columns(conn, schema, table)]

                    print(f"  Actual columns in {full_table_name}: {', '.join(actual_columns)}")

                    missing = set(expected_columns) - set(actual_columns)
                    extra = set(actual_columns) - set(expected_columns)

                    if missing:
                        print(f"    ⚠ Missing columns: {', '.join(missing)}")
                    if extra:
                        print(f"    ℹ Extra columns: {', '.join(extra)}")
                    if not missing and not extra:
                        print(f"    ✓ Perfect match!")
            else:
                print(f"  ✗ Table does not exist in database")

        print()
        print("-" * 80)
        print("5. SUMMARY")
        print("-" * 80)
        print(f"Total schemas: {len(schemas)}")
        print(f"Total tables across all schemas: {sum(len(tables) for tables in all_tables.values())}")
        print(f"PLE tables found: {len(ple_matches)}/{len(PLE_TABLES)}")
        print()

        if len(ple_matches) == len(PLE_TABLES):
            print("✓ All PLE tables exist in the database!")
        else:
            missing_ple = set(PLE_TABLES.keys()) - set(ple_matches.keys())
            print(f"⚠ Missing PLE tables: {', '.join(missing_ple)}")

        print()
        print("=" * 80)

        conn.close()

    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
