"""
DOL -> Company Egress
======================
Passes filing signals from DOL Hub to Company Hub.

Contract: CONTRACT-CO-DOL (egress direction)
Trigger: filing_matched_or_renewal_approaching

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import date


@dataclass
class FilingSignalPayload:
    """Payload for filing signal."""
    ein: str
    company_id: str
    has_5500: bool
    renewal_date: Optional[date] = None
    plan_size: Optional[int] = None


class FilingSignalEgress:
    """
    I/O-only egress spoke for filing signals.

    Routes filing signals from DOL Hub to Company Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, company_hub_input):
        self._company_hub_input = company_hub_input

    def route(self, payload: FilingSignalPayload) -> None:
        self._company_hub_input.receive_filing_signal(payload)
