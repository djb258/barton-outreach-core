"""
Run migration to add Backblaze B2 export tracking columns

This script adds exported_to_b2 and exported_to_b2_at columns to the
marketing.validation_failures_log table.

Usage:
    python backend/migrations/run_add_b2_columns.py

Date: 2025-11-18
Status: Production Ready
"""

import os
import sys
import io
import psycopg2
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')

print("=" * 80)
print("ADD BACKBLAZE B2 EXPORT COLUMNS MIGRATION")
print("=" * 80)
print()

try:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor()

    # Read SQL migration file
    migration_file = os.path.join(
        os.path.dirname(__file__),
        'add_b2_export_columns.sql'
    )

    with open(migration_file, 'r') as f:
        sql = f.read()

    print("Executing migration...")
    print()

    # Execute migration
    cursor.execute(sql)
    conn.commit()

    print("✅ Migration completed successfully!")
    print()

    # Verify columns were created
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'marketing'
          AND table_name = 'validation_failures_log'
          AND column_name IN ('exported_to_b2', 'exported_to_b2_at')
        ORDER BY ordinal_position;
    """)

    columns = cursor.fetchall()

    print("Columns added:")
    for col in columns:
        print(f"  - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")

    print()

    # Verify index was created
    cursor.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = 'marketing'
          AND tablename = 'validation_failures_log'
          AND indexname = 'idx_validation_failures_b2_export';
    """)

    index = cursor.fetchone()
    if index:
        print("Index created:")
        print(f"  - {index[0]}")
        print(f"    {index[1]}")
    else:
        print("⚠️  Index not found (may already exist)")

    print()
    print("=" * 80)
    print("MIGRATION COMPLETE")
    print("=" * 80)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
