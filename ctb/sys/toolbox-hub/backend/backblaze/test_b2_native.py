"""
Test Backblaze B2 connection using native B2 SDK

This uses the b2sdk directly instead of boto3 to verify credentials
and bucket access.
"""

import os
import sys
import io
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

print("=" * 80)
print("BACKBLAZE B2 NATIVE SDK CONNECTION TEST")
print("=" * 80)
print()

# Get credentials
key_id = os.getenv('B2_KEY_ID')
app_key = os.getenv('B2_APPLICATION_KEY')
bucket_name = os.getenv('B2_BUCKET')

print(f"Key ID: {key_id}")
print(f"Application Key: {app_key[:20]}... (truncated)")
print(f"Bucket Name: {bucket_name}")
print()

try:
    # Initialize B2 API
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)

    print("Authorizing account...")
    b2_api.authorize_account("production", key_id, app_key)
    print("✅ Authorization successful!")
    print()

    # List buckets
    print("Listing buckets...")
    buckets = b2_api.list_buckets()

    print(f"Found {len(buckets)} bucket(s):")
    for bucket in buckets:
        print(f"  - {bucket.name} (Type: {bucket.type_})")
    print()

    # Try to get our specific bucket
    print(f"Looking for bucket: {bucket_name}...")
    bucket = b2_api.get_bucket_by_name(bucket_name)
    print(f"✅ Found bucket: {bucket.name}")
    print(f"   Bucket ID: {bucket.id_}")
    print(f"   Bucket Type: {bucket.type_}")
    print()

    # List files in bucket
    print("Listing files in bucket...")
    file_versions = list(bucket.ls(recursive=True, latest_only=True))

    if file_versions:
        print(f"Found {len(file_versions)} file(s):")
        for file_version, folder_name in file_versions[:10]:
            print(f"  - {file_version.file_name} ({file_version.size} bytes)")
        if len(file_versions) > 10:
            print(f"  ... and {len(file_versions) - 10} more")
    else:
        print("Bucket is empty (no files found)")

    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print("Backblaze B2 connection is working correctly.")
    print("You can now upload validation failures to B2.")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
