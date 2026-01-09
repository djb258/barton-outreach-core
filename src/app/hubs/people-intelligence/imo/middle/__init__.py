"""
People Intelligence Hub - Middle Layer
=======================================
Core business logic for People Intelligence Hub.

Phases (People-owned):
    - Phase 5: Email Generation (using Company's pattern)
    - Phase 6: Slot Assignment
    - Phase 7: Enrichment Queue
    - Phase 8: Output Writer

Components:
    - people_hub.py: Core hub logic
    - slot_assignment.py: Slot assignment engine
    - hub_gate.py: Gate validation
    - movement_engine/: Movement detection and tracking
"""

from .people_hub import PeopleSpoke as PeopleHub
from .slot_assignment import SlotAssignment
from .hub_gate import HubGate

__all__ = [
    'PeopleHub',
    'SlotAssignment',
    'HubGate',
]
