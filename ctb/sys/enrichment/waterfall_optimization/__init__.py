"""
Waterfall Optimization Engine (WOE)
===================================
System-level subsystem for dynamically optimizing waterfall ordering
across all enrichment pipelines.

Architecture:
- System-level component (Hub-and-Spoke doctrine)
- Pipeline-agnostic (works across all enrichment pipelines)
- Deterministic, non-networked
- Uses Provider Benchmark Engine (PBE) for metrics

Components:
- WaterfallOptimizer: Core optimization engine
- OptimizationPlan: Data container for optimization results

Usage:
    from ctb.sys.enrichment.waterfall_optimization import WaterfallOptimizer

    optimizer = WaterfallOptimizer()
    plan = optimizer.generate_optimized_order()

    # Inspect plan
    print(plan.ordered_providers)
    print(plan.promoted)
    print(plan.demoted)

Consumers:
- Company Pipeline (Phases 1-4)
- People Pipeline (Phase 5 waterfall)
- Talent Flow Phase 0
- DOL Node (future)
- Blog Intelligence Pipeline (future)
- Outreach Node (future)

Version: 1.0.0
"""

from .waterfall_optimizer import WaterfallOptimizer
from .optimization_plan import OptimizationPlan

__all__ = [
    'WaterfallOptimizer',
    'OptimizationPlan'
]

__version__ = '1.0.0'
