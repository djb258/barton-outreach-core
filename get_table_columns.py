#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get detailed column information for a specific table.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def get_table_columns(schema_name, table_name):
    """Get all columns for a specific table."""
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n" + "="*100)
        print(f"COLUMN DETAILS: {schema_name}.{table_name}")
        print("="*100 + "\n")
        
        # Get detailed column information
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                numeric_scale,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = %s 
              AND table_name = %s
            ORDER BY ordinal_position;
        """, (schema_name, table_name))
        
        columns = cur.fetchall()
        
        if not columns:
            print(f"[ERROR] Table {schema_name}.{table_name} not found or has no columns")
            return
        
        print(f"Total Columns: {len(columns)}\n")
        print("-"*100)
        
        for col in columns:
            col_name = col['column_name']
            data_type = col['data_type']
            
            # Build type string with length/precision
            if col['character_maximum_length']:
                data_type += f"({col['character_maximum_length']})"
            elif col['numeric_precision']:
                if col['numeric_scale']:
                    data_type += f"({col['numeric_precision']},{col['numeric_scale']})"
                else:
                    data_type += f"({col['numeric_precision']})"
            
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f"DEFAULT {col['column_default']}" if col['column_default'] else ""
            
            print(f"{col['ordinal_position']:2d}. {col_name}")
            print(f"    Type: {data_type}")
            print(f"    Nullable: {nullable}")
            if default:
                print(f"    Default: {default}")
            print()
        
        print("-"*100)
        
        # Get any constraints
        cur.execute("""
            SELECT
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = %s
              AND tc.table_name = %s
            ORDER BY tc.constraint_type, kcu.ordinal_position;
        """, (schema_name, table_name))
        
        constraints = cur.fetchall()
        
        if constraints:
            print("\nCONSTRAINTS:")
            print("-"*100)
            for constraint in constraints:
                print(f"  {constraint['constraint_type']}: {constraint['constraint_name']}")
                print(f"    Column: {constraint['column_name']}")
        
        # Get indexes
        cur.execute("""
            SELECT
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = %s
              AND tablename = %s
            ORDER BY indexname;
        """, (schema_name, table_name))
        
        indexes = cur.fetchall()
        
        if indexes:
            print("\n\nINDEXES:")
            print("-"*100)
            for idx in indexes:
                print(f"  {idx['indexname']}")
                print(f"    {idx['indexdef']}")
                print()
        
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Get table from command line or use default
    if len(sys.argv) >= 3:
        schema = sys.argv[1]
        table = sys.argv[2]
    else:
        schema = "intake"
        table = "company_raw_intake"
    
    get_table_columns(schema, table)

