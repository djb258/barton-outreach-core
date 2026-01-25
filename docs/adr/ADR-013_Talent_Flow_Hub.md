# ADR-013: Talent Flow Hub Architecture

## Status
**ACCEPTED**

## Date
2026-01-25

## Context

The Outreach program needed a mechanism to track executive movements (job changes, departures, promotions) that could indicate buying intent. This intelligence feeds into the BIT (Buyer Intent Tracker) scoring system.

Key requirements:
1. Track executive transitions across companies
2. Detect job title changes within companies
3. Emit signals to BIT engine for scoring
4. Operate in **sensor-only mode** (zero cost)
5. Maintain freshness window for signal validity

## Decision

Create a dedicated **Talent Flow Hub** (04.04.06) in the waterfall, positioned after People Intelligence and before Blog Content.

### Design Principles

1. **Sensor-Only Mode**: The hub ONLY detects movements. It NEVER:
   - Triggers paid API calls
   - Enriches person data
   - Creates new records
   - Modifies upstream data

2. **Freshness-Based Status**: Hub status computed from movement freshness:
   - `PASS`: At least 1 movement within 60 days
   - `IN_PROGRESS`: No fresh movements (or monitoring)
   - `BLOCKED`: Upstream People Intelligence is BLOCKED

3. **Confidence Threshold**: Movements require confidence >= 0.70 to count

4. **Signal Integration**: Movements emit to BIT engine with decay

### Waterfall Position

```
CL → Company Target → DOL → People Intelligence → Talent Flow → Blog
                                                       ↑
                                                  (YOU ARE HERE)
```

### Tables Owned

| Schema | Table | Purpose |
|--------|-------|---------|
| `talent_flow` | `movement_history` | Core movement records |
| `people` | `person_movement_history` | Person-level movements |

### Movement Types

| Type | BIT Impact | Description |
|------|------------|-------------|
| `joined` | +10 | Executive joined from another company |
| `left` | +5 | Executive departed |
| `title_change` | +3 | Title changed within company |

## Consequences

### Positive
- Zero-cost intent signal collection
- Passive monitoring improves BIT accuracy
- Clear separation from enrichment hubs
- Freshness-based status prevents stale data reliance

### Negative
- Requires LinkedIn monitoring infrastructure
- Movement detection has inherent latency
- Confidence filtering may miss some valid signals

### Neutral
- Hub status does not gate downstream (sensor-only)
- Signals decay over 90 days

## Alternatives Considered

### Option A: Integrate into People Intelligence — REJECTED
- Would mix sensor and enrichment concerns
- People Intelligence already has clear scope

### Option B: Real-time API monitoring — REJECTED
- Violates zero-cost sensor requirement
- Would incur significant API costs

### Option C: Dedicated sensor hub — ACCEPTED
- Clear scope boundary
- Zero operational cost
- Fits waterfall model

## Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `FRESHNESS_DAYS` | 60 | Signals expire after 60 days |
| `MIN_MOVEMENTS` | 1 | Minimum movements for PASS |
| `CONFIDENCE_THRESHOLD` | 0.70 | Minimum confidence score |
| `BIT_DECAY_DAYS` | 90 | Signal decay period for BIT |

## Implementation

1. Create hub scaffold (`hubs/talent-flow/`)
2. Implement status computation (`hub_status.py`)
3. Create movement detection logic
4. Integrate with BIT signal emission
5. Create SCHEMA.md with Neon-verified ERD
6. Create CHECKLIST.md for compliance
7. Create PRD.md for requirements

## References

- Hub Manifest: `hubs/talent-flow/hub.manifest.yaml`
- Status Logic: `hubs/talent-flow/imo/middle/hub_status.py`
- SCHEMA.md: `hubs/talent-flow/SCHEMA.md`
- CHECKLIST.md: `hubs/talent-flow/CHECKLIST.md`
- PRD.md: `hubs/talent-flow/PRD.md`

## Document Control

| Field | Value |
|-------|-------|
| Created | 2026-01-25 |
| Author | Claude Code |
| Status | ACCEPTED |
| CC Layer | CC-03 |
| Hub ID | 04.04.06 |
