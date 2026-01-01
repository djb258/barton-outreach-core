# PRD — DOL Filings Sub-Hub

## 1. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** DOL Filings
- **Owner:** Outreach Team
- **Version:** 1.0.0

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-DOL-001 |
| **Doctrine ID** | 04.04.03 |
| **Process ID** | Set at runtime |

---

## 3. Purpose

Attach regulatory filings (Form 5500, Schedule A) to **existing companies**.
Source of truth for plan renewal dates and broker relationships.

---

## 4. Lifecycle Gate

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| ACTIVE | Requires lifecycle >= ACTIVE |

---

## 5. Inputs

| Input | Source | Required |
|-------|--------|----------|
| company_sov_id | Company Lifecycle (external) | YES |
| DOL CSV files | Federal DOL data | YES |

---

## 6. Pipeline

```
Load DOL CSV (Form 5500, 5500-SF, Schedule A)
 ↓
Parse and validate records
 ↓
EIN Matching (exact match only, no fuzzy)
 ↓
Match found?
  ├─ YES → Attach filing to company → Emit signals
  └─ NO → STOP (no retries on mismatch)
```

---

## 7. Cost Rules

| Rule | Enforcement |
|------|-------------|
| DOL CSV | Bulk processing, free |
| No paid tools | This hub uses no paid enrichment |
| No retries | Exact EIN match or fail |

---

## 8. Tools

| Tool | Tier | Cost Class |
|------|------|------------|
| DOL CSV | Bulk | Free |

---

## 9. Signals Emitted

| Signal | BIT Impact |
|--------|-----------|
| FORM_5500_FILED | +5.0 |
| LARGE_PLAN | +8.0 |
| BROKER_CHANGE | +7.0 |

---

## 10. Constraints

- [ ] Bulk CSV only
- [ ] Exact EIN match (no fuzzy)
- [ ] No retries on mismatch
- [ ] Emits signals only — no enrichment

---

## 11. Core Metric

**FILING_MATCH_RATE** — Percentage of filings matched to company_master

Healthy Threshold: >= 90%

---

## 12. Upstream Dependencies, Signal Validity, and Downstream Effects

### Execution Position

**Second in canonical order** — After Company Target, before People Intelligence.

### Required Upstream PASS Conditions

| Upstream | Condition |
|----------|-----------|
| Company Target | PASS (company exists with company_sov_id) |
| Company Target | Domain resolved (for cross-reference) |

### Signals Consumed (Origin-Bound)

| Signal | Origin | Validity |
|--------|--------|----------|
| company_sov_id | Company Lifecycle (via CT) | Run-bound to outreach_context_id |
| domain | Company Target | Run-bound to outreach_context_id |

### Signals Emitted

| Signal | Consumers | Validity |
|--------|-----------|----------|
| FORM_5500_FILED | People, Blog | Run-bound to outreach_context_id |
| LARGE_PLAN | People, Blog | Run-bound to outreach_context_id |
| BROKER_CHANGE | People, Blog | Run-bound to outreach_context_id |
| filing_data | Monitoring | Run-bound to outreach_context_id |

### Downstream Effects

| If This Hub | Then |
|-------------|------|
| PASS | People Intelligence may execute |
| FAIL | People, Blog do NOT execute |

### Explicit Prohibitions

- [ ] May NOT consume People Intelligence or Blog signals
- [ ] May NOT unlock People Intelligence alone (CT must also PASS)
- [ ] May NOT fix Company Target errors
- [ ] May NOT refresh signals from prior contexts
- [ ] May NOT retry EIN matches (exact match or FAIL)

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
