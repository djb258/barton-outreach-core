# Waterfall Optimization Engine (WOE)

System-level subsystem for dynamically optimizing waterfall ordering across all enrichment pipelines.

## Overview

The Waterfall Optimization Engine reads Provider Benchmark Engine (PBE) scorecards and produces optimized waterfall tier orderings. It determines which providers should be promoted, demoted, or removed from the waterfall based on performance metrics.

## Architecture

```
                    ┌─────────────────────────────┐
                    │   Provider Benchmark Engine │
                    │          (PBE)              │
                    └─────────────┬───────────────┘
                                  │ Scorecards
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              WATERFALL OPTIMIZATION ENGINE (WOE)                │
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │ WaterfallOpti-  │───▶│        OptimizationPlan          │   │
│  │     mizer       │    │  - ordered_providers             │   │
│  │                 │    │  - promoted/demoted/removed      │   │
│  │ - thresholds    │    │  - rationale                     │   │
│  │ - tier rules    │    │  - timestamp                     │   │
│  └─────────────────┘    └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼ OptimizationPlan
              ┌───────────────────┴───────────────────┐
              │                                       │
    ┌─────────▼─────────┐              ┌─────────────▼───────────┐
    │  Company Pipeline │              │    People Pipeline      │
    │   (Phases 1-4)    │              │   (Phase 5 waterfall)   │
    └───────────────────┘              └─────────────────────────┘
```

## Components

### WaterfallOptimizer

Core optimization engine that reads PBE data and produces tier recommendations.

```python
from ctb.sys.enrichment.waterfall_optimization import WaterfallOptimizer

optimizer = WaterfallOptimizer()
plan = optimizer.generate_optimized_order()

# Access optimized order
print(plan.ordered_providers['tier0'])  # ['firecrawl', 'scraperapi', ...]
print(plan.promoted)                     # ['hunter'] if promoted
print(plan.demoted)                      # ['clearbit'] if demoted
print(plan.rationale)                    # Explanation of changes
```

### OptimizationPlan

Data container holding optimization results.

```python
from ctb.sys.enrichment.waterfall_optimization import OptimizationPlan

# Access plan properties
plan.ordered_providers   # Dict of tier -> providers
plan.promoted            # List of promoted providers
plan.demoted             # List of demoted providers
plan.removed             # List of removed providers
plan.rationale           # Text explanation
plan.timestamp           # When generated
plan.has_changes         # True if any changes made
plan.total_providers     # Count of all providers
plan.to_dict()           # Serialize to dict
```

## Tier Structure

```
Tier 0: Free/Low-Cost
  └── firecrawl, scraperapi, googleplaces
       ↓
Tier 1: Standard Paid
  └── hunter, apollo, clay
       ↓
Tier 1.5: Mid-Tier
  └── prospeo, snov
       ↓
Tier 2: Premium
  └── clearbit, pdl, zenrows
       ↓
Tier 3: Enterprise
  └── zoominfo
```

## Configuration

```python
optimizer = WaterfallOptimizer(config={
    'promotion_threshold': 0.8,     # Score >= 0.8 for promotion
    'demotion_threshold': 0.4,      # Score < 0.4 for demotion
    'removal_threshold': 0.2,       # Score < 0.2 for removal
    'min_calls_for_decision': 10    # Min calls before changes
})
```

## Integration

### Pipeline Engine

```python
# In pipeline_engine/main.py
from ctb.sys.enrichment.waterfall_optimization import WaterfallOptimizer

class PipelineEngine:
    def __init__(self):
        self.waterfall_optimizer = WaterfallOptimizer()

    def optimize_waterfall(self):
        return self.waterfall_optimizer.generate_optimized_order()
```

### Consumer Pipelines

- Company Pipeline (Phases 1-4)
- People Pipeline (Phase 5 waterfall)
- Talent Flow Phase 0
- DOL Node (future)
- Blog Intelligence Pipeline (future)
- Outreach Node (future)

## API Reference

### WaterfallOptimizer

| Method | Description |
|--------|-------------|
| `generate_optimized_order()` | Generate new optimization plan |
| `get_current_order()` | Get current waterfall order |
| `get_optimization_history()` | Get all past plans |
| `get_last_optimization_time()` | Get last run timestamp |
| `has_sufficient_data()` | Check if enough data for decisions |
| `get_provider_tier(name)` | Get tier for provider |
| `reset_optimization()` | Reset to default order |
| `export_state()` | Export state for debugging |

### OptimizationPlan

| Property | Description |
|----------|-------------|
| `ordered_providers` | Dict of tier -> provider list |
| `promoted` | List of promoted providers |
| `demoted` | List of demoted providers |
| `removed` | List of removed providers |
| `rationale` | Explanation text |
| `timestamp` | Generation time |
| `has_changes` | Boolean if any changes |
| `total_providers` | Total provider count |
| `tier_count` | Number of tiers |
| `to_dict()` | Serialize to dict |
| `from_dict(data)` | Deserialize from dict |

## Rules

See [RULES.md](./RULES.md) for complete optimization rules including:
- Tier movement constraints
- Threshold definitions
- Safety rules
- Cost awareness requirements

## Status

**Version**: 1.0.0
**Status**: Shell implementation (placeholder logic)

Future iterations will add:
- Real PBE integration
- Score calculation algorithms
- ML-based optimization
- Context-aware ordering

## Files

```
waterfall_optimization/
├── __init__.py           # Module exports
├── waterfall_optimizer.py # Core optimization engine
├── optimization_plan.py   # Data container
├── RULES.md              # Optimization rules
└── README.md             # This file
```
