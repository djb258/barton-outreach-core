# UI PRD — BIT Engine

**Status**: DERIVED
**Authority**: SUBORDINATE TO PRD_BIT_ENGINE.md
**Generated**: 2026-01-29

---

## UI Identity

| Field | Value |
|-------|-------|
| **UI Name** | BIT Score Dashboard |
| **Owning Hub** | HUB-OUTREACH-001 (BIT component) |
| **Canonical PRD** | docs/prd/PRD_BIT_ENGINE.md |
| **Type** | Read-only |

---

## Explicit Exclusions

This UI does NOT:

- Compute BIT scores
- Emit BIT signals
- Determine tiers
- Modify score weights
- Execute authorization decisions

---

## Screens / Views

| Screen | Type | Description |
|--------|------|-------------|
| Score Overview | Read-only | Company BIT scores with tier breakdown |
| Signal History | Read-only | BIT signals by company over time |
| Tier Distribution | Read-only | Companies by tier |

---

## Canonical Outputs Consumed

| Output | Source | Read Pattern |
|--------|--------|--------------|
| BIT scores | outreach.bit_scores | SELECT |
| BIT signals | outreach.bit_signals | SELECT |
| Tier assignments | Computed from bit_scores | SELECT |

---

## Events Emitted

| Event | Trigger | Destination |
|-------|---------|-------------|
| `refresh_scores` | User clicks refresh | Backend API |
| `filter_by_tier` | User selects tier | Local state + API |

---

## Failure States

| Failure | Display |
|---------|---------|
| No score | "Score not computed" indicator |
| Stale score | "Score may be outdated" badge |

---

## Forbidden Behaviors

- Computing scores
- Modifying weights
- Emitting signals
- Making authorization decisions
