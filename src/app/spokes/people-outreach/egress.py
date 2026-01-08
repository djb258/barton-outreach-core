"""
Outreach -> People Egress
==========================
Passes contact state updates from Outreach Hub to People Hub.

Contract: CONTRACT-PEOPLE-OUTREACH (egress direction)
Trigger: send_completed_or_bounce_detected

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class ContactStatePayload:
    """Payload for contact state update."""
    person_id: str
    last_contacted: datetime
    contact_outcome: str
    is_bounced: bool = False
    is_invalid: bool = False


class ContactStateEgress:
    """
    I/O-only egress spoke for contact state.

    Routes contact state from Outreach Hub to People Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, people_hub_input):
        self._people_hub_input = people_hub_input

    def route(self, payload: ContactStatePayload) -> None:
        self._people_hub_input.receive_contact_state(payload)
