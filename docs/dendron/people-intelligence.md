---
id: people-intelligence
title: People Intelligence Sub-Hub
desc: Slot-based people intelligence - CEO/CFO/HR slot creation and person binding
updated: 2026-01-09
created: 2026-01-08
tags:
  - hub
  - people
  - slots
  - imo
  - certified
  - bulk-seeded
---

# People Intelligence Sub-Hub

## Overview

The People Intelligence Sub-Hub manages **slot creation and person binding** for outreach-ready companies. It is the **4th sub-hub** in the canonical waterfall (after Blog Content, before Outreach Execution).

## Quick Reference

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-PEOPLE |
| **Doctrine ID** | 04.04.02 |
| **Version** | 1.2.0 |
| **Status** | ✅ FULL PASS — BULK SEEDED |
| **Migration Hash** | `678a8d99` |
| **Certification Date** | 2026-01-08 |
| **Bulk Seed Date** | 2026-01-09 |

## Ownership

### Owns (Write Access)

- `people.company_slot` - Slot definitions per company (**190,755 rows** — bulk seeded 2026-01-09)
- `people.people_master` - Person records (170 rows)
- `people.people_candidate` - Candidate queue table (NEW — structure only)
- `people.slot_ingress_control` - Kill switch table (NEW — OFF by default)
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
8. **Email is OPTIONAL enrichment — NEVER blocks slot fill** *(Added 2026-01-09)*

## Slot Contract (Enforced 2026-01-09)

> **DOCTRINE:** A slot is FILLED if and only if `full_name + title + linkedin_url` are all present and non-empty. Email is enrichment-only.

See [[people-slot-contract]] for full documentation.

### Contract Fields

| Field | Requirement | Severity if Missing |
|-------|-------------|---------------------|
| `full_name` | **REQUIRED** | ❌ ERROR (blocks fill) |
| `title` | **REQUIRED** | ❌ ERROR (blocks fill) |
| `linkedin_url` | **REQUIRED** | ❌ ERROR (blocks fill) |
| `email` | Optional enrichment | ⚠️ WARNING only |

### Enforcement Artifacts

| Artifact | Location |
|----------|----------|
| Validation function | `ops/validation/validation_rules.py::validate_slot_contract()` |
| Regression tests | `ops/tests/test_people_slot_contract.py` (15 tests) |
| Contract YAML | `contracts/people-outreach.contract.yaml` |
| Doctrine YAML | `docs/doctrine/doctrine/slot_contract.yaml` |

## Neon Data Paths

### Sovereign Bridge Path (Canonical)

The canonical path from `outreach_id` to valid `company_unique_id`:

```
outreach.outreach.sovereign_id           (UUID)
        ↓ JOIN ON company_sov_id
cl.company_identity_bridge.source_company_id   (04.04.01.xx.xxxxx.xxx)
        ↓ FK VALIDATED
company.company_master.company_unique_id       (string, FK target)
```

### Why This Path?

| ID Source | Format | FK Valid? | Use Case |
|-----------|--------|-----------|----------|
| `outreach.company_target.company_unique_id` | UUID | ❌ NO | Different ID system |
| `cl.company_identity_bridge.source_company_id` | `04.04.01.xx` | ✅ YES | Canonical path |
| `company.company_master.company_unique_id` | `04.04.01.xx` | ✅ FK TARGET | Reference table |

### Slot Creation Query

```sql
INSERT INTO people.company_slot (...)
SELECT 
    gen_random_uuid()::text,
    cm.company_unique_id,        -- From company_master (FK valid)
    o.outreach_id,
    :slot_type,
    'open', TRUE, 'bulk_seed', NOW()
FROM outreach.outreach o
JOIN cl.company_identity_bridge b ON b.company_sov_id = o.sovereign_id
JOIN company.company_master cm ON cm.company_unique_id = b.source_company_id
WHERE NOT EXISTS (SELECT 1 FROM people.company_slot cs 
                  WHERE cs.outreach_id = o.outreach_id AND cs.slot_type = :slot_type);
```

### Bulk Seed Results (2026-01-09)

| Slot Type | Count |
|-----------|-------|
| CEO | 63,585 |
| CFO | 63,585 |
| HR | 63,585 |
| **Total** | **190,755** |

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
- [[people-slot-contract]] - Slot contract doctrine (SLOT-CONTRACT-001 ENFORCED)

---

**Last Updated:** 2026-01-09
**Author:** Claude Code (IMO-Creator)
**Doctrine Version:** Barton IMO v1.2
**Bulk Seed Status:** ✅ COMPLETE — 190,755 slots
**Talent Flow Certification:** TF-001 PRODUCTION-READY
**Slot Contract:** SLOT-CONTRACT-001 ENFORCED
