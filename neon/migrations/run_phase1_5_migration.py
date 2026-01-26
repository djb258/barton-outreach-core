"""
BIT v2 Phase 1.5 Migration Runner - DOL Backfill + Talent Flow Movements

Executes: 2026-01-26-bit-v2-phase1.5-backfill-and-movements.sql
Authority: ADR-017

Usage:
    doppler run -- python neon/migrations/run_phase1_5_migration.py
"""

import os
import psycopg2
from pathlib import Path


def run_migration():
    """Execute the Phase 1.5 migration against Neon."""

    # Get connection from environment
    host = os.environ.get("NEON_HOST")
    database = os.environ.get("NEON_DATABASE")
    user = os.environ.get("NEON_USER")
    password = os.environ.get("NEON_PASSWORD")

    if not all([host, database, user, password]):
        print("ERROR: Missing Neon connection environment variables")
        print("Required: NEON_HOST, NEON_DATABASE, NEON_USER, NEON_PASSWORD")
        print("Run with: doppler run -- python neon/migrations/run_phase1_5_migration.py")
        return False

    # Read migration file
    migration_path = Path(__file__).parent / "2026-01-26-bit-v2-phase1.5-backfill-and-movements.sql"

    if not migration_path.exists():
        print(f"ERROR: Migration file not found: {migration_path}")
        return False

    print("=" * 70)
    print("BIT v2 Phase 1.5 Migration - DOL Backfill + Talent Flow Movements")
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

        # Check movements table
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'talent_flow' AND table_name = 'movements'
            )
        """)
        movements_exists = cursor.fetchone()[0]
        print(f"talent_flow.movements table: {'OK' if movements_exists else 'MISSING'}")

        # Check backfill function
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'dol' AND p.proname = 'backfill_renewal_signals'
            )
        """)
        backfill_exists = cursor.fetchone()[0]
        print(f"dol.backfill_renewal_signals(): {'OK' if backfill_exists else 'MISSING'}")

        # Check trigger
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.triggers
                WHERE trigger_name = 'trg_bridge_to_pressure_signals'
                  AND event_object_schema = 'talent_flow'
                  AND event_object_table = 'movements'
            )
        """)
        trigger_attached = cursor.fetchone()[0]
        print(f"Bridge trigger on movements: {'ATTACHED' if trigger_attached else 'MISSING'}")

        # Get signal counts
        cursor.execute("SELECT COUNT(*) FROM dol.pressure_signals")
        dol_signals = cursor.fetchone()[0]
        print()
        print(f"dol.pressure_signals count: {dol_signals}")

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
