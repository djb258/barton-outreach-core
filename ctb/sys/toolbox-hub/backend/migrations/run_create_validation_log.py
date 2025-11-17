"""
Run migration to create validation_failures_log table
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

if not NEON_CONNECTION_STRING:
    print("❌ NEON_CONNECTION_STRING not set in .env")
    sys.exit(1)

# Read SQL from file
sql_file = os.path.join(os.path.dirname(__file__), 'create_validation_failures_log.sql')
with open(sql_file, 'r') as f:
    sql = f.read()

print("=" * 70)
print("CREATING VALIDATION FAILURES LOG TABLE")
print("=" * 70)
print()

try:
    # Connect to database
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor()

    print("✅ Connected to Neon PostgreSQL")
    print()

    # Execute migration
    print("Running migration...")
    cursor.execute(sql)
    conn.commit()

    print("✅ Table marketing.validation_failures_log created successfully")
    print()

    # Verify table exists
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'marketing'
          AND table_name = 'validation_failures_log'
        ORDER BY ordinal_position;
    """)

    columns = cursor.fetchall()

    print("Table Columns:")
    print("-" * 70)
    for col in columns:
        print(f"  {col[0]:30} {col[1]:20} {'NULL' if col[2] == 'YES' else 'NOT NULL'}")

    print()
    print("=" * 70)
    print("MIGRATION COMPLETE")
    print("=" * 70)

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
