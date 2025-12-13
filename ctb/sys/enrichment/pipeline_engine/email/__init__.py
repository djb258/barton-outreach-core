"""
Email Pattern Discovery Module
==============================
Discovers company email patterns using local guessing + bulk verification.

Cost: ~$500-1000 for 67,000 companies (vs $6,700+ with Hunter.io)

Usage:
    # Dry run (no API calls)
    python pattern_discovery_pipeline.py --dry-run --limit 100

    # Full run
    python pattern_discovery_pipeline.py --limit 1000

    # Test pattern guesser
    python pattern_guesser.py

Components:
    - pattern_guesser.py: Generates email pattern variants (FREE)
    - bulk_verifier.py: MillionVerifier integration (~$37/10K)
    - pattern_discovery_pipeline.py: Full orchestration
"""

from .pattern_guesser import (
    generate_all_email_guesses,
    generate_verification_batch,
    estimate_verification_cost,
    parse_full_name,
    PatternType,
    PATTERN_PRIORITY
)

__all__ = [
    'generate_all_email_guesses',
    'generate_verification_batch',
    'estimate_verification_cost',
    'parse_full_name',
    'PatternType',
    'PATTERN_PRIORITY'
]
