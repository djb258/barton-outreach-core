"""
BIT v2 Phase 1 Distributed Signals Migration Runner

Executes: 2026-01-26-bit-v2-phase1-distributed-signals.sql
Authority: ADR-017

Usage:
    doppler run -- python neon/migrations/run_distributed_signals_migration.py
"""

import os
import psycopg2
from pathlib import Path


def run_migration():
    """Execute the distributed signals migration against Neon."""

    # Get connection from environment
    host = os.environ.get("NEON_HOST")
    database = os.environ.get("NEON_DATABASE")
    user = os.environ.get("NEON_USER")
    password = os.environ.get("NEON_PASSWORD")

    if not all([host, database, user, password]):
        print("ERROR: Missing Neon connection environment variables")
        print("Required: NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD")
        print("Run with: doppler run -- python neon/migrations/run_distributed_signals_migration.py")
        return False

    # Read migration file
    migration_path = Path(__file__).parent / "2026-01-26-bit-v2-phase1-distributed-signals.sql"

    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        return False

    print("=" * 70)
    print("BIT v2 Phase 1 Distributed Signals Migration")
    print("=" * 70)
    print(f"Migration file: {migration_path.name}")
    print(f"Target database: {database}@{host}")
    print()

    migration_sql = migration_path.read_text(encoding="utf-8")

    try:
        # Connect to Neon
        print("Connecting to Neon...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            sslmode="require"
        )
        conn.autocommit = False
        cursor = conn.cursor()

        print("Executing migration...")
        cursor.execute(migration_sql)

        # Commit transaction
        conn.commit()
        print()
        print("Migration completed successfully!")
        print()

        # Verify created objects
        print("Verifying created objects...")
        print()

        # Check tables
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_name = 'pressure_signals'
            ORDER BY table_schema
        """)
        tables = cursor.fetchall()
        print("Signal Tables:")
        for schema, table in tables:
            print(f"  {schema}.{table}")

        # Check view
        cursor.execute("""
            SELECT table_schema, table_name
            FROM information_schema.views
            WHERE table_name = 'vw_all_pressure_signals'
        """)
        views = cursor.fetchall()
        print()
        print("Union View:")
        for schema, view in views:
            print(f"  {schema}.{view}")

        # Check function
        cursor.execute("""
            SELECT n.nspname, p.proname
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE p.proname = 'compute_authorization_band'
        """)
        funcs = cursor.fetchall()
        print()
        print("BIT Computation Function:")
        for schema, func in funcs:
            print(f"  {schema}.{func}()")

        # Check bridge triggers
        cursor.execute("""
            SELECT trigger_name, event_object_schema, event_object_table
            FROM information_schema.triggers
            WHERE trigger_name LIKE '%bridge%'
        """)
        triggers = cursor.fetchall()
        print()
        print("Bridge Triggers:")
        for trigger, schema, table in triggers:
            print(f"  {trigger} ON {schema}.{table}")

        cursor.close()
        conn.close()

        print()
        print("=" * 70)
        print("MIGRATION SUCCESSFUL")
        print("=" * 70)
        return True

    except psycopg2.Error as e:
        print()
        print("=" * 70)
        print("MIGRATION FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)
