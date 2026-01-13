#!/usr/bin/env python3
"""
Execute People Slot Structure Migration
=======================================
Runs 2026-01-08-people-slot-structure.sql against Neon
Creates: slot_ingress_control, people_candidate, views, guard function
"""

import os
import sys

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("ERROR: psycopg2 not installed")
    sys.exit(1)


def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)
    
    conn = psycopg2.connect(database_url)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("=" * 70)
    print("  APPLYING PEOPLE SLOT STRUCTURE MIGRATION")
    print("=" * 70)
    
    try:
        # Read the migration file
        migration_path = r"c:\Users\CUSTOMER PC\Cursor Repo\barton-outreach-cc\src\data\migrations\2026-01-08-people-slot-structure.sql"
        with open(migration_path, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        print(f"\n  Reading migration from: {migration_path}")
        print(f"  Migration size: {len(migration_sql):,} bytes")
        
        # Execute the migration
        print("\n  Executing migration...")
        cur.execute(migration_sql)
        
        # Fetch and display all NOTICE messages
        print("\n  Migration output:")
        
        # Verify key objects exist
        print("\n  Verifying created objects...")
        
        # Check slot_ingress_control
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'people' AND table_name = 'slot_ingress_control'
            ) as exists
        """)
        if cur.fetchone()['exists']:
            print("  ✓ people.slot_ingress_control: EXISTS")
        else:
            print("  ❌ people.slot_ingress_control: MISSING")
        
        # Check people_candidate
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'people' AND table_name = 'people_candidate'
            ) as exists
        """)
        if cur.fetchone()['exists']:
            print("  ✓ people.people_candidate: EXISTS")
        else:
            print("  ❌ people.people_candidate: MISSING")
        
        # Check views
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.views 
                WHERE table_schema = 'people' AND table_name = 'v_open_slots'
            ) as exists
        """)
        if cur.fetchone()['exists']:
            print("  ✓ people.v_open_slots: EXISTS")
        else:
            print("  ❌ people.v_open_slots: MISSING")
        
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.views 
                WHERE table_schema = 'people' AND table_name = 'v_slot_fill_rate'
            ) as exists
        """)
        if cur.fetchone()['exists']:
            print("  ✓ people.v_slot_fill_rate: EXISTS")
        else:
            print("  ❌ people.v_slot_fill_rate: MISSING")
        
        # Check guard function
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'people' AND p.proname = 'slot_can_accept_candidate'
            ) as exists
        """)
        if cur.fetchone()['exists']:
            print("  ✓ people.slot_can_accept_candidate(): EXISTS")
        else:
            print("  ❌ people.slot_can_accept_candidate(): MISSING")
        
        # Check UNIQUE constraint
        cur.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_constraint 
                WHERE conname = 'uq_company_slot_outreach_slot_type'
            ) as exists
        """)
        if cur.fetchone()['exists']:
            print("  ✓ UNIQUE(outreach_id, slot_type): EXISTS")
        else:
            print("  ❌ UNIQUE(outreach_id, slot_type): MISSING")
        
        # Check kill switch status
        cur.execute("""
            SELECT is_enabled 
            FROM people.slot_ingress_control 
            WHERE switch_name = 'slot_ingress'
        """)
        result = cur.fetchone()
        if result:
            status = "ON" if result['is_enabled'] else "OFF"
            print(f"\n  ✓ Kill switch status: {status}")
        
        conn.commit()
        print("\n" + "=" * 70)
        print("  ✅ MIGRATION COMMITTED SUCCESSFULLY")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n  ❌ ERROR: {e}")
        conn.rollback()
        print("  Transaction ROLLED BACK")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
