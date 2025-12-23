"""
Company -> Outreach Ingress
============================
Passes target selection from Company Hub to Outreach Hub.

Contract: CONTRACT-CO-OUTREACH (ingress direction)
Trigger: bit_threshold_crossed

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TargetSelectionPayload:
    """Payload for target selection."""
    company_id: str
    bit_score: float
    bit_components: Dict[str, Any]
    campaign_eligibility: bool


class TargetSelectionIngress:
    """
    I/O-only ingress spoke for target selection.

    Routes target selection from Company Hub to Outreach Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, outreach_hub_input):
        self._outreach_hub_input = outreach_hub_input

    def route(self, payload: TargetSelectionPayload) -> None:
        self._outreach_hub_input.receive_target_selection(payload)
