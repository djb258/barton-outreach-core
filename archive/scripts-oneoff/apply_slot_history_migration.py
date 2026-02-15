#!/usr/bin/env python3
"""
Apply Slot History Migrations to Neon
=====================================
Applies the slot_assignment_history table and trigger to Neon database.

Usage:
    doppler run -- python infra/scripts/apply_slot_history_migration.py
"""

import os
import sys

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def get_connection():
    """Get database connection from DATABASE_URL."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Run with: doppler run -- python infra/scripts/apply_slot_history_migration.py")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    return psycopg2.connect(database_url)


def apply_migration(conn, migration_file: str, description: str):
    """Apply a single migration file."""
    print(f"\n{'='*60}")
    print(f"Applying: {description}")
    print(f"File: {migration_file}")
    print(f"{'='*60}")

    try:
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()

        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
        print(f"✅ SUCCESS: {description}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ FAILED: {description}")
        print(f"   Error: {e}")
        return False


def verify_migration(conn):
    """Verify the migration was applied correctly."""
    print(f"\n{'='*60}")
    print("Verifying Migration...")
    print(f"{'='*60}")

    cursor = conn.cursor()
    checks = []

    # Check 1: slot_assignment_history table exists in people schema
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'people'
            AND table_name = 'slot_assignment_history'
        )
    """)
    table_exists = cursor.fetchone()[0]
    checks.append(("people.slot_assignment_history table", table_exists))

    # Check 2: Trigger exists on people.company_slot
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.triggers
            WHERE trigger_name = 'trg_slot_assignment_history'
            AND event_object_schema = 'people'
            AND event_object_table = 'company_slot'
        )
    """)
    trigger_exists = cursor.fetchone()[0]
    checks.append(("trg_slot_assignment_history trigger", trigger_exists))

    # Check 3: Immutability trigger (no update) exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.triggers
            WHERE trigger_name = 'trg_slot_history_no_update'
            AND event_object_schema = 'people'
            AND event_object_table = 'slot_assignment_history'
        )
    """)
    immutable_update_trigger_exists = cursor.fetchone()[0]
    checks.append(("Immutability trigger (no_update)", immutable_update_trigger_exists))

    # Check 4: Immutability trigger (no delete) exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.triggers
            WHERE trigger_name = 'trg_slot_history_no_delete'
            AND event_object_schema = 'people'
            AND event_object_table = 'slot_assignment_history'
        )
    """)
    immutable_delete_trigger_exists = cursor.fetchone()[0]
    checks.append(("Immutability trigger (no_delete)", immutable_delete_trigger_exists))

    # Check 5: v_slot_tenure_summary view exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.views
            WHERE table_schema = 'people'
            AND table_name = 'v_slot_tenure_summary'
        )
    """)
    view1_exists = cursor.fetchone()[0]
    checks.append(("v_slot_tenure_summary view", view1_exists))

    # Check 6: v_recent_slot_displacements view exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.views
            WHERE table_schema = 'people'
            AND table_name = 'v_recent_slot_displacements'
        )
    """)
    view2_exists = cursor.fetchone()[0]
    checks.append(("v_recent_slot_displacements view", view2_exists))

    cursor.close()

    # Print results
    all_passed = True
    for check_name, passed in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    return all_passed


def main():
    print("="*60)
    print("SLOT HISTORY MIGRATION TOOL")
    print("="*60)

    # Get connection
    print("\nConnecting to Neon database...")
    conn = get_connection()
    print("✅ Connected successfully")

    # Migration files (in order)
    migrations = [
        (
            "infra/migrations/2026-01-11-slot-assignment-history.sql",
            "Create slot_assignment_history table and triggers"
        ),
    ]

    # Apply migrations
    success_count = 0
    for migration_file, description in migrations:
        if apply_migration(conn, migration_file, description):
            success_count += 1

    # Verify
    verification_passed = verify_migration(conn)

    # Summary
    print(f"\n{'='*60}")
    print("MIGRATION SUMMARY")
    print(f"{'='*60}")
    print(f"  Migrations applied: {success_count}/{len(migrations)}")
    print(f"  Verification: {'✅ PASSED' if verification_passed else '❌ FAILED'}")

    conn.close()

    if success_count == len(migrations) and verification_passed:
        print("\n🎉 All migrations applied successfully!")
        return 0
    else:
        print("\n⚠️  Some migrations failed. Check output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
