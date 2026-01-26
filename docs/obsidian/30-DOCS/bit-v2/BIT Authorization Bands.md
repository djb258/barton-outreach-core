# BIT Authorization Bands

> **Authority**: ADR-017
> **Status**: FROZEN (Logic)
> **Computed By**: `company_target.compute_authorization_band()`

## Band Definitions

| Band | Range | Name | Description |
|------|-------|------|-------------|
| 0 | 0-9 | SILENT | No action permitted |
| 1 | 10-24 | WATCH | Internal flag only |
| 2 | 25-39 | EXPLORATORY | 1 educational / 60d |
| 3 | 40-59 | TARGETED | Persona email, proof required |
| 4 | 60-79 | ENGAGED | Phone allowed, multi-source proof |
| 5 | 80+ | DIRECT | Full contact, full-chain proof |

## Permitted Actions by Band

| Action | 0 | 1 | 2 | 3 | 4 | 5 |
|--------|---|---|---|---|---|---|
| Internal flag | - | YES | YES | YES | YES | YES |
| Educational content | - | - | YES | YES | YES | YES |
| Persona email | - | - | - | YES | YES | YES |
| Phone (warm) | - | - | - | - | YES | YES |
| Phone (cold) | - | - | - | - | - | YES |
| Meeting request | - | - | - | - | - | YES |

## Domain Trust Caps (FROZEN)

| Rule | Max Band |
|------|----------|
| Blog alone | 1 (WATCH) |
| No DOL present | 2 (EXPLORATORY) |

## Proof Requirements

| Band | Proof Required | Proof Type |
|------|----------------|------------|
| 0-2 | No | - |
| 3 | Yes | Single-source |
| 4 | Yes | Multi-source |
| 5 | Yes | Full-chain |

## Magnitude Calculation

BIT reads from `company_target.vw_all_pressure_signals` and applies weighted sums:

- DOL weight: 1.0 (full)
- People weight: 0.8
- Blog weight: 0.5 (amplifier only)

Domain activation threshold: magnitude >= 10

## Code Usage

```python
band = company_target.compute_authorization_band(company_id)
if band.authorization_band < required_band:
    raise UnauthorizedOutreachError()
if band.authorization_band >= 3:
    proof = get_valid_proof(company_id, band.authorization_band)
    if not proof:
        raise MissingProofLineError()
```

## Related Documents

- [[BIT Authorization System Overview]]
- [[Proof Line Rule]]

## Tags

#bit #bands #frozen #authorization
