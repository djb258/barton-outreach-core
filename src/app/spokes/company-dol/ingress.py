"""
Company -> DOL Ingress
=======================
Passes EIN lookup requests from Company Hub to DOL Hub.

Contract: CONTRACT-CO-DOL (ingress direction)
Trigger: new_company_needs_filing_data

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EINLookupPayload:
    """Payload for EIN lookup request."""
    company_id: str
    company_name: str
    ein: Optional[str] = None


class EINLookupIngress:
    """
    I/O-only ingress spoke for EIN lookups.

    Routes EIN lookup requests from Company Hub to DOL Hub.
    NO transformation. NO logic. NO state.
    """

    def __init__(self, dol_hub_input):
        self._dol_hub_input = dol_hub_input

    def route(self, payload: EINLookupPayload) -> None:
        self._dol_hub_input.receive_ein_lookup(payload)
