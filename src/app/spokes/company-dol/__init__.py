"""
Company <-> DOL Spoke Connector
================================
Implements CONTRACT-CO-DOL

Bidirectional I/O between Company Intelligence Hub and DOL Filings Hub.

Ingress (Company -> DOL):
    - ein_lookup: EIN lookup requests
    - Identity: company_id, ein (optional)

Egress (DOL -> Company):
    - filing_signal: Filing match and renewal signals
    - Identity: ein + company_id
"""

from .ingress import EINLookupIngress
from .egress import FilingSignalEgress

__all__ = [
    'EINLookupIngress',
    'FilingSignalEgress',
]
