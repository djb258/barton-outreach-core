#!/usr/bin/env python3
"""
Neon Database Schema Inventory
Comprehensive inventory of all schemas, tables, columns, and data coverage.
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from collections import defaultdict
import json
from datetime import datetime

def connect_db():
    """Connect to Neon PostgreSQL."""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def get_all_schemas(cur):
    """Get all user-created schemas (exclude system schemas)."""
    cur.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name
    """)
    return [row['schema_name'] for row in cur.fetchall()]

def get_tables_in_schema(cur, schema):
    """Get all tables in a schema with row counts."""
    cur.execute("""
        SELECT 
            t.table_name,
            t.table_type,
            COALESCE(s.n_live_tup, 0) as row_count
        FROM information_schema.tables t
        LEFT JOIN pg_stat_user_tables s 
            ON t.table_schema = s.schemaname AND t.table_name = s.relname
        WHERE t.table_schema = %s
        ORDER BY t.table_name
    """, (schema,))
    return cur.fetchall()

def get_columns_for_table(cur, schema, table):
    """Get column details for a table."""
    cur.execute("""
        SELECT 
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length,
            c.numeric_precision,
            CASE 
                WHEN pk.column_name IS NOT NULL THEN true 
                ELSE false 
            END as is_primary_key
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.column_name, ku.table_schema, ku.table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku
                ON tc.constraint_name = ku.constraint_name
                AND tc.table_schema = ku.table_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
        ) pk ON c.table_schema = pk.table_schema 
            AND c.table_name = pk.table_name 
            AND c.column_name = pk.column_name
        WHERE c.table_schema = %s AND c.table_name = %s
        ORDER BY c.ordinal_position
    """, (schema, table))
    return cur.fetchall()

def get_foreign_keys(cur, schema, table):
    """Get foreign key relationships for a table."""
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_schema AS foreign_schema,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = %s
            AND tc.table_name = %s
    """, (schema, table))
    return cur.fetchall()

def get_column_coverage(cur, schema, table, columns):
    """Get data coverage for each column (populated vs NULL)."""
    coverage = {}
    
    # Get total row count first
    try:
        cur.execute(f'SELECT COUNT(*) as total FROM "{schema}"."{table}"')
        total = cur.fetchone()['total']
    except Exception as e:
        print(f"  Error getting row count for {schema}.{table}: {e}")
        return coverage
    
    if total == 0:
        return coverage
    
    # Check coverage for each column
    for col in columns:
        col_name = col['column_name']
        try:
            cur.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    COUNT("{col_name}") as populated
                FROM "{schema}"."{table}"
            ''')
            result = cur.fetchone()
            coverage[col_name] = {
                'total': result['total'],
                'populated': result['populated'],
                'nulls': result['total'] - result['populated'],
                'coverage_pct': round(100 * result['populated'] / result['total'], 1) if result['total'] > 0 else 0
            }
        except Exception as e:
            coverage[col_name] = {'error': str(e)}
    
    return coverage

def get_exact_row_count(cur, schema, table):
    """Get exact row count for a table."""
    try:
        cur.execute(f'SELECT COUNT(*) as cnt FROM "{schema}"."{table}"')
        return cur.fetchone()['cnt']
    except Exception as e:
        return f"Error: {e}"

def is_key_column(col_name):
    """Check if column is likely a key/important column."""
    key_patterns = [
        'id', 'uuid', 'ein', 'domain', 'url', 'email', 'linkedin',
        'name', 'company', 'title', 'state', 'tier', 'status',
        'created', 'updated', 'enriched', 'score', 'slot'
    ]
    col_lower = col_name.lower()
    return any(pattern in col_lower for pattern in key_patterns)

def main():
    print("=" * 80)
    print("NEON DATABASE SCHEMA INVENTORY")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)
    
    conn = connect_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all schemas
    schemas = get_all_schemas(cur)
    print(f"\n📊 Found {len(schemas)} schemas: {', '.join(schemas)}\n")
    
    inventory = {}
    
    for schema in schemas:
        print(f"\n{'='*80}")
        print(f"📁 SCHEMA: {schema}")
        print("=" * 80)
        
        tables = get_tables_in_schema(cur, schema)
        if not tables:
            print("  (no tables)")
            continue
        
        inventory[schema] = {'tables': {}}
        
        for table_info in tables:
            table = table_info['table_name']
            table_type = table_info['table_type']
            
            # Get exact row count
            row_count = get_exact_row_count(cur, schema, table)
            
            print(f"\n  📋 TABLE: {schema}.{table}")
            print(f"     Type: {table_type} | Rows: {row_count:,}" if isinstance(row_count, int) else f"     Type: {table_type} | Rows: {row_count}")
            print("     " + "-" * 60)
            
            # Get columns
            columns = get_columns_for_table(cur, schema, table)
            
            # Get foreign keys
            fks = get_foreign_keys(cur, schema, table)
            fk_map = {fk['column_name']: fk for fk in fks}
            
            # Get coverage for key columns only (to save time)
            key_columns = [c for c in columns if is_key_column(c['column_name'])]
            coverage = {}
            if isinstance(row_count, int) and row_count > 0 and row_count < 1000000:
                coverage = get_column_coverage(cur, schema, table, key_columns)
            
            table_data = {
                'row_count': row_count if isinstance(row_count, int) else 0,
                'columns': [],
                'foreign_keys': []
            }
            
            print(f"\n     Columns ({len(columns)}):")
            for col in columns:
                col_name = col['column_name']
                data_type = col['data_type']
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                pk = "🔑 PK" if col['is_primary_key'] else ""
                fk = f"→ {fk_map[col_name]['foreign_schema']}.{fk_map[col_name]['foreign_table']}.{fk_map[col_name]['foreign_column']}" if col_name in fk_map else ""
                
                # Coverage info
                cov_str = ""
                if col_name in coverage and 'coverage_pct' in coverage[col_name]:
                    cov = coverage[col_name]
                    cov_str = f" [{cov['coverage_pct']}% populated, {cov['populated']:,}/{cov['total']:,}]"
                
                # Mark key columns
                key_marker = "⭐" if is_key_column(col_name) else "  "
                
                print(f"       {key_marker} {col_name}: {data_type} {nullable} {pk} {fk}{cov_str}")
                
                table_data['columns'].append({
                    'name': col_name,
                    'type': data_type,
                    'nullable': col['is_nullable'] == 'YES',
                    'is_pk': col['is_primary_key'],
                    'is_key_column': is_key_column(col_name),
                    'coverage': coverage.get(col_name, {})
                })
            
            for fk in fks:
                table_data['foreign_keys'].append({
                    'column': fk['column_name'],
                    'references': f"{fk['foreign_schema']}.{fk['foreign_table']}.{fk['foreign_column']}"
                })
            
            inventory[schema]['tables'][table] = table_data
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("📈 SUMMARY STATISTICS")
    print("=" * 80)
    
    total_tables = 0
    total_rows = 0
    
    for schema, data in inventory.items():
        schema_tables = len(data['tables'])
        schema_rows = sum(t['row_count'] for t in data['tables'].values() if isinstance(t['row_count'], int))
        total_tables += schema_tables
        total_rows += schema_rows
        print(f"  {schema}: {schema_tables} tables, {schema_rows:,} total rows")
    
    print(f"\n  TOTAL: {total_tables} tables, {total_rows:,} rows across {len(inventory)} schemas")
    
    # Output JSON for further processing
    print("\n" + "=" * 80)
    print("💾 Writing inventory to neon_inventory.json...")
    with open('neon_inventory.json', 'w') as f:
        json.dump(inventory, f, indent=2, default=str)
    print("Done!")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
