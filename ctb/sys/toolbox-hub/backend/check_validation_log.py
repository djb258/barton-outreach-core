"""
Check validation failures log table
"""
import os
import sys
import io
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')

try:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("=" * 80)
    print("VALIDATION FAILURES LOG")
    print("=" * 80)
    print()

    # Query validation failures
    cursor.execute("""
        SELECT *
        FROM marketing.validation_failures_log
        ORDER BY created_at DESC
        LIMIT 10;
    """)

    failures = cursor.fetchall()

    if failures:
        print(f"✅ Found {len(failures)} validation failure(s)")
        print()

        for i, failure in enumerate(failures, 1):
            print(f"Failure #{i}:")
            print(f"  ID: {failure['id']}")
            print(f"  Type: {failure['failure_type']}")
            print(f"  Company ID: {failure['company_id']}")
            print(f"  Company Name: {failure['company_name']}")
            print(f"  Fail Reason: {failure['fail_reason']}")
            print(f"  State: {failure['state']}")
            print(f"  Pipeline ID: {failure['pipeline_id']}")
            print(f"  Validation Timestamp: {failure['validation_timestamp']}")
            print(f"  Created At: {failure['created_at']}")
            print(f"  Exported to Sheets: {failure['exported_to_sheets']}")
            print()
    else:
        print("⚠️ No validation failures found in database")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    sys.exit(1)
