# Outreach Sub-Hub DONE State Definitions

**Version**: 1.0
**Effective Date**: 2026-02-02
**Source**: ERD-based verification against Neon PostgreSQL
**Status**: PRODUCTION REFERENCE

---

## Purpose

This document defines the exact criteria for determining when each Outreach sub-hub has completed its work for a given company. These definitions are derived from actual schema inspection and data analysis of the Neon PostgreSQL database.

---

## Core Principle

**DONE = Required fields populated AND execution status indicates success**

Each sub-hub has specific fields that MUST be non-null and specific status values that indicate successful completion. These criteria align with the waterfall doctrine: a sub-hub is DONE when it has passed all gates and is ready to hand off to the next hub.

---

## Sub-Hub Definitions

### 1. Company Target (04.04.01) - ANCHOR HUB

**Table**: `outreach.company_target`

**DONE Criteria**:
```sql
execution_status = 'ready'
AND email_method IS NOT NULL
AND confidence_score IS NOT NULL
AND imo_completed_at IS NOT NULL
```

**Explanation**:
- `execution_status = 'ready'` → Email pattern discovery completed successfully
- `email_method IS NOT NULL` → Discovered pattern (e.g., `{first}.{last}@domain.com`)
- `confidence_score IS NOT NULL` → Confidence in discovered pattern (0.0 to 1.0)
- `imo_completed_at IS NOT NULL` → IMO waterfall timestamp recorded

**Current State**: 37,878 / 41,425 records (91.4%) are DONE

**Failure States**:
- `execution_status = 'pending'` → Still processing (2,692 records)
- `execution_status = 'failed'` → Pattern discovery failed (855 records)
- Check `outreach.company_target_errors` for failure details (4,404 error records)

**Verification Query**:
```sql
SELECT outreach_id
FROM outreach.company_target
WHERE execution_status = 'ready'
  AND email_method IS NOT NULL
  AND confidence_score IS NOT NULL
  AND imo_completed_at IS NOT NULL;
```

---

### 2. People Intelligence (04.04.02)

**Tables**: `people.company_slot`, `outreach.people`

#### Option A: Slot-Level DONE (Company-Level)

**DONE Criteria**:
```sql
-- At least N critical slots filled (e.g., CEO, CFO, HR)
SELECT outreach_id
FROM people.company_slot
WHERE is_filled = TRUE
GROUP BY outreach_id
HAVING COUNT(*) >= 3;  -- Adjust threshold as needed
```

**Explanation**:
- `is_filled = TRUE` → Slot has assigned person
- `COUNT(*) >= 3` → Minimum number of filled slots (customize per business rules)

**Current State**: 27,303 slots filled / 126,576 total slots (21.6%)

#### Option B: Person-Level DONE (Contact-Level)

**DONE Criteria**:
```sql
email_verified = TRUE
AND contact_status NOT IN ('bounced', 'unsubscribed')
```

**Explanation**:
- `email_verified = TRUE` → Email address verified via sub-wheel
- `contact_status` → Active contact status (not bounced/unsubscribed)

**Current State**: 324 people records / 42,192 companies (0.8% coverage)

**Recommended Approach**: Use **Slot-Level DONE** for determining if a company has sufficient people intelligence. Use **Person-Level DONE** for campaign send eligibility.

---

### 3. DOL Filings (04.04.03)

**Table**: `outreach.dol`

**DONE Criteria**:
```sql
ein IS NOT NULL
AND filing_present = TRUE
```

**Explanation**:
- `ein IS NOT NULL` → EIN successfully resolved
- `filing_present = TRUE` → Form 5500 filing found in dol.form_5500

**Optional Enrichment** (not required for DONE):
- `funding_type` → Plan funding type (self-funded, fully-insured, etc.)
- `broker_or_advisor` → Broker/advisor name
- `carrier` → Insurance carrier name

**Current State**: 11,685 / 42,192 records (27.7%) are DONE

**Coverage**: 16,860 / 42,192 (40.0%) have DOL records, but only 69.3% of those have verified filings

**Verification Query**:
```sql
SELECT outreach_id, ein, filing_present, funding_type
FROM outreach.dol
WHERE ein IS NOT NULL
  AND filing_present = TRUE;
```

---

### 4. Blog Content (04.04.05)

**Table**: `outreach.blog`

**DONE Criteria**:
```sql
outreach_id IS NOT NULL
```

**Explanation**:
- `outreach_id IS NOT NULL` → Record exists (FK constraint enforces this)

**Optional Fields** (not required for DONE):
- `context_summary` → Content summary
- `source_type` → Content source (blog, news, press release, etc.)
- `source_url` → Source URL
- `context_timestamp` → Content publication date

**Current State**: 41,425 / 42,192 records (98.2%) are DONE

**Note**: Blog content appears to be auto-generated or default-populated for nearly all companies. This sub-hub has the highest completion rate.

**Verification Query**:
```sql
SELECT outreach_id, context_summary, source_type, created_at
FROM outreach.blog;
```

---

### 5. BIT Scores (Composite)

**Table**: `outreach.bit_scores`

**DONE Criteria**:
```sql
score IS NOT NULL
AND signal_count > 0
```

**Explanation**:
- `score IS NOT NULL` → Composite BIT score calculated
- `signal_count > 0` → At least one signal from sub-hubs

**Score Components** (all NOT NULL when DONE):
- `people_score` → Contribution from People Intelligence
- `dol_score` → Contribution from DOL Filings
- `blog_score` → Contribution from Blog Content
- `talent_flow_score` → Contribution from Talent Flow (movement engine)

**Current State**: 13,226 / 42,192 records (31.3%) are DONE

**Note**: BIT Scores require signals from multiple sub-hubs. Low coverage (31.3%) indicates many companies lack sufficient signals for scoring.

**Verification Query**:
```sql
SELECT outreach_id, score, score_tier, signal_count,
       people_score, dol_score, blog_score, talent_flow_score
FROM outreach.bit_scores
WHERE score IS NOT NULL
  AND signal_count > 0;
```

---

## Composite DONE States

### Tier 1: Marketing-Ready

**Definition**: Company has email pattern and high confidence

```sql
SELECT o.outreach_id
FROM outreach.outreach o
JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
WHERE ct.execution_status = 'ready'
  AND ct.email_method IS NOT NULL
  AND ct.confidence_score >= 0.8;  -- High confidence threshold
```

**Current Estimate**: ~34,000 companies (80% of spine)

---

### Tier 2: Enrichment Complete

**Definition**: All sub-hubs have completed their work

```sql
SELECT o.outreach_id
FROM outreach.outreach o
WHERE EXISTS (SELECT 1 FROM outreach.company_target ct WHERE ct.outreach_id = o.outreach_id AND ct.execution_status = 'ready')
  AND EXISTS (SELECT 1 FROM outreach.blog b WHERE b.outreach_id = o.outreach_id)
  AND EXISTS (SELECT 1 FROM outreach.dol d WHERE d.outreach_id = o.outreach_id AND d.filing_present = TRUE)
  AND EXISTS (SELECT 1 FROM outreach.bit_scores bs WHERE bs.outreach_id = o.outreach_id);
```

**Current Estimate**: ~8,000-10,000 companies (20-24% of spine)

---

### Tier 3: Campaign-Ready

**Definition**: People verified and ready for outreach campaigns

```sql
SELECT o.outreach_id
FROM outreach.outreach o
WHERE EXISTS (
  SELECT 1
  FROM people.company_slot cs
  WHERE cs.outreach_id = o.outreach_id
    AND cs.is_filled = TRUE
  GROUP BY cs.outreach_id
  HAVING COUNT(*) >= 3
)
AND EXISTS (
  SELECT 1
  FROM outreach.people p
  WHERE p.outreach_id = o.outreach_id
    AND p.email_verified = TRUE
);
```

**Current Estimate**: Very low (< 1% of spine due to minimal people coverage)

---

## Waterfall Dependencies

### Execution Order (LOCKED)

```
1. Company Target (04.04.01) → ANCHOR (must complete first)
   ↓
2. DOL Filings (04.04.03) → Requires domain from Company Target
   ↓
3. People Intelligence (04.04.02) → Requires email pattern from Company Target
   ↓
4. Blog Content (04.04.05) → Can run in parallel with People/DOL
   ↓
5. BIT Scores (Composite) → Requires signals from People + DOL + Blog
```

**Critical Rule**: Company Target MUST be DONE before any other sub-hub can proceed.

---

## Error Handling

### Company Target Errors

**Error Table**: `outreach.company_target_errors`

**Query Failed Records**:
```sql
SELECT ct.outreach_id, ct.execution_status, cte.*
FROM outreach.company_target ct
JOIN outreach.company_target_errors cte ON ct.outreach_id = cte.outreach_id
WHERE ct.execution_status = 'failed';
```

**Common Failure Scenarios**:
- Domain resolution failed
- No email patterns discovered
- Catchall domain (is_catchall = TRUE)
- Timeout or rate limiting

---

## CL Alignment Rule

**Golden Rule**: `outreach.outreach` count MUST equal `cl.company_identity` (outreach_id IS NOT NULL) count

**Verification**:
```sql
SELECT
  (SELECT COUNT(*) FROM outreach.outreach) AS outreach_spine,
  (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL) AS cl_with_outreach_id,
  CASE
    WHEN (SELECT COUNT(*) FROM outreach.outreach) =
         (SELECT COUNT(*) FROM cl.company_identity WHERE outreach_id IS NOT NULL)
    THEN 'ALIGNED ✓'
    ELSE 'MISALIGNED ✗'
  END AS status;
```

**Current Status**: 42,192 = 42,192 ✓ ALIGNED

---

## Summary Table

| Sub-Hub | DONE Field(s) | DONE Status | Current DONE Count | Coverage |
|---------|---------------|-------------|---------------------|----------|
| **Company Target** | `execution_status='ready'` AND `email_method IS NOT NULL` | Ready to emit | 37,878 | 91.4% |
| **Blog Content** | `outreach_id IS NOT NULL` | Auto-populated | 41,425 | 98.2% |
| **DOL Filings** | `ein IS NOT NULL` AND `filing_present=TRUE` | Verified | 11,685 | 27.7% |
| **BIT Scores** | `score IS NOT NULL` AND `signal_count > 0` | Scored | 13,226 | 31.3% |
| **People (Slots)** | `is_filled=TRUE` (3+ slots) | Assigned | 27,303 slots | 21.6% |
| **People (Contacts)** | `email_verified=TRUE` | Verified | 324 people | 0.8% |

---

## Operational Guidelines

1. **Always check Company Target first** - It's the anchor hub
2. **Use execution_status for workflow state** - Not the outreach.outreach table (no status column)
3. **DOL and People can run in parallel** - Both depend on Company Target
4. **BIT Scores require multiple signals** - Don't expect 100% coverage
5. **Blog Content is mostly auto-populated** - Don't rely on it for signal quality
6. **People coverage is low** - Prioritize slot filling for campaign readiness

---

## Query Reference

See `DONE_STATE_QUERIES.sql` for production-ready SQL queries.

---

**Document Owner**: Barton Outreach Core Team
**Last Verified**: 2026-02-02 against Neon PostgreSQL
**Next Review**: Quarterly (or when schema changes)
