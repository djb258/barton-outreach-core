"""
Failed Slot Assignment - Failure Spoke
======================================
Handles records that lost the seniority competition.

Resolution Paths:
    - wait_for_vacancy: Monitor for slot opening
    - manual_override: Force assignment
    - alternate_slot: Try different slot type
"""

from ..wheel.wheel_result import FailureType
from .base_failure_spoke import BaseFailureSpoke


class FailedSlotAssignmentSpoke(BaseFailureSpoke):
    """
    Failed Slot Assignment - Phase 3 Failure Spoke.

    Trigger: Lost seniority competition for slot
    Table: marketing.failed_slot_assignment
    """

    def __init__(self):
        super().__init__(
            name="failed_slot_assignment",
            failure_type=FailureType.LOST_SLOT,
            table_name="marketing.failed_slot_assignment",
            resolution_path="wait_for_vacancy",
            severity="info",
            retry_eligible=True,  # Can retry when slot becomes available
            max_retries=5
        )
