"""
Failures - First-Class Failure Spokes
=====================================
"Failures are spokes, not exceptions."
-- Bicycle Wheel Doctrine

Every failure type has:
- Its own database table
- Defined resolution paths
- Can trigger auto-repair
- Reports to Master Failure Hub

Failure Spoke Registry:
    - FailedCompanyMatch: Fuzzy < 80%
    - FailedLowConfidence: Fuzzy 70-79%
    - FailedSlotAssignment: Lost seniority
    - FailedNoPattern: Missing domain/pattern
    - FailedEmailVerification: MV invalid
"""

from .failed_company_match import FailedCompanyMatchSpoke
from .failed_low_confidence import FailedLowConfidenceSpoke
from .failed_slot_assignment import FailedSlotAssignmentSpoke
from .failed_no_pattern import FailedNoPatternSpoke
from .failed_email_verification import FailedEmailVerificationSpoke

__all__ = [
    'FailedCompanyMatchSpoke',
    'FailedLowConfidenceSpoke',
    'FailedSlotAssignmentSpoke',
    'FailedNoPatternSpoke',
    'FailedEmailVerificationSpoke'
]
