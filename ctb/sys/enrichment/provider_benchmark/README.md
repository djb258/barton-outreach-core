# Provider Benchmark Engine (PBE)

System-level subsystem for tracking and evaluating enrichment provider performance.

## Overview

The Provider Benchmark Engine operates at the **SYSTEM level** according to Hub-and-Spoke doctrine, providing centralized provider analytics for all pipelines. It tracks:

- **Cost**: Per-call and accumulated costs
- **Accuracy**: Pattern discovery and verification rates
- **Latency**: Response time measurements
- **Confidence**: Quality scores based on verified hits
- **Failure Modes**: Errors, timeouts, and reliability
- **ROI Scoring**: Dynamic tier recommendations

## Architecture

```
provider_benchmark/
├── __init__.py                    # Module exports
├── provider_registry.json         # Provider tier/category catalog
├── provider_cost_profile.json     # Cost per call estimates
├── provider_metrics.py            # Write-only metrics recorder
├── provider_latency_tracker.py    # Timing measurement utilities
├── provider_scorecard.py          # ROI scoring and recommendations
├── provider_benchmark_engine.py   # System-level orchestrator
└── README.md                      # This file
```

## Components

### ProviderMetrics

Write-only recorder for provider call metrics.

```python
from ctb.sys.enrichment.provider_benchmark import ProviderMetrics

metrics = ProviderMetrics()
metrics.record_call('firecrawl', cost=0.0001)
metrics.record_result('firecrawl',
    pattern_found=True,
    verified=True,
    latency=150.5
)
```

### ProviderLatencyTracker

Context manager for accurate timing measurements.

```python
from ctb.sys.enrichment.provider_benchmark import ProviderLatencyTracker

with ProviderLatencyTracker('hunter') as tracker:
    # ... provider operation ...
    pass

print(f"Latency: {tracker.latency_ms}ms")
```

### ProviderScorecard

Calculates ROI scores and tier recommendations.

```python
from ctb.sys.enrichment.provider_benchmark import ProviderScorecard

scorecard = ProviderScorecard()
scores = scorecard.calculate(metrics.export_metrics(), cost_profile, registry)

for provider, score in scores.items():
    print(f"{provider}: {score['overall_score']} - {score['tier_recommendation']}")
```

### ProviderBenchmarkEngine

Main orchestrator (singleton) that coordinates all components.

```python
from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine

engine = ProviderBenchmarkEngine.get_instance()

# Record metrics
engine.record_call('firecrawl')
engine.record_result('firecrawl', pattern_found=True, verified=True, latency=150.5)

# Get scores
scores = engine.get_scores()

# Get optimization plan
plan = engine.get_tier_optimization_plan()
```

## Provider Tiers

| Tier | Description | Providers |
|------|-------------|-----------|
| 0 | Free/very low cost | firecrawl, scraperapi, googleplaces |
| 1 | Low cost | hunter, apollo, clay |
| 1.5 | Moderate cost | prospeo, snov |
| 2 | Premium | clearbit, pdl, zenrows |
| 3 | Enterprise | zoominfo |

## Scoring Formula

```
overall_score = (quality * 0.4) + (cost_efficiency * 0.3) + (latency * 0.2) + (reliability * 0.1)
```

Where:
- **quality_score** = verified_hits / patterns_found
- **cost_efficiency** = 1 - (cost_per_success / max_cost)
- **latency_score** = 1 - (latency_mean / max_latency)
- **reliability** = 1 - (errors / calls_made)

## Tier Recommendations

| Recommendation | Threshold |
|----------------|-----------|
| **promote** | score >= 0.8 and in lower tier |
| **demote** | score < 0.4 |
| **remove** | score < 0.2 or reliability < 0.5 |
| **keep** | all others |

## Integration with Waterfall

```python
from ctb.sys.enrichment.provider_benchmark import ProviderBenchmarkEngine

engine = ProviderBenchmarkEngine.get_instance()

# In waterfall execution
for provider in ['firecrawl', 'hunter', 'apollo']:
    with engine.track_latency(provider) as tracker:
        result = call_provider(provider, domain)

    engine.record_result(
        provider,
        pattern_found=result.success,
        verified=result.verified,
        latency=tracker.latency_ms
    )

    if result.success:
        break
```

## Export Data

```python
# Export all data to JSON
engine = ProviderBenchmarkEngine.get_instance()
file_path = engine.export_to_file()

# Or get dict for processing
data = engine.export_all()
```

## Used By

- Company Identity Pipeline (Phases 1-4)
- People Pipeline (Phases 5-8)
- Talent Flow Gate (Phase 0)
- DOL Federal Data Node
- Blog Intelligence Node
- Outreach Node

## Key Design Principles

1. **System-level**: Operates independently of any single pipeline
2. **Pipeline-agnostic**: Works across all enrichment pipelines
3. **Deterministic**: No network calls, safe for testing
4. **Thread-safe**: Singleton pattern with locking
5. **Write-only metrics**: Analysis separate from recording

## Version

1.0.0
