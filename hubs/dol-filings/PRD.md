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

## 3.1 Waterfall Position

**Position**: 3rd in canonical waterfall (after CT, before People)

```
1. CL ──────────► PASS ──┐  (EXTERNAL)
                         │ company_unique_id
                         ▼
2. COMPANY TARGET ► PASS ──┐
                           │ verified_pattern, domain
                           ▼
3. DOL FILINGS ───► PASS ──┐  ◄── YOU ARE HERE
                           │ ein, filing_signals
                           ▼
4. PEOPLE ────────► PASS ──┐
                           ▼
5. BLOG ──────────► PASS
```

### Upstream Dependencies

| Upstream | Required Signal | Gate |
|----------|-----------------|------|
| Company Target | company_unique_id | MUST have passed |
| Company Target | domain | MUST be resolved |

### Downstream Consumers

| Downstream | Signals Emitted | Binding |
|------------|-----------------|---------|
| People Intelligence | filing_signals, regulatory_data | outreach_context_id |
| Blog Content | filing_signals | outreach_context_id |

### Waterfall Rules (LOCKED)

- Company Target must PASS before this hub executes
- This hub must PASS before People Intelligence executes
- No retry/rescue from downstream hubs
- Failures stay local — downstream sees FAIL, not partial data

---

## 3.2 External Dependencies & Program Scope

### CL is EXTERNAL to Outreach

| Boundary | System | Ownership |
|----------|--------|-----------|
| **External** | Company Lifecycle (CL) | Mints company_unique_id, shared across all programs |
| **Program** | Outreach Orchestration | Mints outreach_context_id, program-scoped |
| **Sub-Hub** | DOL Filings (this hub) | Second enrichment sub-hub in waterfall |

### Key Doctrine

- **CL is external** — Outreach CONSUMES company_unique_id, does NOT invoke CL
- **No CL gating** — Outreach does NOT verify company existence (CL already did)
- **Run identity** — All operations bound by outreach_context_id from Orchestration
- **Context table** — outreach.outreach_context is the root audit record

### Explicit Prohibitions

- [ ] Does NOT invoke Company Lifecycle (CL is external)
- [ ] Does NOT mint company_unique_id (CL does)
- [ ] Does NOT verify company existence (CL already did)
- [ ] Does NOT create outreach_context_id (Orchestration does)

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

---

**Last Updated**: 2026-01-02
**Hub**: DOL Filings (04.04.03)
**Doctrine**: External CL + Outreach Program v1.0
