# PRD — Blog Content Sub-Hub

## 1. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** Blog Content
- **Owner:** Outreach Team
- **Version:** 1.0.0

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-BLOG-001 |
| **Doctrine ID** | 04.04.05 |
| **Process ID** | Set at runtime |

---

## 3. Purpose

Provide **timing signals** from news, funding events, and content sources.
BIT modulation only — cannot mint, revive, or trigger enrichment.

---

## 4. Lifecycle Gate

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| ACTIVE | Requires lifecycle >= ACTIVE |

---

## 5. Signals Emitted

| Signal | BIT Impact | Description |
|--------|-----------|-------------|
| FUNDING_EVENT | +15.0 | Company received funding |
| ACQUISITION | +12.0 | Company acquired or acquiring |
| LEADERSHIP_CHANGE | +8.0 | Executive change detected |
| EXPANSION | +7.0 | Office/market expansion |
| PRODUCT_LAUNCH | +5.0 | New product announced |
| PARTNERSHIP | +5.0 | Partnership announced |
| LAYOFF | -3.0 | Layoffs announced |
| NEGATIVE_NEWS | -5.0 | Negative press coverage |

---

## 6. Constraints

- [ ] Cannot mint or revive companies
- [ ] Cannot trigger enrichment
- [ ] BIT modulation only
- [ ] Requires company_sov_id (must already exist)
- [ ] Lifecycle read-only

---

## 7. Inputs

| Input | Source | Required |
|-------|--------|----------|
| company_sov_id | Company Lifecycle (external) | YES |
| news_feeds | External feeds | NO |
| funding_alerts | Crunchbase, etc. | NO |
| content_webhooks | Custom integrations | NO |

---

## 8. Tools

No paid enrichment tools. Signal processing only.

---

## 9. Core Metric

**SIGNAL_COVERAGE** — Percentage of active companies with recent signals

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
