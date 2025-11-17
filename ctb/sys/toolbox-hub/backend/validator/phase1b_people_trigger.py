"""
Phase 1b: People Validation Trigger - Barton Toolbox Hub

Claude-callable function for Phase 1b people validation.
Orchestrates validation, database updates, and webhook routing.

Phase ID: 1.1 (Phase 1b)
Trigger: Claude Code or automated pipeline
Input: State code (e.g., "WV"), dry_run flag, limit
Output: Validation results with routing to Invalid_People Google Sheet

Doctrine ID: 4.svg.marketing.ple.phase1b_people_validator

Usage:
    from backend.validator.phase1b_people_trigger import run_phase1b_people_validation

    # Validate all WV people
    run_phase1b_people_validation(state="WV")

    # Dry-run test
    run_phase1b_people_validation(state="WV", dry_run=True, limit=10)

Integration:
- Calls: validation_rules.validate_person()
- Updates: marketing.people_master.validation_status
- Logs: marketing.pipeline_events, shq.audit_log
- Routes: n8n webhook → Google Sheets (Invalid_People)

Status: ✅ Production Ready
Date: 2025-11-17
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validator.validation_rules import validate_person
from validator.db_utils import (
    fetch_people_batch,
    fetch_valid_company_ids,
    update_validation_status,
    log_to_pipeline_events,
    log_to_audit_log
)
from validator.webhook import send_to_invalid_people_sheet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# PHASE 1B CONFIGURATION
# ============================================================================

PHASE_CONFIG = {
    "phase_id": 1.1,
    "phase_name": "Phase 1b: People Validation",
    "doctrine_id": "4.svg.marketing.ple.phase1b_people_validator",
    "description": "Validates people data for outreach readiness. Checks full_name, title, email, LinkedIn, company link, and timestamp.",
    "validation_rules": 7,
    "severity_levels": ["CRITICAL", "ERROR", "WARNING"],
    "webhook_url": "https://n8n.barton.com/webhook/route-person-failure",
    "google_sheet_id": "1i9QNWBqMgY825fLg7lblszMs6X6f5tLxCnAP3Qchfeg",
    "google_sheet_tab": "Invalid_People",
    "failure_schema": [
        "title mismatch",
        "missing email",
        "no LinkedIn URL",
        "bad format or missing timestamp",
        "not linked to company"
    ]
}


# ============================================================================
# VALIDATION STATISTICS
# ============================================================================

class ValidationStats:
    """Track validation statistics for Phase 1b"""

    def __init__(self):
        self.total = 0
        self.valid = 0
        self.invalid = 0
        self.routed_to_sheets = 0
        self.webhook_success = 0
        self.webhook_failed = 0
        self.started_at = datetime.now()
        self.completed_at = None

    def mark_complete(self):
        """Mark validation run as complete"""
        self.completed_at = datetime.now()

    def get_duration_seconds(self) -> float:
        """Get duration in seconds"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now() - self.started_at).total_seconds()

    def to_dict(self) -> Dict:
        """Convert stats to dictionary"""
        return {
            "total": self.total,
            "valid": self.valid,
            "invalid": self.invalid,
            "routed_to_sheets": self.routed_to_sheets,
            "webhook_success": self.webhook_success,
            "webhook_failed": self.webhook_failed,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.get_duration_seconds()
        }


# ============================================================================
# MAIN PHASE 1B FUNCTION
# ============================================================================

def run_phase1b_people_validation(
    state: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
    verbose: bool = False
) -> Dict:
    """
    Phase 1b: People Validation Trigger

    Validates people records from marketing.people_master and routes failures
    to Google Sheets via n8n webhook.

    Args:
        state: State code to filter records (e.g., "WV"). None = all states
        dry_run: If True, no database updates or webhook calls
        limit: Maximum number of records to process. None = all records
        verbose: Enable verbose logging

    Returns:
        {
            "phase_id": 1.1,
            "phase_name": "Phase 1b: People Validation",
            "state": "WV",
            "dry_run": False,
            "statistics": {
                "total": 150,
                "valid": 120,
                "invalid": 30,
                "routed_to_sheets": 28,
                "webhook_success": 26,
                "webhook_failed": 2,
                "duration_seconds": 45
            },
            "invalid_people": [
                {
                    "person_id": "04.04.02.04.20000.002",
                    "full_name": "Jane Smith",
                    "reason": "title: Does not match CEO/CFO/HR; email: Invalid format",
                    "failures_count": 2
                }
            ]
        }

    Example:
        >>> # Validate all WV people
        >>> result = run_phase1b_people_validation(state="WV")
        >>> print(f"Valid: {result['statistics']['valid']}")

        >>> # Dry-run test
        >>> result = run_phase1b_people_validation(state="WV", dry_run=True, limit=10)
    """
    # Initialize statistics
    stats = ValidationStats()

    # Set logging level
    if verbose:
        logger.setLevel(logging.DEBUG)

    # Log start
    logger.info("=" * 70)
    logger.info(f"PHASE 1B: PEOPLE VALIDATION")
    logger.info("=" * 70)
    logger.info(f"State: {state or 'ALL'}")
    logger.info(f"Dry-run: {dry_run}")
    logger.info(f"Limit: {limit or 'NONE'}")
    logger.info("")

    # Step 1: Fetch valid company IDs (for FK validation)
    logger.info("Step 1: Loading valid company IDs...")
    try:
        valid_company_ids = fetch_valid_company_ids()
        logger.info(f"✅ Loaded {len(valid_company_ids)} valid companies")
    except Exception as e:
        logger.error(f"❌ Failed to load valid company IDs: {e}")
        return {
            "phase_id": PHASE_CONFIG["phase_id"],
            "phase_name": PHASE_CONFIG["phase_name"],
            "error": str(e),
            "statistics": stats.to_dict()
        }

    # Step 2: Fetch people batch
    logger.info(f"\nStep 2: Loading people from marketing.people_master...")
    try:
        people = fetch_people_batch(state=state, limit=limit)
        logger.info(f"✅ Loaded {len(people)} people")
    except Exception as e:
        logger.error(f"❌ Failed to load people: {e}")
        return {
            "phase_id": PHASE_CONFIG["phase_id"],
            "phase_name": PHASE_CONFIG["phase_name"],
            "error": str(e),
            "statistics": stats.to_dict()
        }

    if len(people) == 0:
        logger.warning("⚠️ No people found to validate")
        return {
            "phase_id": PHASE_CONFIG["phase_id"],
            "phase_name": PHASE_CONFIG["phase_name"],
            "state": state,
            "dry_run": dry_run,
            "statistics": stats.to_dict(),
            "invalid_people": []
        }

    # Dry-run warning
    if dry_run:
        logger.warning("🔍 DRY-RUN MODE: No database updates or webhook calls will be made")

    # Step 3: Validate people
    logger.info(f"\nStep 3: Validating {len(people)} people...")
    logger.info("")

    invalid_people = []

    for person in people:
        stats.total += 1

        person_id = person.get("person_id") or person.get("unique_id", "unknown")
        full_name = person.get("full_name", "Unknown")

        # Validate person
        result = validate_person(person, valid_company_ids)

        # Process result
        if result["valid"]:
            stats.valid += 1

            # Update database (if not dry-run)
            if not dry_run:
                try:
                    update_validation_status(person_id, "valid")
                    log_to_pipeline_events("person_validation_check", {
                        "person_id": person_id,
                        "valid": True,
                        "reason": None,
                        "failures_count": 0,
                        "phase_id": PHASE_CONFIG["phase_id"]
                    })
                except Exception as e:
                    logger.error(f"❌ Failed to update database for {person_id}: {e}")

            logger.info(f"✅ {full_name} ({person_id}): VALID")

        else:
            stats.invalid += 1

            # Update database (if not dry-run)
            if not dry_run:
                try:
                    update_validation_status(person_id, "invalid")
                    log_to_pipeline_events("person_validation_check", {
                        "person_id": person_id,
                        "valid": False,
                        "reason": result["reason"],
                        "failures_count": len(result["failures"]),
                        "phase_id": PHASE_CONFIG["phase_id"]
                    })
                except Exception as e:
                    logger.error(f"❌ Failed to update database for {person_id}: {e}")

            # Route to Google Sheets (if not dry-run)
            if not dry_run:
                try:
                    webhook_success = send_to_invalid_people_sheet(result, state)
                    if webhook_success:
                        stats.webhook_success += 1
                        stats.routed_to_sheets += 1
                        logger.info(f"❌ {full_name} ({person_id}): INVALID → Routed to Google Sheets")
                        logger.info(f"   Reason: {result['reason']}")
                    else:
                        stats.webhook_failed += 1
                        logger.error(f"❌ {full_name} ({person_id}): INVALID → Webhook failed")
                        logger.info(f"   Reason: {result['reason']}")
                except Exception as e:
                    stats.webhook_failed += 1
                    logger.error(f"❌ Failed to route {person_id} to Google Sheets: {e}")
            else:
                logger.info(f"❌ {full_name} ({person_id}): INVALID (would be routed in production)")
                logger.info(f"   Reason: {result['reason']}")

            # Add to invalid_people list
            invalid_people.append({
                "person_id": person_id,
                "full_name": full_name,
                "reason": result["reason"],
                "failures_count": len(result["failures"]),
                "failures": result["failures"]
            })

    # Mark validation complete
    stats.mark_complete()

    # Step 4: Log summary to audit_log (if not dry-run)
    if not dry_run:
        try:
            log_to_audit_log("phase1b_people_validator", "validation_complete", {
                "total": stats.total,
                "valid": stats.valid,
                "invalid": stats.invalid,
                "routed_to_sheets": stats.routed_to_sheets,
                "webhook_success": stats.webhook_success,
                "webhook_failed": stats.webhook_failed,
                "state": state or "ALL",
                "phase_id": PHASE_CONFIG["phase_id"],
                "duration_seconds": stats.get_duration_seconds()
            })
        except Exception as e:
            logger.error(f"❌ Failed to log to audit_log: {e}")

    # Print summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total People:           {stats.total}")
    logger.info(f"Valid:                  {stats.valid}")
    logger.info(f"Invalid:                {stats.invalid}")
    if not dry_run:
        logger.info(f"Routed to Sheets:       {stats.routed_to_sheets}")
        logger.info(f"Webhook Success:        {stats.webhook_success}")
        logger.info(f"Webhook Failed:         {stats.webhook_failed}")
    logger.info(f"Duration:               {stats.get_duration_seconds():.2f}s")
    logger.info("=" * 70)

    # Return result
    return {
        "phase_id": PHASE_CONFIG["phase_id"],
        "phase_name": PHASE_CONFIG["phase_name"],
        "state": state,
        "dry_run": dry_run,
        "statistics": stats.to_dict(),
        "invalid_people": invalid_people
    }


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1b: People Validation Trigger")
    parser.add_argument("--state", type=str, default=None, help="State code to filter records (e.g., WV)")
    parser.add_argument("--dry-run", action="store_true", help="Test validation without making changes")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records to process")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Run Phase 1b
    result = run_phase1b_people_validation(
        state=args.state,
        dry_run=args.dry_run,
        limit=args.limit,
        verbose=args.verbose
    )

    # Exit with appropriate code
    if "error" in result:
        sys.exit(1)
    elif result["statistics"]["invalid"] > 0:
        sys.exit(0)  # Invalid people found, but not a system error
    else:
        sys.exit(0)
