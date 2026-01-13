"""
Company Target Sub-Hub - Utilities
==================================
Shared utilities for Company Target IMO.

DEPRECATED (v3.0):
- fuzzy.py - MOVED TO CL (matching is CL's job)
- fuzzy_arbitration.py - MOVED TO CL

ACTIVE:
- config.py - Configuration settings
- logging.py - Logging utilities
- normalization.py - String normalization
- patterns.py - Email pattern utilities
- providers.py - API provider utilities
- verification.py - Verification utilities

NOTE: Fuzzy matching is PERMANENTLY REMOVED from Company Target.
      It is now owned by Company Lifecycle (CL).
"""

from .config import *
from .logging import *
from .normalization import *
from .patterns import *
from .providers import *
from .verification import *


# =============================================================================
# TOMBSTONE GUARDS — Prevent resurrection of deleted modules
# =============================================================================
# These stubs exist to provide clear errors if anyone tries to import
# the deleted fuzzy modules. DO NOT IMPLEMENT THESE.

def __getattr__(name):
    """Tombstone guard for deleted fuzzy modules."""
    tombstones = {
        'fuzzy': 'fuzzy.py was DELETED in v3.0. Fuzzy matching is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'FuzzyMatcher': 'FuzzyMatcher was DELETED in v3.0. Fuzzy matching is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'fuzzy_arbitration': 'fuzzy_arbitration.py was DELETED in v3.0. Fuzzy arbitration is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'FuzzyArbitrator': 'FuzzyArbitrator was DELETED in v3.0. Fuzzy arbitration is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'match_company': 'match_company was DELETED in v3.0. Company matching is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
        'resolve_ambiguity': 'resolve_ambiguity was DELETED in v3.0. Ambiguity resolution is now owned by Company Lifecycle (CL). See ADR-CT-IMO-001.',
    }
    if name in tombstones:
        raise ImportError(f"DOCTRINE VIOLATION: {tombstones[name]}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
