"""
Company Intelligence Hub - Phases (1-4)
========================================
Company-owned phases of the enrichment pipeline.

Phase 1: Company Matching - Match raw intake to company_master
Phase 1b: Unmatched Hold Export - Export unmatched records for manual review
Phase 2: Domain Resolution - Resolve company domains via waterfall
Phase 3: Email Pattern Waterfall - Discover email patterns for domain
Phase 4: Pattern Verification - Verify patterns via probe emails

NOTE: Phases 5-8 belong to People Intelligence Hub.
"""

from .phase1_company_matching import Phase1CompanyMatching
from .phase1b_unmatched_hold_export import Phase1bUnmatchedHoldExport
from .phase2_domain_resolution import Phase2DomainResolution
from .phase3_email_pattern_waterfall import Phase3EmailPatternWaterfall
from .phase4_pattern_verification import Phase4PatternVerification

__all__ = [
    'Phase1CompanyMatching',
    'Phase1bUnmatchedHoldExport',
    'Phase2DomainResolution',
    'Phase3EmailPatternWaterfall',
    'Phase4PatternVerification',
]
