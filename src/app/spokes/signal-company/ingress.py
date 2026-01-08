"""
Signal -> Company Ingress (INGRESS ONLY)
=========================================
Passes external signals from Signal Intake to Company Hub.

Contract: CONTRACT-SIGNAL-CO (ingress only - no egress)
Trigger: signal_received

NO LOGIC. NO STATE. PASS-THROUGH ONLY.
NO TRANSFORMATION. NO SCORING. NO STORAGE.
"""

from dataclasses import dataclass
from typing import Optional, Any
from datetime import datetime


@dataclass
class ExternalSignalPayload:
    """Payload for external signal."""
    domain: str
    signal_type: str
    signal_source: str
    raw_content: Any
    timestamp: datetime
    company_name: Optional[str] = None


class ExternalSignalIngress:
    """
    I/O-only ingress spoke for external signals.

    Routes external signals to Company Hub.
    NO transformation. NO logic. NO state.
    NO scoring. NO storage.
    """

    def __init__(self, company_hub_input):
        self._company_hub_input = company_hub_input

    def route(self, payload: ExternalSignalPayload) -> None:
        self._company_hub_input.receive_external_signal(payload)
