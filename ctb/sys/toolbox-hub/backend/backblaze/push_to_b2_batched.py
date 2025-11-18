"""
Batched Push to Backblaze B2 - Optimized for Large Datasets

This module provides batching for large validation failure uploads to B2.
Unlike Google Sheets/n8n, B2 doesn't have execution limits, but batching
still helps with:
- File organization (multiple smaller files vs one huge file)
- Parallel processing potential
- Incremental upload progress tracking
- Easier data analysis (separate files per batch)

For 148,000 people + 37,000 companies with 5% failure rate = 9,250 failures:
- Without batching: 1 huge 9,250-record file
- With batching (1000 records/file): 10 organized files
- **Benefits: Better organization, easier debugging, incremental uploads**

Usage:
    from backend.backblaze.push_to_b2_batched import push_to_b2_batched

    success_count, fail_count = push_to_b2_batched(
        failure_type="company",
        failures=failures,  # All 9,250 records
        batch_size=1000
    )

Status: Production Ready
Date: 2025-11-18
"""

import os
import sys
import io
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .b2_client import B2Client
from .push_to_b2 import _convert_to_csv

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Batch configuration
DEFAULT_BATCH_SIZE = 1000  # Records per file
DELAY_BETWEEN_BATCHES = 0.1  # Seconds (minimal, just for courtesy)


# ============================================================================
# BATCHED PUSH FUNCTION
# ============================================================================

def push_to_b2_batched(
    failure_type: str,
    failures: List[Dict],
    batch_size: int = DEFAULT_BATCH_SIZE,
    pipeline_id: Optional[str] = None,
    state: Optional[str] = None,
    export_format: str = "json",
    delay_between_batches: float = DELAY_BETWEEN_BATCHES
) -> Tuple[int, int]:
    """
    Push validation failures to B2 in batches

    This function:
    - Splits data into batches of batch_size
    - Uploads each batch as a separate file
    - Organizes files by date and batch number
    - Returns (success_count, failure_count)

    Args:
        failure_type: Type of failure ("company" or "person")
        failures: List of all failure records
        batch_size: Number of records per batch file (default: 1000)
        pipeline_id: Pipeline run ID for traceability
        state: State code for audit logging
        export_format: Format to export ("json" or "csv")
        delay_between_batches: Seconds to wait between uploads (default: 0.1)

    Returns:
        Tuple of (successful_records, failed_records)

    Example:
        >>> failures = [...]  # 9,250 company failures
        >>> success, fail = push_to_b2_batched(
        ...     failure_type="company",
        ...     failures=failures,
        ...     batch_size=1000
        ... )
        >>> print(f"Uploaded {success} records in {len(failures) // 1000 + 1} files")
        Uploaded 9250 records in 10 files
    """

    if not failures:
        logger.info(f"No {failure_type} failures to push to B2")
        return 0, 0

    # Generate pipeline ID if not provided
    if not pipeline_id:
        pipeline_id = f"VALIDATION-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Get today's date for file organization
    today = datetime.now().strftime('%Y-%m-%d')

    # Split into batches
    batches = [
        failures[i:i + batch_size]
        for i in range(0, len(failures), batch_size)
    ]

    total_batches = len(batches)
    logger.info(f"Pushing {len(failures)} {failure_type} failures in {total_batches} batches of {batch_size}")
    logger.info(f"Format: {export_format}")
    print()

    successful_records = 0
    failed_records = 0

    try:
        # Initialize B2 client
        client = B2Client()

        for batch_num, batch in enumerate(batches, 1):
            batch_id = f"{pipeline_id}-BATCH-{batch_num:03d}"

            # Build file key (path in bucket)
            file_key = f"{today}/{failure_type}_failures_{batch_id}.{export_format}"

            logger.info(f"Batch {batch_num}/{total_batches}: Uploading {len(batch)} records...")

            # Prepare metadata
            metadata = {
                'pipeline_id': pipeline_id,
                'batch_id': batch_id,
                'batch_number': str(batch_num),
                'total_batches': str(total_batches),
                'failure_type': failure_type,
                'record_count': str(len(batch)),
                'upload_timestamp': datetime.now().isoformat()
            }
            if state:
                metadata['state'] = state

            # Upload based on format
            success = False
            if export_format == "json":
                success = client.upload_json(
                    key=file_key,
                    data=batch,
                    metadata=metadata
                )
            elif export_format == "csv":
                csv_content = _convert_to_csv(batch)
                success = client.upload_csv(
                    key=file_key,
                    csv_content=csv_content,
                    metadata=metadata
                )

            if success:
                successful_records += len(batch)
                logger.info(f"  ✅ Batch {batch_num}/{total_batches} succeeded ({len(batch)} records)")
            else:
                failed_records += len(batch)
                logger.error(f"  ❌ Batch {batch_num}/{total_batches} failed ({len(batch)} records)")

            # Delay between batches (except after last batch)
            if batch_num < total_batches:
                time.sleep(delay_between_batches)

        print()
        logger.info("=" * 70)
        logger.info("BATCH UPLOAD COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Total records: {len(failures)}")
        logger.info(f"Total batches: {total_batches}")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Successful: {successful_records} records")
        logger.info(f"Failed: {failed_records} records")
        logger.info(f"Success rate: {(successful_records / len(failures) * 100):.1f}%")
        logger.info("=" * 70)

        return successful_records, failed_records

    except Exception as e:
        logger.error(f"❌ Error in batched upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return successful_records, len(failures) - successful_records


# ============================================================================
# CONVENIENCE WRAPPERS
# ============================================================================

def push_company_failures_batched(
    failures: List[Dict],
    pipeline_id: Optional[str] = None,
    state: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    export_format: str = "json"
) -> Tuple[int, int]:
    """
    Push company validation failures to B2 in batches

    Args:
        failures: List of company failure dictionaries
        pipeline_id: Pipeline run ID
        state: State code for audit logging
        batch_size: Records per batch (default: 1000)
        export_format: Format to export ("json" or "csv")

    Returns:
        Tuple of (successful_records, failed_records)
    """
    return push_to_b2_batched(
        failure_type="company",
        failures=failures,
        batch_size=batch_size,
        pipeline_id=pipeline_id,
        state=state,
        export_format=export_format
    )


def push_person_failures_batched(
    failures: List[Dict],
    pipeline_id: Optional[str] = None,
    state: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    export_format: str = "json"
) -> Tuple[int, int]:
    """
    Push person validation failures to B2 in batches

    Args:
        failures: List of person failure dictionaries
        pipeline_id: Pipeline run ID
        state: State code for audit logging
        batch_size: Records per batch (default: 1000)
        export_format: Format to export ("json" or "csv")

    Returns:
        Tuple of (successful_records, failed_records)
    """
    return push_to_b2_batched(
        failure_type="person",
        failures=failures,
        batch_size=batch_size,
        pipeline_id=pipeline_id,
        state=state,
        export_format=export_format
    )


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Push validation failures to B2 in batches")
    parser.add_argument("--type", required=True, choices=["company", "person"], help="Failure type")
    parser.add_argument("--data-file", required=True, help="JSON file with validation failures")
    parser.add_argument("--pipeline-id", help="Pipeline run ID")
    parser.add_argument("--state", help="State code (e.g., WV)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Records per batch (default: 1000)")
    parser.add_argument("--format", default="json", choices=["json", "csv"], help="Export format")

    args = parser.parse_args()

    print("=" * 80)
    print("BATCHED PUSH TO BACKBLAZE B2")
    print("=" * 80)
    print()

    # Load data from file
    with open(args.data_file, 'r') as f:
        failures = json.load(f)

    print(f"Loaded {len(failures)} {args.type} failure(s) from {args.data_file}")
    print()

    # Push to B2 in batches
    success_count, fail_count = push_to_b2_batched(
        failure_type=args.type,
        failures=failures,
        batch_size=args.batch_size,
        pipeline_id=args.pipeline_id,
        state=args.state,
        export_format=args.format
    )

    print()
    if fail_count == 0:
        print(f"✅ Successfully uploaded all {success_count} records")
        sys.exit(0)
    else:
        print(f"⚠️  Uploaded {success_count} records, {fail_count} failed")
        sys.exit(1)
