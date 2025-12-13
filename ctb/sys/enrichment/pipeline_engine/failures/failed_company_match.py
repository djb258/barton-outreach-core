"""
Failed Company Match - Failure Spoke
====================================
Handles records that failed company fuzzy matching (< 80%).

Resolution Paths:
    - manual_review: Human confirms/rejects/remaps
    - firecrawl_enrich: Try to get more company data
    - auto_retry: Retry with relaxed threshold
"""

from ..wheel.wheel_result import FailureType
from .base_failure_spoke import BaseFailureSpoke


class FailedCompanyMatchSpoke(BaseFailureSpoke):
    """
    Failed Company Match - Phase 2 Failure Spoke.

    Trigger: Fuzzy match score < 80%
    Table: marketing.failed_company_match
    """

    def __init__(self):
        super().__init__(
            name="failed_company_match",
            failure_type=FailureType.NO_MATCH,
            table_name="marketing.failed_company_match",
            resolution_path="manual_review",
            severity="warning",
            retry_eligible=True,
            max_retries=2
        )
