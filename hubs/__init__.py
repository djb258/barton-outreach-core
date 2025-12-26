"""
Hub & Spoke Architecture - Hubs Registry
=========================================
Central registry for all hubs in the Barton Outreach system.

Architecture follows CL Parent-Child Doctrine:
    - Company Lifecycle (CL) is the PARENT HUB (external repo)
    - Company Target is internal anchor (child sub-hub)
    - All other hubs are spoke-connected through Company Target
    - No sideways hub-to-hub calls

Hub Registry:
    - company-target: Sub-hub (child of CL) - Core metric: BIT_SCORE
    - people-intelligence: Sub-hub - Core metric: SLOT_FILL_RATE
    - dol-filings: Sub-hub - Core metric: FILING_MATCH_RATE
    - outreach-execution: Sub-hub - Core metric: ENGAGEMENT_RATE

Parent Hub (External):
    - company-lifecycle-cl: PARENT - Mints company_unique_id

Doctrine ID Format: 04.04.XX (where XX is hub number)
"""

# Company Target Sub-Hub (receives identity from CL)
from .company_target import (
    CompanyHub,
    CompanyPipeline,
    BITEngine,
    SignalType,
)

# Sub-Hubs
from .people_intelligence import PeopleHub
from .dol_filings import DOLHub
from .outreach_execution import OutreachHub

__all__ = [
    # AXLE
    'CompanyHub',
    'CompanyPipeline',
    'BITEngine',
    'SignalType',
    # Sub-Hubs
    'PeopleHub',
    'DOLHub',
    'OutreachHub',
]
