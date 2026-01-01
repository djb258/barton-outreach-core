# PRD — Company Target Sub-Hub

## 1. Overview

- **System Name:** Barton Outreach Core
- **Hub Name:** Company Target
- **Owner:** Outreach Team
- **Version:** 1.0.0

---

## 2. Hub Identity

| Field | Value |
|-------|-------|
| **Hub ID** | HUB-CT-001 |
| **Doctrine ID** | 04.04.01 |
| **Process ID** | Set at runtime |

---

## 3. Purpose

Determine **outreach readiness** for lifecycle-qualified companies.
Internal anchor table that links all other sub-hubs together.
Receives `company_sov_id` from Company Lifecycle parent — does NOT mint companies.

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
| lifecycle_state | Company Lifecycle (external) | YES |
| outreach_context_id | contexts/outreach_context | YES |

---

## 6. Pipeline

```
Validate lifecycle permission (>= ACTIVE)
 ↓
Phase 1: Company Matching
 ↓
Phase 2: Domain Resolution (DNS/MX check)
 ↓
Phase 3: Email Pattern Waterfall
    ├─ Tier 0 (Free): Firecrawl, Google Places
    ├─ Tier 1 (Low): Hunter, Clearbit, Apollo
    └─ Tier 2 (Premium): Prospeo, Snov, Clay [MAX 1 per context]
 ↓
Pattern found?
  ├─ YES → Phase 4: Pattern Verification → Emit signals
  └─ NO → Check BIT threshold
           ├─ BIT < 25 → STOP
           └─ BIT >= 25 → Queue for next context
```

---

## 7. Cost Rules

| Rule | Enforcement |
|------|-------------|
| Tier-0 tools | Unlimited (free) |
| Tier-1 tools | Gated by lifecycle >= ACTIVE |
| Tier-2 tools | Max ONE attempt per outreach_context |
| All spend | Logged against context + company_sov_id |
| Firewall | Must block illegal calls |

---

## 8. Tools

| Tool | Tier | Cost Class | ADR |
|------|------|------------|-----|
| Firecrawl | 0 | Free | N/A |
| Google Places | 0 | Low | N/A |
| Hunter.io | 1 | Low | ADR-CT-001 |
| Clearbit | 1 | Low | ADR-CT-001 |
| Apollo | 1 | Low | ADR-CT-001 |
| Prospeo | 2 | Premium | ADR-CT-002 |
| Snov | 2 | Premium | ADR-CT-002 |
| Clay | 2 | Premium | ADR-CT-002 |
| SMTP Check | Local | Free | N/A |

---

## 9. Outputs

| Output | Destination |
|--------|-------------|
| company_target record | outreach.company_target table |
| email_pattern | Stored with confidence score |
| BIT signals | Emitted to BIT Engine |

---

## 10. Constraints

- [ ] Does NOT mint companies (company_sov_id comes from CL)
- [ ] Does NOT mutate lifecycle state
- [ ] Requires outreach_context_id for all operations
- [ ] Tier-2 tools limited to one attempt per context
- [ ] All spend logged to spend_log

---

## 11. Core Metric

**BIT_SCORE** — Buyer Intent Tool weighted average

---

## 12. Upstream Dependencies, Signal Validity, and Downstream Effects

### Execution Position

**First in canonical order** — No upstream sub-hub dependencies.

### Required Upstream PASS Conditions

| Upstream | Condition |
|----------|-----------|
| Company Lifecycle (CL) | company_sov_id exists and is valid |
| Company Lifecycle (CL) | lifecycle_state >= ACTIVE |

### Signals Consumed (Origin-Bound)

| Signal | Origin | Validity |
|--------|--------|----------|
| company_sov_id | Company Lifecycle | Run-bound to outreach_context_id |
| lifecycle_state | Company Lifecycle | Run-bound to outreach_context_id |

### Signals Emitted

| Signal | Consumers | Validity |
|--------|-----------|----------|
| domain | DOL, People, Blog | Run-bound to outreach_context_id |
| email_pattern | People Intelligence | Run-bound to outreach_context_id |
| pattern_confidence | People Intelligence | Run-bound to outreach_context_id |
| BIT_SCORE | All downstream | Run-bound to outreach_context_id |

### Downstream Effects

| If This Hub | Then |
|-------------|------|
| PASS | DOL Filings may execute |
| FAIL | DOL, People, Blog do NOT execute |

### Explicit Prohibitions

- [ ] May NOT consume signals from DOL, People, or Blog
- [ ] May NOT repair downstream failures
- [ ] May NOT re-query CL for "fresher" data within same context
- [ ] May NOT refresh signals from prior contexts

---

## Approval

| Role | Name | Date |
|------|------|------|
| Owner | | |
| Reviewer | | |
