# PRD — People Intelligence Sub-Hub

## 1. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** People Intelligence
- **Owner:** Outreach Team
- **Version:** 1.0.0

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-PI-001 |
| **Doctrine ID** | 04.04.02 |
| **Process ID** | Set at runtime |

---

## 3. Purpose

Populate **role slots**, not raw contacts.
Own human identity, employment state, and slot assignments.
Track human lifecycle independently from company lifecycle.

---

## 4. Lifecycle Gate

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| TARGETABLE | Requires lifecycle >= TARGETABLE |
| Additional | Requires verified pattern from Company Target |

---

## 5. Inputs

| Input | Source | Required |
|-------|--------|----------|
| company_sov_id | Company Lifecycle (external) | YES |
| verified_pattern | Company Target | YES |
| outreach_context_id | contexts/outreach_context | YES |

---

## 6. Pipeline

```
Validate lifecycle permission (>= TARGETABLE)
 ↓
Validate verified pattern exists
 ↓
Phase 5: Email Generation
 ↓
Phase 6: Slot Assignment (CHRO, HR_MANAGER, BENEFITS_LEAD, etc.)
 ↓
Phase 7: Enrichment Queue (only for measured deficit)
 ↓
Phase 8: Output Writer (CSV export only)
```

---

## 7. Cost Rules

| Rule | Enforcement |
|------|-------------|
| Apollo | Tier 1, lifecycle >= TARGETABLE |
| Clay | Tier 2, max 1 per context |
| MillionVerifier | Per-use, lifecycle >= TARGETABLE |
| Enrichment | Only to fix MEASURED slot deficit |

---

## 8. Tools

| Tool | Tier | Cost Class | ADR |
|------|------|------------|-----|
| Apollo | 1 | Low | ADR-PI-001 |
| Clay | 2 | Premium | ADR-PI-001 |
| MillionVerifier | 1 | Per-use | ADR-PI-002 |

---

## 9. Constraints

- [ ] No people without company_sov_id
- [ ] Enrichment only to fix measured slot deficit
- [ ] CSV is output only (never canonical)
- [ ] Requires verified pattern from Company Target

---

## 10. Core Metric

**SLOT_FILL_RATE** — Percentage of target slots filled with verified contacts

Healthy Threshold: >= 80%

---

## 11. Upstream Dependencies, Signal Validity, and Downstream Effects

### Execution Position

**Third in canonical order** — After Company Target and DOL Filings.

### Required Upstream PASS Conditions

| Upstream | Condition |
|----------|-----------|
| Company Target | PASS with verified_pattern |
| Company Target | domain resolved |
| DOL Filings | PASS (or no filings) |

### Signals Consumed (Origin-Bound)

| Signal | Origin | Validity |
|--------|--------|----------|
| company_sov_id | Company Lifecycle (via CT) | Run-bound to outreach_context_id |
| verified_pattern | Company Target | Run-bound to outreach_context_id |
| domain | Company Target | Run-bound to outreach_context_id |
| pattern_confidence | Company Target | Run-bound to outreach_context_id |
| regulatory_signals | DOL Filings | Run-bound to outreach_context_id |

### Signals Emitted

| Signal | Consumers | Validity |
|--------|-----------|----------|
| slot_assignments | Blog, Outreach Execution | Run-bound to outreach_context_id |
| people_records | Blog, Outreach Execution | Run-bound to outreach_context_id |
| SLOT_FILL_RATE | Monitoring | Run-bound to outreach_context_id |

### Downstream Effects

| If This Hub | Then |
|-------------|------|
| PASS | Blog Content may execute |
| FAIL | Blog does NOT execute |

### Explicit Prohibitions

- [ ] May NOT consume Blog Content signals
- [ ] May NOT fix Company Target errors (pattern missing → FAIL, not retry)
- [ ] May NOT re-enrich Company Target domain
- [ ] May NOT refresh signals from prior contexts
- [ ] May NOT use stale pattern from prior context

---

## 12. Tables Owned

This sub-hub owns or writes to the following tables:

### Primary Tables (Write)

| Schema | Table | Purpose | Key Columns |
|--------|-------|---------|-------------|
| `outreach` | `people` | Core people records | person_id, company_unique_id, slot_type |
| `outreach` | `slot_assignments` | WHO fills each slot | assignment_id, person_id, slot_type |
| `outreach` | `email_verification` | Verification results | email, result, verified_at |
| `people` | `movement_history` | Job change tracking | person_id, old_company, new_company |
| `people` | `enrichment_state` | Enrichment status | person_id, phase, status |

### Shared Tables (Read + Write)

| Schema | Table | Purpose | Owner |
|--------|-------|---------|-------|
| `marketing` | `people_master` | Legacy people records | Migrating to outreach |
| `marketing` | `company_slot` | Slot definitions | Company Target |

### Read-Only Tables (From Other Hubs)

| Schema | Table | Purpose | Owner |
|--------|-------|---------|-------|
| `outreach` | `company_target` | Company anchor | Company Target |
| `cl` | `company_identity` | Sovereign company ID | CL Parent |
| `outreach` | `column_registry` | Pattern storage | Company Target |

---

## 13. ERD — People Intelligence Tables

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   PEOPLE INTELLIGENCE TABLE RELATIONSHIPS                    │
└─────────────────────────────────────────────────────────────────────────────┘

outreach.company_target (Company Target Hub)
├── target_id PK
├── company_unique_id FK → cl.company_identity
└── email_pattern (verified)
                │
                │ company_unique_id (FK)
                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        outreach.people (CORE TABLE)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ person_id              TEXT      PK   Unique person identifier              │
│ company_unique_id      TEXT      FK   → outreach.company_target             │
│ first_name             TEXT           First name                            │
│ last_name              TEXT           Last name                             │
│ full_name              TEXT           Full display name                     │
│ job_title              TEXT           Current job title                     │
│ seniority              TEXT           Seniority level                       │
│ seniority_rank         INTEGER        Numeric rank (0-100)                  │
│ linkedin_url           TEXT           LinkedIn profile URL                  │
│ generated_email        TEXT           Generated email address               │
│ email_confidence       TEXT           verified/derived/low_confidence       │
│ email_verified         BOOLEAN        Verification status                   │
│ slot_type              TEXT           CHRO/HR_MANAGER/BENEFITS_LEAD/etc.    │
│ slot_assigned_at       TIMESTAMP      When slot was won                     │
│ created_at             TIMESTAMP      Record creation                       │
│ updated_at             TIMESTAMP      Last modification                     │
└─────────────────────────────────────────────────────────────────────────────┘
        │                               │
        │ person_id (FK)                │ person_id (FK)
        ▼                               ▼
┌───────────────────────┐    ┌─────────────────────────────┐
│ outreach.slot_        │    │ outreach.email_             │
│ assignments           │    │ verification                │
├───────────────────────┤    ├─────────────────────────────┤
│ assignment_id    PK   │    │ verification_id   PK        │
│ person_id        FK   │    │ person_id         FK        │
│ company_unique_id FK  │    │ email             TEXT      │
│ slot_type        TEXT │    │ result            TEXT      │
│ seniority_score  INT  │    │ result_code       INT       │
│ replaced_person_id    │    │ is_valid          BOOLEAN   │
│ assigned_at      TS   │    │ is_catch_all      BOOLEAN   │
│ created_at       TS   │    │ credits_used      INT       │
└───────────────────────┘    │ verified_at       TIMESTAMP │
                             └─────────────────────────────┘
        │
        │ person_id (FK)
        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      people.movement_history                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ movement_id            TEXT      PK   Movement event ID                     │
│ person_id              TEXT      FK   → outreach.people                     │
│ old_company_id         TEXT           Previous company                      │
│ new_company_id         TEXT           New company                           │
│ old_title              TEXT           Previous job title                    │
│ new_title              TEXT           New job title                         │
│ movement_type          TEXT           HIRE/PROMOTION/LATERAL/DEPARTURE      │
│ detected_at            TIMESTAMP      When movement was detected            │
│ source                 TEXT           Detection source                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Slot Type Values

| Slot Type | Seniority Rank | Description |
|-----------|----------------|-------------|
| `CHRO` | 100 | Chief HR Officer, VP HR, SVP HR |
| `HR_MANAGER` | 80 | HR Director, HR Manager, HR Lead |
| `BENEFITS_LEAD` | 60 | Benefits Manager, Benefits Director |
| `PAYROLL_ADMIN` | 50 | Payroll Manager, Payroll Director |
| `HR_SUPPORT` | 30 | HR Coordinator, HR Specialist |
| `UNSLOTTED` | 0 | Could not classify |

### Email Confidence Values

| Confidence | Description | Source |
|------------|-------------|--------|
| `verified` | Pattern verified in Phase 4 | Company Target |
| `derived` | Pattern derived from known emails | Company Target |
| `low_confidence` | Fallback pattern, unverified | People Hub |
| `waterfall` | Pattern discovered via on-demand waterfall | People Hub |

### Indexes

| Table | Index Name | Columns | Purpose |
|-------|------------|---------|---------|
| `outreach.people` | `idx_people_company` | `company_unique_id` | FK lookup |
| `outreach.people` | `idx_people_slot` | `slot_type` | Slot queries |
| `outreach.people` | `idx_people_email` | `generated_email` | Email lookup |
| `outreach.slot_assignments` | `idx_slot_company` | `company_unique_id, slot_type` | Slot conflicts |

---

## 14. Pipeline Phase Summary

| Phase | Name | Input | Output | Tools |
|-------|------|-------|--------|-------|
| 5 | Email Generation | people + patterns | emails | Pattern templates |
| 6 | Slot Assignment | people + emails | slot assignments | Title classifier |
| 7 | Enrichment Queue | failures from 5-6 | queue items | Waterfall (optional) |
| 8 | Output Writer | all results | CSV files | File I/O |

### Phase Tools and Costs

| Phase | Tool | Tier | Cost | Limit |
|-------|------|------|------|-------|
| 5 | Waterfall (optional) | 0-2 | Variable | Budget-gated |
| 6 | Title Classifier | 0 | Free | Unlimited |
| 7 | Waterfall Processor | 0-2 | Variable | Batch limit |
| 8 | CSV Writer | 0 | Free | Unlimited |

### External Verification Tools

| Tool | Tier | Cost | Integration |
|------|------|------|-------------|
| MillionVerifier | 1 | ~$37/10k | `bulk_verifier.py` |
| Apollo | 1 | Low | Contact enrichment |
| Clay | 2 | Premium | ONE per context |

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |

---

**Last Updated**: 2026-01-02
**Hub**: People Intelligence (04.04.02)
**Doctrine**: CL Parent-Child v1.0
