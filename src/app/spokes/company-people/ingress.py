"""
Company -> People Ingress
==========================
Passes slot requirements from Company Hub to People Hub.

Contract: CONTRACT-CO-PEOPLE (ingress direction)
Trigger: slot_requirement_created_or_updated

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SlotRequirementPayload:
    """Payload for slot requirement message."""
    company_id: str
    slot_type: str  # CEO, CFO, HR, etc.
    email_pattern: Optional[str] = None
    domain: Optional[str] = None


class SlotRequirementsIngress:
    """
    I/O-only ingress spoke for slot requirements.

    Routes slot requirements from Company Hub to People Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, people_hub_input):
        """
        Args:
            people_hub_input: Reference to People Hub input layer
        """
        self._people_hub_input = people_hub_input

    def route(self, payload: SlotRequirementPayload) -> None:
        """
        Route slot requirement to People Hub.

        Args:
            payload: Slot requirement data (pass-through)
        """
        # PASS-THROUGH ONLY - no transformation
        self._people_hub_input.receive_slot_requirement(payload)
