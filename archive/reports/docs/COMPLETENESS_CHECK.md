# Completeness Check System

> **Last Updated:** 2026-02-06
> **Status:** CANONICAL
> **Purpose:** Check campaign eligibility and enrichment status for any outreach_id

---

## The Rule

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMPAIGN ELIGIBILITY + ENRICHMENT                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   outreach_id                                                                │
│       │                                                                      │
│       ▼                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │              MINIMUM REQUIREMENT (Campaign Eligible)                 │   │
│   ├─────────────────────────────────────────────────────────────────────┤   │
│   │  ☑ People Intelligence (04.04.02) - ≥1 slot filled with contact    │   │
│   │                                                                      │   │
│   │  → YES = CAN CAMPAIGN (someone to email)                            │   │
│   │  → NO  = AIRTABLE QUEUE (need contact first)                        │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│       │                                                                      │
│       ▼                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │              ENRICHMENT LAYERS (Better Outreach)                     │   │
│   ├─────────────────────────────────────────────────────────────────────┤   │
│   │  □ Company Target (04.04.01) - email pattern for additional slots   │   │
│   │  □ DOL Filings (04.04.03) - plan size, funding type, timing         │   │
│   │  □ Blog Content (04.04.05) - news, hiring signals, context          │   │
│   │  □ BIT Score - prioritization, tier assignment                      │   │
│   │                                                                      │
│   │  More complete = BETTER targeting, timing, personalization          │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   GOAL: Enrich all sub-hubs to 100% for optimal outreach quality            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Completeness Check Query

### Check Single Company

```sql
-- Replace $OUTREACH_ID with the actual UUID
SELECT
    o.outreach_id,
    o.domain,

    -- Company Target (04.04.01)
    CASE WHEN ct.email_method IS NOT NULL AND ct.execution_status = 'ready'
         THEN '✅' ELSE '❌' END AS ct_complete,
    ct.email_method,
    ct.execution_status AS ct_status,

    -- People Intelligence (04.04.02)
    CASE WHEN COALESCE(slots.filled_count, 0) >= 1
         THEN '✅' ELSE '❌' END AS people_complete,
    COALESCE(slots.filled_count, 0) AS slots_filled,

    -- DOL Filings (04.04.03)
    CASE WHEN d.ein IS NOT NULL AND d.filing_present = TRUE
         THEN '✅' ELSE '❌' END AS dol_complete,
    d.ein,
    d.filing_present,

    -- Blog Content (04.04.05)
    CASE WHEN b.blog_id IS NOT NULL
         THEN '✅' ELSE '❌' END AS blog_complete,

    -- BIT Score
    CASE WHEN bs.score IS NOT NULL
         THEN '✅' ELSE '❌' END AS bit_complete,
    bs.score AS bit_score,
    bs.score_tier,

    -- Overall
    CASE
        WHEN ct.email_method IS NOT NULL
         AND ct.execution_status = 'ready'
         AND COALESCE(slots.filled_count, 0) >= 1
         AND d.ein IS NOT NULL
         AND d.filing_present = TRUE
         AND b.blog_id IS NOT NULL
         AND bs.score IS NOT NULL
        THEN '✅ COMPLETE'
        ELSE '❌ INCOMPLETE'
    END AS overall_status

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN (
    SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled) AS filled_count
    FROM people.company_slot
    GROUP BY outreach_id
) slots ON o.outreach_id = slots.outreach_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id
WHERE o.outreach_id = $OUTREACH_ID;
```

### Example Output

```
outreach_id: abc123-def456-...
domain: acme.com

ct_complete:     ✅  email_method: {first}.{last}@acme.com
people_complete: ✅  slots_filled: 2
dol_complete:    ❌  ein: NULL, filing_present: NULL
blog_complete:   ✅
bit_complete:    ❌  bit_score: NULL

overall_status:  ❌ INCOMPLETE
```

This company needs: DOL enrichment (EIN resolution) and BIT scoring.

---

## Bulk Completeness Report

### All Companies with Status

```sql
SELECT
    o.outreach_id,
    o.domain,

    -- Sub-hub flags
    (ct.email_method IS NOT NULL AND ct.execution_status = 'ready') AS ct_done,
    (COALESCE(slots.filled_count, 0) >= 1) AS people_done,
    (d.ein IS NOT NULL AND d.filing_present = TRUE) AS dol_done,
    (b.blog_id IS NOT NULL) AS blog_done,
    (bs.score IS NOT NULL) AS bit_done,

    -- Count of completed sub-hubs
    (CASE WHEN ct.email_method IS NOT NULL AND ct.execution_status = 'ready' THEN 1 ELSE 0 END +
     CASE WHEN COALESCE(slots.filled_count, 0) >= 1 THEN 1 ELSE 0 END +
     CASE WHEN d.ein IS NOT NULL AND d.filing_present = TRUE THEN 1 ELSE 0 END +
     CASE WHEN b.blog_id IS NOT NULL THEN 1 ELSE 0 END +
     CASE WHEN bs.score IS NOT NULL THEN 1 ELSE 0 END) AS subhubs_complete,

    -- Overall complete (all 5 sub-hubs done)
    (ct.email_method IS NOT NULL AND ct.execution_status = 'ready'
     AND COALESCE(slots.filled_count, 0) >= 1
     AND d.ein IS NOT NULL AND d.filing_present = TRUE
     AND b.blog_id IS NOT NULL
     AND bs.score IS NOT NULL) AS fully_complete

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN (
    SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled) AS filled_count
    FROM people.company_slot
    GROUP BY outreach_id
) slots ON o.outreach_id = slots.outreach_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id
ORDER BY subhubs_complete DESC, o.domain;
```

---

## Airtable Queue Logic

### Companies Needing Enrichment

```sql
-- Export to Airtable: Companies NOT fully complete
SELECT
    o.outreach_id,
    o.domain,
    ct.company_name,

    -- What's missing
    CASE WHEN ct.email_method IS NULL OR ct.execution_status != 'ready'
         THEN 'CT' ELSE NULL END AS needs_ct,
    CASE WHEN COALESCE(slots.filled_count, 0) < 1
         THEN 'PEOPLE' ELSE NULL END AS needs_people,
    CASE WHEN d.ein IS NULL OR d.filing_present IS NOT TRUE
         THEN 'DOL' ELSE NULL END AS needs_dol,
    CASE WHEN b.blog_id IS NULL
         THEN 'BLOG' ELSE NULL END AS needs_blog,
    CASE WHEN bs.score IS NULL
         THEN 'BIT' ELSE NULL END AS needs_bit,

    -- Concatenated needs list
    CONCAT_WS(', ',
        CASE WHEN ct.email_method IS NULL OR ct.execution_status != 'ready' THEN 'CT' END,
        CASE WHEN COALESCE(slots.filled_count, 0) < 1 THEN 'PEOPLE' END,
        CASE WHEN d.ein IS NULL OR d.filing_present IS NOT TRUE THEN 'DOL' END,
        CASE WHEN b.blog_id IS NULL THEN 'BLOG' END,
        CASE WHEN bs.score IS NULL THEN 'BIT' END
    ) AS enrichment_needed

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN (
    SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled) AS filled_count
    FROM people.company_slot
    GROUP BY outreach_id
) slots ON o.outreach_id = slots.outreach_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id

-- Filter to incomplete only
WHERE NOT (
    ct.email_method IS NOT NULL
    AND ct.execution_status = 'ready'
    AND COALESCE(slots.filled_count, 0) >= 1
    AND d.ein IS NOT NULL
    AND d.filing_present = TRUE
    AND b.blog_id IS NOT NULL
    AND bs.score IS NOT NULL
);
```

---

## Workflow

### 1. Check Completeness

```
Claude: "Check completeness for outreach_id X"
   │
   └──► Run completeness query
          │
          ├── COMPLETE → "Ready for campaign"
          │
          └── INCOMPLETE → "Needs: [CT, PEOPLE, DOL, ...]"
                              │
                              └──► "Send to Airtable queue"
```

### 2. Airtable Queue Processing

```
Airtable Queue
   │
   ├── CT Needed → Run email pattern discovery
   │
   ├── PEOPLE Needed → Find contacts (Hunter, LinkedIn, etc.)
   │
   ├── DOL Needed → EIN resolution + filing lookup
   │
   ├── BLOG Needed → Content discovery
   │
   └── BIT Needed → Run scoring (after other sub-hubs done)
```

### 3. Return to Pipeline

```
Enrichment Complete in Airtable
   │
   └──► Sync back to Neon
          │
          └──► Re-run completeness check
                  │
                  └── NOW COMPLETE → Campaign Ready
```

---

## View Creation (Optional)

Create a materialized view for fast lookups:

```sql
CREATE MATERIALIZED VIEW outreach.mv_completeness AS
SELECT
    o.outreach_id,
    o.domain,
    (ct.email_method IS NOT NULL AND ct.execution_status = 'ready') AS ct_done,
    (COALESCE(slots.filled_count, 0) >= 1) AS people_done,
    (d.ein IS NOT NULL AND d.filing_present = TRUE) AS dol_done,
    (b.blog_id IS NOT NULL) AS blog_done,
    (bs.score IS NOT NULL) AS bit_done,
    (ct.email_method IS NOT NULL AND ct.execution_status = 'ready'
     AND COALESCE(slots.filled_count, 0) >= 1
     AND d.ein IS NOT NULL AND d.filing_present = TRUE
     AND b.blog_id IS NOT NULL
     AND bs.score IS NOT NULL) AS fully_complete
FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN (
    SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled) AS filled_count
    FROM people.company_slot
    GROUP BY outreach_id
) slots ON o.outreach_id = slots.outreach_id
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.blog b ON o.outreach_id = b.outreach_id
LEFT JOIN outreach.bit_scores bs ON o.outreach_id = bs.outreach_id;

-- Refresh daily
-- REFRESH MATERIALIZED VIEW outreach.mv_completeness;
```

---

---

## Error Table Integration

Each sub-hub has an error table that explains WHY it's incomplete:

### Error Tables

| Sub-Hub | Error Table | Purpose |
|---------|-------------|---------|
| Company Target | `outreach.company_target_errors` | Pattern discovery failures |
| People | `outreach.people_errors` | Contact discovery/verification failures |
| DOL | `outreach.dol_errors` | EIN resolution failures |
| Blog | `outreach.blog_errors` | Content discovery failures |
| BIT | `outreach.bit_errors` | Scoring failures |

### Error Dispositions

| Disposition | Meaning | Action |
|-------------|---------|--------|
| `RETRY` | Temporary failure, try again | Auto-retry in pipeline |
| `PARKED` | Permanent blocker (e.g., NO_MX) | Manual review or skip |
| `ARCHIVED` | Resolved or abandoned | No action |

### Completeness Check with Errors

```sql
SELECT
    o.outreach_id,
    o.domain,

    -- Company Target status + error
    CASE
        WHEN ct.email_method IS NOT NULL AND ct.execution_status = 'ready' THEN '✅ DONE'
        WHEN cte.error_id IS NOT NULL THEN '❌ ERROR: ' || cte.error_code
        ELSE '❌ PENDING'
    END AS ct_status,

    -- People status + error
    CASE
        WHEN COALESCE(slots.filled_count, 0) >= 1 THEN '✅ DONE'
        WHEN pe.error_id IS NOT NULL THEN '❌ ERROR: ' || pe.error_code
        ELSE '❌ PENDING'
    END AS people_status,

    -- DOL status + error
    CASE
        WHEN d.ein IS NOT NULL AND d.filing_present = TRUE THEN '✅ DONE'
        WHEN de.error_id IS NOT NULL THEN '❌ ERROR: ' || de.error_code
        ELSE '❌ PENDING'
    END AS dol_status

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.company_target_errors cte ON o.outreach_id = cte.outreach_id
    AND cte.disposition != 'ARCHIVED'
LEFT JOIN (
    SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled) AS filled_count
    FROM people.company_slot
    GROUP BY outreach_id
) slots ON o.outreach_id = slots.outreach_id
LEFT JOIN outreach.people_errors pe ON o.outreach_id = pe.outreach_id
    AND pe.disposition != 'ARCHIVED'
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.dol_errors de ON o.outreach_id = de.outreach_id
    AND de.disposition != 'ARCHIVED'
WHERE o.outreach_id = $OUTREACH_ID;
```

### Example Output with Errors

```
outreach_id: abc123-def456-...
domain: parked-domain.com

ct_status:     ❌ ERROR: NO_MX (domain has no mail server)
people_status: ❌ PENDING (no contacts found yet)
dol_status:    ❌ ERROR: EIN_NOT_FOUND (no matching EIN)

→ Send to Airtable with: CT:NO_MX, PEOPLE:PENDING, DOL:EIN_NOT_FOUND
```

### Airtable Queue with Error Context

```sql
-- Export incomplete companies WITH error reasons
SELECT
    o.outreach_id,
    o.domain,
    ct.company_name,

    -- CT enrichment needed + error reason
    CASE
        WHEN ct.email_method IS NOT NULL AND ct.execution_status = 'ready' THEN NULL
        WHEN cte.error_code IS NOT NULL THEN 'CT:' || cte.error_code
        ELSE 'CT:PENDING'
    END AS ct_action,

    -- People enrichment needed + error reason
    CASE
        WHEN COALESCE(slots.filled_count, 0) >= 1 THEN NULL
        WHEN pe.error_code IS NOT NULL THEN 'PEOPLE:' || pe.error_code
        ELSE 'PEOPLE:PENDING'
    END AS people_action,

    -- DOL enrichment needed + error reason
    CASE
        WHEN d.ein IS NOT NULL AND d.filing_present = TRUE THEN NULL
        WHEN de.error_code IS NOT NULL THEN 'DOL:' || de.error_code
        ELSE 'DOL:PENDING'
    END AS dol_action

FROM outreach.outreach o
LEFT JOIN outreach.company_target ct ON o.outreach_id = ct.outreach_id
LEFT JOIN outreach.company_target_errors cte ON o.outreach_id = cte.outreach_id
    AND cte.disposition = 'PARKED'
LEFT JOIN (
    SELECT outreach_id, COUNT(*) FILTER (WHERE is_filled) AS filled_count
    FROM people.company_slot
    GROUP BY outreach_id
) slots ON o.outreach_id = slots.outreach_id
LEFT JOIN outreach.people_errors pe ON o.outreach_id = pe.outreach_id
    AND pe.disposition != 'ARCHIVED'
LEFT JOIN outreach.dol d ON o.outreach_id = d.outreach_id
LEFT JOIN outreach.dol_errors de ON o.outreach_id = de.outreach_id
    AND de.disposition = 'PARKED'

-- Only incomplete
WHERE NOT (
    ct.email_method IS NOT NULL AND ct.execution_status = 'ready'
    AND COALESCE(slots.filled_count, 0) >= 1
    AND d.ein IS NOT NULL AND d.filing_present = TRUE
);
```

---

## Change Log

| Date | Change |
|------|--------|
| 2026-02-06 | Created completeness check system |
| 2026-02-06 | Added error table integration |
