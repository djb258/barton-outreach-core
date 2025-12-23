"""
Hub & Spoke Architecture - Hubs Registry
=========================================
Central registry for all hubs in the Barton Outreach system.

Architecture follows the Bicycle Wheel Doctrine:
    - Company Intelligence Hub is the AXLE (master node)
    - All other hubs are spoke-connected to Company Hub
    - No sideways hub-to-hub calls (all routing through AXLE)

Hub Registry:
    - company-intelligence: AXLE - Core metric: BIT_SCORE
    - people-intelligence: Sub-hub - Core metric: SLOT_FILL_RATE
    - dol-filings: Sub-hub - Core metric: FILING_MATCH_RATE
    - outreach-execution: Sub-hub - Core metric: ENGAGEMENT_RATE

Doctrine ID Format: 04.04.XX (where XX is hub number)
"""

# AXLE Hub
from .company_intelligence import (
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
