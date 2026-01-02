# People Intelligence Sub-Hub (04.04.02)
## Architecture Overview

**Created**: 2026-01-02
**Updated**: 2026-01-02
**Status**: ACTIVE
**Links**: [[Company-Target-Subhub]] | [[CL_ADMISSION_GATE_DOCTRINE]] | [[PLE-Doctrine]]

---

## Summary

People Intelligence is the **contact enrichment** sub-hub within Barton Outreach Core. It populates **role slots** (not raw contacts), owns human identity, employment state, and slot assignments.

---

## Position in Architecture

```
                    COMPANY TARGET (04.04.01)
                    ─────────────────────────
                    • company_unique_id (from CL)
                    • verified_pattern
                    • domain
                                    │
                                    │ company_unique_id + pattern (downstream)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     PEOPLE INTELLIGENCE (04.04.02)                           │
│                     Contact Enrichment Sub-Hub                               │
├─────────────────────────────────────────────────────────────────────────────┤
│   RECEIVES: company_unique_id, verified_pattern from Company Target         │
│   OWNS: outreach.people, slot_assignments, email_verification               │
│   OUTPUTS: slot_assignments, SLOT_FILL_RATE metric                          │
└─────────────────────────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   Blog Content           Outreach Execution
   (04.04.05)             (04.04.04)
```

---

## Pipeline (Phases 5-8)

| Phase | Name | Purpose | Tools |
|-------|------|---------|-------|
| 5 | Email Generation | Generate emails using verified pattern | Pattern templates |
| 6 | Slot Assignment | Assign people to HR slots | Title classifier |
| 7 | Enrichment Queue | Queue failures for retry | Waterfall (optional) |
| 8 | Output Writer | CSV export | File I/O |

---

## Slot Types (Seniority Order)

| Slot | Rank | Titles |
|------|------|--------|
| CHRO | 100 | Chief HR Officer, VP HR, SVP HR |
| HR_MANAGER | 80 | HR Director, HR Manager, HR Lead |
| BENEFITS_LEAD | 60 | Benefits Manager, Benefits Director |
| PAYROLL_ADMIN | 50 | Payroll Manager, Payroll Director |
| HR_SUPPORT | 30 | HR Coordinator, HR Specialist |
| UNSLOTTED | 0 | Could not classify |

---

## Tables Owned

### Primary Tables (Write)

| Schema | Table | Purpose |
|--------|-------|---------|
| `outreach` | `people` | Core people records |
| `outreach` | `slot_assignments` | WHO fills each slot |
| `outreach` | `email_verification` | Verification results |
| `people` | `movement_history` | Job change tracking |
| `people` | `enrichment_state` | Enrichment status |

### Read-Only Tables (From Upstream)

| Schema | Table | Owner |
|--------|-------|-------|
| `outreach` | `company_target` | Company Target |
| `cl` | `company_identity` | CL Parent |

---

## ERD

```
outreach.company_target (Company Target)
        │
        │ company_unique_id (FK)
        ▼
outreach.people
├── person_id (PK)
├── company_unique_id (FK)
├── first_name, last_name
├── job_title, seniority_rank
├── generated_email, email_confidence
├── slot_type, slot_assigned_at
└── created_at, updated_at
        │
        ├──► outreach.slot_assignments
        ├──► outreach.email_verification
        └──► people.movement_history
```

---

## Cost Rules

| Tool | Tier | Cost | Limit |
|------|------|------|-------|
| Apollo | 1 | Low | Budget-gated |
| Clay | 2 | Premium | **ONE per context** |
| MillionVerifier | 1 | ~$37/10k | Per-use |

---

## Boundary Rules

> **Slot Split Doctrine**: Company Hub defines WHAT roles needed. People Hub defines WHO fills them.

### Cannot Do
- Create company_unique_id (CL ONLY)
- Modify slot_requirements (Company Target)
- Write to company_target (Company Target)
- Consume Blog Content signals (downstream)
- Fix Company Target errors (FAIL, not retry)

### Can Do
- Receive company_unique_id from Company Target
- Create people records
- Assign slots based on title
- Generate emails using verified pattern
- Track movement history

---

## Core Metric

**SLOT_FILL_RATE** — Percentage of target slots filled with verified contacts

| Threshold | Status |
|-----------|--------|
| >= 80% | Healthy |
| >= 60% | Degraded |
| < 60% | Critical |

---

## Error Codes

| Code | Trigger | Resolver |
|------|---------|----------|
| `PI_NO_PATTERN` | Missing verified pattern | Company Target |
| `PI_SLOT_CONFLICT` | Multiple people for slot | Seniority wins |
| `PI_EMAIL_INVALID` | Verification failed | Human |
| `PI_MISSING_COMPANY` | No company_unique_id | Gate block |

---

## Lifecycle Gate

| Condition | Value |
|-----------|-------|
| Minimum State | TARGETABLE |
| Required | verified_pattern from Company Target |
| Required | outreach_context_id |

---

## Key Files

| File | Purpose |
|------|---------|
| `hubs/people-intelligence/hub.manifest.yaml` | Hub configuration |
| `hubs/people-intelligence/PRD.md` | Product requirements |
| `hubs/people-intelligence/ADR.md` | Architecture decisions |
| `hubs/people-intelligence/CHECKLIST.md` | Compliance checklist |
| `imo/middle/people_hub.py` | Main orchestrator |
| `imo/middle/phases/phase5_email_generation.py` | Email generation |
| `imo/middle/phases/phase6_slot_assignment.py` | Slot assignment |
| `imo/middle/phases/phase7_enrichment_queue.py` | Enrichment queue |
| `imo/middle/phases/phase8_output_writer.py` | CSV output |
| `imo/middle/email/bulk_verifier.py` | MillionVerifier integration |

---

## Related Documents

- [[Company-Target-Subhub]]
- [[DOL-EIN-Fuzzy-Discovery]]
- [[ADR-001_Hub_Spoke_Architecture]]
- [[PLE-Doctrine]]

---

## Tags

#people-intelligence #sub-hub #04-04-02 #slot-assignment #email-generation #architecture
