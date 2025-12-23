"""
Signal -> Company Spoke Connector (Ingress Only)
=================================================
Implements CONTRACT-SIGNAL-CO

Unidirectional ingress spoke from Signal Intake to Company Intelligence Hub.
Handles external signals (news, blog mentions, competitor intel).

This is NOT a hub - it's a pure pass-through spoke.

Ingress ONLY (Signal -> Company):
    - external_signal: External signal data
    - Identity: domain, company_name (optional)

NO EGRESS - This spoke is ingress-only.
"""

from .ingress import ExternalSignalIngress

__all__ = [
    'ExternalSignalIngress',
]
