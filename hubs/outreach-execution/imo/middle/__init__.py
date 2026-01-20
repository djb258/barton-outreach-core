"""
Outreach Execution Hub - Middle Layer
======================================
Core business logic for Outreach Execution Hub.

Components:
    - outreach_hub.py: Core hub logic for campaign execution
    - marketing_safety_gate.py: HARD FAIL safety enforcement (MANDATORY)
"""

from .outreach_hub import OutreachSpoke as OutreachHub
from .marketing_safety_gate import (
    MarketingSafetyGate,
    MarketingEligibilityResult,
    SendAttemptAuditRecord,
    SendAttemptStatus,
    # HARD FAIL errors
    MarketingSafetyError,
    IneligibleTierError,
    MarketingDisabledError,
    ActiveOverrideError,
    EligibilityCheckError,
)

__all__ = [
    'OutreachHub',
    # Safety Gate (ENFORCEMENT - MANDATORY)
    'MarketingSafetyGate',
    'MarketingEligibilityResult',
    'SendAttemptAuditRecord',
    'SendAttemptStatus',
    # HARD FAIL errors
    'MarketingSafetyError',
    'IneligibleTierError',
    'MarketingDisabledError',
    'ActiveOverrideError',
    'EligibilityCheckError',
]
