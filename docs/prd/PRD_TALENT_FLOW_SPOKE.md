# PRD: Talent Flow Hub v3.0

**Version:** 3.0 (Constitutional Compliance)
**Status:** Active
**Constitutional Date:** 2026-01-29
**Last Updated:** 2026-01-29
**Doctrine:** IMO-Creator Constitutional Doctrine
**Barton ID Range:** `04.04.06.XX.XXXXX.###`

---

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | IMO-Creator v1.0 |
| **Domain Spec Reference** | `doctrine/REPO_DOMAIN_SPEC.md` |
| **CC Layer** | CC-02 |
| **PRD Constitution** | `templates/doctrine/PRD_CONSTITUTION.md` |
| **CTB Governance** | `docs/CTB_GOVERNANCE.md` |

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
| **Hub Name** | Talent Flow |
| **Hub ID** | talent-flow |
| **Doctrine ID** | 04.04.06 |
| **Owner** | Barton Outreach Core |
| **Version** | 3.0 |
| **Waterfall Order** | 4 |
| **Classification** | Required |

---

## 3. Purpose & Transformation Declaration

### Transformation Statement (REQUIRED)

> **"This hub transforms executive movement data from LinkedIn and news sources (CONSTANTS) into classified movement signals with bi-directional company linkage (VARIABLES) through CAPTURE (movement data ingestion), COMPUTE (company resolution, movement classification), and GOVERN (bi-directional signal emission with idempotency enforcement)."**

| Field | Value |
|-------|-------|
| **Transformation Summary** | Executive movement data → Classified movement signals with bi-directional company linkage |

### Constants (Inputs)

_Immutable inputs received from outside this hub. Reference: `doctrine/REPO_DOMAIN_SPEC.md §2`_

| Constant | Source | Description |
|----------|--------|-------------|
| `linkedin_profile_data` | External Enrichment | LinkedIn executive movement data |
| `news_movement_data` | External Sources | News-based executive changes |
| `outreach_id` | Outreach Spine | Operational identifier for FK linkage |
| `company_domain` | Company Target | Domain for company matching |

### Variables (Outputs)

_Outputs this hub produces. Reference: `doctrine/REPO_DOMAIN_SPEC.md §3`_

| Variable | Destination | Description |
|----------|-------------|-------------|
| `executive_hire_signal` | BIT Engine | New executive hire signal |
| `executive_departure_signal` | BIT Engine | Executive departure signal |
| `lateral_move_signal` | BIT Engine | Same-level company change signal |
| `promotion_signal` | BIT Engine | Internal promotion signal |
| `movement_classification` | Talent Flow tables | Classified movement type |

### Pass Structure

_Constitutional pass mapping per `PRD_CONSTITUTION.md §Pass-to-IMO Mapping`_

| Pass | Type | IMO Layer | Description |
|------|------|-----------|-------------|
| Movement Ingestion | **CAPTURE** | I (Ingress) | Ingest executive movement data |
| Company Resolution | **COMPUTE** | M (Middle) | Match from/to companies to Company Hub records |
| Movement Classification | **COMPUTE** | M (Middle) | Classify as hire, departure, lateral, promotion |
| Bi-Directional Signal Emission | **GOVERN** | O (Egress) | Emit signals to BOTH from and to companies |

### Scope Boundary

| Scope | Description |
|-------|-------------|
| **IN SCOPE** | Movement detection, company resolution, movement classification, bi-directional signal emission |
| **OUT OF SCOPE** | Company identity creation (Company Target owns), BIT scoring (BIT Engine owns), slot assignment (People owns), email generation (People owns) |

---

## Hub Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         TALENT FLOW SPOKE OWNERSHIP                           ║
║                                                                               ║
║   This spoke OWNS:                                                            ║
║   ├── Executive movement detection (hire, departure, lateral)                 ║
║   ├── Company-to-company flow tracking                                        ║
║   ├── Hiring trend analysis                                                   ║
║   ├── Departure pattern detection                                             ║
║   └── Signal emission for movement events                                     ║
║                                                                               ║
║   This spoke DOES NOT OWN:                                                    ║
║   ├── Company identity (company_id, domain, email_pattern)                    ║
║   ├── BIT score calculation (that's BIT Engine)                               ║
║   ├── Slot assignment (that's People Spoke)                                   ║
║   ├── Email generation or verification (that's People Spoke)                  ║
║   └── Outreach decisions (that's Outreach Spoke)                              ║
║                                                                               ║
║   This spoke DETECTS MOVEMENT and EMITS SIGNALS to Company Hub.               ║
║                                                                               ║
║   PREREQUISITE: from_company_id OR to_company_id MUST be valid anchor.        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Purpose

The Talent Flow Spoke monitors executive movements between companies, detecting hires, departures, promotions, and lateral moves. These movements generate high-value signals for the BIT Engine - a new HR hire often indicates benefits review timing.

### Core Functions

1. **Movement Detection** - Identify executive job changes from data sources
2. **Bi-Directional Signals** - Emit signals to BOTH from_company and to_company
3. **Movement Classification** - Categorize as hire, departure, lateral, promotion
4. **Trend Analysis** - Detect hiring/departure patterns
5. **Signal Emission** - Generate BIT-scorable events

### Movement Types

| Type | Signal | BIT Weight | Description |
|------|--------|------------|-------------|
| `EXECUTIVE_HIRE` | To company | +15 | New executive hired |
| `EXECUTIVE_DEPARTURE` | From company | +10 | Executive left |
| `LATERAL_MOVE` | Both companies | +5 | Same-level move |
| `PROMOTION` | To company | +8 | Internal promotion |

---

## 2. Data Flow

```
┌─────────────────┐
│  Data Sources   │
│  (LinkedIn,     │
│   News, Filings)│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TALENT FLOW SPOKE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. MOVEMENT INGESTION                                                      │
│     ├── Parse movement records (person_name, from_company, to_company)      │
│     ├── Validate person identity                                            │
│     └── Assign correlation_id                                               │
│                                                                             │
│  2. COMPANY RESOLUTION                                                      │
│     ├── Match from_company to Company Hub (fuzzy match)                     │
│     ├── Match to_company to Company Hub (fuzzy match)                       │
│     └── Queue unmatched for Company Identity Pipeline                       │
│                                                                             │
│  3. MOVEMENT CLASSIFICATION                                                 │
│     ├── Compare titles (promotion vs lateral)                               │
│     ├── Identify hire (no from_company)                                     │
│     ├── Identify departure (no to_company)                                  │
│     └── Classify lateral (same level, different company)                    │
│                                                                             │
│  4. SIGNAL EMISSION                                                         │
│     ├── EXECUTIVE_HIRE → to_company_id                                      │
│     ├── EXECUTIVE_DEPARTURE → from_company_id                               │
│     ├── LATERAL_MOVE → both companies                                       │
│     └── PROMOTION → to_company_id                                           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   BIT Engine    │
│  (Signal Intake)│
└─────────────────┘
```

---

## 3. Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL processes ║
║             and into all error logs and emitted signals.                      ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every movement record MUST be assigned a correlation_id                  ║
║   2. Every signal emitted MUST include correlation_id                         ║
║   3. Every error logged MUST include correlation_id                           ║
║   4. BI-DIRECTIONAL signals share SAME correlation_id                         ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   GENERATED BY: Talent Flow ingest (one per movement)                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Signal Idempotency Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       SIGNAL IDEMPOTENCY ENFORCEMENT                          ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Movement signals are STRUCTURAL (365-day dedup window)                   ║
║   2. Same person + same movement = ONE signal (even if re-detected)           ║
║   3. Signal dedup key: (company_id, person_id, movement_type, detected_date)  ║
║                                                                               ║
║   DEDUP CHECK (ERD: outreach.bit_signals):                                    ║
║   SELECT * FROM outreach.bit_signals                                          ║
║   WHERE outreach_id = ? AND signal_metadata->>'person_id' = ?                 ║
║     AND signal_type = 'EXECUTIVE_HIRE'                                        ║
║     AND signal_timestamp > NOW() - INTERVAL '365 days';                       ║
║                                                                               ║
║   IF EXISTS: Skip emission, log as duplicate.                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 5. Movement Classification Algorithm

```python
def classify_movement(movement: Dict) -> str:
    """
    Classify movement type based on from/to company and titles.
    """
    from_company = movement.get('from_company_id')
    to_company = movement.get('to_company_id')
    from_title = movement.get('from_title', '').lower()
    to_title = movement.get('to_title', '').lower()

    # No from_company = new hire
    if not from_company and to_company:
        return 'EXECUTIVE_HIRE'

    # No to_company = departure
    if from_company and not to_company:
        return 'EXECUTIVE_DEPARTURE'

    # Same company = internal
    if from_company == to_company:
        if _is_promotion(from_title, to_title):
            return 'PROMOTION'
        return 'LATERAL_MOVE'

    # Different companies = lateral move
    return 'LATERAL_MOVE'

def _is_promotion(from_title: str, to_title: str) -> bool:
    """Check if title change indicates promotion."""
    hierarchy = ['analyst', 'manager', 'director', 'vp', 'svp', 'evp', 'cxo', 'ceo']
    from_level = _get_level(from_title, hierarchy)
    to_level = _get_level(to_title, hierarchy)
    return to_level > from_level
```

---

## 6. Bi-Directional Signal Emission

### Why Bi-Directional?

When an executive moves from Company A to Company B:
- **Company A** loses talent → May need to hire replacement → Sales opportunity
- **Company B** gains talent → New decision maker → Sales opportunity

### Signal Logic

```python
def emit_movement_signals(movement: Dict, correlation_id: str):
    """
    Emit signals to both from_company and to_company.
    """
    from_company = movement.get('from_company_id')
    to_company = movement.get('to_company_id')
    movement_type = classify_movement(movement)

    # Emit to FROM company (if exists)
    if from_company:
        emit_signal(
            company_id=from_company,
            signal_type='EXECUTIVE_DEPARTURE',
            payload={
                'person_name': movement['person_name'],
                'title': movement.get('from_title'),
                'to_company': to_company,
                'movement_type': movement_type
            },
            correlation_id=correlation_id
        )

    # Emit to TO company (if exists)
    if to_company:
        signal_type = 'EXECUTIVE_HIRE' if movement_type != 'PROMOTION' else 'PROMOTION'
        emit_signal(
            company_id=to_company,
            signal_type=signal_type,
            payload={
                'person_name': movement['person_name'],
                'title': movement.get('to_title'),
                'from_company': from_company,
                'movement_type': movement_type
            },
            correlation_id=correlation_id
        )
```

---

## 7. Data Sources

| Source | Data Type | Frequency |
|--------|-----------|-----------|
| LinkedIn Sales Navigator | Executive changes | Daily |
| News/RSS Feeds | Executive announcements | Real-time |
| SEC Filings | Officer changes | On filing |
| Company Press Releases | Hire announcements | Daily |

---

## 8. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Talent Flow Spoke | ✅ Implemented | `spokes/talent_flow/talent_flow_spoke.py` |
| Movement Classification | ✅ Implemented | `classify_movement()` |
| Bi-Directional Signals | ✅ Implemented | `emit_movement_signals()` |
| Company Resolution | ✅ Implemented | Uses Company Hub fuzzy match |
| Signal Deduplication | ✅ Implemented | `ops/enforcement/signal_dedup.py` |
| Correlation ID | ✅ Implemented | `ops/enforcement/correlation_id.py` |

---

## 9. Kill Switches

| Switch | Threshold | Action |
|--------|-----------|--------|
| `movement_flood_per_source` | 500/day | Halt ingestion from source |
| `unmatched_rate_ceiling` | 30% | Pause and review matching |
| `signal_spike_per_company` | 10 movements | Flag for manual review |

---

## 10. Metrics & KPIs

| Metric | Target | Tracking |
|--------|--------|----------|
| Movements Processed | 100% of ingest | Daily |
| Company Match Rate | > 85% | Daily |
| Signal Emission Rate | 100% of matched | Daily |
| False Positive Rate | < 5% | Weekly |

---

**Last Updated:** 2025-12-19
**Author:** Claude Code
**Approved By:** Barton Doctrine
