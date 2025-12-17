# BIT Engine Signal Flow

**Location:** `ctb/sys/enrichment/pipeline_engine/hub/`
**Owner:** Company Hub
**Version:** 1.0

---

## Overview

The BIT (Buyer Intent Tool) Engine is the **sole decision maker** in the Barton Outreach system. It lives **inside** the Company Hub and aggregates signals from all spokes to determine messaging decisions.

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   SPOKES EMIT SIGNALS.  SPOKES DO NOT MAKE DECISIONS.                ║
║                                                                       ║
║   ONLY BIT MAY DECIDE WHO GETS MESSAGED, WHEN, AND HOW.              ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

## Architecture

```
                        SIGNAL AGGREGATION
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
   ┌───────────┐        ┌───────────┐        ┌───────────┐
   │  PEOPLE   │        │    DOL    │        │  TALENT   │
   │   SPOKE   │        │   SPOKE   │        │   FLOW    │
   │           │        │           │        │   SPOKE   │
   │ Signals:  │        │ Signals:  │        │ Signals:  │
   │ +10 slot  │        │ +5 5500   │        │ +10 join  │
   │ +3 email  │        │ +8 large  │        │ -5 leave  │
   │ +2 linked │        │ +7 broker │        │ +3 title  │
   └─────┬─────┘        └─────┬─────┘        └─────┬─────┘
         │                     │                     │
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
╔═════════════════════════════════════════════════════════════════════════╗
║                         COMPANY HUB                                     ║
║                        ┌────────────────────────────────────────┐       ║
║                        │           BIT ENGINE                   │       ║
║                        │                                        │       ║
║                        │   process_signal(BITSignal)            │       ║
║                        │         │                              │       ║
║                        │         ▼                              │       ║
║                        │   ┌─────────────────┐                  │       ║
║                        │   │ CompanyBITScore │                  │       ║
║                        │   │  - score: 0-100 │                  │       ║
║                        │   │  - signal_count │                  │       ║
║                        │   │  - breakdown    │                  │       ║
║                        │   └─────────────────┘                  │       ║
║                        │         │                              │       ║
║                        │         ▼                              │       ║
║                        │   DECISION OUTPUT:                     │       ║
║                        │   - Hot (>=75): Outreach immediately   │       ║
║                        │   - Warm (50-74): Nurture sequence     │       ║
║                        │   - Cold (<50): No outreach            │       ║
║                        └────────────────────────────────────────┘       ║
╚═════════════════════════════════════════════════════════════════════════╝
                               │
                               │ (Score >= 50 only)
                               │
                               ▼
                    ┌─────────────────────────────┐
                    │      OUTREACH NODE          │
                    │   (Executes BIT Decision)   │
                    └─────────────────────────────┘
```

---

## Signal Types

### People Spoke Signals

| Signal | Enum | Impact | When Emitted |
|--------|------|--------|--------------|
| Slot Filled | `SLOT_FILLED` | +10.0 | Executive assigned to slot |
| Slot Vacated | `SLOT_VACATED` | -5.0 | Executive left slot |
| Email Verified | `EMAIL_VERIFIED` | +3.0 | Email confirmed via MillionVerifier |
| LinkedIn Found | `LINKEDIN_FOUND` | +2.0 | LinkedIn profile discovered |

### DOL Spoke Signals

| Signal | Enum | Impact | When Emitted |
|--------|------|--------|--------------|
| Form 5500 Filed | `FORM_5500_FILED` | +5.0 | Annual 5500 detected |
| Large Plan | `LARGE_PLAN` | +8.0 | Plan > 100 participants |
| Broker Change | `BROKER_CHANGE` | +7.0 | Broker of record changed |

### Talent Flow Spoke Signals

| Signal | Enum | Impact | When Emitted |
|--------|------|--------|--------------|
| Executive Joined | `EXECUTIVE_JOINED` | +10.0 | New exec at company |
| Executive Left | `EXECUTIVE_LEFT` | -5.0 | Exec departed |
| Title Change | `TITLE_CHANGE` | +3.0 | Promotion/role change |

### Blog Spoke Signals (PLANNED)

| Signal | Enum | Impact | When Emitted |
|--------|------|--------|--------------|
| Funding Event | `FUNDING_EVENT` | +15.0 | Raised funding |
| Acquisition | `ACQUISITION` | +12.0 | M&A activity |
| Layoff | `LAYOFF` | -3.0 | Workforce reduction |
| Leadership Change | `LEADERSHIP_CHANGE` | +8.0 | C-suite announcement |

---

## How Spokes Emit Signals

### Correct Pattern (Emit Signal to BIT)

```python
from pipeline_engine.hub.bit_engine import BITEngine, SignalType

# Initialize BIT Engine (singleton within Company Hub)
bit_engine = BITEngine()

# Emit signal from People Spoke
def on_slot_filled(company_id: str, person_id: str, slot_type: str):
    """People Spoke emits SLOT_FILLED signal to BIT"""
    bit_engine.create_signal(
        signal_type=SignalType.SLOT_FILLED,
        company_id=company_id,
        source_spoke='people_node',
        metadata={
            'person_id': person_id,
            'slot_type': slot_type
        }
    )
    # DO NOT make outreach decision here!
```

### WRONG Pattern (Direct Outreach Decision)

```python
# NEVER DO THIS IN A SPOKE!
def on_slot_filled(company_id: str, person_id: str):
    """VIOLATION: Spoke making outreach decision"""
    if slot_type == 'CEO':
        # WRONG: Spoke should NOT make this decision
        promote_to_outreach(company_id, person_id)  # VIOLATION!
```

---

## BIT Engine API

### Create Signal

```python
bit_engine.create_signal(
    signal_type: SignalType,      # Required: Signal type enum
    company_id: str,              # Required: Company anchor
    source_spoke: str,            # Required: Originating spoke
    impact: Optional[float],      # Optional: Override default impact
    metadata: Dict[str, Any]      # Optional: Additional context
) -> BITSignal
```

### Get Score

```python
score = bit_engine.get_score(company_id)
# Returns CompanyBITScore with:
#   - score: float (0-100)
#   - signal_count: int
#   - breakdown: Dict[str, float] by source spoke
```

### Get Top Companies

```python
hot_leads = bit_engine.get_companies_above_threshold(75)
# Returns list of companies ready for immediate outreach

warm_leads = bit_engine.get_companies_above_threshold(50)
# Returns list of companies ready for nurture sequence
```

---

## Score Calculation

### Formula

```
BIT_Score = Σ (signal_impact for all signals received)

Where:
  - People signals:     +10 to -5 per signal
  - DOL signals:        +5 to +8 per signal
  - Talent Flow signals: +10 to -5 per signal
  - Blog signals:       +15 to -3 per signal
```

### Score Breakdown

```python
breakdown = score.breakdown()
# Returns:
{
    'total': 85.0,
    'people_node': 25.0,
    'dol_node': 20.0,
    'talent_flow': 30.0,
    'blog_node': 10.0
}
```

### Score Categories

| Category | Score Range | Action |
|----------|-------------|--------|
| **Hot** | >= 75 | Immediate outreach, priority sequencing |
| **Warm** | 50-74 | Nurture sequence, monitor for escalation |
| **Cold** | < 50 | No outreach, continue signal collection |

---

## Outreach Gate

The Outreach Node **cannot execute** without BIT approval:

```python
def promote_to_outreach(company_id: str, person_id: str):
    """Outreach promotion - BIT-gated"""
    # Get BIT score first
    score = bit_engine.get_score_value(company_id)

    # BIT gate check
    if score < 50:
        logger.info(f"BIT Gate: {company_id} score {score} < 50, skipping")
        return {'status': 'skipped', 'reason': 'BIT score below threshold'}

    # BIT approved - proceed with outreach
    return {'status': 'promoted', 'bit_score': score}
```

---

## Movement Engine Integration

The Movement Engine works alongside BIT to manage contact lifecycle states:

```
┌─────────────────────────────────────────────────────────────────┐
│                    MOVEMENT ENGINE                               │
│                                                                 │
│  States: SUSPECT → WARM → TALENTFLOW_WARM → APPOINTMENT         │
│                                                                 │
│  BIT Score triggers state transitions:                          │
│  - BIT >= 25: SUSPECT → WARM                                    │
│  - BIT >= 50: WARM → eligible for outreach                      │
│  - BIT >= 75: Priority sequencing                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Enforcement

### What Spokes MUST Do

1. Call `bit_engine.create_signal()` when events occur
2. Include `company_id` in every signal (anchor required)
3. Specify `source_spoke` for attribution
4. Provide relevant `metadata` for debugging

### What Spokes MUST NOT Do

1. Make outreach decisions
2. Write to `outreach_log` directly
3. Call `promote_to_outreach()` directly
4. Bypass BIT score check

### Audit Verification

```bash
# Verify spokes don't make direct outreach calls
grep -r "promote_to_outreach\|outreach_log" ctb/sys/enrichment/pipeline_engine/spokes/
# Should return NO RESULTS

# Verify spokes emit signals correctly
grep -r "create_signal\|process_signal" ctb/sys/enrichment/pipeline_engine/spokes/
# Should return signal emissions
```

---

## Files

| File | Purpose |
|------|---------|
| `bit_engine.py` | BIT Engine core implementation |
| `company_hub.py` | Company Hub with BIT integration |
| `BIT_SIGNAL_FLOW.md` | This documentation |

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   SIGNAL FLOW:                                                          │
│                                                                         │
│   1. Event occurs in spoke (slot filled, 5500 filed, exec joined)      │
│   2. Spoke calls bit_engine.create_signal()                            │
│   3. BIT Engine updates company score                                   │
│   4. Score crosses threshold → Outreach Node can execute               │
│   5. Outreach Node promotes to campaign (BIT-gated)                    │
│                                                                         │
│   SPOKES → SIGNALS → BIT → DECISION → OUTREACH                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*Last Updated: 2025-12-17*
*BIT Engine Version: 1.0*
