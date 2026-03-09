"""
People Intelligence Hub - Movement Engine
==========================================
Detects and tracks personnel movement (job changes, company changes).

Movement engine belongs to People Hub because:
    - It tracks PEOPLE changing companies
    - Movement events pivot around person records
    - Both old and new company must be valid (validated via Company Hub)

Components:
    - movement_engine.py: Core movement detection
    - movement_rules.py: Movement business rules
    - state_machine.py: Movement state management
"""

from .movement_engine import MovementEngine
from .movement_rules import MovementRules
from .state_machine import StateMachine
from .linkedin_monitor import scan_linkedin_changes, bridge_to_movement_event, LinkedInChange, LinkedInMonitorResult

__all__ = [
    'MovementEngine',
    'MovementRules',
    'StateMachine',
    'scan_linkedin_changes',
    'bridge_to_movement_event',
    'LinkedInChange',
    'LinkedInMonitorResult',
]
