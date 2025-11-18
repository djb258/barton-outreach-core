"""
Backblaze B2 Client - Simplified S3-Compatible Storage

This module provides a simple wrapper around Backblaze B2 using the S3 API.
Backblaze B2 is fully S3-compatible, making it a drop-in replacement for AWS S3.

Why Backblaze B2:
- S3-compatible API (no new learning curve)
- 1/4 the cost of AWS S3
- Free egress (no download fees)
- Simple authentication (no OAuth complexity)
- Native JSON/CSV support

Configuration:
- Requires: B2_ENDPOINT, B2_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET in .env
- Uses boto3 S3 client under the hood

Status: Production Ready
Date: 2025-11-18
"""

import os
import sys
import io
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class B2Client:
    """
    Backblaze B2 client using S3-compatible API

    This client uses boto3's S3 client to interact with Backblaze B2.
    Backblaze B2 is fully S3-compatible with minor configuration changes.

    Example:
        >>> client = B2Client()
        >>> client.upload_json(
        ...     key="validation-failures/2025-11-18/company_failures.json",
        ...     data={"company_id": "...", "fail_reason": "..."}
        ... )
        True
    """

    def __init__(self):
        """Initialize Backblaze B2 client"""
        self.endpoint = os.getenv('B2_ENDPOINT')
        self.key_id = os.getenv('B2_KEY_ID')
        self.app_key = os.getenv('B2_APPLICATION_KEY')
        self.bucket = os.getenv('B2_BUCKET')
        self.prefix = os.getenv('B2_VALIDATION_FAILURES_PREFIX', 'validation-failures/')

        # Validate configuration
        if not all([self.endpoint, self.key_id, self.app_key, self.bucket]):
            raise ValueError(
                "Missing Backblaze B2 configuration. Required env vars:\n"
                "  - B2_ENDPOINT\n"
                "  - B2_KEY_ID\n"
                "  - B2_APPLICATION_KEY\n"
                "  - B2_BUCKET"
            )

        # Create S3 client configured for Backblaze B2
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.app_key,
            config=Config(signature_version='s3v4')
        )

        logger.info(f"Initialized Backblaze B2 client for bucket: {self.bucket}")


    def upload_json(
        self,
        key: str,
        data: Dict | List[Dict],
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload JSON data to B2

        Args:
            key: Object key (path) in the bucket
            data: Data to upload (dict or list of dicts)
            metadata: Optional metadata tags

        Returns:
            True if successful, False otherwise

        Example:
            >>> client.upload_json(
            ...     key="validation-failures/2025-11-18/company_failures.json",
            ...     data=[{"company_id": "...", "fail_reason": "..."}],
            ...     metadata={"pipeline_id": "WV-VALIDATION-20251118"}
            ... )
            True
        """
        try:
            # Add prefix if not already present
            if not key.startswith(self.prefix):
                key = self.prefix + key

            # Convert data to JSON
            json_data = json.dumps(data, indent=2, default=str)

            # Upload to B2
            extra_args = {
                'ContentType': 'application/json',
                'Metadata': metadata or {}
            }

            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json_data.encode('utf-8'),
                **extra_args
            )

            logger.info(f"✅ Uploaded JSON to B2: {key} ({len(json_data)} bytes)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload JSON to B2: {str(e)}")
            return False


    def upload_csv(
        self,
        key: str,
        csv_content: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Upload CSV data to B2

        Args:
            key: Object key (path) in the bucket
            csv_content: CSV string content
            metadata: Optional metadata tags

        Returns:
            True if successful, False otherwise
        """
        try:
            # Add prefix if not already present
            if not key.startswith(self.prefix):
                key = self.prefix + key

            # Upload to B2
            extra_args = {
                'ContentType': 'text/csv',
                'Metadata': metadata or {}
            }

            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=csv_content.encode('utf-8'),
                **extra_args
            )

            logger.info(f"✅ Uploaded CSV to B2: {key} ({len(csv_content)} bytes)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload CSV to B2: {str(e)}")
            return False


    def list_files(self, prefix: Optional[str] = None) -> List[str]:
        """
        List files in B2 bucket

        Args:
            prefix: Optional prefix to filter by

        Returns:
            List of file keys
        """
        try:
            search_prefix = self.prefix
            if prefix:
                search_prefix = self.prefix + prefix if not prefix.startswith(self.prefix) else prefix

            response = self.s3.list_objects_v2(
                Bucket=self.bucket,
                Prefix=search_prefix
            )

            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]

            logger.info(f"Found {len(files)} files with prefix: {search_prefix}")
            return files

        except Exception as e:
            logger.error(f"❌ Failed to list files in B2: {str(e)}")
            return []


    def download_json(self, key: str) -> Optional[Dict | List[Dict]]:
        """
        Download JSON data from B2

        Args:
            key: Object key (path) in the bucket

        Returns:
            Parsed JSON data or None if failed
        """
        try:
            # Add prefix if not already present
            if not key.startswith(self.prefix):
                key = self.prefix + key

            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=key
            )

            content = response['Body'].read().decode('utf-8')
            data = json.loads(content)

            logger.info(f"✅ Downloaded JSON from B2: {key}")
            return data

        except Exception as e:
            logger.error(f"❌ Failed to download JSON from B2: {str(e)}")
            return None


    def get_public_url(self, key: str) -> str:
        """
        Get public URL for a file in B2

        Args:
            key: Object key (path) in the bucket

        Returns:
            Public URL (Note: bucket must be public for this to work)
        """
        # Add prefix if not already present
        if not key.startswith(self.prefix):
            key = self.prefix + key

        # Backblaze B2 public URL format
        # https://f005.backblazeb2.com/file/bucket-name/file-path
        # Note: This requires the bucket to be public
        return f"{self.endpoint}/file/{self.bucket}/{key}"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_b2_client() -> B2Client:
    """Get initialized B2 client"""
    return B2Client()


def test_connection() -> bool:
    """
    Test Backblaze B2 connection

    Returns:
        True if connection successful, False otherwise
    """
    try:
        client = B2Client()

        # Test by listing files (should work even if bucket is empty)
        files = client.list_files()

        logger.info(f"✅ B2 connection successful! Found {len(files)} files in bucket.")
        return True

    except Exception as e:
        logger.error(f"❌ B2 connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test connection
    print("=" * 80)
    print("BACKBLAZE B2 CONNECTION TEST")
    print("=" * 80)
    print()

    if test_connection():
        print("✅ Connection successful!")

        # List existing files
        client = get_b2_client()
        files = client.list_files()

        if files:
            print(f"\nFound {len(files)} file(s):")
            for i, file in enumerate(files[:10], 1):
                print(f"  {i}. {file}")
            if len(files) > 10:
                print(f"  ... and {len(files) - 10} more")
        else:
            print("\nBucket is empty or prefix has no files.")
    else:
        print("❌ Connection failed!")
        print("\nPlease check your .env configuration:")
        print("  - B2_ENDPOINT")
        print("  - B2_KEY_ID")
        print("  - B2_APPLICATION_KEY")
        print("  - B2_BUCKET")
