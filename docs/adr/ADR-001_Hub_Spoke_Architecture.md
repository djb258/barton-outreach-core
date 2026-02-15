# ADR-001: Hub-and-Spoke Architecture → CTB Evolution

> **Status:** [x] Superseded by CTB
> **Original Date:** 2025-12-17
> **Updated:** 2026-02-07
> **Superseded By:** CTB Registry (2026-02-06)

---

## Current Architecture: CTB (Christmas Tree Backbone)

As of 2026-02-06, the system uses **CTB (Christmas Tree Backbone)** as the authoritative data model. The original Hub-and-Spoke pattern is preserved below for historical reference.

### CTB Overview

| Property | Value |
|----------|-------|
| **Total Tables** | 249 |
| **Spine Table** | `outreach.outreach` |
| **Universal Join Key** | `outreach_id` |
| **Sovereign Eligible** | 95,004 |
| **CL-Spine Alignment** | 95,004 = 95,004 (ALIGNED) |

### Three Audiences

All messaging targets exactly one of three slot types:

| Slot | Filled | Total | Fill Rate |
|------|--------|-------|-----------|
| CEO | 62,289 | 95,004 | 65.6% |
| CFO | 57,327 | 95,004 | 60.3% |
| HR | 58,141 | 95,004 | 61.2% |
| **Total** | **177,757** | **285,012** | **62.4%** |

### CTB Leaf Types

| Leaf Type | Count | Description |
|-----------|-------|-------------|
| ARCHIVE | 119 | Archive/backup tables |
| SYSTEM | 36 | System/metadata |
| CANONICAL | 26 | Primary data tables |
| DEPRECATED | 24 | Legacy (read-only) |
| STAGING | 13 | Intake/staging |
| ERROR | 11 | Error tracking |
| MV | 8 | Materialized views |
| REGISTRY | 7 | Lookup/reference |
| SUPPORTING | 5 | Operational data serving CANONICAL tables (ADR required) |

### CTB Sub-Hub Coverage

| Sub-Hub | Table | Records | Coverage |
|---------|-------|---------|----------|
| Spine | `outreach.outreach` | 95,004 | 100% |
| Company Target | `outreach.company_target` | 95,004 | 100% |
| DOL | `outreach.dol` | 70,150 | 73.8% |
| Blog | `outreach.blog` | 95,004 | 100% |
| BIT Scores | `outreach.bit_scores` | 13,226 | 13.9% |
| People | `people.people_master` | 182,661 | — |
| Slots | `people.company_slot` | 285,012 | — |

### CTB Golden Rule

```
IF outreach_id IS NULL:
    STOP. DO NOT PROCEED.
    1. Mint outreach_id in outreach.outreach (operational spine)
    2. Write outreach_id ONCE to cl.company_identity (authority registry)
    3. If CL write fails (already claimed) → HARD FAIL
```

### CTB Documentation

- **[CTB_GOVERNANCE.md](../CTB_GOVERNANCE.md)** - Governance rules
- **[CTB_REMEDIATION_SUMMARY.md](../audit/CTB_REMEDIATION_SUMMARY.md)** - Phase history
- **[OSAM.md](../OSAM.md)** - Semantic access map

---

## Historical: Hub-and-Spoke Architecture (2025-12-17)

The following describes the original Hub-and-Spoke pattern that was superseded by CTB.

### Original Context

The Barton Outreach Core system needed a scalable architecture to handle multiple data enrichment sources, signal processing, and outreach coordination. Key challenges:

1. **Data Anchoring**: Multiple data sources (DOL filings, LinkedIn, news feeds) need to attach to a single company record
2. **Signal Aggregation**: Buyer intent signals from various sources need unified scoring
3. **Processing Order**: Dependent operations (email generation requires company domain) need clear sequencing
4. **Failure Isolation**: One failing data source shouldn't block the entire pipeline
5. **Traceability**: Every action must be traceable back to its origin

### Original Decision

| Field | Value |
|-------|-------|
| **Architecture** | Bicycle Wheel Hub-and-Spoke |
| **Doctrine ID** | 04.04.02.04 |
| **Central Hub** | Company Hub (company_master) |
| **Source** | Barton Doctrine v1.1 |

### Original Architecture Diagram

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

### Original Golden Rule

```
IF company_id IS NULL OR domain IS NULL OR email_pattern IS NULL:
    STOP. DO NOT PROCEED.
    → Route to Company Identity Pipeline first.
```

**Note:** This rule evolved into the CTB Golden Rule which uses `outreach_id` instead of `company_id`.

### Why Hub-and-Spoke Was Superseded

| Issue | Hub-and-Spoke | CTB Solution |
|-------|---------------|--------------|
| Join key fragmentation | Multiple keys (company_id, domain) | Single key (outreach_id) |
| Schema sprawl | Ad-hoc table creation | 249 registered tables with leaf types |
| Orphan records | Possible without enforcement | Prevented by registry |
| Audit trail | Manual | Automated via ctb.table_registry |

---

## Alternatives Considered (Historical)

| Option | Why Not Chosen |
|--------|----------------|
| Event-Driven Microservices | Overhead too high for current team size, harder to trace |
| Monolithic Pipeline | No failure isolation, harder to extend |
| Star Schema (Data Warehouse) | Read-optimized, not suited for operational pipeline |
| Do Nothing | System was already hitting scaling limits |

---

## Rollback

If CTB architecture needs rollback:
1. Restore Hub-and-Spoke spoke files from `.archive/`
2. Re-enable direct company_master writes
3. Disable ctb.table_registry enforcement
4. Update CLAUDE.md to reflect rollback

---

## Approval

| Role | Name | Date |
|------|------|------|
| Hub Owner | Barton Doctrine | 2025-12-17 |
| Reviewer | Claude Code | 2025-12-19 |
| CTB Migration | Claude Code | 2026-02-06 |
| Documentation Update | Claude Code | 2026-02-07 |

---

## References

- `CLAUDE.md` - Bootstrap guide with CTB architecture
- `docs/CTB_GOVERNANCE.md` - CTB governance rules
- `docs/OSAM.md` - Semantic access map
- `docs/prd/` - Individual component PRDs
