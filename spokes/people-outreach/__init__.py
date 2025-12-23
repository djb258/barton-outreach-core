"""
People <-> Outreach Spoke Connector
====================================
Implements CONTRACT-PEOPLE-OUTREACH

Bidirectional I/O between People Intelligence Hub and Outreach Execution Hub.

Ingress (People -> Outreach):
    - contact_selection: Contact info for campaigns
    - Identity: company_id + slot_type + person_id

Egress (Outreach -> People):
    - contact_state: Contact outcome and state updates
    - Identity: person_id
"""

from .ingress import ContactSelectionIngress
from .egress import ContactStateEgress

__all__ = [
    'ContactSelectionIngress',
    'ContactStateEgress',
]
