"""
Provider Benchmark Engine
=========================
System-level orchestrator for provider performance tracking and optimization.

This is the main entry point for the Provider Benchmark Engine subsystem.
It coordinates between:
- ProviderMetrics: Write-only metrics recording
- ProviderLatencyTracker: Timing measurements
- ProviderScorecard: ROI analysis and recommendations

Architecture:
- System-level component (Hub-and-Spoke doctrine)
- Pipeline-agnostic (works across all enrichment pipelines)
- Deterministic, non-networked
- Thread-safe singleton pattern

Usage:
    engine = ProviderBenchmarkEngine.get_instance()

    # Record metrics
    engine.record_call('firecrawl', cost=0.001)
    engine.record_result('firecrawl', pattern_found=True, verified=True, latency=150.5)

    # Get scorecard
    scores = engine.get_scores()

    # Get optimization plan
    plan = engine.get_tier_optimization_plan()
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from threading import Lock

from .provider_metrics import ProviderMetrics, MetricEventType
from .provider_latency_tracker import ProviderLatencyTracker, BatchLatencyTracker
from .provider_scorecard import ProviderScorecard, TierRecommendation


class ProviderBenchmarkEngine:
    """
    System-level orchestrator for provider benchmarking.

    Singleton pattern ensures consistent metrics across all pipelines.

    Features:
    - Unified metrics recording
    - Automatic cost tracking from profiles
    - Latency tracking with context managers
    - ROI scoring and tier recommendations
    - Export capabilities for analysis

    Usage:
        engine = ProviderBenchmarkEngine.get_instance()

        # Simple recording
        engine.record_call('firecrawl')

        # With latency tracking
        with engine.track_latency('hunter') as tracker:
            # ... provider operation ...
            pass

        engine.record_result('hunter',
            pattern_found=True,
            verified=True,
            latency=tracker.latency_ms
        )

        # Get scores
        scores = engine.get_scores()
        print(scores['hunter']['tier_recommendation'])
    """

    _instance: Optional['ProviderBenchmarkEngine'] = None
    _lock: Lock = Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern - returns existing instance if available."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'ProviderBenchmarkEngine':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            cls._instance = None

    def __init__(self):
        """Initialize the benchmark engine."""
        # Prevent re-initialization of singleton
        if hasattr(self, '_initialized') and self._initialized:
            return

        self._initialized = True
        self._metrics = ProviderMetrics()
        self._scorecard = ProviderScorecard()
        self._batch_tracker = BatchLatencyTracker()

        # Load configuration files
        self._base_path = Path(__file__).parent
        self._registry = self._load_json('provider_registry.json')
        self._cost_profile = self._load_json('provider_cost_profile.json')

        self._created_at = datetime.now()
        self._last_score_calculation: Optional[datetime] = None

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load a JSON configuration file."""
        file_path = self._base_path / filename
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    def _save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Save data to a JSON file."""
        file_path = self._base_path / filename
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    # =========================================================================
    # METRICS RECORDING
    # =========================================================================

    def record_call(self, provider_name: str, cost: float = None) -> None:
        """
        Record a provider API call.

        Args:
            provider_name: Name of the provider
            cost: Override cost (uses profile cost if not provided)
        """
        if cost is None:
            cost = self._get_provider_cost(provider_name)
        self._metrics.record_call(provider_name, cost)

    def record_result(
        self,
        provider_name: str,
        pattern_found: bool,
        verified: bool,
        latency: float,
        cost: float = None
    ) -> None:
        """
        Record the result of a provider call.

        Args:
            provider_name: Name of the provider
            pattern_found: Whether a pattern was discovered
            verified: Whether the pattern passed verification
            latency: Response time in milliseconds
            cost: Override cost (uses profile cost if not provided)
        """
        if cost is None:
            cost = self._get_provider_cost(provider_name)
        self._metrics.record_result(provider_name, pattern_found, verified, latency, cost)

    def record_error(self, provider_name: str, error_type: str = 'error') -> None:
        """
        Record a provider error.

        Args:
            provider_name: Name of the provider
            error_type: Type of error ('error' or 'timeout')
        """
        self._metrics.record_error(provider_name, error_type)

    def record_event(
        self,
        provider_name: str,
        event_type: MetricEventType,
        latency: float = 0.0,
        cost: float = None
    ) -> None:
        """
        Record a generic metric event.

        Args:
            provider_name: Name of the provider
            event_type: Type of event
            latency: Optional response time in milliseconds
            cost: Override cost (uses profile cost if not provided)
        """
        if cost is None:
            cost = self._get_provider_cost(provider_name)
        self._metrics.record_event(provider_name, event_type, latency, cost)

    def _get_provider_cost(self, provider_name: str) -> float:
        """Get cost per call from profile."""
        if provider_name in self._cost_profile:
            return self._cost_profile[provider_name].get('cost_per_call', 0.0)
        return 0.0

    # =========================================================================
    # LATENCY TRACKING
    # =========================================================================

    def track_latency(self, provider_name: str) -> ProviderLatencyTracker:
        """
        Create a latency tracker for a provider.

        Can be used as a context manager.

        Args:
            provider_name: Name of the provider

        Returns:
            ProviderLatencyTracker context manager

        Usage:
            with engine.track_latency('firecrawl') as tracker:
                # ... operation ...
                pass
            latency = tracker.latency_ms
        """
        return ProviderLatencyTracker(provider_name)

    def track_batch(self, provider_name: str) -> ProviderLatencyTracker:
        """
        Track latency as part of a batch operation.

        Measurements are automatically collected.

        Args:
            provider_name: Name of the provider

        Returns:
            Context manager for tracking
        """
        return self._batch_tracker.track(provider_name)

    def get_batch_summary(self) -> Dict[str, Any]:
        """Get summary of batch latency measurements."""
        return self._batch_tracker.get_summary()

    def reset_batch_tracker(self) -> None:
        """Reset batch latency tracker."""
        self._batch_tracker.reset()

    # =========================================================================
    # SCORING AND ANALYSIS
    # =========================================================================

    def calculate_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate scores for all providers.

        Returns:
            Dict of provider_name → score details
        """
        self._last_score_calculation = datetime.now()
        return self._scorecard.calculate(
            self._metrics.export_metrics(),
            self._cost_profile,
            self._registry
        )

    def get_scores(self, recalculate: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get provider scores, optionally recalculating.

        Args:
            recalculate: Force recalculation of scores

        Returns:
            Dict of provider_name → score details
        """
        if recalculate or self._last_score_calculation is None:
            return self.calculate_scores()
        return self._scorecard.export_scorecard()['scores']

    def get_recommendations(self) -> Dict[str, str]:
        """
        Get tier recommendations for all providers.

        Returns:
            Dict of provider_name → recommendation
        """
        if self._last_score_calculation is None:
            self.calculate_scores()
        return {
            name: rec.value
            for name, rec in self._scorecard.get_recommendations().items()
        }

    def get_tier_optimization_plan(self) -> Dict[str, Any]:
        """
        Get a tier optimization plan based on current scores.

        Returns:
            Dict with recommended changes
        """
        if self._last_score_calculation is None:
            self.calculate_scores()
        return self._scorecard.get_tier_optimization_plan()

    def get_top_performers(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get top N performing providers.

        Args:
            n: Number of providers to return

        Returns:
            List of score dicts
        """
        if self._last_score_calculation is None:
            self.calculate_scores()
        return [s.to_dict() for s in self._scorecard.get_top_performers(n)]

    def get_underperformers(self, threshold: float = None) -> List[Dict[str, Any]]:
        """
        Get providers performing below threshold.

        Args:
            threshold: Score threshold

        Returns:
            List of score dicts
        """
        if self._last_score_calculation is None:
            self.calculate_scores()
        return [s.to_dict() for s in self._scorecard.get_underperformers(threshold)]

    # =========================================================================
    # PROVIDER REGISTRY
    # =========================================================================

    def get_provider_info(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Get registry info for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Registry entry or None
        """
        return self._registry.get(provider_name)

    def get_providers_by_tier(self, tier: int) -> List[str]:
        """
        Get providers in a specific tier.

        Args:
            tier: Tier number (0, 1, 2, 3)

        Returns:
            List of provider names
        """
        return [
            name for name, info in self._registry.items()
            if info.get('tier') == tier
        ]

    def get_providers_by_category(self, category: str) -> List[str]:
        """
        Get providers in a specific category.

        Args:
            category: Category name (scrape, email_lookup, enrichment, etc.)

        Returns:
            List of provider names
        """
        return [
            name for name, info in self._registry.items()
            if info.get('category') == category
        ]

    def get_all_providers(self) -> List[str]:
        """Get list of all registered providers."""
        return list(self._registry.keys())

    # =========================================================================
    # COST PROFILE
    # =========================================================================

    def get_provider_cost(self, provider_name: str) -> Dict[str, Any]:
        """
        Get cost profile for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Cost profile or empty dict
        """
        return self._cost_profile.get(provider_name, {})

    def estimate_cost(self, provider_name: str, call_count: int) -> float:
        """
        Estimate cost for a number of calls.

        Args:
            provider_name: Name of the provider
            call_count: Number of calls to estimate

        Returns:
            Estimated cost in USD
        """
        cost_per_call = self._get_provider_cost(provider_name)
        return cost_per_call * call_count

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get cost summary from metrics.

        Returns:
            Dict with cost breakdown by provider
        """
        summary = self._metrics.get_summary()
        return {
            'total_cost': summary['total_cost'],
            'by_provider': {
                name: self._metrics.get_provider_metrics(name).get('cost_accumulated', 0.0)
                for name in self._metrics.get_all_providers()
            }
        }

    # =========================================================================
    # DATA EXPORT
    # =========================================================================

    def export_all(self) -> Dict[str, Any]:
        """
        Export all benchmark data.

        Returns:
            Dict with metrics, scores, and configuration
        """
        return {
            'engine_created_at': self._created_at.isoformat(),
            'exported_at': datetime.now().isoformat(),
            'metrics': self._metrics.export_metrics(),
            'scorecard': self._scorecard.export_scorecard() if self._last_score_calculation else None,
            'registry': self._registry,
            'cost_profile': self._cost_profile,
            'batch_latency': self._batch_tracker.get_summary()
        }

    def export_to_file(self, filename: str = None) -> str:
        """
        Export all data to a JSON file.

        Args:
            filename: Output filename (default: benchmark_export_<timestamp>.json)

        Returns:
            Path to the exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'benchmark_export_{timestamp}.json'

        output_path = self._base_path / 'output'
        output_path.mkdir(exist_ok=True)

        file_path = output_path / filename
        with open(file_path, 'w') as f:
            json.dump(self.export_all(), f, indent=2, default=str)

        return str(file_path)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics."""
        return self._metrics.get_summary()

    def get_provider_metrics(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a specific provider."""
        return self._metrics.get_provider_metrics(provider_name)

    # =========================================================================
    # RESET AND MANAGEMENT
    # =========================================================================

    def reset_metrics(self) -> None:
        """Reset all metrics (not scores or config)."""
        self._metrics.reset_all()
        self._batch_tracker.reset()

    def reset_provider_metrics(self, provider_name: str) -> None:
        """Reset metrics for a specific provider."""
        self._metrics.reset_provider(provider_name)

    def reload_config(self) -> None:
        """Reload configuration files."""
        self._registry = self._load_json('provider_registry.json')
        self._cost_profile = self._load_json('provider_cost_profile.json')

    # =========================================================================
    # CONVENIENCE METHODS FOR PIPELINES
    # =========================================================================

    def record_waterfall_attempt(
        self,
        provider_name: str,
        success: bool,
        pattern_verified: bool,
        latency_ms: float
    ) -> None:
        """
        Convenience method for waterfall integrations.

        Args:
            provider_name: Name of the provider
            success: Whether provider returned a result
            pattern_verified: Whether result was verified
            latency_ms: Response time
        """
        self.record_call(provider_name)
        self.record_result(
            provider_name,
            pattern_found=success,
            verified=pattern_verified,
            latency=latency_ms
        )

    def record_waterfall_failure(
        self,
        provider_name: str,
        is_timeout: bool = False
    ) -> None:
        """
        Convenience method for waterfall failures.

        Args:
            provider_name: Name of the provider
            is_timeout: Whether the failure was a timeout
        """
        self.record_call(provider_name)
        self.record_error(provider_name, 'timeout' if is_timeout else 'error')

    def get_recommended_provider_order(self, use_case: str) -> List[str]:
        """
        Get recommended provider order for a use case.

        Combines registry tiers with performance scores.

        Args:
            use_case: The use case to filter by

        Returns:
            List of provider names in recommended order
        """
        # Get providers supporting this use case
        providers = []
        for name, info in self._registry.items():
            if use_case in info.get('use_cases', []):
                providers.append({
                    'name': name,
                    'tier': info.get('tier', 99),
                    'score': 0.5  # Default score
                })

        # Add scores if available
        if self._last_score_calculation:
            scores = self._scorecard.get_scores()
            for p in providers:
                if p['name'] in scores:
                    p['score'] = scores[p['name']].overall_score

        # Sort by tier first, then by score (descending)
        providers.sort(key=lambda x: (x['tier'], -x['score']))

        return [p['name'] for p in providers]


# Module-level convenience function
def get_benchmark_engine() -> ProviderBenchmarkEngine:
    """Get the global benchmark engine instance."""
    return ProviderBenchmarkEngine.get_instance()
