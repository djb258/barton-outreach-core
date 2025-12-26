"""
Company Intelligence Hub - Email Pattern Discovery
===================================================
Email PATTERN discovery and verification (Company-owned).

- pattern_discovery_pipeline.py: Orchestrates pattern discovery
- pattern_guesser.py: Guesses email patterns from known samples

NOTE: Email GENERATION belongs to People Intelligence Hub.
      Company owns the pattern; People generates actual emails.
"""

from .pattern_discovery_pipeline import PatternDiscoveryPipeline
from .pattern_guesser import PatternGuesser

__all__ = [
    'PatternDiscoveryPipeline',
    'PatternGuesser',
]
