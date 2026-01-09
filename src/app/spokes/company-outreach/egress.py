"""
Outreach -> Company Egress
===========================
Passes engagement signals from Outreach Hub to Company Hub.

Contract: CONTRACT-CO-OUTREACH (egress direction)
Trigger: engagement_event_or_campaign_completed

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EngagementSignalPayload:
    """Payload for engagement signal."""
    company_id: str
    opens: int
    replies: int
    campaign_outcome: str
    response_sentiment: Optional[str] = None


class EngagementSignalEgress:
    """
    I/O-only egress spoke for engagement signals.

    Routes engagement signals from Outreach Hub to Company Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, company_hub_input):
        self._company_hub_input = company_hub_input

    def route(self, payload: EngagementSignalPayload) -> None:
        self._company_hub_input.receive_engagement_signal(payload)
