"""
Query Validation Queue - Barton Outreach Core
Analyzes the current state of marketing.company_invalid table

Usage:
    python query_validation_queue.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ Error: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  Warning: python-dotenv not installed. Using system environment variables only.")


def get_db_connection():
    """Get database connection using environment variables"""
    connection_string = os.getenv("DATABASE_URL") or os.getenv("NEON_CONNECTION_STRING")

    if not connection_string:
        print("❌ Error: DATABASE_URL not found in environment")
        sys.exit(1)

    try:
        conn = psycopg2.connect(connection_string)
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)


def analyze_queue():
    """Analyze the failed validation queue"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 80)
    print("FAILED VALIDATION QUEUE ANALYSIS")
    print("=" * 80)
    print()

    # 1. Total count
    cursor.execute("SELECT COUNT(*) as total FROM marketing.company_invalid;")
    total = cursor.fetchone()['total']
    print(f"Total records in queue: {total}")
    print()

    if total == 0:
        print("Queue is empty! Nothing to process.")
        cursor.close()
        conn.close()
        return

    # 2. Count by reason_code
    cursor.execute("""
        SELECT reason_code, COUNT(*) as count
        FROM marketing.company_invalid
        GROUP BY reason_code
        ORDER BY count DESC;
    """)

    print("Failure Reasons Breakdown:")
    print("-" * 80)
    for row in cursor.fetchall():
        print(f"  {row['reason_code']}: {row['count']} companies")
    print()

    # 3. Count by state
    cursor.execute("""
        SELECT state, COUNT(*) as count
        FROM marketing.company_invalid
        GROUP BY state
        ORDER BY count DESC;
    """)

    print("By State:")
    print("-" * 80)
    for row in cursor.fetchall():
        state = row['state'] or 'NULL'
        print(f"  {state}: {row['count']} companies")
    print()

    # 4. Reviewed vs Not Reviewed
    cursor.execute("""
        SELECT reviewed, COUNT(*) as count
        FROM marketing.company_invalid
        GROUP BY reviewed;
    """)

    print("Review Status:")
    print("-" * 80)
    for row in cursor.fetchall():
        status = "Reviewed" if row['reviewed'] else "Not Reviewed"
        print(f"  {status}: {row['count']} companies")
    print()

    # 5. Sample 5 records
    cursor.execute("""
        SELECT
            id,
            company_unique_id,
            company_name,
            website,
            employee_count,
            reason_code,
            validation_errors,
            failed_at,
            reviewed
        FROM marketing.company_invalid
        ORDER BY failed_at DESC
        LIMIT 5;
    """)

    print("Sample 5 Records (Most Recent):")
    print("=" * 80)
    records = cursor.fetchall()

    for i, row in enumerate(records, 1):
        print(f"\n{i}. {row['company_name']} (ID: {row['company_unique_id']})")
        print(f"   Website: {row['website'] or 'N/A'}")
        print(f"   Employee Count: {row['employee_count'] or 'N/A'}")
        print(f"   Reason: {row['reason_code']}")
        print(f"   Failed At: {row['failed_at']}")
        print(f"   Reviewed: {'Yes' if row['reviewed'] else 'No'}")

        # Parse validation_errors
        if row['validation_errors']:
            errors = row['validation_errors']
            if isinstance(errors, list):
                print(f"   Validation Errors:")
                for error in errors[:3]:  # Show first 3 errors
                    if isinstance(error, dict):
                        field = error.get('field', 'unknown')
                        message = error.get('message', 'No message')
                        print(f"     - {field}: {message}")

    print()
    print("=" * 80)
    print(f"Analysis complete. {total} records need processing.")
    print("=" * 80)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    analyze_queue()
