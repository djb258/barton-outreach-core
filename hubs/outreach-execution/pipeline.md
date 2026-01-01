# Outreach Execution — Pipeline Definition

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 OUTREACH EXECUTION PIPELINE                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ GATE: Golden Rule Validation                                 │
│ ─────────────────────────────────────────────────────────── │
│ IF company_sov_id IS NULL → STOP                            │
│ IF domain IS NULL → STOP                                    │
│ IF email_pattern IS NULL → STOP                             │
│ IF lifecycle < TARGETABLE → STOP                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ EVALUATE: BIT Score Assessment                               │
│ ─────────────────────────────────────────────────────────── │
│ • Get BIT score from bit_engine                             │
│ • Determine outreach state:                                 │
│   - 0-24: SUSPECT → DO_NOT_CONTACT                          │
│   - 25-49: WARM → NEWSLETTER/CONTENT                        │
│   - 50-74: HOT → PERSONALIZED_EMAIL                         │
│   - 75+: BURNING → PHONE_AND_EMAIL                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ BIT Score >= 25?│
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
              ▼                             ▼
        ┌─────────┐                   ┌─────────┐
        │   YES   │                   │   NO    │
        └────┬────┘                   └────┬────┘
             │                              │
             ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│ SELECT: Contact         │    │ STOP: Do Not Contact    │
│ ─────────────────────── │    │ ─────────────────────── │
│ • Get primary contact   │    │ • Log as SUSPECT        │
│ • Verify cooling-off    │    │ • Queue for BIT update  │
│ • Rate limit check      │    └─────────────────────────┘
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│ EXECUTE: Send Outreach                                       │
│ ─────────────────────────────────────────────────────────── │
│ • Create campaign if needed                                 │
│ • Add to sequence                                           │
│ • Send email                                                │
│ • Log to send_log                                           │
│ • Update outreach_history                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ TRACK: Engagement                                            │
│ ─────────────────────────────────────────────────────────── │
│ • Track opens                                               │
│ • Track clicks                                              │
│ • Track replies                                             │
│ • Update engagement_events                                  │
│ • Feed signals back to BIT engine                           │
└─────────────────────────────────────────────────────────────┘
```

---

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                    OUTREACH STATE MACHINE                    │
└─────────────────────────────────────────────────────────────┘

    BIT < 25          BIT 25-49         BIT 50-74         BIT 75+
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
   ┌─────────┐       ┌─────────┐       ┌─────────┐       ┌─────────┐
   │ SUSPECT │       │  WARM   │       │   HOT   │       │ BURNING │
   └─────────┘       └─────────┘       └─────────┘       └─────────┘
        │                 │                 │                 │
        ▼                 ▼                 ▼                 ▼
   DO_NOT_          NEWSLETTER/      PERSONALIZED     PHONE_AND_
   CONTACT          CONTENT          _EMAIL           EMAIL
```

---

## Key Files

| Component | File |
|-----------|------|
| Outreach Hub | `imo/middle/outreach_hub.py` |
