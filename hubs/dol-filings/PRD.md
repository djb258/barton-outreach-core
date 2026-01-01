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

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
