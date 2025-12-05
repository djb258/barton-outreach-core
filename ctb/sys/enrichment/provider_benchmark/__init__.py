"""
Provider Benchmark Engine (PBE)
===============================
System-level subsystem for tracking and evaluating enrichment providers.

This module operates at the SYSTEM level according to Hub-and-Spoke doctrine,
providing centralized provider analytics for all pipelines.

Components:
- ProviderMetrics: Tracks provider call metrics
- ProviderLatencyTracker: Measures provider response times
- ProviderScorecard: Calculates ROI and quality scores
- ProviderBenchmarkEngine: System orchestrator

Used by:
- Company Identity Pipeline (Phases 1-4)
- People Pipeline (Phases 5-8)
- Talent Flow Gate (Phase 0)
- DOL Federal Data Node
- Blog Intelligence Node
- Outreach Node
"""

from .provider_metrics import ProviderMetrics
from .provider_latency_tracker import ProviderLatencyTracker
from .provider_scorecard import ProviderScorecard
from .provider_benchmark_engine import ProviderBenchmarkEngine

__all__ = [
    'ProviderMetrics',
    'ProviderLatencyTracker',
    'ProviderScorecard',
    'ProviderBenchmarkEngine',
]

__version__ = '1.0.0'
