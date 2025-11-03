#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive query of ALL Neon database schemas and tables.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def get_all_schemas():
    """Get ALL schemas and tables in the Neon database."""
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get ALL schemas (excluding system schemas)
        print("\n" + "="*100)
        print("COMPLETE NEON DATABASE SCHEMA OVERVIEW")
        print("="*100 + "\n")
        
        cur.execute("""
            SELECT 
                schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
            ORDER BY schema_name;
        """)
        
        schemas = cur.fetchall()
        
        print(f"Found {len(schemas)} user schemas:\n")
        
        for schema in schemas:
            schema_name = schema['schema_name']
            
            # Get all tables in this schema
            cur.execute("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                FROM pg_tables
                WHERE schemaname = %s
                ORDER BY tablename;
            """, (schema_name,))
            
            tables = cur.fetchall()
            
            # Get all views in this schema
            cur.execute("""
                SELECT viewname
                FROM pg_views
                WHERE schemaname = %s
                ORDER BY viewname;
            """, (schema_name,))
            
            views = cur.fetchall()
            
            table_count = len(tables)
            view_count = len(views)
            
            print(f"\n{'='*100}")
            print(f"SCHEMA: {schema_name}")
            print(f"{'='*100}")
            print(f"Tables: {table_count} | Views: {view_count}")
            print("-"*100)
            
            # Show all tables
            if tables:
                print(f"\nTABLES ({table_count}):")
                for table in tables:
                    table_name = table['tablename']
                    size = table['size']
                    
                    # Get row count
                    try:
                        cur.execute(f"SELECT COUNT(*) as count FROM {schema_name}.{table_name}")
                        row_count = cur.fetchone()['count']
                    except:
                        row_count = '?'
                    
                    print(f"  [{schema_name}.{table_name}]")
                    print(f"    Rows: {row_count:,} | Size: {size}")
                    
                    # Get column count
                    cur.execute("""
                        SELECT COUNT(*) as col_count
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s;
                    """, (schema_name, table_name))
                    
                    col_count = cur.fetchone()['col_count']
                    print(f"    Columns: {col_count}")
            
            # Show all views
            if views:
                print(f"\nVIEWS ({view_count}):")
                for view in views:
                    print(f"  [VIEW] {schema_name}.{view['viewname']}")
        
        # Summary
        print("\n" + "="*100)
        print("SUMMARY")
        print("="*100)
        
        cur.execute("""
            SELECT 
                schemaname,
                COUNT(*) as table_count,
                pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))) as total_size
            FROM pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            GROUP BY schemaname
            ORDER BY schemaname;
        """)
        
        summary = cur.fetchall()
        
        total_tables = 0
        for row in summary:
            print(f"  {row['schemaname']}: {row['table_count']} tables, {row['total_size']}")
            total_tables += row['table_count']
        
        print(f"\nTOTAL: {total_tables} tables across {len(schemas)} schemas")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_all_schemas()

