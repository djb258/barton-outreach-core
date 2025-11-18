"""
Download and verify files from Backblaze B2
"""

import os
import sys
import io
import json
from dotenv import load_dotenv
from b2sdk.v2 import InMemoryAccountInfo, B2Api
from b2sdk.download_dest import DownloadDestBytes

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

print("=" * 80)
print("DOWNLOAD AND VERIFY FILES FROM BACKBLAZE B2")
print("=" * 80)
print()

try:
    # Connect to B2
    key_id = os.getenv('B2_KEY_ID')
    app_key = os.getenv('B2_APPLICATION_KEY')
    bucket_name = os.getenv('B2_BUCKET')

    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    b2_api.authorize_account("production", key_id, app_key)
    bucket = b2_api.get_bucket_by_name(bucket_name)

    print(f"✅ Connected to bucket: {bucket.name}")
    print()

    # List all files
    print("Files in validation-failures/:")
    files = list(bucket.ls(folder_to_list='validation-failures/', recursive=True, latest_only=True))

    for file_version, folder_name in files:
        print(f"\n{'='*80}")
        print(f"File: {file_version.file_name}")
        print(f"Size: {file_version.size} bytes")
        print(f"Upload Date: {file_version.upload_timestamp}")
        print(f"File ID: {file_version.id_}")
        print('='*80)

        # Download file
        download_dest = DownloadDestBytes()
        bucket.download_file_by_name(file_version.file_name, download_dest)
        file_data = download_dest.get_bytes_written().decode('utf-8')

        # Parse JSON
        data = json.loads(file_data)

        if isinstance(data, list):
            print(f"Records: {len(data)}")
            print()
            print("Data preview:")
            for i, record in enumerate(data[:3], 1):
                print(f"\n  Record {i}:")
                for key, value in record.items():
                    print(f"    {key}: {value}")
            if len(data) > 3:
                print(f"\n  ... and {len(data) - 3} more records")
        else:
            print("Data:")
            print(json.dumps(data, indent=2))

    print()
    print("=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
