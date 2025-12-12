"""
Failed Low Confidence - Failure Spoke
=====================================
Handles records with low confidence fuzzy match (70-79%).

Resolution Paths:
    - manual_confirm: Human confirms the match
    - manual_reject: Human rejects and routes to no_match
    - auto_confirm: Auto-confirm after timeout period
"""

from ..wheel.wheel_result import FailureType
from .base_failure_spoke import BaseFailureSpoke


class FailedLowConfidenceSpoke(BaseFailureSpoke):
    """
    Failed Low Confidence - Phase 3 Failure Spoke.

    Trigger: Fuzzy match score 70-79%
    Table: marketing.failed_low_confidence
    """

    def __init__(self):
        super().__init__(
            name="failed_low_confidence",
            failure_type=FailureType.LOW_CONFIDENCE,
            table_name="marketing.failed_low_confidence",
            resolution_path="manual_confirm",
            severity="info",
            retry_eligible=False,
            max_retries=0
        )
