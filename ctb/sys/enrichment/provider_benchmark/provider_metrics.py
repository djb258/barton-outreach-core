"""
Provider Metrics Recorder
=========================
Tracks global metrics for each enrichment provider across all pipelines.

This is a write-only recorder. Analysis is performed by ProviderScorecard.

Metrics tracked per provider:
- calls_made: Total API calls
- patterns_found: Successful pattern discoveries
- verified_hits: Patterns that passed verification
- false_positives: Patterns that failed verification
- latency_samples: Response time measurements
- cost_accumulated: Total cost incurred
- errors: Provider errors/failures
- timeouts: Request timeouts

Architecture:
- System-level component (Hub-and-Spoke doctrine)
- Pipeline-agnostic
- Deterministic, non-networked
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class MetricEventType(Enum):
    """Types of metric events."""
    CALL = "call"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    ERROR = "error"
    VERIFIED = "verified"
    FALSE_POSITIVE = "false_positive"


@dataclass
class ProviderMetricEntry:
    """Metrics for a single provider."""
    provider_name: str
    calls_made: int = 0
    patterns_found: int = 0
    verified_hits: int = 0
    false_positives: int = 0
    errors: int = 0
    timeouts: int = 0
    latency_samples: List[float] = field(default_factory=list)
    cost_accumulated: float = 0.0
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'provider_name': self.provider_name,
            'calls_made': self.calls_made,
            'patterns_found': self.patterns_found,
            'verified_hits': self.verified_hits,
            'false_positives': self.false_positives,
            'errors': self.errors,
            'timeouts': self.timeouts,
            'latency_samples_count': len(self.latency_samples),
            'latency_mean_ms': self._calculate_mean_latency(),
            'cost_accumulated': self.cost_accumulated,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

    def _calculate_mean_latency(self) -> float:
        """Calculate mean latency from samples."""
        if not self.latency_samples:
            return 0.0
        return sum(self.latency_samples) / len(self.latency_samples)


class ProviderMetrics:
    """
    Tracks global metrics for each provider.

    Metrics tracked:
    - calls_made
    - patterns_found
    - verified_hits
    - false_positives
    - latency_samples
    - cost_accumulated

    Write-only; analysis is done in ProviderScorecard.

    Usage:
        metrics = ProviderMetrics()
        metrics.record_call('firecrawl')
        metrics.record_result('firecrawl', pattern_found=True, verified=True, latency=150.5)
    """

    def __init__(self):
        """Initialize metrics tracker with empty data store."""
        self.data: Dict[str, ProviderMetricEntry] = {}
        self._created_at = datetime.now()

    def _ensure_provider(self, provider_name: str) -> ProviderMetricEntry:
        """Ensure provider entry exists, create if not."""
        if provider_name not in self.data:
            self.data[provider_name] = ProviderMetricEntry(provider_name=provider_name)
        return self.data[provider_name]

    def record_call(self, provider_name: str, cost: float = 0.0) -> None:
        """
        Record a provider API call.

        Args:
            provider_name: Name of the provider
            cost: Optional cost of the call (default: 0.0)
        """
        entry = self._ensure_provider(provider_name)
        entry.calls_made += 1
        entry.cost_accumulated += cost
        entry.last_updated = datetime.now()

    def record_result(
        self,
        provider_name: str,
        pattern_found: bool,
        verified: bool,
        latency: float,
        cost: float = 0.0
    ) -> None:
        """
        Record the result of a provider call.

        Args:
            provider_name: Name of the provider
            pattern_found: Whether a pattern was discovered
            verified: Whether the pattern passed verification
            latency: Response time in milliseconds
            cost: Optional cost of the call (default: 0.0)
        """
        entry = self._ensure_provider(provider_name)

        # Record latency
        if latency > 0:
            entry.latency_samples.append(latency)

        # Record pattern outcome
        if pattern_found:
            entry.patterns_found += 1
            if verified:
                entry.verified_hits += 1
            else:
                entry.false_positives += 1

        # Record cost
        entry.cost_accumulated += cost
        entry.last_updated = datetime.now()

    def record_error(self, provider_name: str, error_type: str = 'error') -> None:
        """
        Record a provider error.

        Args:
            provider_name: Name of the provider
            error_type: Type of error ('error' or 'timeout')
        """
        entry = self._ensure_provider(provider_name)

        if error_type == 'timeout':
            entry.timeouts += 1
        else:
            entry.errors += 1

        entry.last_updated = datetime.now()

    def record_event(
        self,
        provider_name: str,
        event_type: MetricEventType,
        latency: float = 0.0,
        cost: float = 0.0
    ) -> None:
        """
        Record a generic metric event.

        Args:
            provider_name: Name of the provider
            event_type: Type of event (from MetricEventType)
            latency: Optional response time in milliseconds
            cost: Optional cost of the operation
        """
        entry = self._ensure_provider(provider_name)

        if event_type == MetricEventType.CALL:
            entry.calls_made += 1
        elif event_type == MetricEventType.SUCCESS:
            entry.patterns_found += 1
        elif event_type == MetricEventType.VERIFIED:
            entry.verified_hits += 1
        elif event_type == MetricEventType.FALSE_POSITIVE:
            entry.false_positives += 1
        elif event_type == MetricEventType.ERROR:
            entry.errors += 1
        elif event_type == MetricEventType.TIMEOUT:
            entry.timeouts += 1

        if latency > 0:
            entry.latency_samples.append(latency)

        entry.cost_accumulated += cost
        entry.last_updated = datetime.now()

    def get_provider_metrics(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metrics for a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Dict with provider metrics or None if not found
        """
        if provider_name not in self.data:
            return None
        return self.data[provider_name].to_dict()

    def get_all_providers(self) -> List[str]:
        """
        Get list of all tracked providers.

        Returns:
            List of provider names
        """
        return list(self.data.keys())

    def export_metrics(self) -> Dict[str, Any]:
        """
        Export all metrics data.

        Returns:
            Dict with all provider metrics
        """
        return {
            'created_at': self._created_at.isoformat(),
            'exported_at': datetime.now().isoformat(),
            'providers': {
                name: entry.to_dict()
                for name, entry in self.data.items()
            }
        }

    def reset_provider(self, provider_name: str) -> None:
        """
        Reset metrics for a specific provider.

        Args:
            provider_name: Name of the provider to reset
        """
        if provider_name in self.data:
            self.data[provider_name] = ProviderMetricEntry(provider_name=provider_name)

    def reset_all(self) -> None:
        """Reset all provider metrics."""
        self.data = {}
        self._created_at = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.

        Returns:
            Dict with summary statistics
        """
        total_calls = sum(e.calls_made for e in self.data.values())
        total_patterns = sum(e.patterns_found for e in self.data.values())
        total_verified = sum(e.verified_hits for e in self.data.values())
        total_cost = sum(e.cost_accumulated for e in self.data.values())
        total_errors = sum(e.errors + e.timeouts for e in self.data.values())

        return {
            'total_providers': len(self.data),
            'total_calls': total_calls,
            'total_patterns_found': total_patterns,
            'total_verified': total_verified,
            'total_cost': round(total_cost, 4),
            'total_errors': total_errors,
            'overall_success_rate': round(total_patterns / max(total_calls, 1), 4),
            'overall_verification_rate': round(total_verified / max(total_patterns, 1), 4)
        }
