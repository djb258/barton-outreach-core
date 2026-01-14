"""
People Intelligence Hub - Enrichment Module
============================================
External enrichment integrations for person data.

Available Providers:
    - Prospeo: Person enrichment with verified emails (replaces Clay)
"""

from .prospeo_enrichment import (
    ProspeoClient,
    ProspeoEnrichmentRequest,
    ProspeoPersonResult,
    ProspeoEnrichmentStats,
    enrich_from_csv,
    enrich_from_neon,
)

__all__ = [
    'ProspeoClient',
    'ProspeoEnrichmentRequest',
    'ProspeoPersonResult',
    'ProspeoEnrichmentStats',
    'enrich_from_csv',
    'enrich_from_neon',
]
