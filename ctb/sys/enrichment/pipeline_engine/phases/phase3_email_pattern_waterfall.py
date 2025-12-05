"""
Phase 3: Email Pattern Waterfall
================================
Discovers email patterns using tiered approach:
- Tier 0 (Free): Firecrawl, ScraperAPI, Google Places
- Tier 1 (Low Cost): Hunter.io, Clearbit, Apollo
- Tier 2 (Premium): Prospeo, Snov, Clay

The waterfall stops as soon as a valid pattern is found.
If no pattern found, suggests common patterns for verification in Phase 4.
"""

import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from enum import Enum
import pandas as pd

from ..utils.normalization import normalize_domain
from ..utils.patterns import (
    extract_patterns_from_multiple,
    suggest_patterns_for_domain,
    PatternMatch,
    COMMON_PATTERNS
)
from ..utils.providers import (
    ProviderRegistry,
    ProviderTier,
    ProviderResult,
    execute_tier_waterfall
)
from ..utils.logging import (
    PipelineLogger,
    EventType,
    LogLevel,
    log_phase_start,
    log_phase_complete
)


class PatternSource(Enum):
    """Source of pattern discovery."""
    TIER_0 = "tier_0"               # Free providers
    TIER_1 = "tier_1"               # Low cost providers
    TIER_2 = "tier_2"               # Premium providers
    INPUT_DATA = "input_data"       # From existing email in input
    DATABASE = "database"           # From pattern cache/database
    SUGGESTED = "suggested"         # Common pattern suggestion
    NONE = "none"                   # No pattern found


class PatternStatus(Enum):
    """Status of pattern discovery."""
    FOUND = "found"                 # Pattern discovered
    SUGGESTED = "suggested"         # Pattern suggested but unverified
    FAILED = "failed"               # All tiers exhausted, no pattern
    SKIPPED = "skipped"             # Skipped (no domain, etc.)


@dataclass
class PatternResult:
    """Result of email pattern discovery for a single domain."""
    company_id: str
    domain: str
    pattern: Optional[str] = None       # e.g., '{first}.{last}'
    pattern_source: PatternSource = PatternSource.NONE
    pattern_status: PatternStatus = PatternStatus.FAILED
    tier_used: Optional[int] = None     # 0, 1, or 2
    provider_used: Optional[str] = None # Which provider found the pattern
    confidence: float = 0.0
    sample_emails: List[str] = field(default_factory=list)
    suggested_patterns: List[str] = field(default_factory=list)
    api_calls_made: int = 0
    cost_credits: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase3Stats:
    """Statistics for Phase 3 execution."""
    total_input: int = 0
    domains_processed: int = 0
    patterns_found: int = 0
    patterns_suggested: int = 0
    patterns_failed: int = 0
    tier_0_hits: int = 0
    tier_1_hits: int = 0
    tier_2_hits: int = 0
    input_data_hits: int = 0
    total_api_calls: int = 0
    total_cost_credits: float = 0.0
    duration_seconds: float = 0.0


class Phase3EmailPatternWaterfall:
    """
    Phase 3: Discover email patterns using tiered waterfall.

    Tier progression:
    - Start with Tier 0 (free providers)
    - Escalate to Tier 1 if Tier 0 fails
    - Escalate to Tier 2 if Tier 1 fails
    - Suggest common patterns if all tiers fail

    The waterfall stops as soon as a valid pattern is found.
    """

    def __init__(self, config: Dict[str, Any] = None, logger: PipelineLogger = None):
        """
        Initialize Phase 3.

        Args:
            config: Configuration with API keys and tier settings
                - max_tier: Maximum tier to use (0, 1, or 2)
                - min_confidence: Minimum pattern confidence (default: 0.7)
                - suggest_if_failed: Whether to suggest patterns if all fail
                - use_input_emails: Whether to extract patterns from input emails
                - enable_tier_0: Enable/disable Tier 0
                - enable_tier_1: Enable/disable Tier 1
                - enable_tier_2: Enable/disable Tier 2
            logger: Pipeline logger instance
        """
        self.config = config or {}
        self.logger = logger or PipelineLogger()

        # Configuration
        self.max_tier = self.config.get('max_tier', 2)
        self.min_confidence = self.config.get('min_confidence', 0.7)
        self.suggest_if_failed = self.config.get('suggest_if_failed', True)
        self.use_input_emails = self.config.get('use_input_emails', True)
        self.enable_tier_0 = self.config.get('enable_tier_0', True)
        self.enable_tier_1 = self.config.get('enable_tier_1', True)
        self.enable_tier_2 = self.config.get('enable_tier_2', True)

        # Initialize provider registry
        provider_config = self.config.get('providers', {})
        self.provider_registry = ProviderRegistry(provider_config)

        # Cache for discovered patterns (domain -> PatternResult)
        self._pattern_cache: Dict[str, PatternResult] = {}

    def run(self, domain_df: pd.DataFrame) -> Tuple[pd.DataFrame, Phase3Stats]:
        """
        Run email pattern waterfall.

        Args:
            domain_df: DataFrame with domains from Phase 2
                Expected columns: person_id, resolved_domain, matched_company_id

        Returns:
            Tuple of (result_df with pattern info, Phase3Stats)
        """
        start_time = time.time()
        stats = Phase3Stats(total_input=len(domain_df))

        log_phase_start(self.logger, 3, "Email Pattern Waterfall", len(domain_df))

        # Get unique domains to process (avoid duplicate API calls)
        unique_domains = self._get_unique_domains(domain_df)
        stats.domains_processed = len(unique_domains)

        # Process each unique domain
        domain_patterns: Dict[str, PatternResult] = {}
        for domain_info in unique_domains:
            domain = domain_info['domain']
            company_id = domain_info['company_id']
            input_emails = domain_info.get('input_emails', [])

            result = self._discover_pattern(domain, company_id, input_emails)
            domain_patterns[domain] = result

            # Update stats
            stats.total_api_calls += result.api_calls_made
            stats.total_cost_credits += result.cost_credits

            if result.pattern_status == PatternStatus.FOUND:
                stats.patterns_found += 1
                if result.pattern_source == PatternSource.TIER_0:
                    stats.tier_0_hits += 1
                elif result.pattern_source == PatternSource.TIER_1:
                    stats.tier_1_hits += 1
                elif result.pattern_source == PatternSource.TIER_2:
                    stats.tier_2_hits += 1
                elif result.pattern_source == PatternSource.INPUT_DATA:
                    stats.input_data_hits += 1
            elif result.pattern_status == PatternStatus.SUGGESTED:
                stats.patterns_suggested += 1
            else:
                stats.patterns_failed += 1

        # Build output DataFrame
        result_df = self._build_result_dataframe(domain_df, domain_patterns)

        stats.duration_seconds = time.time() - start_time

        log_phase_complete(
            self.logger, 3, "Email Pattern Waterfall",
            output_count=len(result_df),
            duration_seconds=stats.duration_seconds,
            stats={
                'patterns_found': stats.patterns_found,
                'patterns_suggested': stats.patterns_suggested,
                'patterns_failed': stats.patterns_failed,
                'tier_0_hits': stats.tier_0_hits,
                'tier_1_hits': stats.tier_1_hits,
                'tier_2_hits': stats.tier_2_hits,
                'total_api_calls': stats.total_api_calls
            }
        )

        return result_df, stats

    def _get_unique_domains(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Extract unique domains with associated company IDs and any input emails.

        Args:
            df: Input DataFrame

        Returns:
            List of dicts with domain, company_id, and input_emails
        """
        unique_domains = {}

        for idx, row in df.iterrows():
            domain = row.get('resolved_domain', '') or row.get('domain', '')
            if not domain:
                continue

            normalized = normalize_domain(domain)
            if not normalized:
                continue

            if normalized not in unique_domains:
                unique_domains[normalized] = {
                    'domain': normalized,
                    'company_id': row.get('matched_company_id', ''),
                    'input_emails': []
                }

            # Collect any existing emails for pattern extraction
            email = row.get('email', '')
            if email and '@' in email:
                email_domain = email.split('@')[1].lower()
                if email_domain == normalized:
                    unique_domains[normalized]['input_emails'].append({
                        'email': email,
                        'first_name': row.get('first_name', ''),
                        'last_name': row.get('last_name', '')
                    })

        return list(unique_domains.values())

    def _discover_pattern(self, domain: str, company_id: str,
                          input_emails: List[Dict[str, str]] = None) -> PatternResult:
        """
        Discover email pattern for a domain using tiered waterfall.

        Order:
        1. Check cache
        2. Extract from input emails if available
        3. Try Tier 0 (free)
        4. Try Tier 1 (low cost)
        5. Try Tier 2 (premium)
        6. Suggest common patterns

        Args:
            domain: Domain to discover pattern for
            company_id: Associated company ID
            input_emails: Optional list of existing emails with name data

        Returns:
            PatternResult
        """
        # Check cache first
        if domain in self._pattern_cache:
            return self._pattern_cache[domain]

        result = PatternResult(
            company_id=company_id,
            domain=domain
        )

        # 1. Try extracting from input emails
        if self.use_input_emails and input_emails:
            pattern_match = self._extract_from_input_emails(input_emails, domain)
            if pattern_match and pattern_match.confidence >= self.min_confidence:
                result.pattern = pattern_match.pattern
                result.confidence = pattern_match.confidence
                result.pattern_source = PatternSource.INPUT_DATA
                result.pattern_status = PatternStatus.FOUND
                result.sample_emails = pattern_match.sample_emails[:3]
                result.metadata['extraction_method'] = 'input_emails'

                self.logger.log_event(
                    EventType.PATTERN_DISCOVERED,
                    f"Pattern from input emails: {result.pattern}",
                    entity_type="pattern",
                    entity_id=domain,
                    confidence=result.confidence,
                    source="input_data"
                )

                self._pattern_cache[domain] = result
                return result

        # 2. Try tiered providers
        max_provider_tier = ProviderTier(min(self.max_tier, 2))

        # Execute waterfall
        provider_results = execute_tier_waterfall(
            registry=self.provider_registry,
            domain=domain,
            company_name=None,  # Could be added if needed
            max_tier=max_provider_tier,
            stop_on_pattern=True
        )

        result.api_calls_made = len(provider_results)

        # Process provider results
        for pr in provider_results:
            result.cost_credits += pr.cost_credits

            if pr.success and pr.patterns:
                # Found a pattern
                best_pattern = max(pr.patterns, key=lambda p: p.get('confidence', 0))
                if best_pattern.get('confidence', 0) >= self.min_confidence:
                    result.pattern = best_pattern.get('pattern')
                    result.confidence = best_pattern.get('confidence', 0.8)
                    result.tier_used = pr.tier.value
                    result.provider_used = pr.provider
                    result.sample_emails = best_pattern.get('sample_emails', [])[:3]

                    # Set source based on tier
                    if pr.tier == ProviderTier.TIER_0:
                        result.pattern_source = PatternSource.TIER_0
                    elif pr.tier == ProviderTier.TIER_1:
                        result.pattern_source = PatternSource.TIER_1
                    else:
                        result.pattern_source = PatternSource.TIER_2

                    result.pattern_status = PatternStatus.FOUND

                    self.logger.log_event(
                        EventType.PATTERN_DISCOVERED,
                        f"Pattern from {pr.provider}: {result.pattern}",
                        entity_type="pattern",
                        entity_id=domain,
                        confidence=result.confidence,
                        source=pr.provider,
                        metadata={'tier': pr.tier.value}
                    )

                    self._pattern_cache[domain] = result
                    return result

        # 3. Suggest common patterns if all providers failed
        if self.suggest_if_failed:
            suggestions = suggest_patterns_for_domain(domain)
            if suggestions:
                result.suggested_patterns = [s[0] for s in suggestions[:5]]
                result.pattern = suggestions[0][0]  # Most common pattern
                result.confidence = suggestions[0][1]  # Likelihood score
                result.pattern_source = PatternSource.SUGGESTED
                result.pattern_status = PatternStatus.SUGGESTED
                result.metadata['suggestion_count'] = len(suggestions)

                self.logger.log_event(
                    EventType.PATTERN_DISCOVERED,
                    f"Suggested pattern: {result.pattern} (unverified)",
                    LogLevel.INFO,
                    entity_type="pattern",
                    entity_id=domain,
                    confidence=result.confidence,
                    source="suggestion"
                )
        else:
            self.logger.log_event(
                EventType.PATTERN_FAILED,
                f"No pattern found for {domain}",
                LogLevel.WARNING,
                entity_type="pattern",
                entity_id=domain
            )

        self._pattern_cache[domain] = result
        return result

    def _extract_from_input_emails(self, emails: List[Dict[str, str]],
                                   domain: str) -> Optional[PatternMatch]:
        """
        Extract pattern from input email data.

        Args:
            emails: List of dicts with email, first_name, last_name
            domain: Domain for validation

        Returns:
            PatternMatch if extracted, None otherwise
        """
        if not emails:
            return None

        return extract_patterns_from_multiple(emails, domain)

    def _build_result_dataframe(self, domain_df: pd.DataFrame,
                                domain_patterns: Dict[str, PatternResult]) -> pd.DataFrame:
        """Build output DataFrame with pattern results appended."""
        # Create result columns
        result_data = []

        for idx, row in domain_df.iterrows():
            domain = row.get('resolved_domain', '') or row.get('domain', '')
            normalized = normalize_domain(domain) if domain else None

            if normalized and normalized in domain_patterns:
                pr = domain_patterns[normalized]
                result_data.append({
                    'person_id': row.get('person_id', idx),
                    'email_pattern': pr.pattern,
                    'pattern_source': pr.pattern_source.value if pr.pattern_source else None,
                    'pattern_status': pr.pattern_status.value if pr.pattern_status else None,
                    'pattern_confidence': pr.confidence,
                    'pattern_tier': pr.tier_used,
                    'pattern_provider': pr.provider_used,
                    'pattern_needs_verification': pr.pattern_status == PatternStatus.SUGGESTED
                })
            else:
                result_data.append({
                    'person_id': row.get('person_id', idx),
                    'email_pattern': None,
                    'pattern_source': PatternSource.NONE.value,
                    'pattern_status': PatternStatus.SKIPPED.value,
                    'pattern_confidence': 0.0,
                    'pattern_tier': None,
                    'pattern_provider': None,
                    'pattern_needs_verification': False
                })

        result_df = pd.DataFrame(result_data)

        # Merge with original domain_df
        if 'person_id' not in domain_df.columns:
            domain_df = domain_df.reset_index()
            domain_df = domain_df.rename(columns={'index': 'person_id'})

        output_df = domain_df.merge(
            result_df,
            on='person_id',
            how='left'
        )

        return output_df

    def try_tier_0(self, domain: str) -> Optional[PatternResult]:
        """
        Try Tier 0 providers (free).

        Providers:
        - Firecrawl (website scraping)
        - WebScraper
        - Google Places

        Args:
            domain: Domain to discover pattern for

        Returns:
            PatternResult if found, None otherwise
        """
        if not self.enable_tier_0:
            return None

        result = self._discover_pattern_at_tier(domain, ProviderTier.TIER_0)
        return result if result and result.pattern_status == PatternStatus.FOUND else None

    def try_tier_1(self, domain: str) -> Optional[PatternResult]:
        """
        Try Tier 1 providers (low cost).

        Providers:
        - Hunter.io
        - Clearbit
        - Apollo

        Args:
            domain: Domain to discover pattern for

        Returns:
            PatternResult if found, None otherwise
        """
        if not self.enable_tier_1:
            return None

        result = self._discover_pattern_at_tier(domain, ProviderTier.TIER_1)
        return result if result and result.pattern_status == PatternStatus.FOUND else None

    def try_tier_2(self, domain: str) -> Optional[PatternResult]:
        """
        Try Tier 2 providers (premium).

        Providers:
        - Prospeo
        - Snov.io
        - Clay

        Args:
            domain: Domain to discover pattern for

        Returns:
            PatternResult if found, None otherwise
        """
        if not self.enable_tier_2:
            return None

        result = self._discover_pattern_at_tier(domain, ProviderTier.TIER_2)
        return result if result and result.pattern_status == PatternStatus.FOUND else None

    def _discover_pattern_at_tier(self, domain: str,
                                  tier: ProviderTier) -> Optional[PatternResult]:
        """
        Discover pattern using only a specific tier.

        Args:
            domain: Domain to discover pattern for
            tier: Specific tier to use

        Returns:
            PatternResult or None
        """
        result = PatternResult(
            company_id='',
            domain=domain
        )

        providers = self.provider_registry.get_providers_by_tier(tier)
        for provider in providers:
            try:
                pr = provider.get_email_pattern(domain)
                result.api_calls_made += 1
                result.cost_credits += pr.cost_credits if pr else 0

                if pr and pr.success and pr.patterns:
                    best = max(pr.patterns, key=lambda p: p.get('confidence', 0))
                    if best.get('confidence', 0) >= self.min_confidence:
                        result.pattern = best.get('pattern')
                        result.confidence = best.get('confidence', 0.8)
                        result.tier_used = tier.value
                        result.provider_used = provider.name
                        result.sample_emails = best.get('sample_emails', [])[:3]
                        result.pattern_status = PatternStatus.FOUND

                        if tier == ProviderTier.TIER_0:
                            result.pattern_source = PatternSource.TIER_0
                        elif tier == ProviderTier.TIER_1:
                            result.pattern_source = PatternSource.TIER_1
                        else:
                            result.pattern_source = PatternSource.TIER_2

                        return result

            except Exception as e:
                self.logger.error(
                    f"Provider {provider.name} failed for {domain}",
                    error=e,
                    metadata={'domain': domain, 'tier': tier.value}
                )

        return None

    def get_pattern_statistics(self, result_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Get statistics about pattern discovery results.

        Args:
            result_df: Output from run()

        Returns:
            Dict with pattern statistics
        """
        stats = {
            'total': len(result_df),
            'by_status': {},
            'by_source': {},
            'by_tier': {},
            'needs_verification': 0,
            'avg_confidence': 0.0
        }

        if 'pattern_status' in result_df.columns:
            stats['by_status'] = result_df['pattern_status'].value_counts().to_dict()

        if 'pattern_source' in result_df.columns:
            stats['by_source'] = result_df['pattern_source'].value_counts().to_dict()

        if 'pattern_tier' in result_df.columns:
            tier_counts = result_df['pattern_tier'].dropna().value_counts().to_dict()
            stats['by_tier'] = {int(k): v for k, v in tier_counts.items()}

        if 'pattern_needs_verification' in result_df.columns:
            stats['needs_verification'] = result_df['pattern_needs_verification'].sum()

        if 'pattern_confidence' in result_df.columns:
            valid_conf = result_df[result_df['pattern_confidence'] > 0]['pattern_confidence']
            if len(valid_conf) > 0:
                stats['avg_confidence'] = valid_conf.mean()

        return stats

    def get_verification_queue(self, result_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract records that need pattern verification.

        Args:
            result_df: Output from run()

        Returns:
            DataFrame of records needing verification
        """
        if 'pattern_needs_verification' not in result_df.columns:
            return pd.DataFrame()

        queue_df = result_df[result_df['pattern_needs_verification'] == True].copy()

        # Add queue metadata
        queue_df['verification_type'] = 'pattern'
        queue_df['queued_at'] = datetime.now().isoformat()

        return queue_df


def discover_email_patterns(domain_df: pd.DataFrame,
                            config: Dict[str, Any] = None) -> Tuple[pd.DataFrame, Phase3Stats]:
    """
    Convenience function to run email pattern discovery.

    Args:
        domain_df: DataFrame with domains from Phase 2
        config: Optional configuration

    Returns:
        Tuple of (result_df, Phase3Stats)
    """
    phase3 = Phase3EmailPatternWaterfall(config=config)
    return phase3.run(domain_df)


def discover_pattern_for_domain(domain: str, max_tier: int = 2,
                                config: Dict[str, Any] = None) -> PatternResult:
    """
    Discover email pattern for a single domain.

    Args:
        domain: Domain to discover pattern for
        max_tier: Maximum tier to use (0, 1, or 2)
        config: Optional configuration

    Returns:
        PatternResult
    """
    config = config or {}
    config['max_tier'] = max_tier
    phase3 = Phase3EmailPatternWaterfall(config=config)
    return phase3._discover_pattern(normalize_domain(domain), '', [])
