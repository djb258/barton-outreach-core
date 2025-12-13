"""
Failed Email Verification - Failure Spoke
==========================================
Handles records where MillionVerifier returned invalid/risky.

Resolution Paths:
    - try_alternate_pattern: Try next pattern in priority list
    - manual_entry: Human provides known email
    - mark_unverifiable: Flag as cannot verify
"""

from ..wheel.wheel_result import FailureType
from .base_failure_spoke import BaseFailureSpoke


class FailedEmailVerificationSpoke(BaseFailureSpoke):
    """
    Failed Email Verification - Phase 5 Failure Spoke.

    Trigger: MillionVerifier returns invalid/disposable
    Table: marketing.failed_email_verification
    """

    def __init__(self):
        super().__init__(
            name="failed_email_verification",
            failure_type=FailureType.EMAIL_INVALID,
            table_name="marketing.failed_email_verification",
            resolution_path="try_alternate_pattern",
            severity="warning",
            retry_eligible=True,  # Can retry with alternate pattern
            max_retries=3  # Try up to 3 different patterns
        )
