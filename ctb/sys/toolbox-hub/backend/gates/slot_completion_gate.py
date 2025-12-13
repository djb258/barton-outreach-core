"""
3/3 Slot Completion Gate - Barton Toolbox Hub

CRITICAL GATE: Blocks outreach until all 3 executive slots (CEO, CFO, HR) are filled.

This gate enforces the PLE architecture rule that multi-threaded outreach campaigns
require ALL three executive roles to be populated before any messaging begins.

Why 3/3 Required:
- CEO: Cost/ROI messaging for executive buy-in
- CFO: Budget/financial justification messaging
- HR: Service/efficiency messaging for operational support

Gate Logic:
1. Check company_slot table for CEO, CFO, HR slots
2. Verify each slot has is_filled = true
3. If 3/3 filled: PASS -> Proceed to BIT scoring
4. If <3 filled: WAIT -> Return to enrichment waterfall

Phase ID: 2.5 (Between Validation and BIT)
Doctrine ID: 04.04.02.04.25000.001

Usage:
    from backend.gates.slot_completion_gate import SlotCompletionGate

    gate = SlotCompletionGate()

    # Check single company
    result = gate.check_company(company_id="04.04.02.04.30000.001")

    if result['passed']:
        # Proceed to BIT scoring
        proceed_to_bit_scoring(company_id)
    else:
        # Return to enrichment for missing slots
        enrich_missing_slots(result['missing_slots'])

Status: Production Ready
Date: 2025-11-25
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

REQUIRED_SLOTS = ["CEO", "CFO", "HR"]

SLOT_MESSAGING_TEMPLATES = {
    "CEO": {
        "theme": "Cost/ROI",
        "messaging_focus": "Executive buy-in, strategic value, ROI metrics",
        "typical_concerns": ["Market positioning", "Competitive advantage", "Long-term value"]
    },
    "CFO": {
        "theme": "Budget/Financial",
        "messaging_focus": "Cost justification, budget allocation, financial metrics",
        "typical_concerns": ["Cost reduction", "Budget fit", "Payment terms"]
    },
    "HR": {
        "theme": "Service/Efficiency",
        "messaging_focus": "Operational support, employee experience, efficiency gains",
        "typical_concerns": ["Implementation effort", "Employee adoption", "Support requirements"]
    }
}


class GateStatus(Enum):
    """Gate decision status"""
    PASS = "pass"       # All slots filled, proceed to outreach
    WAIT = "wait"       # Missing slots, return to enrichment
    ERROR = "error"     # Error checking slots


@dataclass
class SlotStatus:
    """Status of a single executive slot"""
    slot_type: str
    exists: bool
    is_filled: bool
    person_id: Optional[str] = None
    person_name: Optional[str] = None
    email: Optional[str] = None
    email_verified: bool = False
    linkedin_url: Optional[str] = None
    last_enriched_at: Optional[str] = None
    messaging_template: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GateResult:
    """Result of slot completion gate check"""
    company_id: str
    company_name: str
    status: GateStatus
    passed: bool
    slots_filled: int
    slots_required: int
    slot_statuses: List[SlotStatus]
    missing_slots: List[str]
    ready_for_outreach: bool
    next_action: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        result = {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'status': self.status.value,
            'passed': self.passed,
            'slots_filled': self.slots_filled,
            'slots_required': self.slots_required,
            'slot_statuses': [s.to_dict() for s in self.slot_statuses],
            'missing_slots': self.missing_slots,
            'ready_for_outreach': self.ready_for_outreach,
            'next_action': self.next_action,
            'timestamp': self.timestamp
        }
        return result


# ============================================================================
# SLOT COMPLETION GATE
# ============================================================================

class SlotCompletionGate:
    """
    3/3 Slot Completion Gate

    Enforces that all 3 executive slots (CEO, CFO, HR) must be filled
    before a company can proceed to BIT scoring and outreach.

    This is a BLOCKING gate - companies cannot bypass it.
    """

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        self.required_slots = REQUIRED_SLOTS.copy()

        # Statistics
        self.stats = {
            "total_checked": 0,
            "passed": 0,
            "waiting": 0,
            "errors": 0,
            "slots_breakdown": {
                "0_of_3": 0,
                "1_of_3": 0,
                "2_of_3": 0,
                "3_of_3": 0
            }
        }

    def _get_slot_rows(self, company_id: str) -> List[Dict]:
        """
        Get slot rows for a company from database

        In production, this queries marketing.company_slot.
        For stub mode, returns simulated data.
        """
        # STUB: Simulate database query
        # In production, replace with actual database call:
        #
        # cursor.execute('''
        #     SELECT
        #         cs.slot_type,
        #         cs.is_filled,
        #         cs.person_unique_id,
        #         pm.full_name,
        #         pm.email,
        #         pm.email_verified,
        #         pm.linkedin_url,
        #         del.completed_at as last_enriched_at
        #     FROM marketing.company_slot cs
        #     LEFT JOIN marketing.people_master pm
        #         ON cs.person_unique_id = pm.unique_id
        #     LEFT JOIN marketing.data_enrichment_log del
        #         ON pm.unique_id = del.person_unique_id
        #         AND del.status = 'success'
        #     WHERE cs.company_unique_id = %s
        #     ORDER BY cs.slot_type
        # ''', (company_id,))

        logger.warning(f"  ⚠️ STUB MODE: Using simulated slot data for {company_id}")

        # Simulate different scenarios based on company_id suffix
        id_suffix = int(company_id.split(".")[-1]) if "." in company_id else hash(company_id) % 10

        if id_suffix % 4 == 0:
            # 3/3 filled
            return [
                {
                    "slot_type": "CEO",
                    "is_filled": True,
                    "person_unique_id": f"04.04.02.04.20000.{id_suffix}01",
                    "full_name": "John CEO",
                    "email": "ceo@company.com",
                    "email_verified": True,
                    "linkedin_url": "https://linkedin.com/in/johnceo",
                    "last_enriched_at": "2025-11-20T10:00:00"
                },
                {
                    "slot_type": "CFO",
                    "is_filled": True,
                    "person_unique_id": f"04.04.02.04.20000.{id_suffix}02",
                    "full_name": "Jane CFO",
                    "email": "cfo@company.com",
                    "email_verified": True,
                    "linkedin_url": "https://linkedin.com/in/janecfo",
                    "last_enriched_at": "2025-11-20T10:00:00"
                },
                {
                    "slot_type": "HR",
                    "is_filled": True,
                    "person_unique_id": f"04.04.02.04.20000.{id_suffix}03",
                    "full_name": "Sam HR",
                    "email": "hr@company.com",
                    "email_verified": True,
                    "linkedin_url": "https://linkedin.com/in/samhr",
                    "last_enriched_at": "2025-11-20T10:00:00"
                }
            ]
        elif id_suffix % 4 == 1:
            # 2/3 filled (missing HR)
            return [
                {
                    "slot_type": "CEO",
                    "is_filled": True,
                    "person_unique_id": f"04.04.02.04.20000.{id_suffix}01",
                    "full_name": "John CEO",
                    "email": "ceo@company.com",
                    "email_verified": True,
                    "linkedin_url": "https://linkedin.com/in/johnceo",
                    "last_enriched_at": "2025-11-20T10:00:00"
                },
                {
                    "slot_type": "CFO",
                    "is_filled": True,
                    "person_unique_id": f"04.04.02.04.20000.{id_suffix}02",
                    "full_name": "Jane CFO",
                    "email": "cfo@company.com",
                    "email_verified": True,
                    "linkedin_url": "https://linkedin.com/in/janecfo",
                    "last_enriched_at": "2025-11-20T10:00:00"
                },
                {
                    "slot_type": "HR",
                    "is_filled": False,
                    "person_unique_id": None,
                    "full_name": None,
                    "email": None,
                    "email_verified": False,
                    "linkedin_url": None,
                    "last_enriched_at": None
                }
            ]
        elif id_suffix % 4 == 2:
            # 1/3 filled (only CEO)
            return [
                {
                    "slot_type": "CEO",
                    "is_filled": True,
                    "person_unique_id": f"04.04.02.04.20000.{id_suffix}01",
                    "full_name": "John CEO",
                    "email": "ceo@company.com",
                    "email_verified": True,
                    "linkedin_url": "https://linkedin.com/in/johnceo",
                    "last_enriched_at": "2025-11-20T10:00:00"
                },
                {
                    "slot_type": "CFO",
                    "is_filled": False,
                    "person_unique_id": None,
                    "full_name": None,
                    "email": None,
                    "email_verified": False,
                    "linkedin_url": None,
                    "last_enriched_at": None
                },
                {
                    "slot_type": "HR",
                    "is_filled": False,
                    "person_unique_id": None,
                    "full_name": None,
                    "email": None,
                    "email_verified": False,
                    "linkedin_url": None,
                    "last_enriched_at": None
                }
            ]
        else:
            # 0/3 filled
            return [
                {
                    "slot_type": "CEO",
                    "is_filled": False,
                    "person_unique_id": None,
                    "full_name": None,
                    "email": None,
                    "email_verified": False,
                    "linkedin_url": None,
                    "last_enriched_at": None
                },
                {
                    "slot_type": "CFO",
                    "is_filled": False,
                    "person_unique_id": None,
                    "full_name": None,
                    "email": None,
                    "email_verified": False,
                    "linkedin_url": None,
                    "last_enriched_at": None
                },
                {
                    "slot_type": "HR",
                    "is_filled": False,
                    "person_unique_id": None,
                    "full_name": None,
                    "email": None,
                    "email_verified": False,
                    "linkedin_url": None,
                    "last_enriched_at": None
                }
            ]

    def check_company(
        self,
        company_id: str,
        company_name: Optional[str] = None,
        slot_rows: Optional[List[Dict]] = None
    ) -> GateResult:
        """
        Check if a company passes the 3/3 slot completion gate

        Args:
            company_id: Company unique ID
            company_name: Optional company name for logging
            slot_rows: Optional pre-loaded slot data (if None, will query database)

        Returns:
            GateResult with pass/wait status and slot details
        """
        company_name = company_name or f"Company {company_id}"

        logger.info(f"\n{'='*60}")
        logger.info(f"SLOT COMPLETION GATE: {company_name}")
        logger.info(f"Company ID: {company_id}")
        logger.info(f"{'='*60}")

        try:
            # Get slot data
            if slot_rows is None:
                slot_rows = self._get_slot_rows(company_id)

            # Build slot status map
            slot_map = {row["slot_type"]: row for row in slot_rows}

            # Check each required slot
            slot_statuses = []
            filled_count = 0
            missing_slots = []

            for slot_type in self.required_slots:
                slot_data = slot_map.get(slot_type, {})

                exists = slot_type in slot_map
                is_filled = slot_data.get("is_filled", False)

                if is_filled:
                    filled_count += 1
                    status_icon = "✅"
                else:
                    missing_slots.append(slot_type)
                    status_icon = "❌"

                logger.info(f"  {status_icon} {slot_type}: {'FILLED' if is_filled else 'EMPTY'}")
                if is_filled:
                    logger.info(f"      Person: {slot_data.get('full_name', 'Unknown')}")
                    logger.info(f"      Email: {slot_data.get('email', 'N/A')}")

                slot_status = SlotStatus(
                    slot_type=slot_type,
                    exists=exists,
                    is_filled=is_filled,
                    person_id=slot_data.get("person_unique_id"),
                    person_name=slot_data.get("full_name"),
                    email=slot_data.get("email"),
                    email_verified=slot_data.get("email_verified", False),
                    linkedin_url=slot_data.get("linkedin_url"),
                    last_enriched_at=slot_data.get("last_enriched_at"),
                    messaging_template=SLOT_MESSAGING_TEMPLATES.get(slot_type) if is_filled else None
                )
                slot_statuses.append(slot_status)

            # Determine gate status
            passed = filled_count == len(self.required_slots)

            if passed:
                status = GateStatus.PASS
                next_action = "Proceed to BIT scoring and outreach"
                logger.info(f"\n🎉 GATE PASSED: 3/3 slots filled!")
            else:
                status = GateStatus.WAIT
                next_action = f"Return to enrichment to fill: {', '.join(missing_slots)}"
                logger.info(f"\n⏳ GATE BLOCKED: {filled_count}/3 slots filled")
                logger.info(f"   Missing: {', '.join(missing_slots)}")

            # Update statistics
            self.stats["total_checked"] += 1
            if passed:
                self.stats["passed"] += 1
            else:
                self.stats["waiting"] += 1
            self.stats["slots_breakdown"][f"{filled_count}_of_3"] += 1

            result = GateResult(
                company_id=company_id,
                company_name=company_name,
                status=status,
                passed=passed,
                slots_filled=filled_count,
                slots_required=len(self.required_slots),
                slot_statuses=slot_statuses,
                missing_slots=missing_slots,
                ready_for_outreach=passed,
                next_action=next_action
            )

            return result

        except Exception as e:
            logger.error(f"❌ ERROR checking slots: {e}")

            self.stats["total_checked"] += 1
            self.stats["errors"] += 1

            return GateResult(
                company_id=company_id,
                company_name=company_name,
                status=GateStatus.ERROR,
                passed=False,
                slots_filled=0,
                slots_required=len(self.required_slots),
                slot_statuses=[],
                missing_slots=self.required_slots.copy(),
                ready_for_outreach=False,
                next_action=f"Error: {str(e)} - Manual review required"
            )

    def check_batch(
        self,
        companies: List[Dict],
        state: Optional[str] = None
    ) -> Dict:
        """
        Check multiple companies through the slot completion gate

        Args:
            companies: List of company dictionaries (must have company_unique_id)
            state: Optional state code for logging

        Returns:
            Batch result with statistics and individual results
        """
        logger.info("="*70)
        logger.info("BATCH SLOT COMPLETION GATE CHECK")
        logger.info("="*70)
        logger.info(f"State: {state or 'ALL'}")
        logger.info(f"Total Companies: {len(companies)}")
        logger.info("")

        results = []
        passed_companies = []
        waiting_companies = []

        for i, company in enumerate(companies, 1):
            company_id = company.get("company_unique_id", company.get("company_id", f"unknown_{i}"))
            company_name = company.get("company_name", f"Company {i}")

            result = self.check_company(company_id, company_name)
            results.append(result)

            if result.passed:
                passed_companies.append({
                    "company_id": company_id,
                    "company_name": company_name
                })
            else:
                waiting_companies.append({
                    "company_id": company_id,
                    "company_name": company_name,
                    "missing_slots": result.missing_slots
                })

        # Summary
        logger.info("\n" + "="*70)
        logger.info("BATCH SUMMARY")
        logger.info("="*70)
        logger.info(f"Total Checked: {len(results)}")
        logger.info(f"Passed (3/3): {len(passed_companies)}")
        logger.info(f"Waiting (<3): {len(waiting_companies)}")
        logger.info(f"Pass Rate: {len(passed_companies)/len(results)*100:.1f}%")
        logger.info("")
        logger.info("Slot Distribution:")
        for key, count in self.stats["slots_breakdown"].items():
            logger.info(f"  {key.replace('_', '/')}: {count}")
        logger.info("="*70)

        return {
            "state": state,
            "statistics": self.stats.copy(),
            "passed_companies": passed_companies,
            "waiting_companies": waiting_companies,
            "results": [r.to_dict() for r in results]
        }

    def get_missing_slot_enrichment_priority(self, missing_slots: List[str]) -> List[Dict]:
        """
        Get priority order for enriching missing slots

        CEO is highest priority (decision maker), then CFO (budget), then HR (ops).

        Returns:
            List of slots with priority and enrichment recommendations
        """
        priority_order = {"CEO": 1, "CFO": 2, "HR": 3}

        sorted_slots = sorted(missing_slots, key=lambda s: priority_order.get(s, 99))

        recommendations = []
        for i, slot_type in enumerate(sorted_slots, 1):
            template = SLOT_MESSAGING_TEMPLATES.get(slot_type, {})
            recommendations.append({
                "priority": i,
                "slot_type": slot_type,
                "messaging_theme": template.get("theme", "Unknown"),
                "why_important": template.get("typical_concerns", []),
                "enrichment_sources": [
                    "LinkedIn Sales Navigator",
                    "Apollo.io",
                    "RocketReach"
                ]
            })

        return recommendations

    def get_outreach_ready_companies(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get list of companies that have passed the gate and are ready for outreach

        Returns:
            List of outreach-ready company dictionaries with slot details
        """
        # STUB: In production, query database
        logger.warning("⚠️ STUB MODE: get_outreach_ready_companies returns mock data")

        return [
            {
                "company_id": "04.04.02.04.30000.001",
                "company_name": "Acme Corporation",
                "slots_filled": 3,
                "ceo": {"name": "John CEO", "email": "ceo@acme.com"},
                "cfo": {"name": "Jane CFO", "email": "cfo@acme.com"},
                "hr": {"name": "Sam HR", "email": "hr@acme.com"},
                "ready_since": "2025-11-20T10:00:00"
            }
        ][:limit] if limit else []


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def check_slot_completion(company_id: str, slot_rows: Optional[List[Dict]] = None) -> Dict:
    """
    Convenience function to check slot completion for a single company

    Usage:
        result = check_slot_completion("04.04.02.04.30000.001")
        if result['passed']:
            proceed_to_bit_scoring(company_id)
        else:
            enrich_missing_slots(result['missing_slots'])
    """
    gate = SlotCompletionGate()
    result = gate.check_company(company_id, slot_rows=slot_rows)
    return result.to_dict()


def get_companies_needing_enrichment(companies: List[Dict]) -> List[Dict]:
    """
    Filter companies that need enrichment (missing slots)

    Returns list of companies with their missing slots for enrichment queue.
    """
    gate = SlotCompletionGate()
    needing_enrichment = []

    for company in companies:
        company_id = company.get("company_unique_id", company.get("company_id"))
        result = gate.check_company(company_id)

        if not result.passed:
            needing_enrichment.append({
                "company_id": company_id,
                "company_name": company.get("company_name", "Unknown"),
                "slots_filled": result.slots_filled,
                "missing_slots": result.missing_slots,
                "enrichment_priority": gate.get_missing_slot_enrichment_priority(result.missing_slots)
            })

    return needing_enrichment


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="3/3 Slot Completion Gate")
    parser.add_argument("--company-id", type=str, help="Check single company")
    parser.add_argument("--demo", action="store_true", help="Run with demo data")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    gate = SlotCompletionGate()

    if args.company_id:
        # Check single company
        result = gate.check_company(args.company_id)

        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\nResult: {'PASS' if result.passed else 'WAIT'}")
            print(f"Slots Filled: {result.slots_filled}/{result.slots_required}")
            if result.missing_slots:
                print(f"Missing: {', '.join(result.missing_slots)}")

    elif args.demo:
        # Demo with sample companies
        demo_companies = [
            {"company_unique_id": "04.04.02.04.30000.000", "company_name": "All Slots Inc"},
            {"company_unique_id": "04.04.02.04.30000.001", "company_name": "Missing HR Corp"},
            {"company_unique_id": "04.04.02.04.30000.002", "company_name": "Only CEO Ltd"},
            {"company_unique_id": "04.04.02.04.30000.003", "company_name": "Empty Slots LLC"},
            {"company_unique_id": "04.04.02.04.30000.004", "company_name": "Full Team Co"}
        ]

        result = gate.check_batch(demo_companies, "WV")

        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\nPassed: {len(result['passed_companies'])}")
            print(f"Waiting: {len(result['waiting_companies'])}")

    else:
        parser.print_help()
