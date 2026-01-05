# People Intelligence Hub — CC-02

CC_VERSION: v1.1.0
LAST_VERIFIED: 2026-01-05

**CC Layer**: CC-02 (Hub)
**Doctrine ID**: 04.04.02
**Doctrine**: Canonical Architecture Doctrine v1.1.0

---

## Authority Boundary

People Intelligence is a **consumer hub** that:
- Receives identity via Company Target (NOT directly from CL)
- Discovers and manages people records
- Assigns slots to executives

## Identity Rules

| Identity | Owner | This Hub |
|----------|-------|----------|
| company_unique_id | CL via CT | CONSUME ONLY |
| person_id | This Hub | MINT |
| slot_assignment_id | This Hub | MINT |

## IMO Structure

```
people-intelligence/
├── CC.md
├── hub.manifest.yaml
├── __init__.py
└── imo/
    ├── input/            # CT + DOL signal ingress
    ├── middle/           # People matching, slots
    │   ├── phases/       # Phases 5-8
    │   ├── movement_engine/
    │   └── sub_wheels/   # Email verification
    └── output/           # People records egress
```

## Upstream Dependencies

| Upstream | Signal Consumed | Required |
|----------|-----------------|----------|
| Company Target | verified_pattern, domain | YES |
| DOL Filings | ein, filing_signals | YES |

## Waterfall Position

Executes AFTER DOL Filings (04.04.03) despite lower doctrine ID.
This is by design — People needs EIN signals from DOL.
