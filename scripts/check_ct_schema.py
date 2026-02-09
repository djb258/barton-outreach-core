"""
Check company_target schema to understand available columns

Author: Claude Code
Date: 2026-02-06
"""

import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2


def check_schema():
    """Check company_target table schema"""

    # Build connection string from environment
    host = os.getenv('NEON_HOST')
    database = os.getenv('NEON_DATABASE')
    user = os.getenv('NEON_USER')
    password = os.getenv('NEON_PASSWORD')

    if not all([host, database, user, password]):
        raise ValueError("Missing required Neon connection environment variables")

    conn_string = f"postgresql://{user}:{password}@{host}/{database}?sslmode=require"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    try:
        print("=" * 80)
        print("COMPANY_TARGET SCHEMA")
        print("=" * 80)
        print()

        query = """
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'outreach'
          AND table_name = 'company_target'
        ORDER BY ordinal_position;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10} {'Default':<20}")
        print("-" * 80)
        for col_name, data_type, nullable, default in rows:
            default_str = str(default)[:20] if default else ""
            print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default_str:<20}")

        print()
        print("=" * 80)
        print("SAMPLE RECORDS")
        print("=" * 80)
        print()

        query_sample = """
        SELECT *
        FROM outreach.company_target
        LIMIT 3;
        """
        cursor.execute(query_sample)
        rows = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]

        for i, row in enumerate(rows, 1):
            print(f"Record {i}:")
            for col_name, val in zip(col_names, row):
                print(f"  {col_name:30} = {val}")
            print()

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    check_schema()
