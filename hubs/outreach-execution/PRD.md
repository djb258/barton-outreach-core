# PRD — Outreach Execution Sub-Hub

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | 1.1.0 |
| **CTB Version** | 1.0.0 |
| **CC Layer** | CC-03 (Context within CC-02 Hub) |

---

## 1. Sovereign Reference (CC-01)

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Sovereign Boundary** | Marketing intelligence and executive enrichment operations |

---

## 2. Hub Identity (CC-02)

| Field | Value |
|-------|-------|
| **Parent Hub** | outreach-core |
| **Parent Hub ID** | outreach-core-001 |
| **Hub Name** | Outreach Execution |
| **Hub ID** | HUB-OE-001 |
| **Doctrine ID** | 04.04.04 |
| **Owner** | Outreach Team |
| **Version** | 1.0.0 |

---

## 3. Process Identity (CC-04)

| Field | Value |
|-------|-------|
| **PID Pattern** | `HUB-OE-001-${TIMESTAMP}-${RANDOM_HEX}` |
| **Session Pattern** | `HUB-OE-001-session-${SESSION_ID}` |
| **Context Binding** | outreach_context_id |

---

## 4. Purpose

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
