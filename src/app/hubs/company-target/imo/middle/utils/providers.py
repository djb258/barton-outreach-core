"""
Provider Utilities - Hub Company Module
=======================================
Wrapper module that imports from the central provider implementation.

This module re-exports all provider classes and utilities from
ctb/sys/enrichment/pipeline_engine/utils/providers.py for use in
the Company Hub pipeline phases.

Tools covered:
- Tool 6: Pattern Discovery (provider waterfall)
- Tool 7: Pattern Generator (uses provider results)

Provider Tiers (per Pipeline Tool Doctrine):
- Tier 0: Free (Firecrawl, Google Places, Web Scraper)
- Tier 1: Low Cost (Hunter, Clearbit, Apollo)
- Tier 2: Premium (Prospeo, Snov, Clay)

Principle: Deterministic → Fuzzy → LLM (last resort only)
NO LLM ALLOWED in pattern discovery - all providers are deterministic.
"""

import os
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# =============================================================================
# Import from central provider implementation
# =============================================================================

try:
    from ctb.sys.enrichment.pipeline_engine.utils.providers import (
        # Enums
        ProviderTier,
        ProviderStatus,
        # Data classes
        EmailSample,
        ProviderResult,
        ProviderStats,
        # Base class
        ProviderBase,
        # Tier 0 providers (Free)
        FirecrawlProvider,
        GooglePlacesProvider,
        WebScraperProvider,
        # Tier 1 providers (Low Cost)
        HunterProvider,
        ClearbitProvider,
        ApolloProvider,
        # Tier 2 providers (Premium)
        ProspeoProvider,
        SnovProvider,
        ClayProvider,
        # Registry and utilities
        ProviderRegistry,
        execute_tier_waterfall,
        get_best_result,
    )
    _PROVIDERS_AVAILABLE = True

except ImportError as e:
    logger.warning(f"Could not import from ctb.sys providers: {e}")
    logger.warning("Falling back to stub implementations")
    _PROVIDERS_AVAILABLE = False

    # Provide stub implementations if import fails
    from enum import Enum
    from dataclasses import dataclass, field

    class ProviderTier(Enum):
        TIER_0 = 0
        TIER_1 = 1
        TIER_2 = 2

    class ProviderStatus(Enum):
        AVAILABLE = "available"
        RATE_LIMITED = "rate_limited"
        UNAVAILABLE = "unavailable"
        NO_API_KEY = "no_api_key"
        ERROR = "error"

    @dataclass
    class EmailSample:
        email: str
        first_name: Optional[str] = None
        last_name: Optional[str] = None
        title: Optional[str] = None
        confidence: float = 0.0
        source: str = ""

    @dataclass
    class ProviderResult:
        success: bool
        pattern: Optional[str] = None
        sample_emails: List[EmailSample] = field(default_factory=list)
        confidence: float = 0.0
        provider_name: str = ""
        tier: ProviderTier = ProviderTier.TIER_0
        cost_credits: float = 0.0
        raw_response: Dict[str, Any] = field(default_factory=dict)
        error_message: Optional[str] = None
        request_time_ms: int = 0

        def has_pattern(self) -> bool:
            return self.success and self.pattern is not None

    @dataclass
    class ProviderStats:
        total_requests: int = 0
        successful_requests: int = 0
        failed_requests: int = 0
        total_credits_used: float = 0.0
        avg_response_time_ms: float = 0.0
        patterns_found: int = 0
        rate_limit_hits: int = 0

    class ProviderBase:
        """Stub base class for providers."""
        def __init__(self, api_key: str = None, config: Dict[str, Any] = None):
            self.api_key = api_key or ""
            self.config = config or {}

        def discover_pattern(self, domain: str, company_name: str = None) -> ProviderResult:
            raise NotImplementedError("Provider not implemented")

        def get_tier(self) -> ProviderTier:
            return ProviderTier.TIER_0

        def get_cost(self) -> float:
            return 0.0

        @property
        def name(self) -> str:
            return self.__class__.__name__.replace('Provider', '').lower()

    # Stub provider classes
    class FirecrawlProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_0
        def get_cost(self): return 0.0001

    class GooglePlacesProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_0
        def get_cost(self): return 0.003

    class WebScraperProvider(ProviderBase):
        def requires_api_key(self): return False
        def get_tier(self): return ProviderTier.TIER_0
        def get_cost(self): return 0.0

    class HunterProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_1
        def get_cost(self): return 0.008

    class ClearbitProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_1
        def get_cost(self): return 0.01

    class ApolloProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_1
        def get_cost(self): return 0.005

    class ProspeoProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_2
        def get_cost(self): return 0.003

    class SnovProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_2
        def get_cost(self): return 0.004

    class ClayProvider(ProviderBase):
        def get_tier(self): return ProviderTier.TIER_2
        def get_cost(self): return 0.01

    class ProviderRegistry:
        """Stub registry."""
        def __init__(self, config: Dict[str, Any] = None):
            self.config = config or {}
            self._providers = {}

        def get_provider(self, name: str) -> Optional[ProviderBase]:
            return self._providers.get(name.lower())

        def get_providers_by_tier(self, tier: ProviderTier) -> List[ProviderBase]:
            return [p for p in self._providers.values() if p.get_tier() == tier]

        def get_all_providers(self) -> Dict[ProviderTier, List[ProviderBase]]:
            return {t: [] for t in ProviderTier}

    def execute_tier_waterfall(registry, domain, company_name=None,
                                max_tier=ProviderTier.TIER_2,
                                stop_on_pattern=True) -> List[ProviderResult]:
        logger.warning("Using stub waterfall - no providers available")
        return []

    def get_best_result(results: List[ProviderResult]) -> Optional[ProviderResult]:
        if not results:
            return None
        with_pattern = [r for r in results if r.has_pattern()]
        if with_pattern:
            return max(with_pattern, key=lambda r: r.confidence)
        return results[0] if results else None


# =============================================================================
# Convenience Functions
# =============================================================================

def create_provider_registry() -> ProviderRegistry:
    """
    Create a provider registry with configuration from environment.

    Reads API keys from environment variables:
    - FIRECRAWL_API_KEY
    - GOOGLE_API_KEY (for Google Places)
    - HUNTER_API_KEY
    - CLEARBIT_API_KEY
    - APOLLO_API_KEY
    - PROSPEO_API_KEY
    - SNOV_API_KEY
    - CLAY_API_KEY

    Returns:
        Configured ProviderRegistry instance
    """
    config = {
        'firecrawl_api_key': os.getenv('FIRECRAWL_API_KEY', ''),
        'google_places_api_key': os.getenv('GOOGLE_API_KEY', ''),
        'hunter_api_key': os.getenv('HUNTER_API_KEY', ''),
        'clearbit_api_key': os.getenv('CLEARBIT_API_KEY', ''),
        'apollo_api_key': os.getenv('APOLLO_API_KEY', ''),
        'prospeo_api_key': os.getenv('PROSPEO_API_KEY', ''),
        'snov_api_key': os.getenv('SNOV_API_KEY', ''),
        'clay_api_key': os.getenv('CLAY_API_KEY', ''),
    }

    return ProviderRegistry(config)


def discover_pattern_waterfall(
    domain: str,
    company_name: str = None,
    max_tier: ProviderTier = ProviderTier.TIER_2
) -> Optional[ProviderResult]:
    """
    Convenience function to discover email pattern using waterfall.

    Creates registry from environment and executes waterfall.

    Args:
        domain: Domain to search
        company_name: Optional company name
        max_tier: Maximum tier to try

    Returns:
        Best ProviderResult or None
    """
    registry = create_provider_registry()
    results = execute_tier_waterfall(
        registry=registry,
        domain=domain,
        company_name=company_name,
        max_tier=max_tier,
        stop_on_pattern=True
    )
    return get_best_result(results)


def get_provider_by_name(name: str) -> Optional[ProviderBase]:
    """
    Get a provider instance by name.

    Args:
        name: Provider name (e.g., 'hunter', 'apollo')

    Returns:
        Provider instance or None
    """
    registry = create_provider_registry()
    return registry.get_provider(name)


def list_available_providers() -> List[str]:
    """
    List all available (configured) providers.

    Returns:
        List of provider names that have API keys configured
    """
    registry = create_provider_registry()
    providers = []
    for tier in [ProviderTier.TIER_0, ProviderTier.TIER_1, ProviderTier.TIER_2]:
        for provider in registry.get_providers_by_tier(tier):
            providers.append(provider.name)
    return providers


# =============================================================================
# Alias for backward compatibility with ScraperAPIProvider
# =============================================================================

# Some code may reference ScraperAPIProvider - alias to WebScraperProvider
ScraperAPIProvider = WebScraperProvider


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ProviderTier",
    "ProviderStatus",
    # Data classes
    "EmailSample",
    "ProviderResult",
    "ProviderStats",
    # Base class
    "ProviderBase",
    # Tier 0 providers (Free)
    "FirecrawlProvider",
    "GooglePlacesProvider",
    "WebScraperProvider",
    "ScraperAPIProvider",  # Alias
    # Tier 1 providers (Low Cost)
    "HunterProvider",
    "ClearbitProvider",
    "ApolloProvider",
    # Tier 2 providers (Premium)
    "ProspeoProvider",
    "SnovProvider",
    "ClayProvider",
    # Registry and utilities
    "ProviderRegistry",
    "execute_tier_waterfall",
    "get_best_result",
    # Convenience functions
    "create_provider_registry",
    "discover_pattern_waterfall",
    "get_provider_by_name",
    "list_available_providers",
]
