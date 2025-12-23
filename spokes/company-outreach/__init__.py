"""
Company <-> Outreach Spoke Connector
=====================================
Implements CONTRACT-CO-OUTREACH

Bidirectional I/O between Company Intelligence Hub and Outreach Execution Hub.

Ingress (Company -> Outreach):
    - target_selection: BIT-qualified companies for campaigns
    - Identity: company_id

Egress (Outreach -> Company):
    - engagement_signal: Campaign engagement results
    - Identity: company_id
"""

from .ingress import TargetSelectionIngress
from .egress import EngagementSignalEgress

__all__ = [
    'TargetSelectionIngress',
    'EngagementSignalEgress',
]
