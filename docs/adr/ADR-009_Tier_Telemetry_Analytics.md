# ADR-009: Tier Telemetry and Drift Analytics

## Status
**ACCEPTED**

## Date
2026-01-20

## Context

With the sovereign completion infrastructure in place, we need visibility into tier distribution and drift over time without modifying tier computation logic.

### Problem Statement

Operations team needs to:
1. Monitor tier distribution across the company population
2. Detect significant tier drift (>5% change)
3. Analyze hub blocking patterns
4. Track freshness decay
5. Identify signal coverage gaps

### Constraints

- **READ-ONLY**: Analytics must not touch tier computation logic
- **NO MUTATIONS**: No triggers or side effects
- **DOES NOT AFFECT**: Kill switches, hub status, or marketing eligibility

## Decision

### 1. Create Read-Only Telemetry Views

| View | Purpose |
|------|---------|
| `vw_tier_distribution` | Count and percentage at each tier |
| `vw_hub_block_analysis` | % blocked by each hub in waterfall |
| `vw_freshness_analysis` | % failing freshness checks per hub |
| `vw_signal_gap_analysis` | % lacking signals per hub |
| `vw_tier_telemetry_summary` | Aggregated dashboard summary |
| `vw_tier_drift_analysis` | Day-over-day tier changes |

### 2. Implement Daily Snapshot Capture

- Table: `outreach.tier_snapshot_history`
- Function: `fn_capture_tier_snapshot()`
- Schedule: Daily at 00:00 UTC (recommended)
- Captures: Tier counts, hub pass rates, block rates, freshness stats

### 3. Create Markdown Report Generator

- Script: `ops/metrics/tier_report.py`
- Output: Formatted markdown with tables and status indicators
- Includes: Tier distribution, hub analysis, freshness, signal gaps, drift

### 4. Python Analytics Module

- Module: `analytics/`
- Exports: `capture_tier_snapshot`, `get_tier_drift`, `generate_markdown_report`
- Usage: Import from analytics module for programmatic access

## Implementation

### SQL Migration
`infra/migrations/2026-01-20-tier-telemetry-views.sql`

### Python Components
- `ops/metrics/tier_snapshot.py` - Daily snapshot job
- `ops/metrics/tier_report.py` - Markdown report generator
- `analytics/__init__.py` - Module exports

## Consequences

### Positive
- Full visibility into tier health without risk
- Drift detection enables proactive intervention
- Historical snapshots support trend analysis
- Markdown reports enable easy sharing

### Negative
- Additional database views to maintain
- Snapshot history grows over time (consider retention policy)

### Risks Mitigated
- Tier drift goes undetected
- Hub blocking patterns hidden
- Freshness decay unmonitored

## Alternatives Considered

### Alternative 1: Direct Table Queries
- Pro: No additional views
- Con: Query complexity, risk of accidental modification
- **Rejected**: Views provide safety and convenience

### Alternative 2: External Analytics Tool
- Pro: Rich visualization
- Con: Additional infrastructure, data export concerns
- **Rejected**: In-database views sufficient for v1.0

## References

- `infra/migrations/2026-01-20-tier-telemetry-views.sql`
- `ops/metrics/tier_snapshot.py`
- `ops/metrics/tier_report.py`
- ADR-006: Sovereign Completion Infrastructure

## Author
IMO-Creator: Tier Telemetry Agent
Date: 2026-01-20
