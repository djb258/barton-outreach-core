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

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
