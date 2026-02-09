# Sub-Hub Completeness Matrix

> **Last Updated:** 2026-02-06
> **Status:** CANONICAL - Tracks enrichment progress toward 100%
> **Sovereign Baseline:** 95,004 companies

---

## The Goal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMPAIGN ELIGIBILITY + ENRICHMENT GOAL                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Sovereign ID (95,004)  ═══════════════════════════════════════════════════ │
│       ║                                                                      │
│       ╠═══ Outreach ID (95,004) ✓ 100% ALIGNED                              │
│       ║                                                                      │
│       ║   ┌─────────────────────────────────────────────────────────────┐   │
│       ║   │ MINIMUM REQUIREMENT (Campaign Eligible)                      │   │
│       ╠═══│ People Intelligence (04.04.02) ─► ≥1 slot filled            │   │
│       ║   │ → With contact = CAN CAMPAIGN                               │   │
│       ║   │ → No contact = AIRTABLE QUEUE                               │   │
│       ║   └─────────────────────────────────────────────────────────────┘   │
│       ║                                                                      │
│       ║   ┌─────────────────────────────────────────────────────────────┐   │
│       ║   │ ENRICHMENT LAYERS (Better Outreach)                          │   │
│       ╠═══│ Company Target (04.04.01) ──► Email pattern for more slots  │   │
│       ╠═══│ DOL Filings (04.04.03) ─────► Plan size, funding, timing    │   │
│       ╠═══│ Blog Content (04.04.05) ────► News, signals, context        │   │
│       ╚═══│ BIT Scores ─────────────────► Prioritization, tier          │   │
│           └─────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  GOAL: 100% enriched = OPTIMAL outreach (better targeting, timing, copy)    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Current State

### Alignment Layer

| Metric | Count | % of Total | Status |
|--------|-------|------------|--------|
| **Sovereign Eligible** | 95,004 | 100% | ✅ Baseline |
| **Outreach Claimed** | 95,004 | 100% | ✅ ALIGNED |

### Sub-Hub Completeness

| Sub-Hub | DONE Count | % Complete | Gap | Priority |
|---------|------------|------------|-----|----------|
| **Company Target** (04.04.01) | 82,074 | 86.4% | 12,930 | P1 |
| **Blog Content** (04.04.05) | 95,004 | 100% | 0 | ✅ DONE |
| **DOL Filings** (04.04.03) | 70,150 | 73.8% | 24,854 | P2 |
| **People Intelligence** (04.04.02) | 59,153 | 62.2% | 35,851 | P1 |
| **BIT Scores** | 13,226 | 13.9% | 81,778 | P3 |

---

## Sub-Hub DONE Definitions

### Company Target (04.04.01)

**DONE when:**
- `email_method IS NOT NULL` (pattern discovered)
- `execution_status = 'ready'`

**Current:** 82,074 / 95,004 (86.4%)

**Gap Analysis:**
| Status | Count | Action Needed |
|--------|-------|---------------|
| Ready with email_method | 82,074 | ✅ DONE |
| Pending | 2,692 | Run pattern discovery |
| Failed (NO_MX) | 4,378 | Domain has no MX - PARKED |
| Failed (other) | 855 | Investigate/retry |
| Missing record | 5,005 | Create CT record |

**Enrichments Needed:**
1. Run email pattern discovery on 2,692 pending
2. Create company_target records for 5,005 missing
3. Review 855 other failures

---

### People Intelligence (04.04.02)

**DONE when:**
- At least 1 slot filled with verified contact
- `people.company_slot.is_filled = TRUE`

**Current:** 59,153 / 95,004 companies with ≥1 filled slot (62.2%)

**Slot-Level Breakdown:**

| Slot | Filled | Empty | Fill Rate |
|------|--------|-------|-----------|
| CEO | 62,006 | 32,998 | 65.3% |
| CFO | 57,164 | 37,840 | 60.2% |
| HR | 57,991 | 37,013 | 61.0% |
| **TOTAL** | 177,161 | 107,851 | 62.2% |

**Gap Analysis:**
| Gap Type | Count | Action Needed |
|----------|-------|---------------|
| Companies with 0 slots filled | 35,851 | Hunter enrichment |
| CEO slots empty | 32,998 | Find CEO contacts |
| CFO slots empty | 37,840 | Find CFO contacts |
| HR slots empty | 37,013 | Find HR contacts |

**Available Enrichment Data:**
| Source | CEO | CFO | HR | Total |
|--------|-----|-----|-----|-------|
| Hunter (in outreach.people) | 35,232 | 5,328 | 4,651 | 45,211 |
| Hunter (enrichment schema) | 11,389 | 5,391 | 6,595 | 23,375 |

**Enrichments Needed:**
1. Link Hunter contacts to slots via domain matching
2. Run slot assignment for unmatched companies
3. Email verification for filled slots

---

### DOL Filings (04.04.03)

**DONE when:**
- `ein IS NOT NULL`
- `filing_present = TRUE`

**Current:** 70,150 / 95,004 (73.8%)

**Gap Analysis:**
| Status | Count | Action Needed |
|--------|-------|---------------|
| EIN resolved + filing found | 70,150 | ✅ DONE |
| EIN resolved, no filing | 7,188 | Expected (no DOL filing) |
| No EIN match | 17,666 | EIN discovery needed |

**Enrichments Needed:**
1. EIN discovery for 17,666 companies
2. Cross-reference with dol.ein_urls (58,069 Hunter EINs)
3. Match remaining via company name fuzzy matching

---

### Blog Content (04.04.05)

**DONE when:**
- `outreach.blog` record exists

**Current:** 95,004 / 95,004 (100%) ✅

**Note:** Blog records are auto-populated. Quality enrichment (actual content) is tracked separately.

**Content Quality:**
| Metric | Count | % |
|--------|-------|---|
| Has context_summary | TBD | TBD |
| Has source_url | TBD | TBD |
| Has recent news | TBD | TBD |

---

### BIT Scores

**DONE when:**
- `score IS NOT NULL`
- `signal_count > 0`

**Current:** 13,226 / 95,004 (13.9%)

**Gap Analysis:**
| Status | Count | Action Needed |
|--------|-------|---------------|
| Scored | 13,226 | ✅ DONE |
| Missing signals | 81,778 | Sub-hub enrichment first |

**Dependencies:**
BIT scoring requires signals from other sub-hubs:
- People signals (slot filled, contact verified)
- DOL signals (filing found, plan size)
- Blog signals (news events, hiring signals)

**Enrichments Needed:**
1. Complete People and DOL sub-hubs first
2. Run BIT scoring on newly enriched companies
3. Refresh stale scores (>30 days old)

---

## Enrichment Priority Matrix

### P1 - Critical Path (Blocks Campaigns)

| Sub-Hub | Gap | Enrichment Action | Data Source |
|---------|-----|-------------------|-------------|
| Company Target | 12,930 | Email pattern discovery | Hunter API |
| People | 35,851 | Slot assignment | Hunter contacts |

### P2 - High Value (Improves Targeting)

| Sub-Hub | Gap | Enrichment Action | Data Source |
|---------|-----|-------------------|-------------|
| DOL | 24,854 | EIN resolution | dol.ein_urls |
| People | 107,851 slots | Additional contact discovery | Hunter API |

### P3 - Scoring (Enables Prioritization)

| Sub-Hub | Gap | Enrichment Action | Data Source |
|---------|-----|-------------------|-------------|
| BIT | 81,778 | Signal aggregation | Sub-hub outputs |

---

## Enrichment Roadmap

### Phase 1: Company Target Completion (Target: 95%)

```
Current: 86.4% → Target: 95%
Gap: 8,161 companies

Actions:
1. Run pattern discovery on 2,692 pending
2. Create CT records for 5,005 missing
3. Review 855 failures
4. PARK remaining NO_MX domains

Expected Result: 90,253 / 95,004 (95%)
```

### Phase 2: People Slot Filling (Target: 80%)

```
Current: 62.2% → Target: 80%
Gap: 16,902 additional companies need slots

Actions:
1. Link Hunter contacts via domain matching
2. Assign CEO slots first (highest value)
3. Assign CFO/HR slots
4. Flag companies for additional enrichment

Expected Result: 76,003 / 95,004 (80%)
```

### Phase 3: DOL Completion (Target: 85%)

```
Current: 73.8% → Target: 85%
Gap: 10,651 companies need EIN

Actions:
1. Match against dol.ein_urls (58K EINs)
2. Fuzzy match company names
3. PARK non-commercial (no DOL expected)

Expected Result: 80,753 / 95,004 (85%)
```

### Phase 4: BIT Scoring (Target: 75%)

```
Current: 13.9% → Target: 75%
Gap: 58,027 companies need scoring

Actions:
1. Run BIT engine on all with ≥1 signal
2. Score based on available sub-hub data
3. Tier assignment

Expected Result: 71,253 / 95,004 (75%)
```

---

## Tracking Queries

### Overall Completeness

```sql
SELECT
    95004 AS sovereign_eligible,
    (SELECT COUNT(*) FROM outreach.company_target WHERE email_method IS NOT NULL) AS ct_done,
    (SELECT COUNT(DISTINCT outreach_id) FROM people.company_slot WHERE is_filled = TRUE) AS people_done,
    (SELECT COUNT(*) FROM outreach.dol WHERE ein IS NOT NULL AND filing_present = TRUE) AS dol_done,
    (SELECT COUNT(*) FROM outreach.blog) AS blog_done,
    (SELECT COUNT(*) FROM outreach.bit_scores WHERE score IS NOT NULL) AS bit_done;
```

### Companies Missing from Each Sub-Hub

```sql
-- Companies not DONE in Company Target
SELECT ct.outreach_id, ct.domain
FROM outreach.company_target ct
WHERE ct.email_method IS NULL
   OR ct.execution_status != 'ready';

-- Companies with no filled slots
SELECT DISTINCT cs.outreach_id
FROM people.company_slot cs
GROUP BY cs.outreach_id
HAVING SUM(CASE WHEN is_filled THEN 1 ELSE 0 END) = 0;

-- Companies not DONE in DOL
SELECT o.outreach_id, o.domain
FROM outreach.outreach o
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
WHERE d.dol_id IS NULL
   OR d.ein IS NULL
   OR d.filing_present = FALSE;
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-06 | Created document with current state analysis |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `DONE_STATE_DEFINITIONS.md` | Detailed DONE criteria per sub-hub |
| `AUTHORITATIVE_TABLE_REFERENCE.md` | Table relationships |
| `CTB_GOVERNANCE.md` | CTB structure and rules |
