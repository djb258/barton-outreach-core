"""
Execute RLS Migration on Neon PostgreSQL
Date: 2026-01-13
"""

import psycopg2
import sys
from pathlib import Path

# Connection string
CONNECTION_STRING = (
    "postgresql://Marketing%20DB_owner:npg_OsE4Z2oPCpiT@"
    "ep-ancient-waterfall-a42vy0du-pooler.us-east-1.aws.neon.tech/"
    "Marketing%20DB?sslmode=require"
)

# Migration file path
MIGRATION_FILE = Path(r"c:\Users\CUSTOM PC\Desktop\Cursor Builds\barton-outreach-core\infra\migrations\2026-01-13-enable-rls-production-tables.sql")

def execute_migration():
    """Execute the RLS migration SQL file"""
    print("=" * 80)
    print("EXECUTING RLS MIGRATION ON NEON POSTGRESQL")
    print("=" * 80)
    print(f"Migration file: {MIGRATION_FILE}")
    print()

    # Read the SQL file
    try:
        with open(MIGRATION_FILE, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        print(f"[OK] Read migration file ({len(sql_content)} characters)")
    except Exception as e:
        print(f"[ERROR] reading migration file: {e}")
        return False

    # Connect to database
    try:
        print("\nConnecting to Neon PostgreSQL...")
        conn = psycopg2.connect(CONNECTION_STRING)
        conn.autocommit = False  # Use transaction
        cursor = conn.cursor()
        print("[OK] Connected successfully")
    except Exception as e:
        print(f"[ERROR] connecting to database: {e}")
        return False

    # Execute migration
    try:
        print("\nExecuting migration SQL...")
        print("-" * 80)

        # Set client encoding
        cursor.execute("SET client_encoding TO 'UTF8';")

        # Execute the SQL
        cursor.execute(sql_content)

        # Fetch and print all notices
        if conn.notices:
            print("\nNOTICES:")
            for notice in conn.notices:
                print(f"  {notice.strip()}")

        # Commit transaction
        conn.commit()
        print("\n" + "-" * 80)
        print("[OK] Migration executed successfully")
        print("[OK] Transaction committed")

    except Exception as e:
        print(f"\n[ERROR] executing migration: {e}")
        print("\nAttempting rollback...")
        try:
            conn.rollback()
            print("[OK] Transaction rolled back")
        except Exception as rollback_error:
            print(f"[ERROR] during rollback: {rollback_error}")
        return False
    finally:
        cursor.close()
        conn.close()
        print("\nDatabase connection closed")

    print("\n" + "=" * 80)
    print("MIGRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)

    return True

if __name__ == "__main__":
    success = execute_migration()
    sys.exit(0 if success else 1)
