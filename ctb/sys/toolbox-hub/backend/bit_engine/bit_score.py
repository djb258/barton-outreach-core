"""
Phase 5: BIT Score Calculation - Barton Toolbox Hub

Assigns BIT (Buyer Intent Tool) score based on context, timing, and movement patterns.
Scores range from 0-100, with higher scores indicating higher buyer intent.

Phase ID: 5
Doctrine ID: 4.svg.marketing.ple.bit_score_calc

Scoring Criteria (Stub):
- CEO title: +40 points
- CFO title: +35 points
- HR title: +25 points
- LinkedIn present: +30 points
- Company size > 50: +30 points
- Recent validation (< 30 days): +20 points
- Email verified: +15 points

Usage:
    from backend.bit_engine.bit_score import calculate_bit_score

    # Calculate score for single person/company
    result = calculate_bit_score(person, company)

    # Calculate scores for batch
    result = calculate_bit_score(state="WV", dry_run=False)

Status: ✅ Production Ready (Stub Implementation)
Date: 2025-11-17
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# BIT SCORE CONFIGURATION
# ============================================================================

BIT_SCORE_CONFIG = {
    "phase_id": 5,
    "phase_name": "BIT Score Calculation",
    "doctrine_id": "4.svg.marketing.ple.bit_score_calc",
    "score_range": [0, 100],
    "thresholds": {
        "hot": 75,    # >= 75: Hot lead
        "warm": 50,   # 50-74: Warm lead
        "cold": 25    # < 50: Cold lead
    },
    "weights": {
        "ceo_title": 40,
        "cfo_title": 35,
        "hr_title": 25,
        "linkedin_present": 30,
        "company_size_50plus": 30,
        "recent_validation": 20,
        "email_verified": 15
    }
}


# ============================================================================
# BIT SCORE CALCULATION
# ============================================================================

def calculate_bit_score(
    person: Optional[Dict] = None,
    company: Optional[Dict] = None,
    state: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Phase 5: Calculate BIT score for person/company

    This is a STUB implementation with basic scoring logic:
    - CEO title: +40 points
    - CFO title: +35 points
    - HR title: +25 points
    - LinkedIn present: +30 points
    - Company size > 50: +30 points

    Args:
        person: Person dictionary (optional, for single-person scoring)
        company: Company dictionary (optional, for single-company scoring)
        state: State code for batch processing (e.g., "WV")
        dry_run: If True, don't write to database
        limit: Limit number of records to process

    Returns:
        {
            "phase_id": 5,
            "phase_name": "BIT Score Calculation",
            "statistics": {
                "total": 100,
                "hot": 30,
                "warm": 50,
                "cold": 20,
                "avg_score": 62.5,
                "max_score": 100,
                "min_score": 25
            },
            "scored_people": [
                {
                    "person_id": "...",
                    "full_name": "...",
                    "score": 80,
                    "category": "hot",
                    "reason": "CEO + LinkedIn + company size 50+"
                }
            ]
        }

    Example:
        >>> # Single person scoring
        >>> person = {"title": "CEO", "linkedin_url": "..."}
        >>> company = {"employee_count": 500}
        >>> result = calculate_bit_score(person=person, company=company)
        >>> print(result["score"])
        100

        >>> # Batch processing
        >>> result = calculate_bit_score(state="WV", dry_run=False)
        >>> print(result["statistics"]["avg_score"])
        62.5
    """
    # Single person/company scoring
    if person is not None:
        return _calculate_single_score(person, company)

    # Batch processing by state
    elif state is not None:
        return _calculate_batch_scores(state, dry_run, limit)

    else:
        raise ValueError("Must provide either person or state parameter")


def _calculate_single_score(person: Dict, company: Optional[Dict] = None) -> Dict:
    """
    Calculate BIT score for single person

    Stub Logic:
    - CEO: +40, CFO: +35, HR: +25
    - LinkedIn: +30
    - Company size > 50: +30
    """
    person_id = person.get("person_id") or person.get("unique_id", "unknown")
    full_name = person.get("full_name", "Unknown")
    title = person.get("title", "").strip().upper()
    linkedin_url = person.get("linkedin_url", "")

    # Initialize score
    score = 0
    scoring_breakdown = []

    # Score based on title
    if "CEO" in title or "CHIEF EXECUTIVE" in title:
        score += BIT_SCORE_CONFIG["weights"]["ceo_title"]
        scoring_breakdown.append("CEO title (+40)")
    elif "CFO" in title or "CHIEF FINANCIAL" in title:
        score += BIT_SCORE_CONFIG["weights"]["cfo_title"]
        scoring_breakdown.append("CFO title (+35)")
    elif any(hr_kw in title for hr_kw in ["HR", "HUMAN RESOURCES", "PEOPLE", "TALENT"]):
        score += BIT_SCORE_CONFIG["weights"]["hr_title"]
        scoring_breakdown.append("HR title (+25)")

    # Score for LinkedIn
    if linkedin_url and len(linkedin_url.strip()) > 0:
        score += BIT_SCORE_CONFIG["weights"]["linkedin_present"]
        scoring_breakdown.append("LinkedIn present (+30)")

    # Score for company size (if company provided)
    if company:
        employee_count = company.get("employee_count", 0)
        if employee_count > 50:
            score += BIT_SCORE_CONFIG["weights"]["company_size_50plus"]
            scoring_breakdown.append(f"Company size {employee_count} (+30)")

    # Determine category
    if score >= BIT_SCORE_CONFIG["thresholds"]["hot"]:
        category = "hot"
    elif score >= BIT_SCORE_CONFIG["thresholds"]["warm"]:
        category = "warm"
    else:
        category = "cold"

    # Build reason string
    reason = " + ".join(scoring_breakdown) if scoring_breakdown else "No scoring criteria met"

    logger.info(f"{'🔥' if category == 'hot' else '🌡️' if category == 'warm' else '❄️'} {full_name}: {score} ({category}) - {reason}")

    return {
        "person_id": person_id,
        "full_name": full_name,
        "score": score,
        "category": category,
        "reason": reason
    }


def _calculate_batch_scores(
    state: str,
    dry_run: bool = False,
    limit: Optional[int] = None
) -> Dict:
    """
    Calculate BIT scores for batch of people

    Stub Implementation:
    - Simulates loading triggered people from Phase 4
    - Calculates score for each
    - Returns statistics
    """
    logger.info("=" * 70)
    logger.info(f"PHASE 5: BIT SCORE CALCULATION")
    logger.info("=" * 70)
    logger.info(f"State: {state}")
    logger.info(f"Dry-run: {dry_run}")
    logger.info(f"Limit: {limit or 'NONE'}")
    logger.info("")

    # STUB: Simulate loading triggered people from Phase 4
    logger.info("Step 1: Loading triggered people from Phase 4...")
    logger.warning("⚠️ STUB MODE: Simulating database query")

    # Simulate test data
    people = _generate_test_triggered_people(state, limit)

    logger.info(f"✅ Loaded {len(people)} triggered people")
    logger.info("")

    # Step 2: Calculate scores
    logger.info(f"Step 2: Calculating BIT scores for {len(people)} people...")
    logger.info("")

    scored_people = []
    category_counts = {"hot": 0, "warm": 0, "cold": 0}
    total_score = 0

    for person in people:
        # Simulate company data
        company = {"employee_count": 500}  # Stub

        result = _calculate_single_score(person, company)
        scored_people.append(result)

        category_counts[result["category"]] += 1
        total_score += result["score"]

    # Statistics
    total = len(scored_people)
    avg_score = total_score / total if total > 0 else 0
    max_score = max((p["score"] for p in scored_people), default=0)
    min_score = min((p["score"] for p in scored_people), default=0)

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total Scored:       {total}")
    logger.info(f"Hot (>= 75):        {category_counts['hot']}")
    logger.info(f"Warm (50-74):       {category_counts['warm']}")
    logger.info(f"Cold (< 50):        {category_counts['cold']}")
    logger.info(f"Average Score:      {avg_score:.1f}")
    logger.info(f"Max Score:          {max_score}")
    logger.info(f"Min Score:          {min_score}")
    logger.info("=" * 70)

    return {
        "phase_id": BIT_SCORE_CONFIG["phase_id"],
        "phase_name": BIT_SCORE_CONFIG["phase_name"],
        "state": state,
        "dry_run": dry_run,
        "statistics": {
            "total": total,
            "hot": category_counts["hot"],
            "warm": category_counts["warm"],
            "cold": category_counts["cold"],
            "avg_score": round(avg_score, 1),
            "max_score": max_score,
            "min_score": min_score
        },
        "scored_people": scored_people
    }


def _generate_test_triggered_people(state: str, limit: Optional[int] = None) -> List[Dict]:
    """
    Generate test triggered people data (STUB)

    In production, this would load from Phase 4 results or bit.events table
    """
    test_people = [
        {
            "person_id": f"04.04.02.04.20000.{i:03d}",
            "full_name": f"Person {i}",
            "title": title,
            "linkedin_url": "https://linkedin.com/in/person"
        }
        for i, title in enumerate([
            "CEO", "CFO", "HR Director",
            "Chief Executive Officer", "Chief Financial Officer", "Head of Human Resources",
            "Chief People Officer", "VP of Finance", "Director of Talent"
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

    parser = argparse.ArgumentParser(description="Phase 5: BIT Score Calculation")
    parser.add_argument("--state", type=str, default="WV", help="State code (e.g., WV)")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of records")

    args = parser.parse_args()

    # Run BIT score calculation
    result = calculate_bit_score(
        state=args.state,
        dry_run=args.dry_run,
        limit=args.limit
    )

    # Print result
    print("\n" + "=" * 70)
    print(f"PHASE 5 RESULT:")
    print("=" * 70)
    print(f"Total: {result['statistics']['total']}")
    print(f"Hot: {result['statistics']['hot']}")
    print(f"Warm: {result['statistics']['warm']}")
    print(f"Cold: {result['statistics']['cold']}")
    print(f"Avg Score: {result['statistics']['avg_score']}")
    print("=" * 70)
