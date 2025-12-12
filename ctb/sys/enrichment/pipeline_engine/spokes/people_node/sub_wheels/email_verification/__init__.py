"""
Email Verification Sub-Wheel
============================
A wheel within the People Node spoke - fractal architecture.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │         EMAIL VERIFICATION SUB-WHEEL                        │
    │                                                             │
    │   ┌───────────────────────────────────────────────────┐     │
    │   │           MILLIONVERIFIER (Hub/Axle)              │     │
    │   │              API Key: $37/10K verifications       │     │
    │   └───────────────────────────────────────────────────┘     │
    │                                                             │
    │   PATTERN_GUESSER ─────────●───────── BULK_VERIFIER         │
    │   (FREE - generates)       │         (CHEAP - verifies)     │
    │                            │                                │
    │                    PATTERN_SAVER                            │
    │                   (saves verified)                          │
    │                                                             │
    │   Failure Spokes:                                           │
    │   - invalid_email: MV returns risky/invalid                 │
    │   - timeout_error: API timeout                              │
    │   - rate_limited: API quota exceeded                        │
    └─────────────────────────────────────────────────────────────┘

Cost Tiers:
    - Pattern Guesser: FREE (generates candidates)
    - Bulk Verifier: $37/10K (MillionVerifier batch)
    - Real-time: $0.001/email (MillionVerifier single)
"""

from .email_verification_wheel import EmailVerificationSubWheel
from .pattern_guesser_spoke import PatternGuesserSpoke
from .bulk_verifier_spoke import BulkVerifierSpoke

__all__ = ['EmailVerificationSubWheel', 'PatternGuesserSpoke', 'BulkVerifierSpoke']
