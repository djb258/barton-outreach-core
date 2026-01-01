# PRD — Outreach Execution Sub-Hub

## 1. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** Outreach Execution
- **Owner:** Outreach Team
- **Version:** 1.0.0

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-OE-001 |
| **Doctrine ID** | 04.04.04 |
| **Process ID** | Set at runtime |

---

## 3. Purpose

Own campaign state, sequence execution, send logs, and engagement tracking.
Manage outreach state machine: draft → scheduled → sent → opened → replied.

**Golden Rule:** No outreach without company_sov_id, domain, AND email_pattern.

---

## 4. Lifecycle Gate

| Minimum Lifecycle State | Gate Condition |
|-------------------------|----------------|
| TARGETABLE | Requires lifecycle >= TARGETABLE |
| Additional | Requires verified pattern + slotted people |

---

## 5. State Machine

| BIT Score | State | Action |
|-----------|-------|--------|
| 0-24 | SUSPECT | DO_NOT_CONTACT |
| 25-49 | WARM | NEWSLETTER/CONTENT |
| 50-74 | HOT | PERSONALIZED_EMAIL |
| 75+ | BURNING | PHONE_AND_EMAIL |

---

## 6. Entities Owned

| Entity | Purpose |
|--------|---------|
| campaigns | Campaign definitions |
| sequences | Email sequence templates |
| send_log | Email send history |
| engagement_events | Opens, clicks, replies |
| reply_tracking | Response tracking |

---

## 7. Constraints

- [ ] NEVER initiates outreach without company_sov_id
- [ ] NEVER initiates outreach without verified domain
- [ ] NEVER initiates outreach without email_pattern
- [ ] Requires BIT score >= 25 for any outreach
- [ ] Cooling-off period enforced between contacts

---

## 8. Core Metric

**ENGAGEMENT_RATE** = (opens + replies) / sends

Healthy Threshold: >= 30%

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
