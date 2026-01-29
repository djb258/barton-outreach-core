# PRD: BIT Engine v3.0

**Version:** 3.0 (Constitutional Compliance)
**Status:** Active
**Constitutional Date:** 2026-01-29
**Last Updated:** 2026-01-29
**Doctrine:** IMO-Creator Constitutional Doctrine
**Barton ID Range:** `04.04.02.04.7XXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | CL-01 (Company Lifecycle) |
| **Sovereign Boundary** | Company identity and lifecycle state |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Hub Name** | BIT Engine (Buyer Intent Tool) |
| **Hub ID** | HUB-BIT-ENGINE |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0 |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This engine transforms sub-hub signals from People, DOL, Blog, and Talent Flow (CONSTANTS) into aggregated buyer intent scores with tier classifications (VARIABLES) through CAPTURE (signal intake with validation), COMPUTE (weighting, decay calculation, score aggregation), and GOVERN (tier assignment and persistence with deduplication enforcement)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Sub-hub signals → Aggregated BIT scores with tier classification |

### Constants (Inputs)

_Immutable inputs received from outside this engine. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `slot_filled_signal` | People Intelligence | Signal when slot is filled |
| `email_verified_signal` | People Intelligence | Signal when email is verified |
| `executive_movement_signal` | Talent Flow | Executive hire/departure signals |
| `form_5500_signal` | DOL Filings | DOL filing detection signal |
| `broker_change_signal` | DOL Filings | Broker change detection signal |
| `funding_event_signal` | Blog Content | Funding/news event signals |

### Variables (Outputs)

_Outputs this engine produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `bit_score` | Outreach BIT Scores table | Aggregated buyer intent score (0-100) |
| `bit_tier` | Outreach BIT Scores table | Tier classification (COLD/WARM/HOT/BURNING) |
| `score_updated_at` | Outreach BIT Scores table | Last score update timestamp |
| `decayed_weight` | BIT Events table | Decay-adjusted signal weight |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Signal Intake | **CAPTURE** | I (Ingress) | Receive and validate signals from sub-hubs |
| Score Calculation | **COMPUTE** | M (Middle) | Apply weights, calculate decay, aggregate scores |
| Tier Classification | **COMPUTE** | M (Middle) | Classify into COLD/WARM/HOT/BURNING |
| Score Persistence | **GOVERN** | O (Egress) | Persist scores with deduplication enforcement |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Signal intake, weighting, score calculation, decay, tier classification, score persistence |
| **OUT OF SCOPE** | Signal generation (sub-hubs own), company identity (Company Target owns), outreach decisions (Outreach Execution owns), slot assignment (People owns) |

---

## Engine Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           BIT ENGINE OWNERSHIP                                ║
║                                                                               ║
║   This engine OWNS:                                                           ║
║   ├── Signal intake from all spokes                                           ║
║   ├── Signal weighting and scoring                                            ║
║   ├── BIT score calculation per company                                       ║
║   ├── Score decay over time                                                   ║
║   ├── Threshold classification (COLD/WARM/HOT/BURNING)                        ║
║   └── Score persistence to Company Hub                                        ║
║                                                                               ║
║   This engine DOES NOT OWN:                                                   ║
║   ├── Signal generation (spokes emit signals)                                 ║
║   ├── Company identity (company_id, domain, email_pattern)                    ║
║   ├── Outreach decisions (that's Outreach Spoke)                              ║
║   ├── Slot assignment (that's People Spoke)                                   ║
║   └── Data enrichment (that's individual spokes)                              ║
║                                                                               ║
║   This engine RECEIVES SIGNALS and CALCULATES SCORES.                         ║
║                                                                               ║
║   PREREQUISITE: company_id MUST be valid for score assignment.                ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Purpose

The BIT (Buyer Intent Tool) Engine is the **scoring hub** of the Barton pipeline. It aggregates signals from all spokes, applies weights, calculates decay, and produces a single buyer intent score per company that drives outreach prioritization.

### Core Functions

1. **Signal Intake** - Receive and validate signals from all spokes
2. **Signal Weighting** - Apply weights based on signal type
3. **Score Calculation** - Aggregate weighted signals into BIT score
4. **Score Decay** - Apply time-based decay to older signals
5. **Threshold Classification** - Classify as COLD/WARM/HOT/BURNING
6. **Score Persistence** - Write scores to Company Hub

### Threshold Definitions

| Tier | Score Range | Action |
|------|-------------|--------|
| COLD | 0-24 | No outreach |
| WARM | 25-49 | Watch list |
| HOT | 50-74 | Outreach eligible |
| BURNING | 75+ | Priority outreach |

---

## 2. Data Flow

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   People    │  │     DOL     │  │    Blog     │  │ Talent Flow │  │   Other     │
│   Spoke     │  │   Spoke     │  │   Spoke     │  │   Spoke     │  │   Spokes    │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │                │
       └────────────────┴────────────────┼────────────────┴────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BIT ENGINE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. SIGNAL INTAKE                                                           │
│     ├── Validate signal structure                                           │
│     ├── Verify company_id anchor                                            │
│     ├── Check signal deduplication                                          │
│     └── Record correlation_id                                               │
│                                                                             │
│  2. SIGNAL WEIGHTING                                                        │
│     ├── Look up signal_type weight                                          │
│     ├── Apply source multiplier                                             │
│     └── Calculate base_score                                                │
│                                                                             │
│  3. SCORE AGGREGATION                                                       │
│     ├── Sum all weighted signals per company                                │
│     ├── Apply decay function                                                │
│     └── Cap at maximum (100)                                                │
│                                                                             │
│  4. THRESHOLD CLASSIFICATION                                                │
│     ├── COLD: 0-24                                                          │
│     ├── WARM: 25-49                                                         │
│     ├── HOT: 50-74                                                          │
│     └── BURNING: 75+                                                        │
│                                                                             │
│  5. SCORE PERSISTENCE                                                       │
│     ├── Update company.bit_score                                            │
│     ├── Update company.bit_tier                                             │
│     └── Record last_scored_at                                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Company Hub   │
│  (bit_score)    │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ Outreach Spoke  │
│ (bit >= 50)     │
└─────────────────┘
```

---

## 3. Signal Weighting Table

| Signal Type | Base Weight | Decay Period | Source |
|-------------|-------------|--------------|--------|
| FORM_5500_FILED | +5 | 365 days | DOL Spoke |
| LARGE_PLAN | +10 | 365 days | DOL Spoke |
| BROKER_CHANGE | +20 | 180 days | DOL Spoke |
| SLOT_FILLED | +3 | 90 days | People Spoke |
| EMAIL_VERIFIED | +2 | 90 days | People Spoke |
| EXECUTIVE_HIRE | +15 | 180 days | Talent Flow |
| EXECUTIVE_DEPARTURE | +10 | 180 days | Talent Flow |
| LATERAL_MOVE | +5 | 180 days | Talent Flow |
| PROMOTION | +8 | 180 days | Talent Flow |
| FUNDING_ROUND | +25 | 90 days | Blog Spoke |
| ACQUISITION | +20 | 90 days | Blog Spoke |
| LAYOFFS | +15 | 60 days | Blog Spoke |
| EXPANSION | +10 | 90 days | Blog Spoke |
| EXECUTIVE_CHANGE | +12 | 90 days | Blog Spoke |

---

## 4. Score Decay Model

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           BIT SCORE DECAY MODEL                               ║
║                                                                               ║
║   FORMULA: decayed_score = base_score * decay_factor                          ║
║                                                                               ║
║   decay_factor = max(0, 1 - (days_since_signal / decay_period))               ║
║                                                                               ║
║   EXAMPLE (BROKER_CHANGE, 90 days old):                                       ║
║   decay_factor = max(0, 1 - (90 / 180)) = 0.5                                 ║
║   decayed_score = 20 * 0.5 = 10 points                                        ║
║                                                                               ║
║   DECAY PERIODS BY SIGNAL TYPE:                                               ║
║   ├── Structural signals (Form 5500): 365 days                                ║
║   ├── Movement signals (Hire/Depart): 180 days                                ║
║   ├── Event signals (Funding/News): 90 days                                   ║
║   └── Operational signals (Email): 90 days                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Score Calculation Algorithm

```python
def calculate_bit_score(company_id: str) -> int:
    """
    Calculate BIT score for a company by aggregating all active signals.
    """
    signals = load_signals_for_company(company_id)

    total_score = 0.0

    for signal in signals:
        # Get base weight
        base_weight = SIGNAL_WEIGHTS.get(signal['signal_type'], 0)

        # Calculate days since signal
        days_old = (datetime.now() - signal['detected_at']).days

        # Get decay period for signal type
        decay_period = DECAY_PERIODS.get(signal['signal_type'], 90)

        # Calculate decay factor
        decay_factor = max(0, 1 - (days_old / decay_period))

        # Calculate decayed score
        decayed_score = base_weight * decay_factor

        total_score += decayed_score

    # Cap at 100
    final_score = min(100, int(total_score))

    return final_score

def classify_tier(score: int) -> str:
    """Classify BIT score into tier."""
    if score >= 75:
        return 'BURNING'
    elif score >= 50:
        return 'HOT'
    elif score >= 25:
        return 'WARM'
    return 'COLD'
```

---

## 6. Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL signals    ║
║             from source spoke through BIT scoring.                            ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every signal received MUST have correlation_id (FAIL if missing)         ║
║   2. Score updates MUST log correlation_id of contributing signals            ║
║   3. Every error logged MUST include correlation_id                           ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   SOURCE: Originating spoke (inherited through signal chain)                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 7. Signal Deduplication

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       SIGNAL DEDUPLICATION RULES                              ║
║                                                                               ║
║   OPERATIONAL SIGNALS (EMAIL_VERIFIED, SLOT_FILLED):                          ║
║   ├── Dedup window: 24 hours                                                  ║
║   └── Key: (company_id, signal_type, person_id)                               ║
║                                                                               ║
║   STRUCTURAL SIGNALS (FORM_5500, EXECUTIVE_HIRE):                             ║
║   ├── Dedup window: 365 days                                                  ║
║   └── Key: (company_id, signal_type, unique_identifier)                       ║
║                                                                               ║
║   EVENT SIGNALS (FUNDING, ACQUISITION):                                       ║
║   ├── Dedup window: 90 days                                                   ║
║   └── Key: (company_id, signal_type, event_date)                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 8. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| BIT Engine | ✅ Implemented | `hub/company/bit_engine.py` |
| Signal Intake | ✅ Implemented | `ingest_signal()` |
| Score Calculation | ✅ Implemented | `calculate_score()` |
| Decay Model | ✅ Implemented | `_apply_decay()` |
| Threshold Classification | ✅ Implemented | `get_bit_tier()` |
| Signal Deduplication | ✅ Implemented | `ops/enforcement/signal_dedup.py` |
| Correlation ID | ✅ Implemented | `ops/enforcement/correlation_id.py` |

---

## 9. Kill Switches

| Switch | Threshold | Action |
|--------|-----------|--------|
| `signal_flood_per_source` | 500/day | Halt intake from source |
| `signal_flood_per_company` | 50/day | Flag company for review |
| `bit_spike_per_run` | 100 | Halt scoring run |
| `daily_cost_ceiling` | $50 | Halt all processing |

---

## 10. Schema

```sql
-- Signal storage
CREATE TABLE bit.events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(25) NOT NULL REFERENCES marketing.company_master(company_unique_id),
    event_type VARCHAR(50) NOT NULL,
    event_payload JSONB,
    detected_at TIMESTAMP DEFAULT NOW(),
    correlation_id UUID NOT NULL,
    source_spoke VARCHAR(50) NOT NULL,
    base_weight INTEGER NOT NULL,
    decayed_weight NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_bit_events_company ON bit.events(company_id);
CREATE INDEX idx_bit_events_type ON bit.events(event_type);
CREATE INDEX idx_bit_events_correlation ON bit.events(correlation_id);

-- Company score cache
ALTER TABLE marketing.company_master ADD COLUMN IF NOT EXISTS bit_score INTEGER DEFAULT 0;
ALTER TABLE marketing.company_master ADD COLUMN IF NOT EXISTS bit_tier VARCHAR(10) DEFAULT 'COLD';
ALTER TABLE marketing.company_master ADD COLUMN IF NOT EXISTS last_scored_at TIMESTAMP;
```

---

## 11. Metrics & KPIs

| Metric | Target | Tracking |
|--------|--------|----------|
| Signals Processed | 100% | Real-time |
| Score Freshness | < 1 hour | Hourly |
| HOT Companies | > 30% | Daily |
| Signal Dedup Rate | < 10% | Daily |

---

**Last Updated:** 2025-12-19
**Author:** Claude Code
**Approved By:** Barton Doctrine
