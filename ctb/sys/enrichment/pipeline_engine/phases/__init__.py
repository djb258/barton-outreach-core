"""
Pipeline Engine - Phase Modules
===============================
Multi-phase people enrichment pipeline.
"""

from .phase1_company_matching import Phase1CompanyMatching
from .phase1b_unmatched_hold_export import Phase1bUnmatchedHoldExport
from .phase2_domain_resolution import Phase2DomainResolution
from .phase3_email_pattern_waterfall import Phase3EmailPatternWaterfall
from .phase4_pattern_verification import Phase4PatternVerification
from .phase5_email_generation import Phase5EmailGeneration
from .phase6_slot_assignment import Phase6SlotAssignment
from .phase7_enrichment_queue import Phase7EnrichmentQueue
from .phase8_output_writer import Phase8OutputWriter

__all__ = [
    'Phase1CompanyMatching',
    'Phase1bUnmatchedHoldExport',
    'Phase2DomainResolution',
    'Phase3EmailPatternWaterfall',
    'Phase4PatternVerification',
    'Phase5EmailGeneration',
    'Phase6SlotAssignment',
    'Phase7EnrichmentQueue',
    'Phase8OutputWriter',
]
