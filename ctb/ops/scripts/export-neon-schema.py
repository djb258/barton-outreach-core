#!/usr/bin/env python3
"""
Export complete Neon database schema to JSON
Generates comprehensive schema map with all tables, columns, indexes, and constraints
"""

import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def get_database_connection():
    """Connect to Neon PostgreSQL database"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("[OK] Connected to Neon database")
        return conn
    except Exception as e:
        print(f"[ERROR] Failed to connect: {e}")
        raise

def get_all_schemas(cursor):
    """Get all schemas in the database"""
    cursor.execute("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
        ORDER BY schema_name;
    """)
    return [row[0] for row in cursor.fetchall()]

def get_tables_in_schema(cursor, schema_name):
    """Get all tables in a schema"""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """, (schema_name,))
    return [row[0] for row in cursor.fetchall()]

def get_columns_for_table(cursor, schema_name, table_name):
    """Get all columns for a table with their properties"""
    cursor.execute("""
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

    columns = []
    for row in cursor.fetchall():
        column = {
            'name': row[0],
            'type': row[1],
            'nullable': row[3] == 'YES',
        }
        if row[2]:  # max_length
            column['max_length'] = row[2]
        if row[4]:  # default
            column['default'] = row[4]
        columns.append(column)

    return columns

def get_indexes_for_table(cursor, schema_name, table_name):
    """Get all indexes for a table"""
    cursor.execute("""
        SELECT
            i.relname as index_name,
            a.attname as column_name,
            ix.indisunique as is_unique,
            ix.indisprimary as is_primary
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = %s AND t.relname = %s
        ORDER BY i.relname, a.attnum;
    """, (schema_name, table_name))

    indexes = {}
    for row in cursor.fetchall():
        index_name = row[0]
        if index_name not in indexes:
            indexes[index_name] = {
                'columns': [],
                'unique': row[2],
                'primary': row[3]
            }
        indexes[index_name]['columns'].append(row[1])

    return [{'name': k, **v} for k, v in indexes.items()]

def get_foreign_keys_for_table(cursor, schema_name, table_name):
    """Get all foreign keys for a table"""
    cursor.execute("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_schema AS foreign_schema,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = %s
        AND tc.table_name = %s
        ORDER BY tc.constraint_name;
    """, (schema_name, table_name))

    foreign_keys = []
    for row in cursor.fetchall():
        foreign_keys.append({
            'constraint_name': row[0],
            'column': row[1],
            'references': {
                'schema': row[2],
                'table': row[3],
                'column': row[4]
            }
        })

    return foreign_keys

def get_row_count(cursor, schema_name, table_name):
    """Get approximate row count for a table"""
    try:
        cursor.execute(f"""
            SELECT COUNT(*) FROM "{schema_name}"."{table_name}";
        """)
        return cursor.fetchone()[0]
    except:
        return None

def export_schema():
    """Export complete database schema to JSON"""
    conn = get_database_connection()
    cursor = conn.cursor()

    print("\n[INFO] Scanning database schemas...")

    schema_map = {
        'database': 'Marketing DB',
        'exported_at': datetime.now().isoformat(),
        'host': 'ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech',
        'schemas': {}
    }

    # Get all schemas
    schemas = get_all_schemas(cursor)
    print(f"[INFO] Found {len(schemas)} schemas: {', '.join(schemas)}\n")

    for schema_name in schemas:
        print(f"[SCHEMA] Processing: {schema_name}")
        tables = get_tables_in_schema(cursor, schema_name)

        schema_map['schemas'][schema_name] = {
            'tables': {},
            'table_count': len(tables)
        }

        for table_name in tables:
            print(f"  - {table_name}")

            # Get all table details
            columns = get_columns_for_table(cursor, schema_name, table_name)
            indexes = get_indexes_for_table(cursor, schema_name, table_name)
            foreign_keys = get_foreign_keys_for_table(cursor, schema_name, table_name)
            row_count = get_row_count(cursor, schema_name, table_name)

            schema_map['schemas'][schema_name]['tables'][table_name] = {
                'columns': columns,
                'indexes': indexes,
                'foreign_keys': foreign_keys,
                'row_count': row_count,
                'column_count': len(columns)
            }

    cursor.close()
    conn.close()

    print("\n[OK] Schema export complete!")
    return schema_map

def save_schema_map(schema_map):
    """Save schema map to multiple locations"""

    # Primary location
    primary_path = 'ctb/docs/schema_map.json'
    with open(primary_path, 'w') as f:
        json.dump(schema_map, f, indent=2)
    print(f"[SAVE] Saved to: {primary_path}")

    # Secondary location (.gitingest)
    secondary_path = '.gitingest/schema_map.json'
    with open(secondary_path, 'w') as f:
        json.dump(schema_map, f, indent=2)
    print(f"[SAVE] Saved to: {secondary_path}")

    # Generate summary
    print("\n[SUMMARY] Schema Summary:")
    total_tables = sum(s['table_count'] for s in schema_map['schemas'].values())
    print(f"   Total Schemas: {len(schema_map['schemas'])}")
    print(f"   Total Tables: {total_tables}")

    for schema_name, schema_data in schema_map['schemas'].items():
        print(f"\n   {schema_name}:")
        for table_name, table_data in schema_data['tables'].items():
            row_count = table_data['row_count']
            col_count = table_data['column_count']
            idx_count = len(table_data['indexes'])
            fk_count = len(table_data['foreign_keys'])

            print(f"     • {table_name}: {col_count} cols, {idx_count} indexes, {fk_count} FKs, ~{row_count} rows")

if __name__ == '__main__':
    print("=" * 60)
    print("  NEON SCHEMA EXPORT")
    print("=" * 60)
    print()

    try:
        schema_map = export_schema()
        save_schema_map(schema_map)

        print("\n" + "=" * 60)
        print("  Schema export successful!")
        print("=" * 60)
        print()

    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
