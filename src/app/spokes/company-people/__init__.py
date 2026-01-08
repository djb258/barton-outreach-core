"""
Company <-> People Spoke Connector
===================================
Implements CONTRACT-CO-PEOPLE

Bidirectional I/O between Company Intelligence Hub and People Intelligence Hub.

Ingress (Company -> People):
    - slot_requirements: Slot requirements for roles needed
    - Identity: company_id + slot_type

Egress (People -> Company):
    - slot_assignments: Slot assignment status
    - Identity: company_id + slot_type + person_id
"""

from .ingress import SlotRequirementsIngress
from .egress import SlotAssignmentsEgress

__all__ = [
    'SlotRequirementsIngress',
    'SlotAssignmentsEgress',
]
