# ADR-001: Hub-and-Spoke Architecture

> **Status:** [x] Accepted
> **Date:** 2025-12-17
> **Updated:** 2025-12-19

---

## Context

The Barton Outreach Core system needed a scalable architecture to handle multiple data enrichment sources, signal processing, and outreach coordination. Key challenges:

1. **Data Anchoring**: Multiple data sources (DOL filings, LinkedIn, news feeds) need to attach to a single company record
2. **Signal Aggregation**: Buyer intent signals from various sources need unified scoring
3. **Processing Order**: Dependent operations (email generation requires company domain) need clear sequencing
4. **Failure Isolation**: One failing data source shouldn't block the entire pipeline
5. **Traceability**: Every action must be traceable back to its origin

---

## Decision

| Field | Value |
|-------|-------|
| **Architecture** | Bicycle Wheel Hub-and-Spoke |
| **Doctrine ID** | 04.04.02.04 |
| **Central Authority** | Outreach Spine (`outreach.outreach`) |
| **Execution Sub-Hub** | Company Target (IMO gate) |
| **Source** | Barton Doctrine v1.1 (Spine-First Architecture) |

> **Update (v3.0):** The original "Company Hub" concept has been split:
> - **Identity**: Company Lifecycle (CL) — external, mints `sovereign_id`
> - **Spine**: Outreach Spine — mints `outreach_id`, binds to CL
> - **Execution Prep**: Company Target — single-pass IMO gate, operates on `outreach_id`

### Architecture Pattern

```
                         ┌─────────────────┐
                         │   People Spoke  │
                         └────────┬────────┘
                                  │
┌─────────────────┐      ┌────────▼────────┐      ┌─────────────────┐
│   DOL Spoke     │──────▶   COMPANY HUB   ◀──────│   Blog Spoke    │
└─────────────────┘      └────────┬────────┘      └─────────────────┘
                                  │
                         ┌────────▼────────┐
                         │  Talent Flow    │
                         │     Spoke       │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │   BIT Engine    │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │ Outreach Spoke  │
                         └─────────────────┘
```

### The Golden Rule (v3.0 — Spine-First)

```
IF outreach_id IS NULL:
    STOP. DO NOT PROCEED.
    → outreach_id must be minted via Outreach Spine first
    → Spine requires sovereign_id from CL with identity_status = 'PASS'
```

> **DEPRECATED**: The original rule referenced `company_id` — this is replaced by `outreach_id`.
> Company Target now operates as an IMO gate (execution-readiness), not an identity authority.
> See `ADR-CT-IMO-001` for rationale.

---

## Alternatives Considered

| Option | Why Not Chosen |
|--------|----------------|
| Event-Driven Microservices | Overhead too high for current team size, harder to trace |
| Monolithic Pipeline | No failure isolation, harder to extend |
| Star Schema (Data Warehouse) | Read-optimized, not suited for operational pipeline |
| Do Nothing | System was already hitting scaling limits |

---

## Consequences

### Enables

- **Clear ownership**: Each spoke owns specific data and operations
- **Failure isolation**: DOL spoke failure doesn't block People spoke
- **Easy extension**: New spokes plug into existing hub
- **Unified tracing**: correlation_id flows from hub through all spokes
- **Signal aggregation**: BIT Engine receives from all spokes uniformly
- **Clear processing order**: Company first, then spokes, then BIT, then outreach

### Prevents

- **Orphan records**: No data exists without company anchor
- **Duplicate signals**: Signal deduplication enforced at hub level
- **Untraced errors**: Every operation has correlation_id
- **Processing chaos**: Clear phase ordering (1→4, then spokes)

---

## Guard Rails

| Type | Value |
|------|-------|
| Rate Limit | 500 signals/day per spoke |
| Timeout | 30 seconds per operation |
| Kill Switch | `signal_flood_per_source`, `daily_cost_ceiling` |

---

## Implementation

### Hub Components

> **NOTE (2026-01-07):** Company Target has been refactored to a single-pass IMO gate.
> See `ADR-CT-IMO-001` for details. The components below are partially deprecated.

- `hubs/company-target/imo/middle/company_target_imo.py` - **PRIMARY**: Single-pass IMO gate
- ~~`hub/company/company_hub.py`~~ - **DEPRECATED**: Central hub with cache and fuzzy matching
- ~~`hub/company/company_pipeline.py`~~ - **DEPRECATED**: Phase 1-4 execution (Phase 1/1b moved to CL)
- `hubs/company-target/imo/middle/bit_engine.py` - Signal aggregation and scoring
- ~~`hub/company/neon_writer.py`~~ - **DEPRECATED**: IMO handles writes directly

### Spoke Components
- `spokes/people/people_spoke.py` - Email generation, slot assignment
- `spokes/dol/dol_spoke.py` - Form 5500 processing
- `spokes/blog/blog_spoke.py` - News/RSS processing
- `spokes/talent_flow/talent_flow_spoke.py` - Movement detection
- `spokes/outreach/outreach_spoke.py` - Output/campaign management

### Enforcement Components
- `ops/enforcement/correlation_id.py` - ID validation and generation
- `ops/enforcement/signal_dedup.py` - Deduplication logic
- `ops/enforcement/hub_gate.py` - Anchor validation
- `ops/enforcement/error_codes.py` - Standardized error codes

---

## Rollback

If the hub-and-spoke architecture fails:
1. Revert to direct database writes (legacy `outreach_core/` modules)
2. Disable BIT Engine signal aggregation
3. Process spokes independently without hub coordination
4. Archive `hub/` and `spokes/` directories

Note: `.archive/` contains original implementation for reference.

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | Barton Doctrine | 2025-12-17 |
| Reviewer | Claude Code | 2025-12-19 |
| Implementation | Claude Code | 2025-12-19 |

---

## References

- `CLAUDE.md` - Bootstrap guide with architecture overview
- `docs/COMPLETE_SYSTEM_ERD.md` - Entity relationship diagram
- `docs/COMPLETE_DATA_FLOW.md` - Data flow documentation
- `docs/prd/` - Individual component PRDs
