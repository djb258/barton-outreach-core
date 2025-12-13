"""
Provider Latency Tracker
========================
Helper module to measure provider response times with context manager support.

Provides accurate timing measurements for provider API calls without
actually making network requests. Designed for benchmarking and testing.

Architecture:
- System-level component (Hub-and-Spoke doctrine)
- Deterministic, non-networked
- Context manager pattern for clean timing

Usage:
    with ProviderLatencyTracker('firecrawl') as tracker:
        # ... provider call simulation ...

    latency_ms = tracker.latency_ms
"""

import time
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LatencyMeasurement:
    """Result of a latency measurement."""
    provider_name: str
    start_time: float
    end_time: float
    latency_ms: float
    success: bool
    error_message: Optional[str] = None
    measured_at: datetime = None

    def __post_init__(self):
        if self.measured_at is None:
            self.measured_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'provider_name': self.provider_name,
            'latency_ms': round(self.latency_ms, 2),
            'success': self.success,
            'error_message': self.error_message,
            'measured_at': self.measured_at.isoformat() if self.measured_at else None
        }


class ProviderLatencyTracker:
    """
    Helper to measure how long a provider lookup takes.

    Can be used as a context manager or standalone.

    Context Manager Usage:
        with ProviderLatencyTracker('firecrawl') as tracker:
            # ... simulated provider call ...

        print(f"Latency: {tracker.latency_ms}ms")

    Standalone Usage:
        tracker = ProviderLatencyTracker('firecrawl')
        tracker.start()
        # ... simulated provider call ...
        tracker.stop()
        print(f"Latency: {tracker.latency_ms}ms")
    """

    def __init__(self, provider_name: str = 'unknown'):
        """
        Initialize latency tracker.

        Args:
            provider_name: Name of the provider being tracked
        """
        self.provider_name = provider_name
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._success: bool = True
        self._error_message: Optional[str] = None

    def __enter__(self) -> 'ProviderLatencyTracker':
        """Start timing when entering context."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Stop timing when exiting context."""
        self.stop()

        # Record any exception that occurred
        if exc_type is not None:
            self._success = False
            self._error_message = str(exc_val) if exc_val else str(exc_type)

        # Don't suppress exceptions
        return False

    def start(self) -> None:
        """Start the latency timer."""
        self._start_time = time.perf_counter()
        self._end_time = None
        self._success = True
        self._error_message = None

    def stop(self, success: bool = True, error_message: str = None) -> None:
        """
        Stop the latency timer.

        Args:
            success: Whether the operation was successful
            error_message: Optional error message if failed
        """
        self._end_time = time.perf_counter()
        self._success = success
        self._error_message = error_message

    @property
    def latency_ms(self) -> float:
        """
        Get the measured latency in milliseconds.

        Returns:
            Latency in milliseconds, or 0.0 if not measured
        """
        if self._start_time is None or self._end_time is None:
            return 0.0
        return (self._end_time - self._start_time) * 1000

    @property
    def latency_seconds(self) -> float:
        """
        Get the measured latency in seconds.

        Returns:
            Latency in seconds, or 0.0 if not measured
        """
        return self.latency_ms / 1000

    @property
    def is_measured(self) -> bool:
        """Check if a measurement has been taken."""
        return self._start_time is not None and self._end_time is not None

    @property
    def success(self) -> bool:
        """Check if the tracked operation was successful."""
        return self._success

    def get_measurement(self) -> Optional[LatencyMeasurement]:
        """
        Get the latency measurement as a structured object.

        Returns:
            LatencyMeasurement or None if not measured
        """
        if not self.is_measured:
            return None

        return LatencyMeasurement(
            provider_name=self.provider_name,
            start_time=self._start_time,
            end_time=self._end_time,
            latency_ms=self.latency_ms,
            success=self._success,
            error_message=self._error_message
        )

    def reset(self) -> None:
        """Reset the tracker for reuse."""
        self._start_time = None
        self._end_time = None
        self._success = True
        self._error_message = None


class BatchLatencyTracker:
    """
    Track latency for multiple operations.

    Useful for measuring batch provider calls or comparing multiple providers.

    Usage:
        batch = BatchLatencyTracker()

        with batch.track('firecrawl'):
            # ... firecrawl call ...

        with batch.track('hunter'):
            # ... hunter call ...

        print(batch.get_summary())
    """

    def __init__(self):
        """Initialize batch tracker."""
        self._measurements: list[LatencyMeasurement] = []

    def track(self, provider_name: str) -> ProviderLatencyTracker:
        """
        Create a tracker for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            ProviderLatencyTracker context manager
        """
        return _BatchTrackerContext(self, provider_name)

    def add_measurement(self, measurement: LatencyMeasurement) -> None:
        """
        Add a measurement to the batch.

        Args:
            measurement: LatencyMeasurement to add
        """
        self._measurements.append(measurement)

    def get_measurements(self) -> list[LatencyMeasurement]:
        """Get all measurements."""
        return self._measurements.copy()

    def get_by_provider(self, provider_name: str) -> list[LatencyMeasurement]:
        """
        Get measurements for a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            List of measurements for that provider
        """
        return [m for m in self._measurements if m.provider_name == provider_name]

    def get_summary(self) -> dict:
        """
        Get summary statistics for all measurements.

        Returns:
            Dict with summary stats by provider
        """
        by_provider = {}

        for m in self._measurements:
            if m.provider_name not in by_provider:
                by_provider[m.provider_name] = {
                    'count': 0,
                    'total_ms': 0.0,
                    'min_ms': float('inf'),
                    'max_ms': 0.0,
                    'successes': 0,
                    'failures': 0
                }

            stats = by_provider[m.provider_name]
            stats['count'] += 1
            stats['total_ms'] += m.latency_ms
            stats['min_ms'] = min(stats['min_ms'], m.latency_ms)
            stats['max_ms'] = max(stats['max_ms'], m.latency_ms)

            if m.success:
                stats['successes'] += 1
            else:
                stats['failures'] += 1

        # Calculate averages
        for provider, stats in by_provider.items():
            if stats['count'] > 0:
                stats['avg_ms'] = round(stats['total_ms'] / stats['count'], 2)
                stats['min_ms'] = round(stats['min_ms'], 2) if stats['min_ms'] != float('inf') else 0.0
                stats['max_ms'] = round(stats['max_ms'], 2)
            else:
                stats['avg_ms'] = 0.0
                stats['min_ms'] = 0.0

        return {
            'total_measurements': len(self._measurements),
            'by_provider': by_provider
        }

    def reset(self) -> None:
        """Clear all measurements."""
        self._measurements = []


class _BatchTrackerContext:
    """Internal context manager for batch tracking."""

    def __init__(self, batch: BatchLatencyTracker, provider_name: str):
        self._batch = batch
        self._tracker = ProviderLatencyTracker(provider_name)

    def __enter__(self) -> ProviderLatencyTracker:
        return self._tracker.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        result = self._tracker.__exit__(exc_type, exc_val, exc_tb)
        measurement = self._tracker.get_measurement()
        if measurement:
            self._batch.add_measurement(measurement)
        return result


def measure_latency(func: Callable, provider_name: str = 'unknown', *args, **kwargs) -> tuple[Any, float]:
    """
    Measure the latency of a function call.

    Args:
        func: Function to measure
        provider_name: Name for tracking purposes
        *args: Arguments to pass to function
        **kwargs: Keyword arguments to pass to function

    Returns:
        Tuple of (function_result, latency_ms)
    """
    with ProviderLatencyTracker(provider_name) as tracker:
        result = func(*args, **kwargs)
    return result, tracker.latency_ms
