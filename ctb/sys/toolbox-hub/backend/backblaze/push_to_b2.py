"""
Push Validation Failures to Backblaze B2

Simple, direct upload of validation failures to B2 object storage.
No webhooks, no OAuth, no complexity - just direct S3-compatible uploads.

Benefits over Google Sheets:
- No authentication complexity (simple API keys)
- No rate limiting concerns
- Automatic versioning
- Direct file access
- 1/4 the cost of AWS S3
- Free egress (no download fees)

Usage:
    from backend.backblaze.push_to_b2 import push_company_failures

    success = push_company_failures(
        failures=[{"company_id": "...", "fail_reason": "..."}],
        pipeline_id="WV-VALIDATION-20251118"
    )

Status: Production Ready
Date: 2025-11-18
"""

import os
import sys
import io
import json
import csv
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .b2_client import B2Client

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# PUSH TO B2 - MAIN FUNCTION
# ============================================================================

def push_to_b2(
    failure_type: str,
    failures: List[Dict],
    pipeline_id: Optional[str] = None,
    state: Optional[str] = None,
    export_format: str = "json"
) -> bool:
    """
    Push validation failures to Backblaze B2

    This function:
    - Uploads validation failures directly to B2
    - Organizes files by date and type
    - Supports both JSON and CSV formats
    - Includes metadata for traceability

    Args:
        failure_type: Type of failure ("company" or "person")
        failures: List of failure records
        pipeline_id: Pipeline run ID for traceability
        state: State code (e.g., "WV")
        export_format: Format to export ("json" or "csv")

    Returns:
        True if successful, False otherwise

    Example:
        >>> failures = [
        ...     {"company_id": "04.04.01.33.00033.033", "company_name": "WV SUPREME COURT", "fail_reason": "Missing industry"}
        ... ]
        >>> push_to_b2("company", failures, pipeline_id="WV-VALIDATION-20251118")
        True
    """

    if not failures:
        logger.info(f"No {failure_type} failures to push to B2")
        return True

    # Generate pipeline ID if not provided
    if not pipeline_id:
        pipeline_id = f"VALIDATION-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Get today's date for file organization
    today = datetime.now().strftime('%Y-%m-%d')

    # Build file key (path in bucket)
    file_key = f"{today}/{failure_type}_failures_{pipeline_id}.{export_format}"

    logger.info(f"Pushing {len(failures)} {failure_type} failure(s) to B2...")
    logger.info(f"File: {file_key}")

    try:
        # Initialize B2 client
        client = B2Client()

        # Prepare metadata
        metadata = {
            'pipeline_id': pipeline_id,
            'failure_type': failure_type,
            'record_count': str(len(failures)),
            'upload_timestamp': datetime.now().isoformat()
        }
        if state:
            metadata['state'] = state

        # Upload based on format
        if export_format == "json":
            success = client.upload_json(
                key=file_key,
                data=failures,
                metadata=metadata
            )
        elif export_format == "csv":
            # Convert to CSV
            csv_content = _convert_to_csv(failures)
            success = client.upload_csv(
                key=file_key,
                csv_content=csv_content,
                metadata=metadata
            )
        else:
            logger.error(f"Invalid export format: {export_format}. Use 'json' or 'csv'.")
            return False

        if success:
            logger.info(f"✅ Successfully pushed {len(failures)} {failure_type} failures to B2")
            logger.info(f"   File: {file_key}")

            # Print public URL (if bucket is public)
            public_url = client.get_public_url(file_key)
            logger.info(f"   URL: {public_url}")
        else:
            logger.error(f"❌ Failed to push {failure_type} failures to B2")

        return success

    except Exception as e:
        logger.error(f"❌ Error pushing to B2: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================================
# CSV CONVERSION
# ============================================================================

def _convert_to_csv(data: List[Dict]) -> str:
    """
    Convert list of dictionaries to CSV string

    Args:
        data: List of dictionaries

    Returns:
        CSV string
    """
    if not data:
        return ""

    # Get all unique keys from all records
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())

    fieldnames = sorted(all_keys)

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


# ============================================================================
# CONVENIENCE WRAPPERS
# ============================================================================

def push_company_failures(
    failures: List[Dict],
    pipeline_id: Optional[str] = None,
    state: Optional[str] = None,
    export_format: str = "json"
) -> bool:
    """
    Push company validation failures to B2

    Args:
        failures: List of company failure dictionaries
        pipeline_id: Pipeline run ID
        state: State code (e.g., "WV")
        export_format: Format to export ("json" or "csv")

    Returns:
        True if successful, False otherwise
    """
    return push_to_b2(
        failure_type="company",
        failures=failures,
        pipeline_id=pipeline_id,
        state=state,
        export_format=export_format
    )


def push_person_failures(
    failures: List[Dict],
    pipeline_id: Optional[str] = None,
    state: Optional[str] = None,
    export_format: str = "json"
) -> bool:
    """
    Push person validation failures to B2

    Args:
        failures: List of person failure dictionaries
        pipeline_id: Pipeline run ID
        state: State code (e.g., "WV")
        export_format: Format to export ("json" or "csv")

    Returns:
        True if successful, False otherwise
    """
    return push_to_b2(
        failure_type="person",
        failures=failures,
        pipeline_id=pipeline_id,
        state=state,
        export_format=export_format
    )


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Push validation failures to Backblaze B2")
    parser.add_argument("--type", required=True, choices=["company", "person"], help="Failure type")
    parser.add_argument("--data-file", required=True, help="JSON file with validation failures")
    parser.add_argument("--pipeline-id", help="Pipeline run ID")
    parser.add_argument("--state", help="State code (e.g., WV)")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="Export format")

    args = parser.parse_args()

    print("=" * 80)
    print("PUSH VALIDATION FAILURES TO BACKBLAZE B2")
    print("=" * 80)
    print()

    # Load data from file
    with open(args.data_file, 'r') as f:
        failures = json.load(f)

    print(f"Loaded {len(failures)} {args.type} failure(s) from {args.data_file}")
    print()

    # Push to B2
    success = push_to_b2(
        failure_type=args.type,
        failures=failures,
        pipeline_id=args.pipeline_id,
        state=args.state,
        export_format=args.format
    )

    print()
    print("=" * 80)
    if success:
        print("✅ PUSH SUCCESSFUL")
        sys.exit(0)
    else:
        print("❌ PUSH FAILED")
        sys.exit(1)
