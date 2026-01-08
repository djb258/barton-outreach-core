"""
Company Target Sub-Hub - Phases (2-4 Only)
==========================================
Execution prep phases for the Company Target IMO.

DEPRECATED (v3.0):
- Phase 1: Company Matching - MOVED TO CL
- Phase 1b: Unmatched Hold Export - MOVED TO CL

ACTIVE:
- Phase 2: Domain Resolution - Validate domain from spine
- Phase 3: Email Pattern Waterfall - Discover email patterns
- Phase 4: Pattern Verification - Verify patterns via SMTP

NOTE: Company Target operates on outreach_id ONLY.
      It NEVER references sovereign_id or performs matching.

PRIMARY ENTRYPOINT: Use run_company_target_imo() instead of individual phases.
"""

from .phase2_domain_resolution import Phase2DomainResolution
from .phase3_email_pattern_waterfall import Phase3EmailPatternWaterfall
from .phase4_pattern_verification import Phase4PatternVerification

__all__ = [
    'Phase2DomainResolution',
    'Phase3EmailPatternWaterfall',
    'Phase4PatternVerification',
]


# =============================================================================
# TOMBSTONE GUARDS — Prevent resurrection of deleted modules
# =============================================================================
# These stubs exist to provide clear errors if anyone tries to import
# the deleted legacy modules. DO NOT IMPLEMENT THESE.

def __getattr__(name):
    """Tombstone guard for deleted legacy modules."""
    tombstones = {
        'Phase1CompanyMatching': 'Phase 1 (Company Matching) was DELETED in v3.0. Matching is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'phase1_company_matching': 'phase1_company_matching was DELETED in v3.0. Matching is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'Phase1bUnmatchedHoldExport': 'Phase 1b (Unmatched Hold) was DELETED in v3.0. Hold queues are now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'phase1b_unmatched_hold_export': 'phase1b_unmatched_hold_export was DELETED in v3.0. Hold queues are now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
    }
    if name in tombstones:
        raise ImportError(f"DOCTRINE VIOLATION: {tombstones[name]}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
