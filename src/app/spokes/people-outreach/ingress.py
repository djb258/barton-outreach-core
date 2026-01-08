"""
People -> Outreach Ingress
===========================
Passes contact selection from People Hub to Outreach Hub.

Contract: CONTRACT-PEOPLE-OUTREACH (ingress direction)
Trigger: contact_requested_for_campaign

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ContactSelectionPayload:
    """Payload for contact selection."""
    company_id: str
    slot_type: str
    person_id: str
    email: str
    full_name: str
    contact_readiness: str


class ContactSelectionIngress:
    """
    I/O-only ingress spoke for contact selection.

    Routes contact selection from People Hub to Outreach Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, outreach_hub_input):
        self._outreach_hub_input = outreach_hub_input

    def route(self, payload: ContactSelectionPayload) -> None:
        self._outreach_hub_input.receive_contact_selection(payload)
