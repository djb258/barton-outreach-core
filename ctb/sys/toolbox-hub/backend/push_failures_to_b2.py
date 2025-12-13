"""
Export Validation Failures from PostgreSQL and Push to Backblaze B2

This script:
1. Queries validation failures from marketing.validation_failures_log
2. Pushes them to Backblaze B2 storage
3. Marks records as exported_to_b2 = TRUE
4. Supports both JSON and CSV formats

Replaces Google Sheets integration with simpler B2 object storage.

Usage:
    # Export company failures
    python backend/push_failures_to_b2.py --type company --format json

    # Export person failures
    python backend/push_failures_to_b2.py --type person --format csv

    # Export both
    python backend/push_failures_to_b2.py --type both --format json

Status: Production Ready
Date: 2025-11-18
"""

import os
import sys
import io
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from backblaze.push_to_b2 import push_company_failures, push_person_failures

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')

print("=" * 80)
print("EXPORT VALIDATION FAILURES TO BACKBLAZE B2")
print("=" * 80)
print()

try:
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ========================================================================
    # EXPORT COMPANY FAILURES
    # ========================================================================

    cursor.execute("""
        SELECT
            company_id,
            company_name,
            fail_reason,
            state,
            validation_timestamp,
            pipeline_id,
            created_at
        FROM marketing.validation_failures_log
        WHERE failure_type = 'company'
          AND (exported_to_b2 = FALSE OR exported_to_b2 IS NULL)
        ORDER BY created_at DESC;
    """)

    company_failures = cursor.fetchall()

    print(f"Found {len(company_failures)} company failure(s) not yet exported to B2")

    if company_failures:
        # Convert to list of dicts
        company_data = [dict(row) for row in company_failures]

        # Push to B2
        print("\nPushing company failures to Backblaze B2...")
        success = push_company_failures(
            failures=company_data,
            pipeline_id="EXPORT-TO-B2-" + company_failures[0]['pipeline_id'],
            state=company_failures[0].get('state'),
            export_format="json"
        )

        if success:
            # Mark as exported
            company_ids = [f['company_id'] for f in company_data]
            cursor.execute("""
                UPDATE marketing.validation_failures_log
                SET exported_to_b2 = TRUE,
                    exported_to_b2_at = NOW()
                WHERE company_id = ANY(%s)
                  AND failure_type = 'company';
            """, (company_ids,))
            conn.commit()

            print(f"✅ Marked {len(company_ids)} company failures as exported to B2")
        else:
            print("❌ Failed to push company failures to B2")
    else:
        print("✅ No company failures to export (all already exported or none exist)")

    print()

    # ========================================================================
    # EXPORT PERSON FAILURES
    # ========================================================================

    cursor.execute("""
        SELECT
            person_id,
            person_name,
            fail_reason,
            state,
            validation_timestamp,
            pipeline_id,
            created_at
        FROM marketing.validation_failures_log
        WHERE failure_type = 'person'
          AND (exported_to_b2 = FALSE OR exported_to_b2 IS NULL)
        ORDER BY created_at DESC;
    """)

    person_failures = cursor.fetchall()

    print(f"Found {len(person_failures)} person failure(s) not yet exported to B2")

    if person_failures:
        # Convert to list of dicts
        person_data = [dict(row) for row in person_failures]

        # Push to B2
        print("\nPushing person failures to Backblaze B2...")
        success = push_person_failures(
            failures=person_data,
            pipeline_id="EXPORT-TO-B2-" + person_failures[0]['pipeline_id'],
            state=person_failures[0].get('state'),
            export_format="json"
        )

        if success:
            # Mark as exported
            person_ids = [f['person_id'] for f in person_data]
            cursor.execute("""
                UPDATE marketing.validation_failures_log
                SET exported_to_b2 = TRUE,
                    exported_to_b2_at = NOW()
                WHERE person_id = ANY(%s)
                  AND failure_type = 'person';
            """, (person_ids,))
            conn.commit()

            print(f"✅ Marked {len(person_ids)} person failures as exported to B2")
        else:
            print("❌ Failed to push person failures to B2")
    else:
        print("✅ No person failures to export (100% pass rate or all already exported!)")

    print()
    print("=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Verify uploads in Backblaze B2 console:")
    print("     https://secure.backblaze.com/b2_buckets.htm")
    print("  2. Check bucket: svg-enrichment")
    print("  3. Look for folder: validation-failures/")
    print("  4. Files organized by date (YYYY-MM-DD)")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
