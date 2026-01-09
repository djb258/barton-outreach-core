# BIT Signal Weights - Doctrine Reference

**Status:** LOCKED
**Lock Date:** 2026-01-08
**Doctrine:** Spine-First Architecture v1.1
**Authority:** Doctrine Enforcement Engineer

---

## Purpose

This file is the **AUTHORITATIVE SOURCE** for BIT signal weights. All code MUST read weights from the constant map defined in `bit_engine.py`. Any discrepancy between this document and code is a **DOCTRINE VIOLATION**.

---

## Signal Weights (LOCKED)

### People Sub-Hub Signals

| Signal Type | Weight | Decay Period | Description |
|-------------|--------|--------------|-------------|
| `SLOT_FILLED` | +10.0 | 90 days | Executive slot filled |
| `SLOT_VACATED` | -5.0 | 90 days | Executive slot vacated |
| `EMAIL_VERIFIED` | +3.0 | 90 days | Email address verified |
| `LINKEDIN_FOUND` | +2.0 | 90 days | LinkedIn profile found |

### DOL Sub-Hub Signals

| Signal Type | Weight | Decay Period | Description |
|-------------|--------|--------------|-------------|
| `FORM_5500_FILED` | +5.0 | 365 days | Form 5500 filing detected |
| `LARGE_PLAN` | +8.0 | 365 days | Large plan (>100 participants) |
| `BROKER_CHANGE` | +7.0 | 180 days | Broker of record change |

### Blog Sub-Hub Signals

| Signal Type | Weight | Decay Period | Description |
|-------------|--------|--------------|-------------|
| `FUNDING_EVENT` | +15.0 | 90 days | Funding round announced |
| `ACQUISITION` | +12.0 | 90 days | M&A activity |
| `LEADERSHIP_CHANGE` | +8.0 | 90 days | C-level change |
| `EXPANSION` | +7.0 | 90 days | New office/market |
| `PRODUCT_LAUNCH` | +5.0 | 90 days | New product/service |
| `PARTNERSHIP` | +5.0 | 90 days | Strategic partnership |
| `LAYOFF` | -3.0 | 60 days | Workforce reduction |
| `NEGATIVE_NEWS` | -5.0 | 60 days | Negative press |

### Talent Flow Signals

| Signal Type | Weight | Decay Period | Description |
|-------------|--------|--------------|-------------|
| `EXECUTIVE_JOINED` | +10.0 | 180 days | Executive hire |
| `EXECUTIVE_LEFT` | -5.0 | 180 days | Executive departure |
| `TITLE_CHANGE` | +3.0 | 180 days | Title/role change |

---

## Tier Bands (LOCKED)

| Tier | Score Range | Action |
|------|-------------|--------|
| COLD | 0-24 | No outreach |
| WARM | 25-49 | Watch list |
| HOT | 50-74 | Outreach eligible |
| BURNING | 75+ | Priority outreach |

---

## Decay Model (LOCKED)

```
decayed_score = base_score * max(0, 1 - (days_since_signal / decay_period))
```

### Decay Periods by Category

| Category | Decay Period | Examples |
|----------|--------------|----------|
| Structural | 365 days | Form 5500, Large Plan |
| Movement | 180 days | Executive hire/depart, Broker change |
| Event | 90 days | Funding, Acquisition, Expansion |
| Negative | 60 days | Layoff, Negative news |
| Operational | 90 days | Email verified, LinkedIn found |

---

## Guardrails (LOCKED)

| Guardrail | Value | Description |
|-----------|-------|-------------|
| Max Score | 100 | Score capped at 100 |
| Min Score | 0 | Score floor at 0 |
| Max Delta per Run | 50 | Single operation cannot change score by >50 |
| Correlation ID | REQUIRED | All writes must have correlation_id |

---

## Non-Goals (EXPLICIT)

BIT Engine does NOT:

1. **Author messaging** - BIT does not generate outreach content
2. **Detect intent** - BIT does not interpret buyer psychology
3. **Make decisions** - BIT only provides scores, not recommendations
4. **Store identity** - BIT uses outreach_id, does not mint identities
5. **Trigger enrichment** - BIT is passive, does not call APIs

BIT Engine ONLY:

1. **Aggregates signals** - From sub-hubs via spokes
2. **Calculates scores** - Deterministic, weight-based
3. **Applies decay** - Time-based, formulaic
4. **Classifies tiers** - Based on locked thresholds

---

## Verification

Code weights MUST match this document. Run verification:

```python
from bit_engine import SIGNAL_IMPACTS, SIGNAL_DECAY_PERIODS

# These values MUST match doctrine
assert SIGNAL_IMPACTS[SignalType.FUNDING_EVENT] == 15.0
assert SIGNAL_IMPACTS[SignalType.SLOT_FILLED] == 10.0
assert SIGNAL_DECAY_PERIODS[SignalType.FORM_5500_FILED] == 365
```

---

## Change Process

1. Changes to signal weights require ADR
2. ADR must be approved by Doctrine owner
3. Both this document AND code must be updated atomically
4. Unit tests must verify consistency

---

**LOCKED:** This document is authoritative. Deviations are violations.
**Last Updated:** 2026-01-08
**Owner:** BIT Engine Doctrine
