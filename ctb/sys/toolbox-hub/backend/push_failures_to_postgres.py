"""
Push Validation Failures Directly to PostgreSQL

Reads failures from validation_failures.json and inserts into marketing.validation_failures_log
"""
import os
import sys
import io
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')
PIPELINE_ID = f"WV-VALIDATION-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

print("=" * 80)
print("PUSH VALIDATION FAILURES TO POSTGRESQL")
print("=" * 80)
print(f"Pipeline ID: {PIPELINE_ID}")
print()

try:
    # Load validation failures
    failures_file = os.path.join(os.path.dirname(__file__), '..', 'validation_failures.json')
    with open(failures_file, 'r') as f:
        failures_data = json.load(f)

    company_failures = failures_data.get('company_failures', [])
    person_failures = failures_data.get('person_failures', [])

    print(f"Loaded from file:")
    print(f"  Company failures: {len(company_failures)}")
    print(f"  Person failures: {len(person_failures)}")
    print()

    if not company_failures and not person_failures:
        print("✅ No failures to push (perfect validation!)")
        sys.exit(0)

    # Connect to database
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    print("✅ Connected to Neon PostgreSQL")
    print()

    # Insert company failures
    if company_failures:
        print("Inserting company failures...")
        for i, failure in enumerate(company_failures, 1):
            cursor.execute("""
                INSERT INTO marketing.validation_failures_log (
                    company_id, company_name, fail_reason, state,
                    validation_timestamp, pipeline_id, failure_type, created_at
                )
                VALUES (%(company_id)s, %(company_name)s, %(fail_reason)s, %(state)s,
                        %(validation_timestamp)s, %(pipeline_id)s, 'company', NOW())
                ON CONFLICT (company_id, pipeline_id, failure_type) DO UPDATE
                SET fail_reason = EXCLUDED.fail_reason,
                    validation_timestamp = EXCLUDED.validation_timestamp,
                    updated_at = NOW()
                RETURNING id, company_name;
            """, {
                'company_id': failure.get('company_id'),
                'company_name': failure.get('company_name'),
                'fail_reason': failure.get('fail_reason'),
                'state': failure.get('state', 'N/A'),
                'validation_timestamp': failure.get('validation_timestamp'),
                'pipeline_id': PIPELINE_ID
            })

            result = cursor.fetchone()
            print(f"  ✅ #{i}: {result['company_name']} (ID: {result['id']})")

        conn.commit()
        print()
        print(f"✅ Inserted {len(company_failures)} company failure(s)")

    # Insert person failures
    if person_failures:
        print()
        print("Inserting person failures...")
        for i, failure in enumerate(person_failures, 1):
            cursor.execute("""
                INSERT INTO marketing.validation_failures_log (
                    person_id, person_name, fail_reason, state,
                    validation_timestamp, pipeline_id, failure_type, created_at
                )
                VALUES (%(person_id)s, %(person_name)s, %(fail_reason)s, %(state)s,
                        %(validation_timestamp)s, %(pipeline_id)s, 'person', NOW())
                ON CONFLICT (person_id, pipeline_id, failure_type) DO UPDATE
                SET fail_reason = EXCLUDED.fail_reason,
                    validation_timestamp = EXCLUDED.validation_timestamp,
                    updated_at = NOW()
                RETURNING id, person_name;
            """, {
                'person_id': failure.get('person_id'),
                'person_name': failure.get('person_name') or failure.get('full_name'),
                'fail_reason': failure.get('fail_reason'),
                'state': failure.get('state', 'N/A'),
                'validation_timestamp': failure.get('validation_timestamp'),
                'pipeline_id': PIPELINE_ID
            })

            result = cursor.fetchone()
            print(f"  ✅ #{i}: {result['person_name']} (ID: {result['id']})")

        conn.commit()
        print()
        print(f"✅ Inserted {len(person_failures)} person failure(s)")

    # Summary query
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    cursor.execute("""
        SELECT
            failure_type,
            COUNT(*) as count,
            MIN(created_at) as first_created,
            MAX(created_at) as last_created
        FROM marketing.validation_failures_log
        WHERE pipeline_id = %s
        GROUP BY failure_type;
    """, (PIPELINE_ID,))

    summary = cursor.fetchall()
    for row in summary:
        print(f"{row['failure_type'].upper()} failures: {row['count']}")
        print(f"  First created: {row['first_created']}")
        print(f"  Last created: {row['last_created']}")

    print()
    print("=" * 80)
    print("✅ PUSH COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Query validation_failures_log table for analysis")
    print("  2. Export to Google Sheets (manual or via script)")
    print("  3. Use this data for reporting and tracking")

    cursor.close()
    conn.close()

except FileNotFoundError:
    print(f"❌ Error: validation_failures.json not found")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
