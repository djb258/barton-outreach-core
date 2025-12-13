"""
People Node - Spoke #1
======================
Handles people data: titles, emails, slot assignments.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    PEOPLE NODE                               │
    │                    (Spoke #1)                                │
    ├─────────────────────────────────────────────────────────────┤
    │                                                             │
    │   ┌─────────────────┐   ┌─────────────────┐                 │
    │   │ FUZZY_MATCHING  │   │ SLOT_ASSIGNMENT │                 │
    │   │ (company gate)  │   │ (seniority)     │                 │
    │   └─────────────────┘   └─────────────────┘                 │
    │                                                             │
    │   ┌─────────────────────────────────────────────────┐       │
    │   │         EMAIL_VERIFICATION SUB-WHEEL            │       │
    │   │   ┌───────────────────────────────────────┐     │       │
    │   │   │        MILLIONVERIFIER (Hub)          │     │       │
    │   │   └───────────────────────────────────────┘     │       │
    │   │   pattern_guesser (FREE)                        │       │
    │   │   bulk_verifier ($37/10K)                       │       │
    │   └─────────────────────────────────────────────────┘       │
    │                                                             │
    └─────────────────────────────────────────────────────────────┘

Failure Spokes:
    - FAILED_COMPANY_MATCH: Fuzzy < 80%
    - FAILED_LOW_CONFIDENCE: Fuzzy 70-79%
    - FAILED_SLOT_ASSIGNMENT: Lost seniority
    - FAILED_NO_PATTERN: No domain/pattern
    - FAILED_EMAIL_VERIFICATION: MV invalid
"""

from .people_node_spoke import PeopleNodeSpoke
from .hub_gate_spoke import HubGateSpoke
from .slot_assignment_spoke import SlotAssignmentSpoke

__all__ = ['PeopleNodeSpoke', 'HubGateSpoke', 'SlotAssignmentSpoke']
