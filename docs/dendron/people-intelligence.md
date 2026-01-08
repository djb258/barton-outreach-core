---
id: people-intelligence
title: People Intelligence Sub-Hub
desc: Slot-based people intelligence - CEO/CFO/HR slot creation and person binding
updated: 2026-01-08
created: 2026-01-08
tags:
  - hub
  - people
  - slots
  - imo
  - certified
---

# People Intelligence Sub-Hub

## Overview

The People Intelligence Sub-Hub manages **slot creation and person binding** for outreach-ready companies. It is the **4th sub-hub** in the canonical waterfall (after Blog Content, before Outreach Execution).

## Quick Reference

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-PEOPLE |
| **Doctrine ID** | 04.04.02 |
| **Version** | 1.1.0 |
| **Status** | ✅ FULL PASS |
| **Migration Hash** | `678a8d99` |
| **Certification Date** | 2026-01-08 |

## Ownership

### Owns (Write Access)

- `people.company_slot` - Slot definitions per company (1,359 rows)
- `people.people_master` - Person records (170 rows)
- `people.person_movement_history` - Employment changes (append-only)
- `people.people_sidecar` - Enrichment data
- `people.people_resolution_queue` - Ambiguous bindings
- `people.people_invalid` - Invalid person data
- `people.people_errors` - Error capture (1,053 rows)

### Does NOT Own (Read-Only)

- Company identity (CL owns)
- Outreach spine (Orchestration owns)
- Email patterns (Company Target owns)
- DOL filings (DOL Sub-Hub owns)
- Blog signals (Blog Content owns)

## IMO Architecture

```
INPUT (I)           MIDDLE (M)              OUTPUT (O)
──────────         ──────────              ───────────
outreach.outreach  Slot Creation:         PASS:
    ↓              company_slot            → outreach.people
company_target         ↓                       (export)
    ↓              Person Binding:
dol.ein_linkage    people_master          FAIL:
    ↓                  ↓                   → people.people_errors
blog.blog_context  Movement Tracking:         (capture)
                   person_movement_history
```

## Canonical Slot Types

| Slot | Type | Description |
|------|------|-------------|
| **CEO** | Canonical | Chief Executive Officer - always created |
| **CFO** | Canonical | Chief Financial Officer - always created |
| **HR** | Canonical | HR Director/Manager - always created |
| **BEN** | Conditional | Benefits Manager - DOL/size triggered |

## Schema Evolution (2026-01-08)

Migration `004_people_slot_schema_evolution.sql` added 4 doctrine-required columns:

| Column | Type | Coverage | Notes |
|--------|------|----------|-------|
| `outreach_id` | UUID NULL | 306/1,359 (22.5%) | Via dol.ein_linkage |
| `canonical_flag` | BOOLEAN | 100% | TRUE for CEO/CFO/HR |
| `creation_reason` | TEXT | 100% | 'canonical' or trigger |
| `slot_status` | TEXT | 100% | Lifecycle state |

### Backfill Errors

- **1,053 slots** logged to `people.people_errors`
- Error code: `PI-E901` (schema_evolution)
- Retry strategy: `manual_fix`
- These slots lack `outreach_id` but remain operational

## Error System

### Error Codes (20 total)

| Range | Stage | Count |
|-------|-------|-------|
| PI-E1xx | slot_creation | 3 |
| PI-E2xx | slot_fill | 4 |
| PI-E3xx | movement_detect | 3 |
| PI-E4xx | enrichment | 4 |
| PI-E5xx | promotion | 3 |
| PI-E9xx | system | 3 |

### Kill Switches

| Switch | Env Variable | Default |
|--------|--------------|---------|
| Slot Autofill | `PEOPLE_SLOT_AUTOFILL_ENABLED` | true |
| Movement Detect | `PEOPLE_MOVEMENT_DETECT_ENABLED` | true |
| Auto Replay | `PEOPLE_AUTO_REPLAY_ENABLED` | true |

## Waterfall Position

```
┌──────────────────┐
│ Company Target   │ ← 1st
└────────┬─────────┘
         ▼
┌──────────────────┐
│ DOL Filings      │ ← 2nd
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Blog Content     │ ← 3rd
└────────┬─────────┘
         ▼
┌──────────────────┐
│ People Intel     │ ← 4th (THIS HUB) ✅ CERTIFIED
└────────┬─────────┘
         ▼
┌──────────────────┐
│ Outreach Exec    │ ← 5th
└──────────────────┘
```

## Core Doctrine Rules

1. **Slots are created when Outreach ID enters People — not before**
2. **3 canonical slots ALWAYS: CEO, CFO, HR**
3. **Benefits Manager (BEN) is CONDITIONAL, logged, non-canonical**
4. **People binds to slots; slots never float**
5. **Movement history is APPEND-ONLY (audit safe)**
6. **No People table writes upstream — signals only**
7. **LinkedIn URL is the external identity anchor**

## Key Files

| File | Purpose |
|------|---------|
| [PRD.md](../../hubs/people-intelligence/PRD.md) | Product requirements |
| [ADR.md](../../hubs/people-intelligence/ADR.md) | Architecture decisions (3 ADRs) |
| [CHECKLIST.md](../../hubs/people-intelligence/CHECKLIST.md) | Compliance checklist |
| [PEOPLE_SUBHUB_ERD.md](../../hubs/people-intelligence/imo/PEOPLE_SUBHUB_ERD.md) | Entity diagram |
| [PI_ERROR_CODES.md](../../hubs/people-intelligence/imo/PI_ERROR_CODES.md) | Error code registry |
| [PI_READINESS_REPORT.md](../../hubs/people-intelligence/imo/PI_READINESS_REPORT.md) | Certification report |
| [people_errors.py](../../hubs/people-intelligence/imo/middle/people_errors.py) | Error handling module |
| [replay_worker.py](../../hubs/people-intelligence/imo/middle/replay_worker.py) | Replay worker |

## Related

- [[dol-subhub]] - Upstream: EIN linkage
- [[company-target]] - Upstream: Email patterns
- [[blog-content]] - Upstream: Blog signals
- [[outreach-execution]] - Downstream: Contact execution
- [[talent-flow]] - Child: Executive movement sensor (TF-001 CERTIFIED)

---

**Last Updated:** 2026-01-08
**Author:** Claude Code (IMO-Creator)
**Doctrine Version:** Barton IMO v1.1
**Talent Flow Certification:** TF-001 PRODUCTION-READY
