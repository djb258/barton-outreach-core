"""
Hub Gate Spoke - Company Matching
=================================
First spoke in the People Node - validates company anchor.

"IF company_id IS NULL: STOP. Route to Company Identity Pipeline first."
-- The Golden Rule

Match Tiers:
    GOLD (1.0): Domain exact match
    SILVER (0.95): Exact name match
    BRONZE (0.85-0.92): Fuzzy match with city guardrail
"""

from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz
import logging

from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType


logger = logging.getLogger(__name__)


# Match tier thresholds
MATCH_TIERS = {
    'GOLD': 1.0,      # Domain exact match
    'SILVER': 0.95,   # Exact name match
    'BRONZE': 0.85,   # Fuzzy match minimum
}

FUZZY_THRESHOLD_HIGH = 80  # Green - auto-accept
FUZZY_THRESHOLD_REVIEW = 70  # Yellow - manual review
COLLISION_THRESHOLD = 0.03  # Difference to trigger collision check


class HubGateSpoke(Spoke):
    """
    Hub Gate - Validates company anchor before People Node processing.

    This is the gateway that ensures every person record has a valid
    company anchor before proceeding through the wheel.
    """

    def __init__(self, hub: Hub, companies: Dict[str, Dict]):
        """
        Initialize with company lookup data.

        Args:
            hub: The central hub
            companies: Dict of company_id -> company data
        """
        super().__init__(name="hub_gate", hub=hub)
        self.companies = companies
        self._name_index = self._build_name_index()

    def _build_name_index(self) -> Dict[str, List[str]]:
        """Build normalized name index for fuzzy matching"""
        index = {}
        for company_id, company in self.companies.items():
            name = company.get('company_name', '').lower().strip()
            if name:
                # Group by first few characters for faster lookup
                key = name[:3] if len(name) >= 3 else name
                if key not in index:
                    index[key] = []
                index[key].append(company_id)
        return index

    def process(self, data: Any) -> SpokeResult:
        """
        Match a person's company to the hub.

        Returns success with matched company info or failure with reason.
        """
        if not hasattr(data, 'company_name_raw'):
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.VALIDATION_ERROR,
                failure_reason="Missing company_name_raw field"
            )

        company_name_raw = data.company_name_raw

        # Try matching
        match_result = self.match_company(company_name_raw)

        if match_result['tier'] is None:
            return SpokeResult(
                status=ResultStatus.FAILED,
                failure_type=FailureType.NO_MATCH,
                failure_reason=f"No company match found for: {company_name_raw}",
                data=data
            )

        if match_result['score'] < FUZZY_THRESHOLD_HIGH:
            if match_result['score'] >= FUZZY_THRESHOLD_REVIEW:
                return SpokeResult(
                    status=ResultStatus.FAILED,
                    failure_type=FailureType.LOW_CONFIDENCE,
                    failure_reason=f"Low confidence match ({match_result['score']}%)",
                    data=data,
                    metrics=match_result
                )
            else:
                return SpokeResult(
                    status=ResultStatus.FAILED,
                    failure_type=FailureType.NO_MATCH,
                    failure_reason=f"Score below threshold ({match_result['score']}%)",
                    data=data
                )

        # SUCCESS - Update data with match info
        matched_company = self.companies[match_result['company_id']]
        data.matched_company_id = match_result['company_id']
        data.matched_company_name = matched_company.get('company_name')
        data.matched_domain = matched_company.get('domain')
        data.fuzzy_score = match_result['score']

        return SpokeResult(
            status=ResultStatus.SUCCESS,
            data=data,
            metrics={
                'tier': match_result['tier'],
                'score': match_result['score'],
                'company_id': match_result['company_id']
            }
        )

    def match_company(self, company_name: str) -> Dict[str, Any]:
        """
        Match a company name to the hub.

        Returns:
            {
                'tier': 'GOLD'|'SILVER'|'BRONZE'|None,
                'score': float (0-100),
                'company_id': str|None,
                'collision': bool
            }
        """
        if not company_name:
            return {'tier': None, 'score': 0, 'company_id': None, 'collision': False}

        normalized = company_name.lower().strip()

        # TIER 1: Exact domain match (if domain provided)
        # Not applicable here - domain matching happens in company identity pipeline

        # TIER 2: Exact name match
        for company_id, company in self.companies.items():
            if company.get('company_name', '').lower().strip() == normalized:
                return {
                    'tier': 'SILVER',
                    'score': 95,
                    'company_id': company_id,
                    'collision': False
                }

        # TIER 3: Fuzzy matching
        best_match = None
        second_best = None

        for company_id, company in self.companies.items():
            company_name_db = company.get('company_name', '')
            if not company_name_db:
                continue

            # Use token_set_ratio for better matching with word order variations
            score = fuzz.token_set_ratio(normalized, company_name_db.lower())

            if best_match is None or score > best_match['score']:
                second_best = best_match
                best_match = {
                    'company_id': company_id,
                    'company_name': company_name_db,
                    'score': score
                }
            elif second_best is None or score > second_best['score']:
                second_best = {
                    'company_id': company_id,
                    'company_name': company_name_db,
                    'score': score
                }

        if best_match is None:
            return {'tier': None, 'score': 0, 'company_id': None, 'collision': False}

        # Check for collision (two matches too close)
        collision = False
        if second_best and best_match['score'] > 0:
            score_diff = (best_match['score'] - second_best['score']) / 100
            if score_diff < COLLISION_THRESHOLD and best_match['score'] >= FUZZY_THRESHOLD_REVIEW:
                collision = True
                logger.warning(
                    f"Collision detected: '{company_name}' matches both "
                    f"'{best_match['company_name']}' ({best_match['score']}) and "
                    f"'{second_best['company_name']}' ({second_best['score']})"
                )

        tier = 'BRONZE' if best_match['score'] >= MATCH_TIERS['BRONZE'] * 100 else None

        return {
            'tier': tier,
            'score': best_match['score'],
            'company_id': best_match['company_id'],
            'collision': collision
        }

    def get_match_stats(self) -> Dict[str, int]:
        """Get statistics on match tiers"""
        return {
            'total_companies': len(self.companies),
            'companies_with_domain': sum(
                1 for c in self.companies.values()
                if c.get('domain')
            ),
            'companies_with_pattern': sum(
                1 for c in self.companies.values()
                if c.get('email_pattern')
            )
        }
