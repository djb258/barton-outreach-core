"""
People -> Company Egress
=========================
Passes slot assignment status from People Hub to Company Hub.

Contract: CONTRACT-CO-PEOPLE (egress direction)
Trigger: slot_assigned_or_vacated

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SlotAssignmentPayload:
    """Payload for slot assignment message."""
    company_id: str
    slot_type: str
    person_id: str
    is_filled: bool
    fill_quality_score: Optional[float] = None
    movement_alert: Optional[str] = None


class SlotAssignmentsEgress:
    """
    I/O-only egress spoke for slot assignments.

    Routes slot assignment status from People Hub to Company Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, company_hub_input):
        """
        Args:
            company_hub_input: Reference to Company Hub input layer
        """
        self._company_hub_input = company_hub_input

    def route(self, payload: SlotAssignmentPayload) -> None:
        """
        Route slot assignment to Company Hub.

        Args:
            payload: Slot assignment data (pass-through)
        """
        # PASS-THROUGH ONLY - no transformation
        self._company_hub_input.receive_slot_assignment(payload)
