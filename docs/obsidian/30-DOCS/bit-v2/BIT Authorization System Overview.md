# BIT Authorization System v2.0

> **Authority**: ADR-017
> **Status**: DEPLOYED (Phase 1 + 1.5)
> **Freeze Date**: 2026-01-26

## Overview

BIT (Buyer Intent Tool) v2.0 is an **authorization index**, not a lead score. It determines what outreach actions are **permitted** based on detected organizational movement.

## Key Shift

```
OLD: Score high enough → send marketing
NEW: Detect phase transition → intercept with proof
```

## Architecture

```
DOL Hub ──────► dol.pressure_signals ────────┐
People Hub ───► people.pressure_signals ─────┼──► company_target.vw_all_pressure_signals
Blog Hub ─────► blog.pressure_signals ───────┘              │
                                                            ▼
                                           company_target.compute_authorization_band()
                                                            │
                                                            ▼
                                                      Band 0-5
```

### Distributed Signal Architecture

Each sub-hub **OWNS** its own signal table:

| Hub | Table | Domain |
|-----|-------|--------|
| DOL | `dol.pressure_signals` | STRUCTURAL_PRESSURE |
| People | `people.pressure_signals` | DECISION_SURFACE |
| Blog | `blog.pressure_signals` | NARRATIVE_VOLATILITY |

Company Target **OWNS** the union view and BIT computation.

## Three Domains

| Domain | Hub | Trust | Role |
|--------|-----|-------|------|
| STRUCTURAL_PRESSURE | DOL | Highest | Gravity (required) |
| DECISION_SURFACE | People | Medium | Direction |
| NARRATIVE_VOLATILITY | Blog | Lowest | Amplifier only |

## Convergence Rules

- 1 domain moving = noise
- 2 domains aligned = watch
- 3 domains aligned = act
- **Blog alone = max Band 1**
- **No DOL = max Band 2**

## Related Documents

- [[BIT Authorization Bands]]
- [[Proof Line Rule]]
- [[BIT Pressure Signals]]

## Tags

#bit #v2 #authorization #frozen #adr-017
