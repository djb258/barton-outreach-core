#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clear all data from active tables and prepare for fresh data import.
Preserves schema structure and foreign key relationships.

CTB Classification Metadata:
CTB Branch: sys/tools
Barton ID: 08.02.02
Unique ID: CTB-DBRESET
Enforcement: ORBT
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

def clear_database():
    """Clear all data from active tables, preserving schema structure."""
    database_url = os.getenv('NEON_DATABASE_URL')
    
    if not database_url:
        print("[ERROR] NEON_DATABASE_URL not set")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False  # Use transactions
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print("\n" + "="*100)
        print("DATABASE RESET - CLEAR ALL DATA")
        print("="*100 + "\n")
        
        # First, show what we're about to clear
        print("CURRENT DATA COUNTS:")
        print("-"*100)
        
        tables_to_clear = [
            ('intake', 'company_raw_intake'),
            ('marketing', 'pipeline_events'),
            ('marketing', 'pipeline_errors'),
            ('marketing', 'email_verification'),
            ('marketing', 'contact_enrichment'),
            ('marketing', 'people_master'),
            ('marketing', 'company_slots'),
            ('marketing', 'company_master'),
            ('public', 'shq_validation_log'),
        ]
        
        total_rows_before = 0
        for schema, table in tables_to_clear:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
                count = cur.fetchone()['count']
                print(f"  {schema}.{table}: {count:,} rows")
                total_rows_before += count
            except Exception as e:
                print(f"  {schema}.{table}: [ERROR] {e}")
        
        print(f"\nTOTAL ROWS TO DELETE: {total_rows_before:,}")
        print("-"*100)
        
        # Confirm before proceeding
        print("\n[WARNING] This will permanently delete all data from active tables!")
        print("[INFO] Archive tables will NOT be touched (historical data preserved)")
        print("\nType 'YES' to proceed or anything else to cancel: ", end='')
        
        # For automation, check if running in non-interactive mode
        if os.getenv('AUTO_CONFIRM') == 'YES':
            confirmation = 'YES'
            print("YES (auto-confirmed)")
        else:
            confirmation = input().strip()
        
        if confirmation != 'YES':
            print("\n[CANCELLED] No data was deleted.")
            cur.close()
            conn.close()
            return
        
        print("\n" + "="*100)
        print("CLEARING DATA...")
        print("="*100 + "\n")
        
        # Clear tables in order (respecting foreign key constraints)
        # Start with dependent tables first
        
        clearing_order = [
            ('marketing', 'email_verification', 'Email verification records'),
            ('marketing', 'contact_enrichment', 'Contact enrichment data'),
            ('marketing', 'people_master', 'People/contacts'),
            ('marketing', 'pipeline_errors', 'Pipeline errors'),
            ('marketing', 'pipeline_events', 'Pipeline events'),
            ('marketing', 'company_slots', 'Company role slots'),
            ('marketing', 'company_master', 'Company master records'),
            ('intake', 'company_raw_intake', 'Raw intake data'),
            ('public', 'shq_validation_log', 'Validation logs'),
        ]
        
        cleared_count = 0
        for schema, table, description in clearing_order:
            try:
                print(f"Clearing {schema}.{table} ({description})... ", end='')
                
                # Get count before
                cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
                before_count = cur.fetchone()['count']
                
                # TRUNCATE is faster than DELETE and resets sequences
                # CASCADE will handle any remaining FK constraints
                cur.execute(f"TRUNCATE TABLE {schema}.{table} RESTART IDENTITY CASCADE")
                
                print(f"[OK] Deleted {before_count:,} rows")
                cleared_count += 1
                
            except Exception as e:
                print(f"[ERROR] {e}")
                conn.rollback()
                print("\n[ROLLBACK] Transaction rolled back due to error.")
                cur.close()
                conn.close()
                return
        
        # Commit the transaction
        conn.commit()
        
        print("\n" + "="*100)
        print("VERIFICATION - DATA AFTER CLEARING")
        print("="*100 + "\n")
        
        total_rows_after = 0
        for schema, table in tables_to_clear:
            try:
                cur.execute(f"SELECT COUNT(*) as count FROM {schema}.{table}")
                count = cur.fetchone()['count']
                status = "[OK]" if count == 0 else "[WARNING]"
                print(f"  {status} {schema}.{table}: {count:,} rows")
                total_rows_after += count
            except Exception as e:
                print(f"  [ERROR] {schema}.{table}: {e}")
        
        print(f"\nTOTAL ROWS REMAINING: {total_rows_after:,}")
        
        print("\n" + "="*100)
        print("SUMMARY")
        print("="*100)
        print(f"  Tables cleared: {cleared_count}")
        print(f"  Rows deleted: {total_rows_before:,}")
        print(f"  Rows remaining: {total_rows_after:,}")
        print(f"  Status: {'SUCCESS' if total_rows_after == 0 else 'PARTIAL'}")
        print("\n[READY] Database is now ready for fresh data import!")
        print("="*100 + "\n")
        
        # Show schema integrity
        print("SCHEMA INTEGRITY CHECK:")
        print("-"*100)
        cur.execute("""
            SELECT 
                schemaname,
                COUNT(*) as table_count
            FROM pg_tables
            WHERE schemaname IN ('intake', 'marketing', 'company', 'people', 'public', 'BIT', 'PLE')
            GROUP BY schemaname
            ORDER BY schemaname;
        """)
        
        schemas = cur.fetchall()
        for schema in schemas:
            print(f"  [OK] {schema['schemaname']}: {schema['table_count']} tables (structure intact)")
        
        print("\n[OK] All schemas and table structures preserved")
        print("="*100 + "\n")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_database()

