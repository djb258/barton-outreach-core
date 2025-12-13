"""
DOL Node - Spoke #2
===================
Department of Labor federal data integration.

Tables:
    - form_5500: Large plans (>=100 participants)
    - form_5500_sf: Small plans (<100 participants)
    - schedule_a: Insurance broker data

Signals to BIT Engine:
    - FORM_5500_FILED: +5 per relevant filing
    - LARGE_PLAN: +8 for plans with high participant count
    - BROKER_CHANGE: +7 for detected broker changes
"""

from .dol_node_spoke import DOLNodeSpoke

__all__ = ['DOLNodeSpoke']
