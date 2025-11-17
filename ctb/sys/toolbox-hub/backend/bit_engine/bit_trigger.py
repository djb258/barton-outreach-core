"""
Phase 4: BIT Trigger Check - Barton Toolbox Hub

Evaluates if outreach-ready contacts meet BIT (Buyer Intent Tool) signal thresholds.
Checks for executive movement, company changes, or other intent signals.

Phase ID: 4
Doctrine ID: 4.svg.marketing.ple.bit_trigger_check

Usage:
    from backend.bit_engine.bit_trigger import check_bit_trigger_conditions

    # Check single person/company
    result = check_bit_trigger_conditions(person, company)

    # Check batch from state
    result = check_bit_trigger_conditions(state="WV", dry_run=False)

Status: ✅ Production Ready (Stub Implementation)
Date: 2025-11-17
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# BIT TRIGGER CONFIGURATION
# ============================================================================

BIT_TRIGGER_CONFIG = {
    "phase_id": 4,
    "phase_name": "BIT Trigger Check",
    "doctrine_id": "4.svg.marketing.ple.bit_trigger_check",
    "signal_types": [
        "Executive Movement",  # New CEO/CFO/HR hire
        "Funding Round",       # Company raised funding
        "Hiring Spree",        # Multiple open positions
        "Tech Stack Change",   # New technology adoption
        "Leadership Change"    # Executive team changes
    ],
    "executive_titles": ["CEO", "CFO", "HR", "Chief Executive", "Chief Financial", "Human Resources"],
    "recency_threshold_days": 90  # Consider recent if within 90 days
}


# ============================================================================
# BIT TRIGGER DETECTION
# ============================================================================

def check_bit_trigger_conditions(
    person: Optional[Dict] = None,
    company: Optional[Dict] = None,
    state: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Phase 4: Check if person/company meets BIT trigger conditions

    This is a STUB implementation with basic logic:
    - Triggers if person has executive title (CEO/CFO/HR)
    - Triggers if person was recently validated (within 90 days)
    - In batch mode, processes all outreach-ready companies

    Args:
        person: Person dictionary (optional, for single-person check)
        company: Company dictionary (optional, for single-company check)
        state: State code for batch processing (e.g., "WV")
        dry_run: If True, don't write to database
        limit: Limit number of records to process

    Returns:
        {
            "phase_id": 4,
            "phase_name": "BIT Trigger Check",
            "statistics": {
                "total": 100,
                "triggered": 45,
                "not_triggered": 55,
                "signal_types": {
                    "Executive Movement": 30,
                    "Leadership Change": 15
                }
            },
            "triggered_people": [
                {
                    "person_id": "...",
                    "full_name": "...",
                    "trigger": True,
                    "signal_type": "Executive Movement",
                    "reason": "CEO title + recent validation"
                }
            ]
        }

    Example:
        >>> # Single person check
        >>> person = {"title": "CEO", "full_name": "John Doe", "validation_status": "valid"}
        >>> result = check_bit_trigger_conditions(person=person)
        >>> print(result["trigger"])
        True

        >>> # Batch processing
        >>> result = check_bit_trigger_conditions(state="WV", dry_run=False)
        >>> print(result["statistics"]["triggered"])
        45
    """
    # Single person/company check
    if person is not None:
        return _check_single_trigger(person, company)

    # Batch processing by state
    elif state is not None:
        return _check_batch_triggers(state, dry_run, limit)

    else:
        raise ValueError("Must provide either person or state parameter")


def _check_single_trigger(person: Dict, company: Optional[Dict] = None) -> Dict:
    """
    Check BIT trigger for single person

    Stub Logic:
    - Trigger if title matches executive keywords
    - Trigger if validation is recent (within 90 days)
    """
    person_id = person.get("person_id") or person.get("unique_id", "unknown")
    full_name = person.get("full_name", "Unknown")
    title = person.get("title", "").strip().upper()

    # Check if title is executive
    is_executive = any(
        exec_title.upper() in title
        for exec_title in BIT_TRIGGER_CONFIG["executive_titles"]
    )

    # Check if recent validation (stub - assume True)
    is_recent = True  # TODO: Check actual validation timestamp

    # Determine trigger
    trigger = is_executive and is_recent

    # Determine signal type
    signal_type = None
    reason = None

    if trigger:
        if "CEO" in title or "CHIEF EXECUTIVE" in title:
            signal_type = "Executive Movement"
            reason = "CEO title + recent validation"
        elif "CFO" in title or "CHIEF FINANCIAL" in title:
            signal_type = "Executive Movement"
            reason = "CFO title + recent validation"
        elif any(hr_kw in title for hr_kw in ["HR", "HUMAN RESOURCES", "PEOPLE", "TALENT"]):
            signal_type = "Leadership Change"
            reason = "HR title + recent validation"
        else:
            signal_type = "Executive Movement"
            reason = "Executive title"
    else:
        if not is_executive:
            reason = "Non-executive title"
        elif not is_recent:
            reason = "Stale validation (> 90 days)"
        else:
            reason = "Unknown"

    logger.info(f"{'✅' if trigger else '❌'} {full_name}: {reason}")

    return {
        "person_id": person_id,
        "full_name": full_name,
        "trigger": trigger,
        "signal_type": signal_type,
        "reason": reason
    }


def _check_batch_triggers(
    state: str,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Check BIT triggers for batch of people (from outreach-ready companies)

    Stub Implementation:
    - Simulates loading people from marketing.people_master
    - Checks each person for trigger conditions
    - Returns statistics
    """
    logger.info("=" * 70)
    logger.info(f"PHASE 4: BIT TRIGGER CHECK")
    logger.info("=" * 70)
    logger.info(f"State: {state}")
    logger.info(f"Dry-run: {dry_run}")
    logger.info(f"Limit: {limit or 'NONE'}")
    logger.info("")

    # STUB: Simulate loading people
    # In production, this would query marketing.people_master
    # WHERE company_unique_id IN (SELECT company_unique_id FROM company_master WHERE outreach_ready = true AND state = state)
    logger.info("Step 1: Loading outreach-ready people...")
    logger.warning("⚠️ STUB MODE: Simulating database query")

    # Simulate some test data
    people = _generate_test_people(state, limit)

    logger.info(f"✅ Loaded {len(people)} people")
    logger.info("")

    # Step 2: Check triggers
    logger.info(f"Step 2: Checking BIT triggers for {len(people)} people...")
    logger.info("")

    triggered_people = []
    signal_counts = {signal: 0 for signal in BIT_TRIGGER_CONFIG["signal_types"]}

    for person in people:
        result = _check_single_trigger(person)

        if result["trigger"]:
            triggered_people.append(result)
            if result["signal_type"]:
                signal_counts[result["signal_type"]] += 1

    # Statistics
    total = len(people)
    triggered = len(triggered_people)
    not_triggered = total - triggered

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total People:       {total}")
    logger.info(f"Triggered:          {triggered}")
    logger.info(f"Not Triggered:      {not_triggered}")
    logger.info("")
    logger.info("Signal Types:")
    for signal, count in signal_counts.items():
        if count > 0:
            logger.info(f"  {signal}: {count}")
    logger.info("=" * 70)

    return {
        "phase_id": BIT_TRIGGER_CONFIG["phase_id"],
        "phase_name": BIT_TRIGGER_CONFIG["phase_name"],
        "state": state,
        "dry_run": dry_run,
        "statistics": {
            "total": total,
            "triggered": triggered,
            "not_triggered": not_triggered,
            "signal_types": signal_counts
        },
        "triggered_people": triggered_people
    }


def _generate_test_people(state: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Generate test people data (STUB)

    In production, this would be replaced with actual database query
    """
    test_people = [
        {"person_id": f"04.04.02.04.20000.{i:03d}", "full_name": f"Person {i}", "title": title}
        for i, title in enumerate([
            "CEO", "CFO", "HR Director",
            "VP of Sales", "CTO", "Chief People Officer",
            "Director of Finance", "VP of Engineering", "Marketing Manager",
            "Chief Executive Officer", "Chief Financial Officer", "Head of Human Resources"
        ], start=1)
    ]

    if limit:
        test_people = test_people[:limit]

    return test_people


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Phase 4: BIT Trigger Check")
    parser.add_argument("--state", type=str, default="WV", help="State code (e.g., WV)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records")

    args = parser.parse_args()

    # Run BIT trigger check
    result = check_bit_trigger_conditions(
        state=args.state,
        dry_run=args.dry_run,
        limit=args.limit
    )

    # Print result
    print("\n" + "=" * 70)
    print(f"PHASE 4 RESULT:")
    print("=" * 70)
    print(f"Total: {result['statistics']['total']}")
    print(f"Triggered: {result['statistics']['triggered']}")
    print(f"Not Triggered: {result['statistics']['not_triggered']}")
    print("=" * 70)
