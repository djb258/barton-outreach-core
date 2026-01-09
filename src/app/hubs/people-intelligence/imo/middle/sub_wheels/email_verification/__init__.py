"""
Email Verification Sub-Wheel
=============================
A fractal sub-wheel of the People Intelligence Hub.

Handles email verification as a complete mini-wheel with its own spokes:
    - bulk_verifier_spoke.py: Bulk email verification
    - email_verification_wheel.py: Wheel orchestration
    - pattern_guesser_spoke.py: Pattern-based email guessing

This is a sub-wheel because email verification is complex enough
to warrant its own hub-and-spoke structure.
"""

from .bulk_verifier_spoke import BulkVerifierSpoke
from .email_verification_wheel import EmailVerificationWheel
from .pattern_guesser_spoke import PatternGuesserSpoke

__all__ = [
    'BulkVerifierSpoke',
    'EmailVerificationWheel',
    'PatternGuesserSpoke',
]
