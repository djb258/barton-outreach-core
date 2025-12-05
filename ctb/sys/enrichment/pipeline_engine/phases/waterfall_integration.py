"""
Waterfall Integration Module
============================
Integrates the Email Pattern Waterfall into Phase 5 and Phase 7.

This module provides:
- On-demand pattern discovery for companies missing patterns
- Tiered waterfall execution (Tier 0 → Tier 1 → Tier 2)
- Pattern caching to avoid duplicate API calls
- Cost tracking and tier escalation logic
- Provider Benchmark Engine (PBE) integration for metrics

Usage:
- Phase 5: Call waterfall for companies missing patterns during email generation
- Phase 7: Process queued items through waterfall for pattern discovery

Waterfall Tiers:
- Tier 0 (Free): WebScraper, Firecrawl, Google Places
- Tier 1 (Low Cost): Hunter.io, Clearbit, Apollo
- Tier 2 (Premium): Prospeo, Snov, Clay

RULES:
- Company-First doctrine: company_id anchor required
- Stop on first pattern found (unless configured otherwise)
- No external database writes
- Deterministic flow: no fuzzy matching
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

from ..utils.providers import (
    ProviderRegistry,
    ProviderTier,
    ProviderResult,
    ProviderBase,
    execute_tier_waterfall,
    get_best_result
)
from ..utils.normalization import normalize_domain

# Provider Benchmark Engine (System-Level) - Optional import
try:
    from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine
    _PBE_AVAILABLE = True
except ImportError:
    _PBE_AVAILABLE = False


class WaterfallMode(Enum):
    """Mode of waterfall execution."""
    TIER_0_ONLY = 0       # Only try free providers
    TIER_0_AND_1 = 1      # Try free, then low-cost
    FULL_WATERFALL = 2    # Try all tiers (default)


class WaterfallStatus(Enum):
    """Status of waterfall execution for a domain."""
    NOT_ATTEMPTED = "not_attempted"
    IN_PROGRESS = "in_progress"
    PATTERN_FOUND = "pattern_found"
    SUGGESTED = "suggested"
    EXHAUSTED = "exhausted"  # All tiers tried, no pattern
    SKIPPED = "skipped"      # No domain to process
    ERROR = "error"


@dataclass
class WaterfallResult:
    """Result of waterfall execution for a single domain."""
    domain: str
    company_id: str
    status: WaterfallStatus
    pattern: Optional[str] = None
    confidence: float = 0.0
    tier_used: Optional[int] = None
    provider_used: Optional[str] = None
    sample_emails: List[str] = field(default_factory=list)
    suggested_patterns: List[str] = field(default_factory=list)
    api_calls_made: int = 0
    total_cost: float = 0.0
    execution_time_ms: int = 0
    error_message: Optional[str] = None


@dataclass
class WaterfallStats:
    """Statistics for waterfall batch execution."""
    domains_processed: int = 0
    patterns_found: int = 0
    patterns_suggested: int = 0
    exhausted: int = 0
    errors: int = 0
    tier_0_hits: int = 0
    tier_1_hits: int = 0
    tier_2_hits: int = 0
    total_api_calls: int = 0
    total_cost: float = 0.0
    duration_seconds: float = 0.0


class EmailPatternWaterfall:
    """
    Email Pattern Waterfall for People Pipeline.

    Provides on-demand pattern discovery using tiered providers.
    Integrates with Phase 5 (during email generation) and
    Phase 7 (processing enrichment queue).

    COMPANY-FIRST: Requires company_id anchor for all operations.
    """

    # Common email patterns for suggestions
    COMMON_PATTERNS = [
        ('{first}.{last}', 0.4),      # john.doe@company.com
        ('{first}{last}', 0.25),      # johndoe@company.com
        ('{f}{last}', 0.15),          # jdoe@company.com
        ('{first}_{last}', 0.08),     # john_doe@company.com
        ('{f}.{last}', 0.06),         # j.doe@company.com
        ('{first}', 0.03),            # john@company.com
        ('{last}.{first}', 0.02),     # doe.john@company.com
        ('{first}{l}', 0.01),         # johnd@company.com
    ]

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Email Pattern Waterfall.

        Args:
            config: Configuration dictionary with:
                - mode: WaterfallMode (default: FULL_WATERFALL)
                - min_confidence: Minimum confidence to accept (default: 0.7)
                - suggest_on_fail: Suggest patterns if all tiers fail (default: True)
                - enable_caching: Cache results per domain (default: True)
                - provider configs: API keys for providers
        """
        self.config = config or {}

        # Waterfall settings
        self.mode = WaterfallMode(self.config.get('waterfall_mode', 2))
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.suggest_on_fail = self.config.get('suggest_on_fail', True)
        self.enable_caching = self.config.get('enable_caching', True)

        # Initialize provider registry
        provider_config = self._extract_provider_config()
        self.registry = ProviderRegistry(provider_config)

        # Pattern cache: domain -> WaterfallResult
        self._pattern_cache: Dict[str, WaterfallResult] = {}

        # Stats tracking
        self.stats = WaterfallStats()

        # Provider Benchmark Engine reference
        self._pbe = None
        if _PBE_AVAILABLE:
            try:
                self._pbe = ProviderBenchmarkEngine.get_instance()
            except Exception:
                pass

    def _extract_provider_config(self) -> Dict[str, Any]:
        """Extract provider configuration from main config."""
        provider_keys = [
            'firecrawl_api_key', 'google_places_api_key',
            'hunter_api_key', 'clearbit_api_key', 'apollo_api_key',
            'prospeo_api_key', 'snov_api_key', 'clay_api_key'
        ]

        provider_config = {}
        for key in provider_keys:
            if key in self.config:
                provider_config[key] = self.config[key]

        # Pass through any provider-specific settings
        for key in ['firecrawl', 'hunter', 'apollo', 'prospeo', 'snov', 'clay']:
            if key in self.config:
                provider_config[key] = self.config[key]

        return provider_config

    def discover_pattern(
        self,
        domain: str,
        company_id: str,
        company_name: str = None,
        force_refresh: bool = False
    ) -> WaterfallResult:
        """
        Discover email pattern for a single domain.

        Args:
            domain: Domain to discover pattern for
            company_id: Company ID (required - Company-First doctrine)
            company_name: Optional company name for context
            force_refresh: Bypass cache and re-query providers

        Returns:
            WaterfallResult with pattern info
        """
        start_time = time.time()

        # Validate inputs
        if not domain:
            return WaterfallResult(
                domain='',
                company_id=company_id,
                status=WaterfallStatus.SKIPPED,
                error_message='No domain provided'
            )

        # Normalize domain
        normalized_domain = normalize_domain(domain) if domain else None
        if not normalized_domain:
            return WaterfallResult(
                domain=domain,
                company_id=company_id,
                status=WaterfallStatus.SKIPPED,
                error_message='Invalid domain'
            )

        # Check cache
        if self.enable_caching and not force_refresh:
            cached = self._pattern_cache.get(normalized_domain)
            if cached:
                return cached

        # Initialize result
        result = WaterfallResult(
            domain=normalized_domain,
            company_id=company_id,
            status=WaterfallStatus.IN_PROGRESS
        )

        # Determine max tier based on mode
        max_tier = ProviderTier.TIER_0
        if self.mode == WaterfallMode.TIER_0_AND_1:
            max_tier = ProviderTier.TIER_1
        elif self.mode == WaterfallMode.FULL_WATERFALL:
            max_tier = ProviderTier.TIER_2

        # Execute waterfall
        try:
            provider_results = execute_tier_waterfall(
                registry=self.registry,
                domain=normalized_domain,
                company_name=company_name,
                max_tier=max_tier,
                stop_on_pattern=True
            )

            result.api_calls_made = len(provider_results)

            # Sum up costs and record PBE metrics for each provider
            for pr in provider_results:
                result.total_cost += pr.cost_credits
                # PBE Hook: Record each provider result
                self._record_pbe_result(pr)

            # Find best result
            best = get_best_result(provider_results)

            if best and best.has_pattern() and best.confidence >= self.min_confidence:
                result.pattern = best.pattern
                result.confidence = best.confidence
                result.tier_used = best.tier.value
                result.provider_used = best.provider_name
                result.sample_emails = [e.email for e in best.sample_emails[:5]]
                result.status = WaterfallStatus.PATTERN_FOUND

                # Update stats
                self._update_tier_stats(best.tier)
            elif self.suggest_on_fail:
                # Suggest common patterns
                result.suggested_patterns = [p[0] for p in self.COMMON_PATTERNS[:5]]
                result.pattern = self.COMMON_PATTERNS[0][0]  # Most common
                result.confidence = self.COMMON_PATTERNS[0][1]
                result.status = WaterfallStatus.SUGGESTED
                self.stats.patterns_suggested += 1
            else:
                result.status = WaterfallStatus.EXHAUSTED
                self.stats.exhausted += 1

        except Exception as e:
            result.status = WaterfallStatus.ERROR
            result.error_message = str(e)
            self.stats.errors += 1

        # Calculate execution time
        result.execution_time_ms = int((time.time() - start_time) * 1000)

        # Update stats
        self.stats.domains_processed += 1
        self.stats.total_api_calls += result.api_calls_made
        self.stats.total_cost += result.total_cost

        if result.status == WaterfallStatus.PATTERN_FOUND:
            self.stats.patterns_found += 1

        # Cache result
        if self.enable_caching:
            self._pattern_cache[normalized_domain] = result

        return result

    def discover_patterns_batch(
        self,
        domains_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, WaterfallStats]:
        """
        Discover patterns for multiple domains.

        Args:
            domains_df: DataFrame with domains to process
                Required columns: domain (or resolved_domain), company_id
                Optional columns: company_name

        Returns:
            Tuple of (results_df, WaterfallStats)
        """
        start_time = time.time()

        # Reset stats for this batch
        self.stats = WaterfallStats()

        results = []

        for idx, row in domains_df.iterrows():
            domain = row.get('domain', '') or row.get('resolved_domain', '')
            company_id = str(row.get('company_id', '') or row.get('matched_company_id', ''))
            company_name = row.get('company_name', '')

            if not company_id:
                results.append({
                    'domain': domain,
                    'company_id': '',
                    'status': WaterfallStatus.SKIPPED.value,
                    'pattern': None,
                    'confidence': 0.0,
                    'error': 'Missing company_id'
                })
                continue

            result = self.discover_pattern(domain, company_id, company_name)

            results.append({
                'domain': result.domain,
                'company_id': result.company_id,
                'status': result.status.value,
                'pattern': result.pattern,
                'confidence': result.confidence,
                'tier_used': result.tier_used,
                'provider_used': result.provider_used,
                'sample_emails': ','.join(result.sample_emails[:3]),
                'suggested_patterns': ','.join(result.suggested_patterns[:3]),
                'api_calls': result.api_calls_made,
                'cost': result.total_cost,
                'execution_time_ms': result.execution_time_ms,
                'error': result.error_message
            })

        self.stats.duration_seconds = time.time() - start_time

        return pd.DataFrame(results), self.stats

    def _update_tier_stats(self, tier: ProviderTier) -> None:
        """Update tier hit statistics."""
        if tier == ProviderTier.TIER_0:
            self.stats.tier_0_hits += 1
        elif tier == ProviderTier.TIER_1:
            self.stats.tier_1_hits += 1
        elif tier == ProviderTier.TIER_2:
            self.stats.tier_2_hits += 1

    def _record_pbe_result(self, provider_result: ProviderResult) -> None:
        """
        Record a provider result to Provider Benchmark Engine (PBE).

        PBE Hook - records metrics for each waterfall provider call.
        Silently ignores errors since metrics are non-critical.

        Args:
            provider_result: The ProviderResult from waterfall execution
        """
        if not self._pbe:
            return
        try:
            self._pbe.record_waterfall_attempt(
                provider_name=provider_result.provider_name,
                success=provider_result.has_pattern(),
                pattern_verified=provider_result.confidence >= self.min_confidence,
                latency_ms=provider_result.latency_ms
            )
        except Exception:
            pass  # Silently ignore PBE errors - metrics are non-critical

    def _record_pbe_error(self, provider_name: str, is_timeout: bool = False) -> None:
        """
        Record a provider error to PBE.

        Args:
            provider_name: Name of the provider that failed
            is_timeout: Whether the error was a timeout
        """
        if not self._pbe:
            return
        try:
            self._pbe.record_waterfall_failure(
                provider_name=provider_name,
                is_timeout=is_timeout
            )
        except Exception:
            pass

    def get_cached_pattern(self, domain: str) -> Optional[WaterfallResult]:
        """
        Get cached pattern for domain if available.

        Args:
            domain: Domain to look up

        Returns:
            WaterfallResult or None
        """
        normalized = normalize_domain(domain) if domain else None
        if normalized:
            return self._pattern_cache.get(normalized)
        return None

    def clear_cache(self) -> int:
        """
        Clear the pattern cache.

        Returns:
            Number of entries cleared
        """
        count = len(self._pattern_cache)
        self._pattern_cache.clear()
        return count

    def get_available_providers(self) -> Dict[str, List[str]]:
        """
        Get list of available providers by tier.

        Returns:
            Dict mapping tier name to list of provider names
        """
        providers = self.registry.get_all_providers()
        return {
            'tier_0': [p.name for p in providers.get(ProviderTier.TIER_0, [])],
            'tier_1': [p.name for p in providers.get(ProviderTier.TIER_1, [])],
            'tier_2': [p.name for p in providers.get(ProviderTier.TIER_2, [])]
        }


class Phase5WaterfallAdapter:
    """
    Adapter for integrating waterfall into Phase 5 (Email Generation).

    When Phase 5 encounters a company without a pattern, this adapter
    can trigger on-demand pattern discovery via the waterfall.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Phase 5 waterfall adapter.

        Args:
            config: Configuration with:
                - enable_waterfall: Enable on-demand discovery (default: False)
                - waterfall_mode: Mode of operation (0, 1, or 2)
                - max_waterfall_per_run: Max domains to waterfall (default: 100)
        """
        self.config = config or {}
        self.enable_waterfall = self.config.get('enable_waterfall', False)
        self.max_per_run = self.config.get('max_waterfall_per_run', 100)

        self._waterfall = None
        self._patterns_discovered = 0

    def get_waterfall(self) -> EmailPatternWaterfall:
        """Get or create waterfall instance."""
        if self._waterfall is None:
            self._waterfall = EmailPatternWaterfall(self.config)
        return self._waterfall

    def discover_missing_pattern(
        self,
        domain: str,
        company_id: str,
        company_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to discover a pattern for a company missing one.

        Only runs if:
        - enable_waterfall is True
        - max_per_run limit not reached
        - Valid domain and company_id

        Args:
            domain: Company domain
            company_id: Company ID (required)
            company_name: Optional company name

        Returns:
            Dict with pattern info if found, None otherwise
        """
        if not self.enable_waterfall:
            return None

        if self._patterns_discovered >= self.max_per_run:
            return None

        if not domain or not company_id:
            return None

        waterfall = self.get_waterfall()
        result = waterfall.discover_pattern(domain, company_id, company_name)

        if result.status == WaterfallStatus.PATTERN_FOUND:
            self._patterns_discovered += 1
            return {
                'pattern': result.pattern,
                'confidence': result.confidence,
                'tier': result.tier_used,
                'provider': result.provider_used,
                'verification_status': 'derived'  # From waterfall
            }
        elif result.status == WaterfallStatus.SUGGESTED:
            self._patterns_discovered += 1
            return {
                'pattern': result.pattern,
                'confidence': result.confidence,
                'tier': None,
                'provider': 'suggestion',
                'verification_status': 'suggested'
            }

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get waterfall adapter statistics."""
        if self._waterfall:
            return {
                'patterns_discovered': self._patterns_discovered,
                'waterfall_stats': {
                    'domains_processed': self._waterfall.stats.domains_processed,
                    'patterns_found': self._waterfall.stats.patterns_found,
                    'suggested': self._waterfall.stats.patterns_suggested,
                    'total_cost': self._waterfall.stats.total_cost
                }
            }
        return {'patterns_discovered': 0, 'waterfall_stats': {}}


class Phase7WaterfallProcessor:
    """
    Processor for running waterfall on Phase 7 enrichment queue.

    Processes queued items that need pattern discovery,
    respecting tier limits and cost constraints.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Phase 7 waterfall processor.

        Args:
            config: Configuration with:
                - max_items_per_batch: Items to process per batch (default: 50)
                - max_tier: Maximum tier to use (default: 2)
                - budget_limit: Maximum cost per batch (default: 100.0)
                - priority_filter: Only process certain priorities
        """
        self.config = config or {}
        self.max_items = self.config.get('max_items_per_batch', 50)
        self.max_tier = self.config.get('max_tier', 2)
        self.budget_limit = self.config.get('budget_limit', 100.0)
        self.priority_filter = self.config.get('priority_filter', None)

        self._waterfall = None

    def get_waterfall(self) -> EmailPatternWaterfall:
        """Get or create waterfall instance."""
        if self._waterfall is None:
            waterfall_config = {
                **self.config,
                'waterfall_mode': self.max_tier
            }
            self._waterfall = EmailPatternWaterfall(waterfall_config)
        return self._waterfall

    def process_queue(
        self,
        queue_df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, WaterfallStats]:
        """
        Process enrichment queue items through waterfall.

        Only processes items with reason='pattern_missing'.

        Args:
            queue_df: Enrichment queue DataFrame from Phase 7
                Required columns: entity_type, entity_id, company_id, reason

        Returns:
            Tuple of (resolved_df, unresolved_df, WaterfallStats)
        """
        if queue_df is None or len(queue_df) == 0:
            return pd.DataFrame(), queue_df, WaterfallStats()

        # Filter to pattern-missing items only
        pattern_items = queue_df[
            queue_df['reason'].isin(['pattern_missing', 'PATTERN_MISSING'])
        ].copy()

        if len(pattern_items) == 0:
            return pd.DataFrame(), queue_df, WaterfallStats()

        # Apply priority filter if configured
        if self.priority_filter:
            pattern_items = pattern_items[
                pattern_items['priority'].isin(self.priority_filter)
            ]

        # Limit to max items
        items_to_process = pattern_items.head(self.max_items)

        waterfall = self.get_waterfall()
        resolved = []
        unresolved_ids = set()
        current_cost = 0.0

        for idx, row in items_to_process.iterrows():
            # Check budget
            if current_cost >= self.budget_limit:
                break

            company_id = row.get('company_id', '')
            entity_id = row.get('entity_id', '')
            domain = row.get('domain', '') or row.get('resolved_domain', '')

            # If no domain in queue, we can't process
            if not domain:
                unresolved_ids.add(row.get('queue_id', idx))
                continue

            result = waterfall.discover_pattern(
                domain=domain,
                company_id=company_id
            )

            current_cost += result.total_cost

            if result.status in [WaterfallStatus.PATTERN_FOUND, WaterfallStatus.SUGGESTED]:
                resolved.append({
                    'queue_id': row.get('queue_id', idx),
                    'entity_id': entity_id,
                    'company_id': company_id,
                    'domain': domain,
                    'pattern': result.pattern,
                    'confidence': result.confidence,
                    'status': result.status.value,
                    'tier_used': result.tier_used,
                    'provider_used': result.provider_used,
                    'cost': result.total_cost
                })
            else:
                unresolved_ids.add(row.get('queue_id', idx))

        # Build output DataFrames
        resolved_df = pd.DataFrame(resolved) if resolved else pd.DataFrame()

        # Unresolved = items we tried but failed + items we didn't try (budget/limit)
        unresolved_df = queue_df[
            queue_df.apply(
                lambda r: r.get('queue_id', r.name) in unresolved_ids or
                          r.name >= len(items_to_process),
                axis=1
            )
        ] if len(queue_df) > 0 else pd.DataFrame()

        return resolved_df, unresolved_df, waterfall.stats


# Convenience functions

def create_waterfall(config: Dict[str, Any] = None) -> EmailPatternWaterfall:
    """Create a configured waterfall instance."""
    return EmailPatternWaterfall(config)


def discover_pattern_for_company(
    domain: str,
    company_id: str,
    config: Dict[str, Any] = None
) -> WaterfallResult:
    """
    Convenience function to discover pattern for a single company.

    Args:
        domain: Company domain
        company_id: Company ID (required)
        config: Optional configuration

    Returns:
        WaterfallResult
    """
    waterfall = EmailPatternWaterfall(config)
    return waterfall.discover_pattern(domain, company_id)
