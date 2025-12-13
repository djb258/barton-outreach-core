# Waterfall Optimization Engine (WOE) - RULES

## Overview

The Waterfall Optimization Engine dynamically optimizes provider waterfall ordering based on Provider Benchmark Engine (PBE) metrics. These rules govern how providers are promoted, demoted, or removed from the waterfall.

---

## Core Principles

### 1. Company-First Doctrine
All optimization decisions prioritize accurate company data. Provider performance is measured by company enrichment success, not individual call counts.

### 2. Determinism
When insufficient data exists, the engine maintains existing tier order. No guessing, no random shuffling.

### 3. Stability
Changes apply only to NEW batches. In-flight enrichment jobs are never affected by optimization changes.

### 4. Non-Blocking
Optimization is advisory. Pipeline execution continues even if WOE fails or returns empty results.

---

## Tier Structure

```
Tier 0: Free/Low-Cost (firecrawl, scraperapi, googleplaces)
   ↓
Tier 1: Standard Paid (hunter, apollo, clay)
   ↓
Tier 1.5: Mid-Tier (prospeo, snov)
   ↓
Tier 2: Premium (clearbit, pdl, zenrows)
   ↓
Tier 3: Enterprise (zoominfo)
```

### Tier Movement Rules

1. **No Cross-Tier Jumps**: A provider can move at most ONE tier per optimization cycle
   - Tier 0 → Tier 1 (OK)
   - Tier 0 → Tier 2 (NOT ALLOWED)

2. **Promotion Threshold**: Score >= 0.8 to be considered for promotion
   - High ROI
   - Low cost per success
   - High verified accuracy
   - Good latency (P50 < 2s)

3. **Demotion Threshold**: Score < 0.4 triggers demotion consideration
   - Low success rate
   - High cost per success
   - Poor accuracy

4. **Removal Threshold**: Score < 0.2 removes provider from waterfall
   - Consistently failing
   - Unacceptable error rates
   - Provider health issues

---

## Optimization Factors

### Factor Weights (Future Implementation)

| Factor | Weight | Description |
|--------|--------|-------------|
| ROI Score | 30% | Success rate / cost |
| Cost per Success | 20% | Actual cost for verified data |
| Verified Accuracy | 20% | Data that passed validation |
| Latency (P50) | 15% | Median response time |
| Reliability | 15% | (1 - error_rate - timeout_rate) |

### Data Requirements

- **Minimum Calls for Decision**: 10 calls before tier changes
- **Observation Window**: 7 days rolling window
- **Confidence Interval**: 95% for promotion decisions

---

## Optimization Cycle

### Frequency
- Optimization runs on-demand (not scheduled)
- Triggered by pipeline orchestrator
- Results cached until next run

### Process

1. Read PBE scorecard (current provider metrics)
2. Calculate composite scores for each provider
3. Compare against thresholds
4. Generate promotion/demotion recommendations
5. Apply tier movement rules
6. Return OptimizationPlan

### Constraints

- Maximum 2 promotions per cycle
- Maximum 2 demotions per cycle
- Removed providers require manual re-addition

---

## Safety Rules

### Provider Health Override
If a provider is marked unhealthy by PBE, it is automatically excluded from the waterfall regardless of historical scores.

### Cost Awareness
High-cost providers (Tier 2, Tier 3) require high accuracy to maintain their position:
- Tier 2: Minimum 70% verified accuracy
- Tier 3: Minimum 80% verified accuracy

### Repeated Failures
Providers with 3+ consecutive failures in the same batch are temporarily disabled for that batch.

---

## Integration Points

### Input: Provider Benchmark Engine (PBE)
- `get_scores()` - Current provider metrics
- `get_recommendations()` - Tier recommendations
- `get_metrics_summary()` - Aggregate statistics

### Output: OptimizationPlan
- `ordered_providers` - New tier ordering
- `promoted` - Providers moved up
- `demoted` - Providers moved down
- `removed` - Providers removed from waterfall
- `rationale` - Human-readable explanation

### Consumers
- Company Pipeline (Phases 1-4)
- People Pipeline (Phase 5 waterfall)
- Talent Flow Phase 0
- DOL Node (future)
- Blog Intelligence Pipeline (future)
- Outreach Node (future)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-05 | Initial shell implementation |

---

## Future Enhancements

1. **ML-based optimization**: Use historical patterns to predict provider performance
2. **Context-aware ordering**: Different orderings for different company types
3. **Real-time reordering**: Dynamic tier adjustments during batch execution
4. **A/B testing support**: Compare optimization strategies
