# PRD: BIT Engine v3.0

**Version:** 3.0 (Spine-First Architecture)
**Status:** PRODUCTION READY
**Refactor Date:** 2026-01-08
**Last Updated:** 2026-01-08
**Doctrine:** Spine-First Architecture v1.1
**Barton ID Range:** `04.04.02.04.7XXXX.###`

---

## Engine Ownership Statement

```
+===============================================================================+
|                           BIT ENGINE OWNERSHIP                                |
|                                                                               |
|   This engine OWNS:                                                           |
|   +-- Signal intake from all sub-hubs                                         |
|   +-- Signal weighting and scoring                                            |
|   +-- BIT score calculation per company                                       |
|   +-- Score decay over time                                                   |
|   +-- Threshold classification (COLD/WARM/HOT/BURNING)                        |
|   +-- Score persistence to outreach.bit_scores                                |
|                                                                               |
|   This engine DOES NOT OWN:                                                   |
|   +-- Signal generation (sub-hubs emit signals)                               |
|   +-- Company identity (outreach_id from spine)                               |
|   +-- Outreach decisions (that's Outreach Sub-Hub)                            |
|   +-- Slot assignment (that's People Sub-Hub)                                 |
|   +-- Data enrichment (that's individual sub-hubs)                            |
|                                                                               |
|   IDENTITY: outreach_id is the ONLY identity. sovereign_id is HIDDEN.         |
|   PREREQUISITE: outreach_id MUST exist in spine for score assignment.         |
|                                                                               |
+===============================================================================+
```

---

## Doctrine Guards (LOCKED)

```python
# Spine Guard - BIT uses outreach_id only
ENFORCE_OUTREACH_SPINE_ONLY = True
assert ENFORCE_OUTREACH_SPINE_ONLY is True

# Correlation ID Guard - Required for all writes
ENFORCE_CORRELATION_ID = True
assert ENFORCE_CORRELATION_ID is True

# Error Guard - No silent failures
ENFORCE_ERROR_PERSISTENCE = True
assert ENFORCE_ERROR_PERSISTENCE is True
```

---

## 1. Purpose

The BIT (Buyer Intent Tool) Engine is the **scoring hub** of the Barton pipeline. It aggregates signals from all sub-hubs, applies weights, calculates decay, and produces a single buyer intent score per company that drives outreach prioritization.

### Core Functions

1. **Signal Intake** - Receive and validate signals from all sub-hubs
2. **Signal Weighting** - Apply weights based on signal type
3. **Score Calculation** - Aggregate weighted signals into BIT score
4. **Score Decay** - Apply time-based decay to older signals
5. **Threshold Classification** - Classify as COLD/WARM/HOT/BURNING
6. **Score Persistence** - Write scores to outreach.bit_scores

### Threshold Definitions

| Tier | Score Range | Action |
|------|-------------|--------|
| COLD | 0-24 | No outreach |
| WARM | 25-49 | Watch list |
| HOT | 50-74 | Outreach eligible |
| BURNING | 75+ | Priority outreach |

---

## 2. Data Flow (Spine-First)

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   People    │  │     DOL     │  │    Blog     │  │ Talent Flow │
│  Sub-Hub    │  │  Sub-Hub    │  │  Sub-Hub    │  │             │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │
       └────────────────┴────────────────┼────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BIT ENGINE                                      │
│                    (Spine-First Architecture v1.1)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. SIGNAL INTAKE                                                            │
│     +-- Validate signal structure                                            │
│     +-- Verify outreach_id in spine                                          │
│     +-- Check signal deduplication                                           │
│     +-- REQUIRE correlation_id (DOCTRINE)                                    │
│                                                                              │
│  2. SIGNAL WEIGHTING                                                         │
│     +-- Look up signal_type weight                                           │
│     +-- Apply decay period                                                   │
│     +-- Calculate base_score                                                 │
│                                                                              │
│  3. SCORE AGGREGATION                                                        │
│     +-- Sum all weighted signals per outreach_id                             │
│     +-- Apply decay function                                                 │
│     +-- Cap at maximum (100)                                                 │
│                                                                              │
│  4. THRESHOLD CLASSIFICATION                                                 │
│     +-- COLD: 0-24                                                           │
│     +-- WARM: 25-49                                                          │
│     +-- HOT: 50-74                                                           │
│     +-- BURNING: 75+                                                         │
│                                                                              │
│  5. SCORE PERSISTENCE                                                        │
│     +-- Write to outreach.bit_scores (FK: outreach_id)                       │
│     +-- Write to outreach.bit_signals (FK: outreach_id)                      │
│     +-- Errors to outreach.bit_errors                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Outreach Sub-Hub│
│ (bit >= 50)     │
└─────────────────┘
```

---

## 3. Signal Weighting Table

| Signal Type | Base Weight | Decay Period | Source |
|-------------|-------------|--------------|--------|
| FORM_5500_FILED | +5 | 365 days | DOL Sub-Hub |
| LARGE_PLAN | +8 | 365 days | DOL Sub-Hub |
| BROKER_CHANGE | +7 | 180 days | DOL Sub-Hub |
| SLOT_FILLED | +10 | 90 days | People Sub-Hub |
| SLOT_VACATED | -5 | 90 days | People Sub-Hub |
| EMAIL_VERIFIED | +3 | 90 days | People Sub-Hub |
| LINKEDIN_FOUND | +2 | 90 days | People Sub-Hub |
| EXECUTIVE_JOINED | +10 | 180 days | Talent Flow |
| EXECUTIVE_LEFT | -5 | 180 days | Talent Flow |
| TITLE_CHANGE | +3 | 180 days | Talent Flow |
| FUNDING_EVENT | +15 | 90 days | Blog Sub-Hub |
| ACQUISITION | +12 | 90 days | Blog Sub-Hub |
| LEADERSHIP_CHANGE | +8 | 90 days | Blog Sub-Hub |
| EXPANSION | +7 | 90 days | Blog Sub-Hub |
| PRODUCT_LAUNCH | +5 | 90 days | Blog Sub-Hub |
| PARTNERSHIP | +5 | 90 days | Blog Sub-Hub |
| LAYOFF | -3 | 60 days | Blog Sub-Hub |
| NEGATIVE_NEWS | -5 | 60 days | Blog Sub-Hub |

---

## 4. Score Decay Model

```
+===============================================================================+
|                           BIT SCORE DECAY MODEL                               |
|                                                                               |
|   FORMULA: decayed_score = base_score * decay_factor                          |
|                                                                               |
|   decay_factor = max(0, 1 - (days_since_signal / decay_period))               |
|                                                                               |
|   EXAMPLE (BROKER_CHANGE, 90 days old):                                       |
|   decay_factor = max(0, 1 - (90 / 180)) = 0.5                                 |
|   decayed_score = 7 * 0.5 = 3.5 points                                        |
|                                                                               |
|   DECAY PERIODS BY SIGNAL TYPE:                                               |
|   +-- Structural signals (Form 5500): 365 days                                |
|   +-- Movement signals (Hire/Depart): 180 days                                |
|   +-- Event signals (Funding/News): 90 days                                   |
|   +-- Negative signals (Layoff): 60 days                                      |
|   +-- Operational signals (Email): 90 days                                    |
|                                                                               |
+===============================================================================+
```

---

## 5. Data Model (Spine-First)

### outreach.bit_signals

| Column | Type | Description |
|--------|------|-------------|
| signal_id | UUID | PK |
| outreach_id | UUID | FK to outreach.outreach (SPINE) |
| signal_type | VARCHAR | Signal category |
| signal_impact | NUMERIC | Impact value |
| source_spoke | VARCHAR | Originating sub-hub |
| correlation_id | UUID | REQUIRED - traceability |
| process_id | UUID | Process traceability |
| decay_period_days | INTEGER | Decay period |
| signal_timestamp | TIMESTAMPTZ | When signal occurred |
| created_at | TIMESTAMPTZ | Record created |

### outreach.bit_scores

| Column | Type | Description |
|--------|------|-------------|
| outreach_id | UUID | PK + FK to outreach.outreach |
| score | NUMERIC | Current BIT score |
| score_tier | VARCHAR | COLD/WARM/HOT/BURNING |
| signal_count | INTEGER | Total signals received |
| people_score | NUMERIC | Score from People Sub-Hub |
| dol_score | NUMERIC | Score from DOL Sub-Hub |
| blog_score | NUMERIC | Score from Blog Sub-Hub |
| talent_flow_score | NUMERIC | Score from Talent Flow |
| last_signal_at | TIMESTAMPTZ | Last signal received |
| last_scored_at | TIMESTAMPTZ | Last score calculation |
| created_at | TIMESTAMPTZ | Record created |
| updated_at | TIMESTAMPTZ | Record updated |

### outreach.bit_errors

| Column | Type | Description |
|--------|------|-------------|
| error_id | UUID | PK |
| outreach_id | UUID | FK to spine (nullable) |
| pipeline_stage | VARCHAR | ingest/validate/calculate/persist |
| failure_code | VARCHAR | BIT-X-XXX code |
| blocking_reason | TEXT | Human-readable |
| severity | VARCHAR | INFO/WARN/ERROR/FATAL |
| retry_allowed | BOOLEAN | Always FALSE |
| correlation_id | UUID | Traceability |
| process_id | UUID | Process traceability |
| raw_input | JSONB | Original payload |
| stack_trace | TEXT | Exception trace |
| created_at | TIMESTAMPTZ | When recorded |

---

## 6. Correlation ID Doctrine (HARD LAW)

```
+===============================================================================+
|                       CORRELATION ID ENFORCEMENT                              |
|                                                                               |
|   DOCTRINE: correlation_id MUST be propagated unchanged across ALL signals    |
|             from source sub-hub through BIT scoring.                          |
|                                                                               |
|   RULES:                                                                      |
|   1. Every signal received MUST have correlation_id (FAIL if missing)         |
|   2. Score updates MUST log correlation_id of contributing signals            |
|   3. Every error logged MUST include correlation_id                           |
|                                                                               |
|   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              |
|   SOURCE: Originating sub-hub (inherited through signal chain)                |
|                                                                               |
+===============================================================================+
```

---

## 7. Error Codes

| Code | Stage | Description |
|------|-------|-------------|
| BIT-V-NO-CORRELATION | validate | Missing correlation_id |
| BIT-V-NOT-IN-SPINE | validate | outreach_id not in spine |
| BIT-V-INVALID-SIGNAL | validate | Invalid signal structure |
| BIT-P-SIGNAL-FAIL | persist | Failed to write signal |
| BIT-P-SCORE-FAIL | persist | Failed to write score |

---

## 8. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| BIT Engine | DONE | `hubs/company-target/imo/middle/bit_engine.py` |
| BIT Writer | DONE | `hubs/company-target/imo/output/bit_writer.py` |
| Signal Intake | DONE | `BITEngine.process_signal()` |
| Score Calculation | DONE | `CompanyBITScore.add_signal()` |
| Decay Model | DONE | `SIGNAL_DECAY_PERIODS` |
| Threshold Classification | DONE | `CompanyBITScore.get_tier()` |
| Spine Guard | DONE | `ENFORCE_OUTREACH_SPINE_ONLY` |
| Correlation Guard | DONE | `ENFORCE_CORRELATION_ID` |
| Error Persistence | DONE | `outreach.bit_errors` |
| Neon Tables | DONE | `outreach.bit_signals`, `outreach.bit_scores` |

---

## 9. Views

| View | Purpose |
|------|---------|
| `outreach.v_bit_hot_companies` | Companies with score >= 50 |
| `outreach.v_bit_recent_signals` | Signals from last 90 days with decay |
| `outreach.v_bit_tier_distribution` | Company count by tier |

---

## 10. Kill Switches

| Switch | Threshold | Action |
|--------|-----------|--------|
| `signal_flood_per_source` | 500/day | Halt intake from source |
| `signal_flood_per_company` | 50/day | Flag company for review |
| `bit_spike_per_run` | 100 | Halt scoring run |
| `daily_cost_ceiling` | $50 | Halt all processing |

---

## 11. Metrics & KPIs

| Metric | Target | Tracking |
|--------|--------|----------|
| Signals Processed | 100% | Real-time |
| Score Freshness | < 1 hour | Hourly |
| HOT Companies | > 30% | Daily |
| Signal Dedup Rate | < 10% | Daily |

---

## 12. Non-Goals (EXPLICIT)

BIT Engine does NOT:

| Non-Goal | Rationale |
|----------|-----------|
| **Author messaging** | BIT does not generate outreach content. That's Outreach Sub-Hub. |
| **Detect intent** | BIT does not interpret buyer psychology. It only aggregates signals. |
| **Make decisions** | BIT provides scores, not recommendations. Outreach Sub-Hub decides. |
| **Store identity** | BIT uses outreach_id. It does NOT mint identities (Spine does). |
| **Trigger enrichment** | BIT is passive. It does NOT call APIs or fetch data. |
| **Bypass spine** | BIT NEVER writes without valid outreach_id in spine. |
| **Modify signals** | BIT records signals as received. No transformation. |

BIT Engine ONLY:

| Goal | Description |
|------|-------------|
| **Aggregates signals** | From sub-hubs via spokes |
| **Calculates scores** | Deterministic, weight-based |
| **Applies decay** | Time-based, formulaic |
| **Classifies tiers** | Based on locked thresholds |
| **Persists to Neon** | Signals → `outreach.bit_signals`, Scores → `outreach.bit_scores` |

---

## 13. Outreach Sub-Hub Interface (READ ONLY)

Outreach Sub-Hub can READ BIT scores but CANNOT write signals or scores.

```python
from bit_engine import BITReadOnlyInterface

# Outreach Sub-Hub uses read-only interface
bit_reader = BITReadOnlyInterface()

# Check if company is eligible for outreach
if bit_reader.is_outreach_eligible(outreach_id):
    # Proceed with outreach

# Get all hot companies for campaign
hot_companies = bit_reader.get_hot_companies(limit=100)
```

| Method | Purpose |
|--------|---------|
| `get_score(outreach_id)` | Get score for one company |
| `get_hot_companies(limit)` | Get companies with score >= 50 |
| `get_tier_distribution()` | Get count by tier |
| `is_outreach_eligible(outreach_id)` | Check if score >= 50 |

---

## 14. Migration Notes (v2.1 -> v3.0)

### Breaking Changes

1. **Identity**: Changed from `company_unique_id` to `outreach_id`
2. **Tables**: Moved from `funnel.bit_signal_log` to `outreach.bit_signals`
3. **Correlation ID**: Now REQUIRED (was optional)
4. **Writer**: New `bit_writer.py` replaces BIT methods in `neon_writer.py`

### Deprecated

| Item | Replacement |
|------|-------------|
| `funnel.bit_signal_log` | `outreach.bit_signals` |
| `marketing.company_master.bit_score` | `outreach.bit_scores` |
| `neon_writer.log_bit_signal()` | `bit_writer.BITWriter.write_signal()` |
| `bit.bit_company_score` | `outreach.bit_scores` |
| `bit.bit_signal` | `outreach.bit_signals` |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-17 | Initial PRD |
| 2.1 | 2025-12-19 | Hardened: Correlation ID, Signal Idempotency |
| 3.0 | 2026-01-08 | Spine-First Architecture: outreach_id identity, new tables, error discipline |
| **3.1** | **2026-01-08** | **LOCKED**: Runtime guards, decay function, read-only interface, Non-Goals |

---

**Document Version:** 3.1
**Last Updated:** 2026-01-08
**Owner:** BIT Engine
**Status:** PRODUCTION READY (LOCKED)
**Doctrine:** Spine-First Architecture v1.1
