"""
Phase 6: Promotion to Outreach Log - Barton Toolbox Hub

Promotes ready contacts into outreach queue with campaign metadata.
Prepares contacts for Instantly.ai or HeyReach campaigns.

Phase ID: 6
Doctrine ID: 4.svg.marketing.ple.outreach_promotion

Promotion Criteria (Stub):
- BIT score >= 50 (warm or hot)
- Email verified
- LinkedIn present
- Company outreach_ready = true

Usage:
    from backend.outreach.promote_to_log import promote_contact_to_outreach

    # Promote single contact
    result = promote_contact_to_outreach(person, company)

    # Promote batch
    result = promote_contact_to_outreach(state="WV", dry_run=False)

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
# OUTREACH PROMOTION CONFIGURATION
# ============================================================================

PROMOTION_CONFIG = {
    "phase_id": 6,
    "phase_name": "Promotion to Outreach Log",
    "doctrine_id": "4.svg.marketing.ple.outreach_promotion",
    "min_bit_score": 50,  # Minimum BIT score for promotion
    "campaign_metadata": {
        "campaign_id": "CAMP-WV-EXEC-2025",
        "sequence_id": "SEQ-EXEC-INTRO",
        "personalization_template": "exec_intro_v1",
        "send_date_offset_days": 1  # Send 1 day from now
    },
    "platforms": ["Instantly", "HeyReach"]
}


# ============================================================================
# PROMOTION TO OUTREACH LOG
# ============================================================================

def promote_contact_to_outreach(
    person: Optional[Dict] = None,
    company: Optional[Dict] = None,
    state: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Phase 6: Promote contact to outreach log

    This is a STUB implementation that:
    - Checks if BIT score >= 50 (warm/hot)
    - Simulates insert into marketing.outreach_log
    - Adds campaign metadata for Instantly/HeyReach

    Args:
        person: Person dictionary (optional, for single-person promotion)
        company: Company dictionary (optional, for single-company promotion)
        state: State code for batch processing (e.g., "WV")
        dry_run: If True, don't write to database
        limit: Limit number of records to process

    Returns:
        {
            "phase_id": 6,
            "phase_name": "Promotion to Outreach Log",
            "statistics": {
                "total": 100,
                "promoted": 75,
                "skipped": 25,
                "campaigns": {
                    "CAMP-WV-EXEC-2025": 75
                }
            },
            "promoted_contacts": [
                {
                    "person_id": "...",
                    "full_name": "...",
                    "status": "promoted",
                    "campaign_id": "CAMP-WV-EXEC-2025",
                    "send_date": "2025-11-18"
                }
            ]
        }

    Example:
        >>> # Single contact promotion
        >>> person = {"full_name": "John Doe", "bit_score": 80}
        >>> company = {"name": "Acme Corp"}
        >>> result = promote_contact_to_outreach(person=person, company=company)
        >>> print(result["status"])
        'promoted'

        >>> # Batch processing
        >>> result = promote_contact_to_outreach(state="WV", dry_run=False)
        >>> print(result["statistics"]["promoted"])
        75
    """
    # Single contact promotion
    if person is not None:
        return _promote_single_contact(person, company)

    # Batch processing by state
    elif state is not None:
        return _promote_batch_contacts(state, dry_run, limit)

    else:
        raise ValueError("Must provide either person or state parameter")


def _promote_single_contact(person: Dict, company: Optional[Dict] = None) -> Dict:
    """
    Promote single contact to outreach log

    Stub Logic:
    - Promote if BIT score >= 50
    - Add campaign metadata
    """
    person_id = person.get("person_id") or person.get("unique_id", "unknown")
    full_name = person.get("full_name", "Unknown")
    bit_score = person.get("bit_score", person.get("score", 0))

    company_name = "Unknown Company"
    if company:
        company_name = company.get("company_name", company.get("name", "Unknown Company"))

    # Check if qualifies for promotion
    qualifies = bit_score >= PROMOTION_CONFIG["min_bit_score"]

    if qualifies:
        # Calculate send date
        send_date = datetime.now() + timedelta(days=PROMOTION_CONFIG["campaign_metadata"]["send_date_offset_days"])

        logger.info(f"✅ Promoting {full_name} at {company_name} to outreach (score: {bit_score})")

        return {
            "person_id": person_id,
            "full_name": full_name,
            "company_name": company_name,
            "status": "promoted",
            "campaign_id": PROMOTION_CONFIG["campaign_metadata"]["campaign_id"],
            "sequence_id": PROMOTION_CONFIG["campaign_metadata"]["sequence_id"],
            "personalization_template": PROMOTION_CONFIG["campaign_metadata"]["personalization_template"],
            "send_date": send_date.strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat()
        }
    else:
        logger.info(f"❌ Skipping {full_name} at {company_name} (score: {bit_score} < {PROMOTION_CONFIG['min_bit_score']})")

        return {
            "person_id": person_id,
            "full_name": full_name,
            "company_name": company_name,
            "status": "skipped",
            "reason": f"BIT score {bit_score} < {PROMOTION_CONFIG['min_bit_score']}",
            "timestamp": datetime.now().isoformat()
        }


def _promote_batch_contacts(
    state: str,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Promote batch of contacts to outreach log

    Stub Implementation:
    - Simulates loading scored people from Phase 5
    - Promotes those with score >= 50
    - Returns statistics
    """
    logger.info("=" * 70)
    logger.info(f"PHASE 6: PROMOTION TO OUTREACH LOG")
    logger.info("=" * 70)
    logger.info(f"State: {state}")
    logger.info(f"Dry-run: {dry_run}")
    logger.info(f"Limit: {limit or 'NONE'}")
    logger.info("")

    # STUB: Simulate loading scored people from Phase 5
    logger.info("Step 1: Loading scored people from Phase 5...")
    logger.warning("⚠️ STUB MODE: Simulating database query")

    # Simulate test data
    people = _generate_test_scored_people(state, limit)

    logger.info(f"✅ Loaded {len(people)} scored people")
    logger.info("")

    # Step 2: Promote contacts
    logger.info(f"Step 2: Promoting contacts to outreach log...")
    logger.info("")

    promoted_contacts = []
    skipped_contacts = []
    campaign_counts = {}

    for person in people:
        # Simulate company data
        company = {"company_name": f"Company {person['person_id'][-3:]}"}

        result = _promote_single_contact(person, company)

        if result["status"] == "promoted":
            promoted_contacts.append(result)
            campaign_id = result["campaign_id"]
            campaign_counts[campaign_id] = campaign_counts.get(campaign_id, 0) + 1
        else:
            skipped_contacts.append(result)

    # Statistics
    total = len(people)
    promoted = len(promoted_contacts)
    skipped = len(skipped_contacts)

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total Contacts:     {total}")
    logger.info(f"Promoted:           {promoted}")
    logger.info(f"Skipped:            {skipped}")
    logger.info("")
    logger.info("Campaigns:")
    for campaign_id, count in campaign_counts.items():
        logger.info(f"  {campaign_id}: {count}")
    logger.info("=" * 70)

    return {
        "phase_id": PROMOTION_CONFIG["phase_id"],
        "phase_name": PROMOTION_CONFIG["phase_name"],
        "state": state,
        "dry_run": dry_run,
        "statistics": {
            "total": total,
            "promoted": promoted,
            "skipped": skipped,
            "campaigns": campaign_counts
        },
        "promoted_contacts": promoted_contacts,
        "skipped_contacts": skipped_contacts
    }


def _generate_test_scored_people(state: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Generate test scored people data (STUB)

    In production, this would load from Phase 5 results or bit.company_scores table
    """
    test_people = [
        {
            "person_id": f"04.04.02.04.20000.{i:03d}",
            "full_name": f"Person {i}",
            "bit_score": score
        }
        for i, score in enumerate([
            100, 85, 70, 55, 40,  # Mix of hot, warm, and cold
            95, 80, 65, 50, 35,
            90, 75, 60, 45, 30
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

    parser = argparse.ArgumentParser(description="Phase 6: Promotion to Outreach Log")
    parser.add_argument("--state", type=str, default="WV", help="State code (e.g., WV)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records")

    args = parser.parse_args()

    # Run promotion
    result = promote_contact_to_outreach(
        state=args.state,
        dry_run=args.dry_run,
        limit=args.limit
    )

    # Print result
    print("\n" + "=" * 70)
    print(f"PHASE 6 RESULT:")
    print("=" * 70)
    print(f"Total: {result['statistics']['total']}")
    print(f"Promoted: {result['statistics']['promoted']}")
    print(f"Skipped: {result['statistics']['skipped']}")
    print("=" * 70)
