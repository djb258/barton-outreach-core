# Sovereign Completion Overview

## Conformance

| Field | Value |
|-------|-------|
| **Doctrine Version** | CL Parent-Child Doctrine v1.1 |
| **CC Layer** | CC-02 (Hub) |

---

## Hub Identity

| Field | Value |
|-------|-------|
| **Sovereign ID** | barton-enterprises |
| **Hub Name** | Sovereign Completion |
| **Hub ID** | 04.04.02.04.SC |

---

## Purpose

The Sovereign Completion system is the **single source of truth** for determining whether a company is eligible for marketing outreach and at what intensity level.

It answers the question: **"Is this company ready for marketing, and how aggressively can we reach out?"**

---

## Key Concepts

### Marketing Tiers

| Tier | Name | Requirement | Outreach Level |
|------|------|-------------|----------------|
| -1 | INELIGIBLE | Any hub FAIL/BLOCKED or override active | No outreach |
| 0 | Cold | Company Target PASS | Basic cold outreach only |
| 1 | Persona | People Intelligence PASS | Persona-targeted outreach |
| 2 | Trigger | Talent Flow PASS | Event-triggered outreach |
| 3 | Aggressive | ALL hubs PASS + BIT >= 50 | Full campaign engagement |

### Required Hubs

1. **Company Target** (order: 1) - Domain, email pattern
2. **DOL Filings** (order: 2) - EIN, filing signals
3. **People Intelligence** (order: 3) - Slot assignments, contacts
4. **Talent Flow** (order: 4) - Movement signals

### Hub Statuses

- **PASS** - Hub requirements fully met
- **IN_PROGRESS** - Processing not yet complete
- **FAIL** - Hub validation failed
- **BLOCKED** - Blocked by upstream dependency

---

## Architecture

```
Hub Registry (6 hubs)
        │
        ▼
Company Hub Status (company × hub)
        │
        ▼
vw_sovereign_completion (aggregates hub status)
        │
        ▼
vw_marketing_eligibility (computes tier)
        │
        ▼
vw_marketing_eligibility_with_overrides (applies kill switches)
        │
        ▼
AUTHORITATIVE TIER FOR MARKETING DECISIONS
```

---

## Key Views

### vw_sovereign_completion

**Purpose:** Aggregates hub statuses per company

**Key Columns:**
- `company_unique_id`
- `company_target_status`, `dol_status`, `people_status`, `talent_flow_status`
- `overall_status` (COMPLETE, IN_PROGRESS, BLOCKED)
- `missing_requirements` (JSONB)

### vw_marketing_eligibility

**Purpose:** Computes marketing tier from hub completion

**Key Columns:**
- `marketing_tier` (-1, 0, 1, 2, 3)
- `tier_explanation`
- `next_tier_requirement`

### vw_marketing_eligibility_with_overrides

**Purpose:** AUTHORITATIVE view with kill switches applied

**Key Columns:**
- `computed_tier` (from vw_marketing_eligibility)
- `effective_tier` (after overrides)
- `has_active_override`
- `override_types`, `override_reasons`

---

## Usage

### Check company eligibility

```sql
SELECT company_unique_id, effective_tier, effective_tier_explanation
FROM outreach.vw_marketing_eligibility_with_overrides
WHERE company_unique_id = 'your-company-id';
```

### Get tier distribution

```sql
SELECT effective_tier, COUNT(*) as company_count
FROM outreach.vw_marketing_eligibility_with_overrides
GROUP BY effective_tier
ORDER BY effective_tier;
```

### Find companies ready for Tier 2+ outreach

```sql
SELECT company_unique_id, effective_tier
FROM outreach.vw_marketing_eligibility_with_overrides
WHERE effective_tier >= 2
AND has_active_override = FALSE;
```

---

## Related Documentation

- [[Kill Switch System]]
- [[Marketing Tier Doctrine]]
- [[Hub Registry]]
- [[ADR-006_Sovereign_Completion_Infrastructure]]

---

## Tags

#hub/sovereign-completion #cc/cc-02 #status/active #type/overview
