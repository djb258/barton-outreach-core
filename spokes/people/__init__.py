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

# Lazy imports to avoid circular dependency issues
# The wheel module path needs to be adjusted for production
def __getattr__(name):
    """Lazy import for spoke classes."""
    if name == 'PeopleNodeSpoke':
        from .people_spoke import PeopleNodeSpoke
        return PeopleNodeSpoke
    elif name == 'PersonRecord':
        from .people_spoke import PersonRecord
        return PersonRecord
    elif name == 'HubGateSpoke':
        from .hub_gate import HubGateSpoke
        return HubGateSpoke
    elif name == 'SlotAssignmentSpoke':
        from .slot_assignment import SlotAssignmentSpoke
        return SlotAssignmentSpoke
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ['PeopleNodeSpoke', 'PersonRecord', 'HubGateSpoke', 'SlotAssignmentSpoke']
