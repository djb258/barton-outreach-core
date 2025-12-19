# PRD: Outreach Spoke v2.1

**Version:** 2.1 (Hardened per Barton Doctrine)
**Status:** Active
**Hardening Date:** 2025-12-19
**Last Updated:** 2025-12-19
**Doctrine:** Bicycle Wheel v1.1 / Barton Doctrine
**Barton ID Range:** `04.04.02.04.6XXXX.###`
**Changes:** Primary contact selection, BIT threshold enforcement, cooling-off period, correlation ID propagation

---

## Spoke Ownership Statement

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          OUTREACH SPOKE OWNERSHIP                             ║
║                                                                               ║
║   This spoke OWNS:                                                            ║
║   ├── Outreach candidate evaluation                                           ║
║   ├── Primary contact selection (HR > CEO > CFO priority)                     ║
║   ├── BIT threshold enforcement (>= 50 for outreach)                          ║
║   ├── Cooling-off period enforcement (30-day minimum)                         ║
║   ├── Campaign assignment and tracking                                        ║
║   └── Outreach log persistence                                                ║
║                                                                               ║
║   This spoke DOES NOT OWN:                                                    ║
║   ├── Company identity (company_id, domain, email_pattern)                    ║
║   ├── BIT score calculation (that's BIT Engine)                               ║
║   ├── Email generation or verification (that's People Spoke)                  ║
║   ├── Slot assignment (that's People Spoke)                                   ║
║   ├── Signal emission (signals come FROM other spokes)                        ║
║   └── Actual email sending (that's external system - Instantly/HeyReach)      ║
║                                                                               ║
║   This spoke is the OUTPUT spoke - final decision point before sending.       ║
║                                                                               ║
║   PREREQUISITE: company_id + domain + email_pattern + bit_score >= 50         ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 1. Purpose

The Outreach Spoke is the **OUTPUT node** of the Barton pipeline. It evaluates companies for outreach readiness, selects the primary contact, enforces cooling-off periods, and promotes candidates to the outreach log for campaign execution.

### Core Functions

1. **Candidate Evaluation** - Check BIT threshold (>= 50), anchor slot, domain/pattern
2. **Primary Contact Selection** - Select contact with priority: HR > CEO > CFO
3. **Cooling-Off Enforcement** - Prevent over-messaging (30-day minimum between contacts)
4. **Campaign Assignment** - Assign companies to appropriate outreach campaigns
5. **Outreach Log Persistence** - Write promotion records to Neon

### The Golden Rule (OUTPUT)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   OUTREACH CRITERIA (ALL MUST BE TRUE):                                     │
│                                                                             │
│   ✓ company_id IS NOT NULL                                                  │
│   ✓ domain IS NOT NULL                                                      │
│   ✓ email_pattern IS NOT NULL                                               │
│   ✓ bit_score >= 50 (HOT threshold)                                         │
│   ✓ has at least one filled anchor slot (HR/CEO/CFO)                        │
│   ✓ NOT in cooling-off period (>= 30 days since last contact)               │
│                                                                             │
│   IF ANY CONDITION FAILS: DO NOT PROMOTE TO OUTREACH                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow

```
┌─────────────────┐
│   BIT Engine    │
│  (bit_score)    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTREACH SPOKE                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. CANDIDATE EVALUATION                                                    │
│     ├── Load companies with bit_score >= 50                                 │
│     ├── Validate company anchor (company_id, domain, email_pattern)         │
│     ├── Check anchor slot (at least HR, CEO, or CFO filled)                 │
│     └── Verify not in cooling-off period                                    │
│                                                                             │
│  2. PRIMARY CONTACT SELECTION                                               │
│     ├── Priority 1: HR slot (hr_person_id)                                  │
│     ├── Priority 2: CEO slot (ceo_person_id)                                │
│     ├── Priority 3: CFO slot (cfo_person_id)                                │
│     └── Get person data (name, email, title)                                │
│                                                                             │
│  3. CAMPAIGN ASSIGNMENT                                                     │
│     ├── Match company to campaign by industry/size                          │
│     └── Assign sequence_id                                                  │
│                                                                             │
│  4. OUTREACH LOG WRITE                                                      │
│     ├── Create outreach_log record                                          │
│     ├── Set status = 'queued'                                               │
│     └── Record correlation_id for tracing                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Outreach Log   │
│  (Neon DB)      │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│ External System │
│ (Instantly/     │
│  HeyReach)      │
└─────────────────┘
```

---

## 3. Correlation ID Doctrine (HARD LAW)

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       CORRELATION ID ENFORCEMENT                              ║
║                                                                               ║
║   DOCTRINE: correlation_id MUST be propagated unchanged across ALL processes ║
║             and into all error logs and outreach records.                     ║
║                                                                               ║
║   RULES:                                                                      ║
║   1. Every outreach evaluation MUST include correlation_id                    ║
║   2. Every outreach_log record MUST include correlation_id                    ║
║   3. Every error logged MUST include correlation_id                           ║
║   4. correlation_id MUST NOT be modified mid-processing                       ║
║                                                                               ║
║   FORMAT: UUID v4 (e.g., "550e8400-e29b-41d4-a716-446655440000")              ║
║   GENERATED BY: Company Pipeline (inherited through processing)               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 4. Primary Contact Selection

### Priority Order

| Priority | Slot | Rationale |
|----------|------|-----------|
| 1 | HR | Primary buyer for benefits/HR tech |
| 2 | CEO | Executive decision maker |
| 3 | CFO | Budget authority |

### Selection Algorithm

```python
def _get_primary_contact(company_id: str, company_data: Dict) -> Optional[Dict]:
    """
    Select primary contact with HR > CEO > CFO priority.
    Returns person data if found, None otherwise.
    """
    slot_priority = [
        ('hr', 'HR'),
        ('ceo', 'CEO'),
        ('cfo', 'CFO')
    ]

    for slot_key, slot_type in slot_priority:
        person_id = company_data.get(f'{slot_key}_person_id')
        if person_id:
            person_data = load_person_by_id(person_id)
            if person_data and person_data.get('email'):
                return {
                    'id': person_id,
                    'name': person_data.get('full_name'),
                    'email': person_data.get('email'),
                    'title': person_data.get('title'),
                    'slot_type': slot_type
                }

    return None  # No valid contact found
```

---

## 5. Cooling-Off Period

### Rules

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       COOLING-OFF PERIOD ENFORCEMENT                          ║
║                                                                               ║
║   MINIMUM: 30 days between outreach attempts to same company                  ║
║                                                                               ║
║   CHECK: SELECT MAX(sent_at) FROM outreach_log                                ║
║          WHERE company_id = ? AND status IN ('sent', 'delivered')             ║
║                                                                               ║
║   IF last_contact_date + 30 days > NOW():                                     ║
║       REJECT candidate (reason: 'cooling_off')                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

## 6. Kill Switches

| Switch | Threshold | Action |
|--------|-----------|--------|
| `daily_send_limit` | 200 emails | Halt all outreach for day |
| `hourly_send_limit` | 30 emails | Pause for 1 hour |
| `bounce_rate_ceiling` | 10% | Halt and review |
| `unsubscribe_spike` | 5% | Halt and review |

---

## 7. Outreach Log Schema

```sql
CREATE TABLE marketing.outreach_log (
    outreach_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id VARCHAR(25) NOT NULL REFERENCES marketing.company_master(company_unique_id),
    person_id VARCHAR(25) NOT NULL REFERENCES marketing.people_master(unique_id),
    correlation_id UUID NOT NULL,
    campaign_id VARCHAR(50),
    sequence_id VARCHAR(50),
    bit_score INTEGER NOT NULL,
    slot_type VARCHAR(10) NOT NULL,
    status VARCHAR(20) DEFAULT 'queued',  -- queued, sent, delivered, opened, clicked, replied, bounced, unsubscribed
    queued_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    replied_at TIMESTAMP,
    external_id VARCHAR(100),  -- Instantly/HeyReach ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_outreach_company ON marketing.outreach_log(company_id);
CREATE INDEX idx_outreach_status ON marketing.outreach_log(status);
CREATE INDEX idx_outreach_correlation ON marketing.outreach_log(correlation_id);
```

---

## 8. Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Outreach Spoke | ✅ Implemented | `spokes/outreach/outreach_spoke.py` |
| Primary Contact Selection | ✅ Implemented | `_get_primary_contact()` |
| BIT Threshold Check | ✅ Implemented | `process()` |
| Cooling-Off Check | ✅ Implemented | `_check_cooling_off()` |
| Neon Writer | ✅ Implemented | `hub/company/neon_writer.py` |
| Outreach Log Schema | ✅ Defined | Above |
| Kill Switches | ✅ Defined | `tests/dry_run_orchestrator.py` |

---

## 9. Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          OUTREACH SPOKE DEPENDENCIES                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   REQUIRED FROM COMPANY HUB:                                                │
│   ├── company_id (valid anchor)                                             │
│   ├── domain (for email generation)                                         │
│   └── email_pattern (for email generation)                                  │
│                                                                             │
│   REQUIRED FROM PEOPLE SPOKE:                                               │
│   ├── hr_person_id, ceo_person_id, cfo_person_id (slot assignments)         │
│   └── Person records with verified emails                                   │
│                                                                             │
│   REQUIRED FROM BIT ENGINE:                                                 │
│   └── bit_score >= 50 (HOT threshold)                                       │
│                                                                             │
│   EXTERNAL DEPENDENCIES:                                                    │
│   ├── Instantly API (for email sending)                                     │
│   └── HeyReach API (for LinkedIn outreach)                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Metrics & KPIs

| Metric | Target | Tracking |
|--------|--------|----------|
| Candidates Evaluated | 100% of HOT companies | Daily |
| Pass Rate | > 80% | Daily |
| Bounce Rate | < 5% | Per campaign |
| Open Rate | > 20% | Per campaign |
| Reply Rate | > 3% | Per campaign |

---

**Last Updated:** 2025-12-19
**Author:** Claude Code
**Approved By:** Barton Doctrine
