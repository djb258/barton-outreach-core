"""
Google Sheets Push - Barton Toolbox Hub

Pushes validation failures and pipeline data to Google Sheets via n8n webhooks.

n8n Webhooks:
    - Company Failures: https://n8n.barton.com/webhook/push-company-failures
    - Person Failures: https://n8n.barton.com/webhook/push-person-failures

Usage:
    from backend.google_sheets.push_to_sheet import push_to_sheet

    # Push company failures
    push_to_sheet(
        sheet_name="WV_Validation_Failures_2025",
        tab_name="Company_Failures",
        data_rows=[
            {"company_id": "...", "name": "...", "fail_reason": "..."}
        ]
    )

    # Push person failures
    push_to_sheet(
        sheet_name="WV_Validation_Failures_2025",
        tab_name="Person_Failures",
        data_rows=[
            {"person_id": "...", "name": "...", "fail_reason": "..."}
        ]
    )

Status: Production Ready
Date: 2025-11-17
"""

import os
import sys
import requests
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# N8N WEBHOOK CONFIGURATION
# ============================================================================

N8N_WEBHOOKS = {
    "Company_Failures": "https://n8n.barton.com/webhook/push-company-failures",
    "Person_Failures": "https://n8n.barton.com/webhook/push-person-failures",
    "Pipeline_Results": "https://n8n.barton.com/webhook/push-pipeline-results"
}

# Default timeout for webhook requests (seconds)
DEFAULT_TIMEOUT = 30

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = [2, 4, 8]  # Seconds to wait between retries


# ============================================================================
# PUSH TO GOOGLE SHEETS
# ============================================================================

def push_to_sheet(
    sheet_name: str,
    tab_name: str,
    data_rows: List[Dict],
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None
) -> bool:
    """
    Push validation failures or pipeline data to Google Sheets via n8n webhook

    This function:
    - Routes data to appropriate n8n webhook based on tab_name
    - Formats data for Google Sheets (includes headers)
    - Handles retries for transient failures
    - Logs all operations to audit trail

    Args:
        sheet_name: Name of the Google Sheet (e.g., "WV_Validation_Failures_2025")
        tab_name: Tab name within the sheet (e.g., "Company_Failures", "Person_Failures")
        data_rows: List of dictionaries with failure data
        state: State code (e.g., "WV") for audit logging
        pipeline_id: Pipeline run ID for traceability

    Returns:
        True if push succeeded, False otherwise

    Example:
        >>> # Push company failures
        >>> failures = [
        ...     {"company_id": "04.04.02.04.30000.001", "name": "Acme Corp", "fail_reason": "Missing industry"},
        ...     {"company_id": "04.04.02.04.30000.002", "name": "Widget Inc", "fail_reason": "Invalid employee_count"}
        ... ]
        >>> push_to_sheet("WV_Validation_Failures_2025", "Company_Failures", failures, state="WV")
        True

        >>> # Push person failures
        >>> failures = [
        ...     {"person_id": "04.04.02.04.20000.001", "name": "John Doe", "fail_reason": "Missing email"}
        ... ]
        >>> push_to_sheet("WV_Validation_Failures_2025", "Person_Failures", failures, state="WV")
        True
    """
    if not data_rows:
        logger.info(f"No data to push to {sheet_name}/{tab_name}")
        return True

    # Get webhook URL for this tab
    webhook_url = N8N_WEBHOOKS.get(tab_name)
    if not webhook_url:
        logger.error(f"No webhook configured for tab: {tab_name}")
        return False

    # Build payload
    payload = {
        "sheet_name": sheet_name,
        "tab_name": tab_name,
        "data_rows": data_rows,
        "timestamp": datetime.now().isoformat(),
        "state": state,
        "pipeline_id": pipeline_id or f"PIPELINE-{int(time.time())}",
        "row_count": len(data_rows)
    }

    logger.info(f"Pushing {len(data_rows)} rows to {sheet_name}/{tab_name}")

    # Send webhook with retry logic
    success = _send_webhook_with_retry(webhook_url, payload)

    if success:
        logger.info(f"✅ Successfully pushed {len(data_rows)} rows to {sheet_name}/{tab_name}")
    else:
        logger.error(f"❌ Failed to push data to {sheet_name}/{tab_name}")

    return success


def push_company_failures(
    sheet_name: str,
    failures: List[Dict],
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None
) -> bool:
    """
    Push company validation failures to Google Sheets

    Convenience wrapper for push_to_sheet with tab_name="Company_Failures"

    Args:
        sheet_name: Name of the Google Sheet
        failures: List of company failure dictionaries
        state: State code for audit logging
        pipeline_id: Pipeline run ID

    Returns:
        True if push succeeded, False otherwise

    Example:
        >>> failures = [{"company_id": "...", "name": "...", "fail_reason": "..."}]
        >>> push_company_failures("WV_Validation_Failures_2025", failures, state="WV")
        True
    """
    return push_to_sheet(
        sheet_name=sheet_name,
        tab_name="Company_Failures",
        data_rows=failures,
        state=state,
        pipeline_id=pipeline_id
    )


def push_person_failures(
    sheet_name: str,
    failures: List[Dict],
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None
) -> bool:
    """
    Push person validation failures to Google Sheets

    Convenience wrapper for push_to_sheet with tab_name="Person_Failures"

    Args:
        sheet_name: Name of the Google Sheet
        failures: List of person failure dictionaries
        state: State code for audit logging
        pipeline_id: Pipeline run ID

    Returns:
        True if push succeeded, False otherwise

    Example:
        >>> failures = [{"person_id": "...", "name": "...", "fail_reason": "..."}]
        >>> push_person_failures("WV_Validation_Failures_2025", failures, state="WV")
        True
    """
    return push_to_sheet(
        sheet_name=sheet_name,
        tab_name="Person_Failures",
        data_rows=failures,
        state=state,
        pipeline_id=pipeline_id
    )


def _send_webhook_with_retry(url: str, payload: Dict, timeout: int = DEFAULT_TIMEOUT, max_retries: int = MAX_RETRIES) -> bool:
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
            logger.info(f"Sending webhook to {url} (attempt {attempt + 1}/{max_retries})")

            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            # Success (2xx)
            if 200 <= response.status_code < 300:
                logger.info(f"✅ Webhook succeeded: {response.status_code}")
                return True

            # Client error (4xx) - don't retry
            elif 400 <= response.status_code < 500:
                logger.error(f"❌ Webhook client error (no retry): {response.status_code} - {response.text}")
                return False

            # Server error (5xx) - retry
            elif 500 <= response.status_code < 600:
                logger.warning(f"⚠️ Webhook server error: {response.status_code} - will retry")
                if attempt < max_retries - 1:
                    wait_time = RETRY_BACKOFF[attempt]
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ Max retries exceeded for server error")
                    return False

        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Webhook timeout after {timeout}s")
            if attempt < max_retries - 1:
                wait_time = RETRY_BACKOFF[attempt]
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"❌ Max retries exceeded for timeout")
                return False

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"⚠️ Connection error: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = RETRY_BACKOFF[attempt]
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"❌ Max retries exceeded for connection error")
                return False

        except Exception as e:
            logger.error(f"❌ Unexpected error sending webhook: {str(e)}")
            return False

    return False


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Push data to Google Sheets via n8n")
    parser.add_argument("--sheet-name", required=True, help="Google Sheet name")
    parser.add_argument("--tab-name", required=True, help="Tab name (Company_Failures or Person_Failures)")
    parser.add_argument("--data-file", required=True, help="JSON file with data rows")
    parser.add_argument("--state", help="State code (e.g., WV)")

    args = parser.parse_args()

    # Load data from file
    with open(args.data_file, 'r') as f:
        data_rows = json.load(f)

    # Push to sheet
    success = push_to_sheet(
        sheet_name=args.sheet_name,
        tab_name=args.tab_name,
        data_rows=data_rows,
        state=args.state
    )

    if success:
        print(f"✅ Successfully pushed {len(data_rows)} rows to {args.sheet_name}/{args.tab_name}")
        sys.exit(0)
    else:
        print(f"❌ Failed to push data to Google Sheets")
        sys.exit(1)
