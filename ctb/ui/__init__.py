"""
CTB UI Module
=============

User-facing components for the Barton Outreach system.

DOCTRINE:
    - UI NEVER bypasses kill switches
    - All status reads through CheckboxEngine
    - All writes through official override functions
"""

from .checkbox_engine import (
    MarketingTier,
    TIER_NAMES,
    CompanyStatus,
    OverrideRequest,
    OverrideResult,
    CheckboxEngine,
)

__all__ = [
    'MarketingTier',
    'TIER_NAMES',
    'CompanyStatus',
    'OverrideRequest',
    'OverrideResult',
    'CheckboxEngine',
]
