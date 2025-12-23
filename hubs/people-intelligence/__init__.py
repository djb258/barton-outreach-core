"""
People Intelligence Hub
========================
Owns humans, movement detection, and slot ASSIGNMENTS (not requirements).

Core Entities Owned:
    - people_master
    - slot_assignments (assignments only - requirements are in Company Hub)
    - movement_history
    - enrichment_state

Core Metric: SLOT_FILL_RATE

Doctrine ID: 04.04.02
"""

from .imo.middle.people_hub import PeopleSpoke as PeopleHub
from .imo.middle.slot_assignment import SlotAssignment
from .imo.middle.hub_gate import HubGate

__all__ = [
    'PeopleHub',
    'SlotAssignment',
    'HubGate',
]
