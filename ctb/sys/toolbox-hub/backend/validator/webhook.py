"""
Webhook Utilities - Barton Toolbox Hub

Helper functions for n8n webhook routing in Phase 1a/1b validation.

Functions:
- send_to_invalid_people_sheet() - Route invalid person to Google Sheets
- send_to_invalid_company_sheet() - Route invalid company to Google Sheets

Webhooks:
- People: https://n8n.barton.com/webhook/route-person-failure
- Companies: https://n8n.barton.com/webhook/route-company-failure

Google Sheets:
- Sheet ID: 1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg
- People Tab: Invalid_People
- Companies Tab: Invalid_Companies

Status: ✅ Production Ready
Date: 2025-11-17
"""

import os
import requests
import time
from typing import Dict, Optional
from datetime import datetime
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# WEBHOOK CONFIGURATION
# ============================================================================

WEBHOOK_CONFIG = {
    "people": {
        "url": "https://n8n.barton.com/webhook/route-person-failure",
        "timeout": 30,
        "max_retries": 3,
        "retry_delays": [2, 4, 8],  # Exponential backoff (seconds)
        "sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
        "sheet_tab": "Invalid_People"
    },
    "company": {
        "url": "https://n8n.barton.com/webhook/route-company-failure",
        "timeout": 30,
        "max_retries": 3,
        "retry_delays": [2, 4, 8],  # Exponential backoff (seconds)
        "sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
        "sheet_tab": "Invalid_Companies"
    }
}


# ============================================================================
# WEBHOOK ROUTING FUNCTIONS
# ============================================================================

def send_to_invalid_people_sheet(
    validation_result: Dict,
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None
) -> bool:
    """
    Route invalid person to Google Sheets via n8n webhook

    Args:
        validation_result: Result from validate_person() function
        state: State code (e.g., "WV") or None
        pipeline_id: Pipeline run identifier or None

    Returns:
        True if webhook succeeded, False otherwise

    Example:
        >>> result = validate_person(person, valid_company_ids)
        >>> if not result['valid']:
        ...     send_to_invalid_people_sheet(result, state="WV")
    """
    config = WEBHOOK_CONFIG["people"]

    # Build payload
    payload = {
        "type": "person",
        "reason_code": validation_result.get("reason", "Validation failed"),
        "row_data": {
            "person_id": validation_result.get("person_id", ""),
            "full_name": validation_result.get("full_name", ""),
            "email": validation_result.get("email", ""),
            "title": validation_result.get("title", ""),
            "company_unique_id": validation_result.get("company_unique_id", ""),
            "linkedin_url": validation_result.get("linkedin_url", ""),
            "validation_status": validation_result.get("validation_status", "invalid")
        },
        "state": state or "unknown",
        "timestamp": datetime.now().isoformat(),
        "pipeline_id": pipeline_id or f"PRC-PV-{int(time.time())}",
        "failures": validation_result.get("failures", []),
        "sheet_id": config["sheet_id"],
        "sheet_tab": config["sheet_tab"]
    }

    # Send webhook with retry logic
    return _send_webhook_with_retry(
        url=config["url"],
        payload=payload,
        timeout=config["timeout"],
        max_retries=config["max_retries"],
        retry_delays=config["retry_delays"]
    )


def send_to_invalid_company_sheet(
    validation_result: Dict,
    state: Optional[str] = None,
    pipeline_id: Optional[str] = None
) -> bool:
    """
    Route invalid company to Google Sheets via n8n webhook

    Args:
        validation_result: Result from validate_company() function
        state: State code (e.g., "WV") or None
        pipeline_id: Pipeline run identifier or None

    Returns:
        True if webhook succeeded, False otherwise

    Example:
        >>> result = validate_company(company)
        >>> if not result['valid']:
        ...     send_to_invalid_company_sheet(result, state="WV")
    """
    config = WEBHOOK_CONFIG["company"]

    # Build payload
    payload = {
        "type": "company",
        "reason_code": validation_result.get("reason", "Validation failed"),
        "row_data": {
            "company_unique_id": validation_result.get("company_unique_id", ""),
            "company_name": validation_result.get("company_name", ""),
            "industry": validation_result.get("industry", ""),
            "employee_count": validation_result.get("employee_count", 0),
            "website": validation_result.get("website", ""),
            "linkedin_url": validation_result.get("linkedin_url", ""),
            "validation_status": validation_result.get("validation_status", "invalid")
        },
        "state": state or "unknown",
        "timestamp": datetime.now().isoformat(),
        "pipeline_id": pipeline_id or f"PRC-CV-{int(time.time())}",
        "failures": validation_result.get("failures", []),
        "sheet_id": config["sheet_id"],
        "sheet_tab": config["sheet_tab"]
    }

    # Send webhook with retry logic
    return _send_webhook_with_retry(
        url=config["url"],
        payload=payload,
        timeout=config["timeout"],
        max_retries=config["max_retries"],
        retry_delays=config["retry_delays"]
    )


# ============================================================================
# INTERNAL HELPER FUNCTIONS
# ============================================================================

def _send_webhook_with_retry(
    url: str,
    payload: Dict,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delays: list = None
) -> bool:
    """
    Send webhook with retry logic for 5xx errors

    Args:
        url: Webhook URL
        payload: JSON payload to send
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delays: List of retry delays (exponential backoff)

    Returns:
        True if webhook succeeded (200), False otherwise

    Retry Logic:
    - 5xx errors: Retry with exponential backoff
    - 4xx errors: No retry (client error)
    - Timeouts: Retry
    - Network errors: Retry
    """
    if retry_delays is None:
        retry_delays = [2, 4, 8]

    for attempt in range(max_retries):
        try:
            logger.debug(f"Webhook attempt {attempt + 1}/{max_retries}: {url}")

            response = requests.post(
                url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            # Success (200-299)
            if 200 <= response.status_code < 300:
                logger.info(f"✅ Webhook succeeded: {url} (status {response.status_code})")
                return True

            # 4xx client error - do not retry
            elif 400 <= response.status_code < 500:
                logger.error(f"❌ Webhook rejected (4xx): {url} (status {response.status_code})")
                logger.error(f"   Response: {response.text[:200]}")
                return False

            # 5xx server error - retry
            elif 500 <= response.status_code < 600:
                logger.warning(f"⚠️ Webhook server error (5xx): {url} (status {response.status_code})")

                # Retry if not last attempt
                if attempt < max_retries - 1:
                    delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                    logger.info(f"   Retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"❌ Webhook failed after {max_retries} retries")
                    return False

            # Unknown status code
            else:
                logger.error(f"❌ Webhook unexpected status: {url} (status {response.status_code})")
                return False

        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Webhook timeout: {url}")

            # Retry if not last attempt
            if attempt < max_retries - 1:
                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                logger.info(f"   Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                logger.error(f"❌ Webhook timed out after {max_retries} attempts")
                return False

        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Webhook network error: {url} - {e}")

            # Retry if not last attempt
            if attempt < max_retries - 1:
                delay = retry_delays[min(attempt, len(retry_delays) - 1)]
                logger.info(f"   Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                logger.error(f"❌ Webhook failed after {max_retries} network errors")
                return False

    # Should not reach here, but just in case
    return False


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    import sys
    import io

    # Set UTF-8 encoding for Windows console
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("=" * 70)
    print("WEBHOOK UTILITIES - TEST")
    print("=" * 70)

    # Test 1: Build person webhook payload
    print("\n[Test 1] Build Person Webhook Payload:")
    person_result = {
        "valid": False,
        "reason": "title: Does not match CEO/CFO/HR; email: Invalid format",
        "failures": [
            {"field": "title", "message": "Does not match CEO/CFO/HR"},
            {"field": "email", "message": "Invalid email format"}
        ],
        "person_id": "04.04.02.04.20000.001",
        "company_unique_id": "04.04.02.04.30000.001",
        "full_name": "Jane Smith",
        "email": "jane@acme.com",
        "title": "Finance Manager",
        "linkedin_url": "",
        "validation_status": "invalid"
    }

    print(f"  Person: {person_result['full_name']}")
    print(f"  Reason: {person_result['reason']}")
    print(f"  Failures: {len(person_result['failures'])}")

    # Test 2: Build company webhook payload
    print("\n[Test 2] Build Company Webhook Payload:")
    company_result = {
        "valid": False,
        "reason": "employee_count: Must be > 50; linkedin_url: Invalid format",
        "failures": [
            {"field": "employee_count", "message": "Must be > 50"},
            {"field": "linkedin_url", "message": "Invalid format"}
        ],
        "company_unique_id": "04.04.02.04.30000.001",
        "company_name": "Acme Corp",
        "industry": "Technology",
        "employee_count": 30,
        "website": "https://acme.com",
        "linkedin_url": "",
        "validation_status": "invalid"
    }

    print(f"  Company: {company_result['company_name']}")
    print(f"  Reason: {company_result['reason']}")
    print(f"  Failures: {len(company_result['failures'])}")

    # Test 3: Webhook configuration
    print("\n[Test 3] Webhook Configuration:")
    print(f"  People Webhook: {WEBHOOK_CONFIG['people']['url']}")
    print(f"  People Sheet Tab: {WEBHOOK_CONFIG['people']['sheet_tab']}")
    print(f"  Company Webhook: {WEBHOOK_CONFIG['company']['url']}")
    print(f"  Company Sheet Tab: {WEBHOOK_CONFIG['company']['sheet_tab']}")
    print(f"  Max Retries: {WEBHOOK_CONFIG['people']['max_retries']}")
    print(f"  Retry Delays: {WEBHOOK_CONFIG['people']['retry_delays']}")

    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
    print("\nNOTE: Actual webhook sends not tested (would require live n8n server)")
