"""
Batched Push to Google Sheets - Optimized for Large Datasets

This module provides optimized batching for pushing large numbers of validation
failures to Google Sheets. Instead of one execution per row, it batches up to
50 rows per execution.

For 148,000 people + 37,000 companies with 5% failure rate = 9,250 failures:
- Without batching: 9,250 executions
- With batching (50 rows/batch): 185 executions
- **Savings: 98% reduction in executions**

Usage:
    from backend.google_sheets.push_to_sheet_batched import push_to_sheet_batched

    # Push 1000 failures in batches of 50
    success_count, fail_count = push_to_sheet_batched(
        sheet_name="WV_Validation_Failures_2025",
        tab_name="Company_Failures",
        data_rows=failures,  # List of 1000 dicts
        batch_size=50,
        state="WV"
    )

Status: Production Ready
Date: 2025-11-17
"""

import os
import sys
import requests
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# N8N WEBHOOK CONFIGURATION
# ============================================================================

N8N_WEBHOOKS = {
    "Company_Failures": "https://dbarton.app.n8n.cloud/webhook/push-company-failures",
    "Person_Failures": "https://dbarton.app.n8n.cloud/webhook/push-person-failures",
    "Pipeline_Results": "https://dbarton.app.n8n.cloud/webhook/push-pipeline-results"
}

# Batch configuration
DEFAULT_BATCH_SIZE = 50  # Rows per execution
DEFAULT_TIMEOUT = 30  # Seconds
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 4, 8]  # Seconds between retries

# Rate limiting (to avoid overwhelming n8n)
DELAY_BETWEEN_BATCHES = 0.5  # Seconds


# ============================================================================
# BATCHED PUSH FUNCTION
# ============================================================================

def push_to_sheet_batched(
    sheet_name: str,
    tab_name: str,
    data_rows: List[Dict],
    batch_size: int = DEFAULT_BATCH_SIZE,
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    delay_between_batches: float = DELAY_BETWEEN_BATCHES
) -> Tuple[int, int]:
    """
    Push validation failures to Google Sheets in batches

    This function:
    - Splits data_rows into batches of batch_size
    - Sends each batch as one webhook request
    - Includes exponential backoff retry for each batch
    - Returns (success_count, failure_count)

    Args:
        sheet_name: Name of the Google Sheet
        tab_name: Tab name within the sheet
        data_rows: List of all failure records
        batch_size: Number of rows per batch (default: 50)
        state: State code for audit logging
        pipeline_id: Pipeline run ID for traceability
        delay_between_batches: Seconds to wait between batches (default: 0.5)

    Returns:
        Tuple of (successful_rows, failed_rows)

    Example:
        >>> failures = [...]  # 1000 company failures
        >>> success, fail = push_to_sheet_batched(
        ...     "WV_Validation_Failures_2025",
        ...     "Company_Failures",
        ...     failures,
        ...     batch_size=50
        ... )
        >>> print(f"Pushed {success} rows in {len(failures) // 50} batches")
        Pushed 1000 rows in 20 batches
    """

    if not data_rows:
        logger.info(f"No data to push to {sheet_name}/{tab_name}")
        return 0, 0

    # Get webhook URL
    webhook_url = N8N_WEBHOOKS.get(tab_name)
    if not webhook_url:
        logger.error(f"No webhook configured for tab: {tab_name}")
        return 0, len(data_rows)

    # Generate pipeline ID if not provided
    if not pipeline_id:
        pipeline_id = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # Split into batches
    batches = [
        data_rows[i:i + batch_size]
        for i in range(0, len(data_rows), batch_size)
    ]

    total_batches = len(batches)
    logger.info(f"Pushing {len(data_rows)} rows in {total_batches} batches of {batch_size}")
    logger.info(f"Target: {sheet_name}/{tab_name}")
    logger.info(f"Webhook: {webhook_url}")
    print()

    successful_rows = 0
    failed_rows = 0

    for batch_num, batch in enumerate(batches, 1):
        batch_id = f"{pipeline_id}-BATCH-{batch_num}"

        # Build payload
        payload = {
            "sheet_name": sheet_name,
            "tab_name": tab_name,
            "data_rows": batch,
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "pipeline_id": batch_id,
            "row_count": len(batch),
            "batch_info": {
                "batch_number": batch_num,
                "total_batches": total_batches,
                "batch_size": len(batch)
            }
        }

        # Send batch with retry
        logger.info(f"Batch {batch_num}/{total_batches}: Pushing {len(batch)} rows...")

        success = _send_webhook_with_retry(webhook_url, payload)

        if success:
            successful_rows += len(batch)
            logger.info(f"  ✅ Batch {batch_num}/{total_batches} succeeded ({len(batch)} rows)")
        else:
            failed_rows += len(batch)
            logger.error(f"  ❌ Batch {batch_num}/{total_batches} failed ({len(batch)} rows)")

        # Delay between batches (except after last batch)
        if batch_num < total_batches:
            time.sleep(delay_between_batches)

    print()
    logger.info("=" * 70)
    logger.info("BATCH PUSH COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Total rows: {len(data_rows)}")
    logger.info(f"Total batches: {total_batches}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Successful: {successful_rows} rows")
    logger.info(f"Failed: {failed_rows} rows")
    logger.info(f"Success rate: {(successful_rows / len(data_rows) * 100):.1f}%")
    logger.info("=" * 70)

    return successful_rows, failed_rows


# ============================================================================
# WEBHOOK RETRY LOGIC
# ============================================================================

def _send_webhook_with_retry(
    url: str,
    payload: Dict,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES
) -> bool:
    """
    Send webhook request with exponential backoff retry logic

    Retry Logic:
    - 5xx errors (server errors): Retry with backoff [2s, 4s, 8s]
    - 4xx errors (client errors): No retry (permanent failure)
    - Connection errors: Retry
    - Timeouts: Retry

    Args:
        url: Webhook URL
        payload: JSON payload to send
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts

    Returns:
        True if request succeeded (200-299), False otherwise
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            # Success (2xx)
            if 200 <= response.status_code < 300:
                return True

            # Client error (4xx) - don't retry
            elif 400 <= response.status_code < 500:
                logger.error(f"    ⚠️  Client error (no retry): {response.status_code} - {response.text[:100]}")
                return False

            # Server error (5xx) - retry
            elif 500 <= response.status_code < 600:
                logger.warning(f"    ⚠️  Server error: {response.status_code} - will retry")
                if attempt < max_retries - 1:
                    wait_time = RETRY_BACKOFF[attempt]
                    logger.info(f"    Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"    ❌ Max retries exceeded for server error")
                    return False

        except requests.exceptions.Timeout:
            logger.warning(f"    ⚠️  Timeout after {timeout}s")
            if attempt < max_retries - 1:
                wait_time = RETRY_BACKOFF[attempt]
                logger.info(f"    Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"    ❌ Max retries exceeded for timeout")
                return False

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"    ⚠️  Connection error: {str(e)[:100]}")
            if attempt < max_retries - 1:
                wait_time = RETRY_BACKOFF[attempt]
                logger.info(f"    Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"    ❌ Max retries exceeded for connection error")
                return False

        except Exception as e:
            logger.error(f"    ❌ Unexpected error: {str(e)}")
            return False

    return False


# ============================================================================
# CONVENIENCE WRAPPERS
# ============================================================================

def push_company_failures_batched(
    sheet_name: str,
    failures: List[Dict],
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> Tuple[int, int]:
    """
    Push company validation failures to Google Sheets in batches

    Args:
        sheet_name: Name of the Google Sheet
        failures: List of company failure dictionaries
        state: State code for audit logging
        pipeline_id: Pipeline run ID
        batch_size: Rows per batch (default: 50)

    Returns:
        Tuple of (successful_rows, failed_rows)
    """
    return push_to_sheet_batched(
        sheet_name=sheet_name,
        tab_name="Company_Failures",
        data_rows=failures,
        batch_size=batch_size,
        state=state,
        pipeline_id=pipeline_id
    )


def push_person_failures_batched(
    sheet_name: str,
    failures: List[Dict],
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> Tuple[int, int]:
    """
    Push person validation failures to Google Sheets in batches

    Args:
        sheet_name: Name of the Google Sheet
        failures: List of person failure dictionaries
        state: State code for audit logging
        pipeline_id: Pipeline run ID
        batch_size: Rows per batch (default: 50)

    Returns:
        Tuple of (successful_rows, failed_rows)
    """
    return push_to_sheet_batched(
        sheet_name=sheet_name,
        tab_name="Person_Failures",
        data_rows=failures,
        batch_size=batch_size,
        state=state,
        pipeline_id=pipeline_id
    )


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Push data to Google Sheets in batches via n8n")
    parser.add_argument("--sheet-name", required=True, help="Google Sheet name")
    parser.add_argument("--tab-name", required=True, help="Tab name (Company_Failures or Person_Failures)")
    parser.add_argument("--data-file", required=True, help="JSON file with data rows")
    parser.add_argument("--state", help="State code (e.g., WV)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Rows per batch (default: 50)")

    args = parser.parse_args()

    # Load data from file
    with open(args.data_file, 'r') as f:
        data_rows = json.load(f)

    # Push to sheet in batches
    success_count, fail_count = push_to_sheet_batched(
        sheet_name=args.sheet_name,
        tab_name=args.tab_name,
        data_rows=data_rows,
        batch_size=args.batch_size,
        state=args.state
    )

    if fail_count == 0:
        print(f"\n✅ Successfully pushed all {success_count} rows")
        sys.exit(0)
    else:
        print(f"\n⚠️  Pushed {success_count} rows, {fail_count} failed")
        sys.exit(1)
