"""
Test uploading validation failures to Backblaze B2

This script tests uploading a sample validation failure using the native B2 SDK.
"""

import os
import sys
import io
import json
from datetime import datetime
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

print("=" * 80)
print("TEST UPLOAD TO BACKBLAZE B2")
print("=" * 80)
print()

# Sample validation failure
sample_failure = {
    "company_id": "04.04.01.33.00033.033",
    "company_name": "WV SUPREME COURT",
    "fail_reason": "Missing industry",
    "state": "WV",
    "validation_timestamp": "2025-11-18T10:00:00",
    "pipeline_id": "WV-VALIDATION-20251118-TEST"
}

print("Sample failure to upload:")
print(json.dumps(sample_failure, indent=2))
print()

try:
    # Get credentials
    key_id = os.getenv('B2_KEY_ID')
    app_key = os.getenv('B2_APPLICATION_KEY')
    bucket_name = os.getenv('B2_BUCKET')

    # Initialize B2 API
    print("Connecting to Backblaze B2...")
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)
    print("✅ Connected!")
    print()

    # Get bucket
    bucket = b2_api.get_bucket_by_name(bucket_name)
    print(f"✅ Found bucket: {bucket.name}")
    print()

    # Prepare file
    today = datetime.now().strftime('%Y-%m-%d')
    file_name = f"validation-failures/{today}/company_failures_TEST.json"
    file_data = json.dumps([sample_failure], indent=2).encode('utf-8')

    print(f"Uploading file: {file_name}")
    print(f"File size: {len(file_data)} bytes")
    print()

    # Upload file
    file_info = bucket.upload_bytes(
        data_bytes=file_data,
        file_name=file_name,
        content_type='application/json',
        file_infos={
            'pipeline_id': 'WV-VALIDATION-20251118-TEST',
            'failure_type': 'company',
            'record_count': '1'
        }
    )

    print("✅ Upload successful!")
    print(f"   File ID: {file_info.id_}")
    print(f"   File Name: {file_info.file_name}")
    print(f"   Size: {file_info.size} bytes")
    print()

    # List files to verify
    print("Verifying upload...")
    files = list(bucket.ls(folder_to_list='validation-failures/', recursive=True, latest_only=True))

    if files:
        print(f"✅ Found {len(files)} file(s) in validation-failures/:")
        for file_version, folder_name in files:
            print(f"   - {file_version.file_name} ({file_version.size} bytes)")
    else:
        print("⚠️  No files found (unexpected)")

    print()
    print("=" * 80)
    print("✅ TEST UPLOAD SUCCESSFUL!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Verify file in B2 console:")
    print("     https://secure.backblaze.com/b2_buckets.htm")
    print(f"  2. Look for: {file_name}")
    print("  3. Ready to upload real validation failures!")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
