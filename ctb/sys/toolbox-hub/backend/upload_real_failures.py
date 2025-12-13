"""
Upload Real Validation Failures from PostgreSQL to Backblaze B2

This script:
1. Queries validation_failures_log table
2. Uploads failures to B2 using native B2 SDK
3. Marks records as exported_to_b2 = TRUE

Date: 2025-11-18
"""

import os
import sys
import io
import json
import psycopg2
import psycopg2.extras
from datetime import datetime
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

NEON_CONNECTION_STRING = os.getenv('NEON_CONNECTION_STRING')
B2_KEY_ID = os.getenv('B2_KEY_ID')
B2_APP_KEY = os.getenv('B2_APPLICATION_KEY')
B2_BUCKET = os.getenv('B2_BUCKET')

print("=" * 80)
print("UPLOAD VALIDATION FAILURES TO BACKBLAZE B2")
print("=" * 80)
print()

try:
    # Connect to PostgreSQL
    print("Connecting to Neon PostgreSQL...")
    conn = psycopg2.connect(NEON_CONNECTION_STRING)
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    print("✅ Connected to PostgreSQL")
    print()

    # Connect to Backblaze B2
    print("Connecting to Backblaze B2...")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
    bucket = b2_api.get_bucket_by_name(B2_BUCKET)
    print(f"✅ Connected to B2 bucket: {bucket.name}")
    print()

    # ========================================================================
    # EXPORT COMPANY FAILURES
    # ========================================================================

    print("Querying company failures...")
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
    print(f"Found {len(company_failures)} company failure(s) to export")

    if company_failures:
        # Convert to list of dicts and serialize dates
        company_data = []
        for row in company_failures:
            row_dict = dict(row)
            # Convert datetime objects to ISO strings
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            company_data.append(row_dict)

        # Prepare file
        today = datetime.now().strftime('%Y-%m-%d')
        pipeline_id = company_data[0]['pipeline_id']
        file_name = f"validation-failures/{today}/company_failures_{pipeline_id}.json"
        file_data = json.dumps(company_data, indent=2).encode('utf-8')

        print(f"\nUploading to B2: {file_name}")
        print(f"File size: {len(file_data)} bytes")

        # Upload to B2
        file_info = bucket.upload_bytes(
            data_bytes=file_data,
            file_name=file_name,
            content_type='application/json',
            file_infos={
                'pipeline_id': pipeline_id,
                'failure_type': 'company',
                'record_count': str(len(company_data)),
                'upload_timestamp': datetime.now().isoformat()
            }
        )

        print(f"✅ Upload successful!")
        print(f"   File ID: {file_info.id_}")
        print(f"   Size: {file_info.size} bytes")

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

        print(f"✅ Marked {len(company_ids)} records as exported")
        print()
        print("Company failures:")
        for i, failure in enumerate(company_data, 1):
            print(f"  {i}. {failure['company_name']} - {failure['fail_reason']}")

    else:
        print("✅ No company failures to export")

    print()

    # ========================================================================
    # EXPORT PERSON FAILURES
    # ========================================================================

    print("Querying person failures...")
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
    print(f"Found {len(person_failures)} person failure(s) to export")

    if person_failures:
        # Convert to list of dicts and serialize dates
        person_data = []
        for row in person_failures:
            row_dict = dict(row)
            for key, value in row_dict.items():
                if hasattr(value, 'isoformat'):
                    row_dict[key] = value.isoformat()
            person_data.append(row_dict)

        # Prepare file
        today = datetime.now().strftime('%Y-%m-%d')
        pipeline_id = person_data[0]['pipeline_id']
        file_name = f"validation-failures/{today}/person_failures_{pipeline_id}.json"
        file_data = json.dumps(person_data, indent=2).encode('utf-8')

        print(f"\nUploading to B2: {file_name}")
        print(f"File size: {len(file_data)} bytes")

        # Upload to B2
        file_info = bucket.upload_bytes(
            data_bytes=file_data,
            file_name=file_name,
            content_type='application/json',
            file_infos={
                'pipeline_id': pipeline_id,
                'failure_type': 'person',
                'record_count': str(len(person_data)),
                'upload_timestamp': datetime.now().isoformat()
            }
        )

        print(f"✅ Upload successful!")
        print(f"   File ID: {file_info.id_}")
        print(f"   Size: {file_info.size} bytes")

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

        print(f"✅ Marked {len(person_ids)} records as exported")

    else:
        print("✅ No person failures to export (100% pass rate!)")

    print()
    print("=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Verify files in Backblaze B2 console:")
    print("     https://secure.backblaze.com/b2_buckets.htm")
    print("  2. Navigate to bucket: svg-enrichment")
    print("  3. Look for folder: validation-failures/2025-11-18/")
    print("  4. Files should appear with today's date")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
