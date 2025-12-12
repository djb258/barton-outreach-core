"""
Failed No Pattern - Failure Spoke
=================================
Handles records missing domain or email pattern.

Resolution Paths:
    - firecrawl_enrich: Use Firecrawl to discover domain/pattern
    - manual_entry: Human adds pattern manually
    - apollo_lookup: Use Apollo API to find pattern
"""

from ..wheel.wheel_result import FailureType
from .base_failure_spoke import BaseFailureSpoke


class FailedNoPatternSpoke(BaseFailureSpoke):
    """
    Failed No Pattern - Phase 4 Failure Spoke.

    Trigger: Missing domain or email pattern
    Table: marketing.failed_no_pattern
    """

    def __init__(self):
        super().__init__(
            name="failed_no_pattern",
            failure_type=FailureType.NO_PATTERN,
            table_name="marketing.failed_no_pattern",
            resolution_path="firecrawl_enrich",
            severity="warning",
            retry_eligible=True,  # Can retry after enrichment
            max_retries=3
        )
