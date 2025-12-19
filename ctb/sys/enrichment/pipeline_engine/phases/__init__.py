"""
Pipeline Engine - Phase Modules
===============================
Multi-phase people enrichment pipeline.

Neon Integration:
- Phase 1 supports loading companies from Neon database
- Use match_company_from_neon() for production lookups
"""

from .phase1_company_matching import (
    Phase1CompanyMatching,
    match_single_company,
    match_company_from_neon,
    CompanyMatchResult,
    MatchType,
    Phase1Stats,
)
from .phase1b_unmatched_hold_export import Phase1bUnmatchedHoldExport
from .phase2_domain_resolution import Phase2DomainResolution
from .phase3_email_pattern_waterfall import Phase3EmailPatternWaterfall
from .phase4_pattern_verification import Phase4PatternVerification
from .phase5_email_generation import Phase5EmailGeneration
from .phase6_slot_assignment import Phase6SlotAssignment
from .phase7_enrichment_queue import Phase7EnrichmentQueue
from .phase8_output_writer import Phase8OutputWriter

__all__ = [
    # Phase 1 - Company Matching (with Neon support)
    'Phase1CompanyMatching',
    'match_single_company',
    'match_company_from_neon',
    'CompanyMatchResult',
    'MatchType',
    'Phase1Stats',
    # Other phases
    'Phase1bUnmatchedHoldExport',
    'Phase2DomainResolution',
    'Phase3EmailPatternWaterfall',
    'Phase4PatternVerification',
    'Phase5EmailGeneration',
    'Phase6SlotAssignment',
    'Phase7EnrichmentQueue',
    'Phase8OutputWriter',
]
