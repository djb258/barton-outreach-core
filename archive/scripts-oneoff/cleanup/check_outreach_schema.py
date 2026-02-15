"""
Check schema of outreach.outreach table
"""

import os
import sys
import psycopg2

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def get_neon_connection():
    """Establish Neon database connection"""
    return psycopg2.connect(
        host=os.environ['NEON_HOST'],
        port=os.environ.get('NEON_PORT', '5432'),
        database=os.environ['NEON_DATABASE'],
        user=os.environ['NEON_USER'],
        password=os.environ['NEON_PASSWORD'],
        sslmode='require'
    )

def check_schema():
    """Check outreach.outreach schema"""
    conn = get_neon_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'outreach'
          AND table_name = 'outreach'
        ORDER BY ordinal_position
    """)

    print("outreach.outreach schema:")
    print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable':<10} {'Default':<30}")
    print("-" * 90)
    for row in cursor.fetchall():
        col_name, data_type, nullable, default = row
        default_str = default[:27] + "..." if default and len(default) > 30 else (default or "")
        print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default_str:<30}")

    # Sample data
    print("\n\nSample records:")
    cursor.execute("SELECT * FROM outreach.outreach LIMIT 3")
    columns = [desc[0] for desc in cursor.description]
    print(f"Columns: {', '.join(columns)}")

    for row in cursor.fetchall():
        print(f"\nRecord:")
        for col, val in zip(columns, row):
            print(f"  {col}: {val}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_schema()
