"""
Spokes - Major Domain Functions
===============================
Each spoke connects to the Company Hub and processes data in its domain.

Architecture:
    DOL NODE ──────────────────●────────────────── PEOPLE NODE
         │                     │                        │
         │               COMPANY HUB                    │
         │              (Central Axle)                  │
         │                     │                        │
    BLOG NODE ─────────────────┴─────────────────── TALENT FLOW

Spoke Registry:
    - people_node: Titles, emails, slot assignments (ACTIVE)
    - dol_node: Form 5500, Schedule A, violations (ACTIVE)
    - blog_node: News, sentiment, events (PLANNED)
    - talent_flow: Movement detection, job changes (SHELL)
    - outreach_node: Campaign targeting (PLANNED)
"""

from .people_node import PeopleNodeSpoke
from .dol_node import DOLNodeSpoke

__all__ = ['PeopleNodeSpoke', 'DOLNodeSpoke']
