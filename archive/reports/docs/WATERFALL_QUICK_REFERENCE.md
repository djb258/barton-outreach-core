# Outreach Waterfall — Quick Reference Card

**Version**: 1.0 | **Updated**: 2026-02-02

---

## The Flow (30-Second Version)

```
Company Name → CL (verify + domain) → Sovereign ID → Outreach ID → CT (pattern) → DOL → Blog → People → CAMPAIGN
```

---

## Who Owns What

| Hub | Owns | Gets From |
|-----|------|-----------|
| **CL** | Domain, LinkedIn, Sovereign ID | Raw input |
| **CT** | Email pattern, BIT score | Domain from CL |
| **DOL** | EIN linkage | Identity from CL |
| **Blog** | Content signals | URLs from CL |
| **People** | Slots, Emails | Pattern from CT |

---

## Key IDs

| ID | Minted By | Meaning |
|----|-----------|---------|
| `sovereign_company_id` | CL | CL is DONE |
| `outreach_id` | Outreach | Tracking key for all sub-hubs |

---

## Decision Tree

```
Is sovereign_company_id NULL?
  YES → CL not done → STOP (CT cannot run)
  NO  → CL done → Continue

Does CT have email_method?
  NO  → CT not done → People cannot run
  YES → CT done → People can run

Did DOL fail?
  YES → PARK it, continue anyway (non-blocking)
```

---

## Error Dispositions

| Disposition | Meaning | Action |
|-------------|---------|--------|
| **RETRY** | Fixable, try again | Pipeline will retry |
| **PARKED** | Structural, cannot fix | Leave alone |
| **ARCHIVED** | Historical | No action |
| **IGNORE** | Accounted for | No action |

---

## Readiness Tiers

| Tier | Ready For |
|------|-----------|
| NOT_READY | Nothing |
| TIER_0 | Basic targeting |
| TIER_2 | Full enrichment |
| TIER_3 | Campaigns |

---

## Three Rules

1. **CL owns domain** — CT never discovers domains
2. **Sovereign ID = CL DONE** — No ID means no downstream
3. **DOL is non-blocking** — Failures don't stop the waterfall

---

## Quick Checks

**Is this company actionable?**
```sql
SELECT * FROM shq.vw_promotion_readiness
WHERE outreach_id = 'xxx' AND readiness_tier != 'NOT_READY';
```

**Why is this company NOT_READY?**
```sql
SELECT * FROM shq.vw_blocking_errors_by_outreach
WHERE outreach_id = 'xxx';
```

**What's the CT state?**
```sql
SELECT execution_status, email_method, confidence_score
FROM outreach.company_target WHERE outreach_id = 'xxx';
```

---

**Full documentation**: `docs/OUTREACH_WATERFALL_DOCTRINE.md`
