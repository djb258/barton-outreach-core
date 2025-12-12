"""
Sub-Wheels - Fractal Wheels at Spoke Endpoints
==============================================
Spokes can have their own wheels. This is the fractal nature of the architecture.

Email Verification is a sub-wheel of People Node:
    - Hub: MillionVerifier API
    - Spokes: pattern_guesser, bulk_verifier
    - Failure Spokes: invalid_email, timeout_error
"""

from .email_verification import EmailVerificationSubWheel

__all__ = ['EmailVerificationSubWheel']
