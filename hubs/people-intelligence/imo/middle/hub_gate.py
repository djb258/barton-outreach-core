"""
Hub Gate Spoke - Company Matching
=================================
First spoke in the People Node - validates company anchor.

"IF company_id IS NULL: STOP. Route to Company Identity Pipeline first."
-- The Golden Rule

Match Tiers:
    GOLD (1.0): Domain exact match
    SILVER (0.95): Exact name match

Note: Fuzzy matching (BRONZE tier) removed per doctrine.
"""

from typing import Any, Dict, List, Optional, Tuple
import logging

# PHANTOM IMPORTS - ctb.* module does not exist (commented out per doctrine)
# from ctb.sys.enrichment.pipeline_engine.wheel.bicycle_wheel import Spoke, Hub
# from ctb.sys.enrichment.pipeline_engine.wheel.wheel_result import SpokeResult, ResultStatus, FailureType

# Stub placeholders to prevent NameError
Spoke = Hub = object
SpokeResult = object
class ResultStatus: SUCCEEDED = "SUCCEEDED"; FAILED = "FAILED"
class FailureType: VALIDATION_ERROR = "VALIDATION_ERROR"; NO_MATCH = "NO_MATCH"; LOW_CONFIDENCE = "LOW_CONFIDENCE"


logger = logging.getLogger(__name__)


# Match tier thresholds (fuzzy matching removed per doctrine)
MATCH_TIERS = {
    'GOLD': 1.0,      # Domain exact match
    'SILVER': 0.95,   # Exact name match
}


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
                failure_reason=f"No exact company match found for: {company_name_raw}",
                data=data
            )

        # SUCCESS - Exact match found (fuzzy matching removed per doctrine)
        matched_company = self.companies[match_result['company_id']]
        data.matched_company_id = match_result['company_id']
        data.matched_company_name = matched_company.get('company_name')
        data.matched_domain = matched_company.get('domain')
        data.match_score = match_result['score']

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

        # TIER 3: No fuzzy matching - per doctrine, fuzzy matching removed
        # If exact match fails, return no match
        return {'tier': None, 'score': 0, 'company_id': None, 'collision': False}

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
