"""
Export validation failures to CSV for Google Sheets import
"""
import os
import sys
import io
import csv
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')

print("=" * 80)
print("EXPORT VALIDATION FAILURES TO CSV")
print("=" * 80)
print()

try:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Query company failures
    cursor.execute("""
        SELECT
            company_id,
            company_name,
            fail_reason,
            state,
            validation_timestamp,
            pipeline_id,
            created_at,
            exported_to_sheets
        FROM marketing.validation_failures_log
        WHERE failure_type = 'company'
          AND exported_to_sheets = FALSE
        ORDER BY created_at DESC;
    """)

    company_failures = cursor.fetchall()

    # Query person failures
    cursor.execute("""
        SELECT
            person_id,
            person_name,
            fail_reason,
            state,
            validation_timestamp,
            pipeline_id,
            created_at,
            exported_to_sheets
        FROM marketing.validation_failures_log
        WHERE failure_type = 'person'
          AND exported_to_sheets = FALSE
        ORDER BY created_at DESC;
    """)

    person_failures = cursor.fetchall()

    print(f"Found {len(company_failures)} company failure(s)")
    print(f"Found {len(person_failures)} person failure(s)")
    print()

    # Export company failures
    if company_failures:
        company_csv = "company_failures.csv"
        with open(company_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'company_id', 'company_name', 'fail_reason', 'state',
                'validation_timestamp', 'pipeline_id', 'created_at', 'exported_to_sheets'
            ])
            writer.writeheader()
            for row in company_failures:
                writer.writerow(row)

        print(f"✅ Exported to: {company_csv}")
        print()
        print("Company Failures:")
        for i, failure in enumerate(company_failures, 1):
            print(f"  {i}. {failure['company_name']} - {failure['fail_reason']}")
    else:
        print("✅ No company failures to export")

    print()

    # Export person failures
    if person_failures:
        person_csv = "person_failures.csv"
        with open(person_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'person_id', 'person_name', 'fail_reason', 'state',
                'validation_timestamp', 'pipeline_id', 'created_at', 'exported_to_sheets'
            ])
            writer.writeheader()
            for row in person_failures:
                writer.writerow(row)

        print(f"✅ Exported to: {person_csv}")
        print()
        print("Person Failures:")
        for i, failure in enumerate(person_failures, 1):
            print(f"  {i}. {failure['person_name']} - {failure['fail_reason']}")
    else:
        print("✅ No person failures to export (100% pass rate!)")

    print()
    print("=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Open company_failures.csv")
    print("  2. Copy data to Google Sheets:")
    print("     https://docs.google.com/spreadsheets/d/1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg/edit")
    print("  3. Paste into 'Company_Failures' tab")
    print("  4. Agent can now enrich the data")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
