# Phase 2: Outreach Readiness Evaluator

**Status:** ✅ Production Ready
**Date:** 2025-11-17
**Doctrine ID:** 04.04.02.04.10000.003
**Blueprint:** 04.svg.marketing.outreach.v1
**Purpose:** Promote validated companies from "valid" → "outreach_ready"

---

## 📋 Overview

The Outreach Readiness Evaluator is **Phase 2** of the company validation pipeline. It determines whether Phase 1 validated companies are ready for active outreach campaigns by verifying that:

1. All 3 executive slots (CEO, CFO, HR) are **filled**
2. Each person has successful **enrichment data**
3. Each person's email is **verified**
4. Each person's title **matches** their slot type

**Phase Flow:**
```
Phase 1: Validation (structure + slot presence)
    ↓
Phase 2: Outreach Readiness (slot fills + enrichment + verification)
    ↓
Phase 3: Outreach Campaigns (BIT signals + outbound actions)
```

---

## 🎯 Phase 2 Requirements

### Prerequisite: Phase 1 Validation

Company must have:
- `validation_status = 'valid'` (Phase 1 passed)
- All 3 slot records exist (CEO, CFO, HR)

### Phase 2 Checks (Per Slot)

For **each** of the 3 slots (CEO, CFO, HR):

| Check | Requirement | Table/Field | Failure Reason |
|-------|------------|-------------|----------------|
| **1. Slot Filled** | `is_filled = true` AND `person_unique_id != NULL` | `marketing.company_slot` | "CEO slot not filled" |
| **2. Person Exists** | Person record found | `marketing.people_master` | "Person 04...001 not found" |
| **3. Enrichment Success** | `enrichment_status = 'success'` | `marketing.contact_enrichment` | "Person 04...001 missing enrichment data" |
| **4. Email Verified** | `email_status = 'valid'` | `marketing.email_verification` | "Person 04...001 email not verified" |
| **5. Title Match** | Title contains role keywords | `marketing.people_master.title` | "Title 'Manager' does not match CEO" |

**Total Checks:** 5 checks × 3 slots = **15 checks per company**

---

## 🔧 Title Matching Rules

### CEO Slot

Title must contain:
- "CEO" (case-insensitive), OR
- "Chief Executive"

**Valid Examples:**
- "Chief Executive Officer"
- "CEO"
- "President and CEO"
- "Founder & CEO"

**Invalid Examples:**
- "CFO"
- "Manager"
- "President" (without CEO)

### CFO Slot

Title must contain:
- "CFO" (case-insensitive), OR
- "Chief Financial"

**Valid Examples:**
- "Chief Financial Officer"
- "CFO"
- "VP of Finance and CFO"
- "Treasurer & CFO"

**Invalid Examples:**
- "CEO"
- "Finance Manager"
- "VP of Finance" (without CFO)

### HR Slot

Title must contain (any of):
- "HR"
- "Human Resources"
- "People"
- "Talent"

**Valid Examples:**
- "Director of Human Resources"
- "Chief People Officer"
- "VP of Talent Acquisition"
- "HR Manager"
- "Head of People Operations"

**Invalid Examples:**
- "CEO"
- "Operations Manager"
- "Recruiter" (unless includes "Talent" or "HR")

---

## 📊 Return Format

### Success Case

```python
{
    "company_unique_id": "04.04.02.04.30000.001",
    "company_name": "Acme Corporation",
    "outreach_ready": True,
    "reason": "All checks passed",
    "slot_results": [
        {
            "slot_type": "CEO",
            "person_id": "04.04.02.04.20000.001",
            "checks": {
                "is_filled": True,
                "exists_in_people": True,
                "enriched": True,
                "email_verified": True,
                "title_matches": True
            },
            "failures": [],
            "passed": True
        },
        {
            "slot_type": "CFO",
            "person_id": "04.04.02.04.20000.002",
            "checks": {
                "is_filled": True,
                "exists_in_people": True,
                "enriched": True,
                "email_verified": True,
                "title_matches": True
            },
            "failures": [],
            "passed": True
        },
        {
            "slot_type": "HR",
            "person_id": "04.04.02.04.20000.003",
            "checks": {
                "is_filled": True,
                "exists_in_people": True,
                "enriched": True,
                "email_verified": True,
                "title_matches": True
            },
            "failures": [],
            "passed": True
        }
    ],
    "missing_slots": [],
    "total_checks": 15,
    "passed_checks": 15
}
```

### Failure Case (Partial Readiness)

```python
{
    "company_unique_id": "04.04.02.04.30000.005",
    "company_name": "Example LLC",
    "outreach_ready": False,
    "reason": "Person 04.04.02.04.20000.008 email not verified",
    "slot_results": [
        {
            "slot_type": "CEO",
            "person_id": "04.04.02.04.20000.007",
            "checks": {
                "is_filled": True,
                "exists_in_people": True,
                "enriched": True,
                "email_verified": True,
                "title_matches": True
            },
            "failures": [],
            "passed": True
        },
        {
            "slot_type": "CFO",
            "person_id": "04.04.02.04.20000.008",
            "checks": {
                "is_filled": True,
                "exists_in_people": True,
                "enriched": True,
                "email_verified": False,  # FAILS HERE
                "title_matches": True
            },
            "failures": [
                "Person 04.04.02.04.20000.008 email not verified"
            ],
            "passed": False
        },
        {
            "slot_type": "HR",
            "person_id": None,
            "checks": {
                "is_filled": False,  # FAILS HERE
                "exists_in_people": False,
                "enriched": False,
                "email_verified": False,
                "title_matches": False
            },
            "failures": [
                "HR slot not filled"
            ],
            "passed": False
        }
    ],
    "missing_slots": [],
    "total_checks": 15,
    "passed_checks": 10
}
```

---

## 🗄️ Database Schema

### Tables Read

**marketing.company_master**
```sql
SELECT
    company_unique_id,
    company_name,
    validation_status,
    outreach_ready,
    state
FROM marketing.company_master
WHERE company_unique_id = '04.04.02.04.30000.001';
```

**marketing.company_slot**
```sql
SELECT
    slot_type,
    is_filled,
    person_unique_id,
    filled_at,
    last_refreshed_at
FROM marketing.company_slot
WHERE company_unique_id = '04.04.02.04.30000.001'
  AND slot_type IN ('CEO', 'CFO', 'HR');
```

**marketing.people_master**
```sql
SELECT
    unique_id,
    full_name,
    email,
    title,
    linkedin_url,
    company_unique_id
FROM marketing.people_master
WHERE unique_id = '04.04.02.04.20000.001';
```

**marketing.contact_enrichment**
```sql
SELECT COUNT(*) as count
FROM marketing.contact_enrichment
WHERE person_unique_id = '04.04.02.04.20000.001'
  AND enrichment_status = 'success'
ORDER BY enriched_at DESC
LIMIT 1;
```

**marketing.email_verification**
```sql
SELECT email_status
FROM marketing.email_verification
WHERE person_unique_id = '04.04.02.04.20000.001'
ORDER BY verified_at DESC
LIMIT 1;
```

### Tables Written

**marketing.company_master** (UPDATE)
```sql
UPDATE marketing.company_master
SET outreach_ready = true,  -- or false
    updated_at = NOW()
WHERE company_unique_id = '04.04.02.04.30000.001';
```

**marketing.pipeline_events** (INSERT)
```sql
INSERT INTO marketing.pipeline_events
(event_type, payload, created_at)
VALUES (
  'outreach_readiness_check',
  '{
    "company_unique_id": "04.04.02.04.30000.001",
    "outreach_ready": true,
    "reason": "All checks passed",
    "passed_checks": 15,
    "total_checks": 15,
    "pipeline_id": "READINESS-EVAL-20251117150030"
  }',
  NOW()
);
```

**shq.audit_log** (INSERT)
```sql
INSERT INTO shq.audit_log
(component, event_type, event_data, created_at)
VALUES (
  'outreach_readiness_evaluator',
  'outreach_readiness_evaluation',
  '{
    "total_evaluated": 50,
    "outreach_ready": 42,
    "not_ready": 8,
    "pipeline_id": "READINESS-EVAL-20251117150030"
  }',
  NOW()
);
```

---

## 🚀 Usage Examples

### Single Company Evaluation

```bash
# Evaluate single company by ID
python backend/enrichment/evaluate_outreach_readiness.py \
  --company 04.04.02.04.30000.005
```

**Output:**
```
======================================================================
🚀 OUTREACH READINESS EVALUATOR - Phase 2
======================================================================
Mode: LIVE
Pipeline ID: READINESS-EVAL-20251117150030

Evaluating single company: 04.04.02.04.30000.005
✅ READY: Example LLC
   Passed: 15/15 checks

======================================================================
📊 OUTREACH READINESS EVALUATION SUMMARY
======================================================================

📈 RESULTS:
  Total Evaluated:    1
  ✅ Ready:            1
  ❌ Not Ready:        0
  📌 Already Ready:    0
  ⚠️  Not Validated:   0

🔍 FAILURE BREAKDOWN:
  Slot Not Filled:     0
  Person Not Found:    0
  Enrichment Missing:  0
  Email Not Verified:  0
  Title Mismatch:      0

⏱️  TIMING:
  Duration:           0.45s
======================================================================

✅ SUCCESS: Evaluated 1 companies
   1 companies marked outreach_ready = true

📄 Report saved to: logs/outreach_readiness_report_20251117_150030.json
```

### Batch Evaluation (All Validated WV Companies)

```bash
# Evaluate all validated West Virginia companies
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated
```

**Output:**
```
======================================================================
🚀 OUTREACH READINESS EVALUATOR - Phase 2
======================================================================
Mode: LIVE
Pipeline ID: READINESS-EVAL-20251117150030

✅ Loaded 50 validated companies

======================================================================
Evaluating 50 Companies for Outreach Readiness
======================================================================
✅ Acme Corporation: READY (15/15 checks)
✅ Example LLC: READY (15/15 checks)
❌ Test Industries: NOT READY - Person 04.04.02.04.20000.015 email not verified
   Checks: 14/15
❌ Small Corp: NOT READY - HR slot not filled
   Checks: 10/15
...

======================================================================
📊 OUTREACH READINESS EVALUATION SUMMARY
======================================================================

📈 RESULTS:
  Total Evaluated:    50
  ✅ Ready:            42
  ❌ Not Ready:        8
  📌 Already Ready:    0
  ⚠️  Not Validated:   0

🔍 FAILURE BREAKDOWN:
  Slot Not Filled:     3
  Person Not Found:    0
  Enrichment Missing:  2
  Email Not Verified:  5
  Title Mismatch:      1

⏱️  TIMING:
  Duration:           5.67s
======================================================================

✅ SUCCESS: Evaluated 50 companies
   42 companies marked outreach_ready = true

📄 Report saved to: logs/outreach_readiness_report_20251117_150030.json
```

### Dry-Run Mode (Test Without Changes)

```bash
# Test evaluation logic without updating database
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated \
  --dry-run
```

### Limit Batch Size

```bash
# Evaluate only first 10 validated companies
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated \
  --limit 10
```

### Verbose Logging

```bash
# Enable debug logging
python backend/enrichment/evaluate_outreach_readiness.py \
  --company 04.04.02.04.30000.005 \
  --verbose
```

---

## 📊 Monitoring Queries

### Check Outreach Ready Status

```sql
-- Companies ready for outreach
SELECT
    company_unique_id,
    company_name,
    state,
    validation_status,
    outreach_ready,
    updated_at
FROM marketing.company_master
WHERE state = 'WV'
  AND validation_status = 'valid'
  AND outreach_ready = true
ORDER BY updated_at DESC;
```

### Find Not-Ready Companies

```sql
-- Validated but not yet ready
SELECT
    company_unique_id,
    company_name,
    state,
    validation_status,
    outreach_ready
FROM marketing.company_master
WHERE state = 'WV'
  AND validation_status = 'valid'
  AND (outreach_ready = false OR outreach_ready IS NULL);
```

### Readiness Rate by State

```sql
-- Calculate readiness rate
SELECT
    state,
    COUNT(*) as total_validated,
    COUNT(*) FILTER (WHERE outreach_ready = true) as ready_count,
    ROUND(100.0 * COUNT(*) FILTER (WHERE outreach_ready = true) / NULLIF(COUNT(*), 0), 1) as ready_percentage
FROM marketing.company_master
WHERE validation_status = 'valid'
GROUP BY state
ORDER BY ready_percentage DESC;
```

### Recent Readiness Evaluations

```sql
-- Check recent evaluations from pipeline_events
SELECT
    payload->>'company_unique_id' as company_id,
    payload->>'outreach_ready' as ready,
    payload->>'reason' as reason,
    payload->>'passed_checks' as passed,
    payload->>'total_checks' as total,
    created_at
FROM marketing.pipeline_events
WHERE event_type = 'outreach_readiness_check'
ORDER BY created_at DESC
LIMIT 20;
```

### Failure Breakdown Analysis

```sql
-- Analyze readiness failures
SELECT
    event_data->>'failures' as failure_breakdown,
    COUNT(*) as evaluation_count
FROM shq.audit_log
WHERE component = 'outreach_readiness_evaluator'
  AND event_type = 'outreach_readiness_evaluation'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY event_data->>'failures'
ORDER BY evaluation_count DESC;
```

---

## 🔍 Troubleshooting

### Issue 1: All Companies Fail "Slot Not Filled"

**Symptom:**
```
❌ Acme Corporation: NOT READY - CEO slot not filled
   Checks: 0/15
```

**Cause:** Slots exist but `is_filled = false` or `person_unique_id IS NULL`

**Solution:**
```sql
-- Check slot fill status
SELECT
    cs.company_unique_id,
    c.company_name,
    cs.slot_type,
    cs.is_filled,
    cs.person_unique_id
FROM marketing.company_slot cs
JOIN marketing.company_master c ON cs.company_unique_id = c.company_unique_id
WHERE c.state = 'WV'
  AND cs.slot_type IN ('CEO', 'CFO', 'HR')
  AND (cs.is_filled = false OR cs.person_unique_id IS NULL);

-- If slots should be filled, run enrichment process
-- (This is typically handled by separate enrichment pipeline)
```

### Issue 2: "Person Not Found" Errors

**Symptom:**
```
❌ Example LLC: NOT READY - Person 04.04.02.04.20000.999 not found in people_master
```

**Cause:** Slot has `person_unique_id` but person doesn't exist in `people_master`

**Solution:**
```sql
-- Find orphaned slot assignments
SELECT
    cs.company_unique_id,
    cs.slot_type,
    cs.person_unique_id
FROM marketing.company_slot cs
LEFT JOIN marketing.people_master p ON cs.person_unique_id = p.unique_id
WHERE cs.is_filled = true
  AND cs.person_unique_id IS NOT NULL
  AND p.unique_id IS NULL;

-- Fix: Either create missing person record or unfill the slot
UPDATE marketing.company_slot
SET is_filled = false,
    person_unique_id = NULL
WHERE person_unique_id = '04.04.02.04.20000.999';
```

### Issue 3: "Enrichment Missing" Errors

**Symptom:**
```
❌ Test Corp: NOT READY - Person 04.04.02.04.20000.050 missing enrichment data
```

**Cause:** Person exists but no successful enrichment record

**Solution:**
```sql
-- Check enrichment status
SELECT
    p.unique_id,
    p.full_name,
    ce.enrichment_status,
    ce.enriched_at,
    ce.error_message
FROM marketing.people_master p
LEFT JOIN marketing.contact_enrichment ce ON p.unique_id = ce.person_unique_id
WHERE p.unique_id = '04.04.02.04.20000.050'
ORDER BY ce.enriched_at DESC
LIMIT 1;

-- If enrichment failed, check error and retry
-- If never enriched, trigger enrichment process
```

### Issue 4: "Email Not Verified" Errors

**Symptom:**
```
❌ Small LLC: NOT READY - Person 04.04.02.04.20000.033 email not verified
```

**Cause:** Email verification status is not 'valid'

**Solution:**
```sql
-- Check email verification status
SELECT
    p.unique_id,
    p.full_name,
    p.email,
    ev.email_status,
    ev.verified_at,
    ev.verification_error
FROM marketing.people_master p
LEFT JOIN marketing.email_verification ev ON p.unique_id = ev.person_unique_id
WHERE p.unique_id = '04.04.02.04.20000.033'
ORDER BY ev.verified_at DESC
LIMIT 1;

-- If verification failed, check error and retry
-- If never verified, trigger email verification process
```

### Issue 5: "Title Mismatch" Errors

**Symptom:**
```
❌ Demo Corp: NOT READY - Person title 'Manager' does not match CEO
```

**Cause:** Person's title doesn't contain role keywords (CEO/CFO/HR)

**Solution:**
```sql
-- Check title mismatches
SELECT
    cs.company_unique_id,
    cs.slot_type,
    p.unique_id,
    p.full_name,
    p.title
FROM marketing.company_slot cs
JOIN marketing.people_master p ON cs.person_unique_id = p.unique_id
WHERE cs.is_filled = true
  AND (
    (cs.slot_type = 'CEO' AND p.title NOT ILIKE '%ceo%' AND p.title NOT ILIKE '%chief executive%')
    OR (cs.slot_type = 'CFO' AND p.title NOT ILIKE '%cfo%' AND p.title NOT ILIKE '%chief financial%')
    OR (cs.slot_type = 'HR' AND p.title NOT ILIKE '%hr%' AND p.title NOT ILIKE '%human resources%'
        AND p.title NOT ILIKE '%people%' AND p.title NOT ILIKE '%talent%')
  );

-- Fix: Update person title or reassign slot to correct person
UPDATE marketing.people_master
SET title = 'Chief Executive Officer'
WHERE unique_id = '04.04.02.04.20000.xxx';
```

---

## 📚 Related Documentation

- **Phase 1 Validation:** `PHASE1_VALIDATION_SUMMARY.md`
- **Retroactive Validation:** `RETROACTIVE_VALIDATION_GUIDE.md`
- **Complete Implementation:** `COMPLETE_VALIDATION_IMPLEMENTATION.md`
- **Validation Rules Module:** `backend/validator/validation_rules.py`
- **Outreach Readiness Evaluator:** `backend/enrichment/evaluate_outreach_readiness.py`

---

## 🎯 Integration with Pipeline

### Upstream Dependencies

**Phase 1 (Validation):**
- Company must pass Phase 1 validation (`validation_status = 'valid'`)
- All 3 slots (CEO, CFO, HR) must exist as records

**Enrichment Process:**
- Slots must be filled (`is_filled = true`, `person_unique_id != NULL`)
- Contact enrichment must run successfully
- Email verification must complete successfully

### Downstream Actions

**If `outreach_ready = true`:**
1. **BIT (Buyer Intent Tool)** can generate signals
2. **Outbound campaigns** can be triggered
3. **Personalization engines** can generate content
4. **Sales sequences** can be initiated

**If `outreach_ready = false`:**
1. Route to **manual review queue**
2. Trigger **enrichment retry** for missing data
3. Alert **data quality team** for title mismatches
4. Log to **pipeline_events** for tracking

---

## 🎊 Key Features

✅ **5 Comprehensive Checks Per Slot** (15 total per company)
✅ **Title Matching Logic** for CEO, CFO, HR roles
✅ **Detailed Failure Reasons** for actionable insights
✅ **Batch Processing** for validated companies by state
✅ **Database Updates** (`outreach_ready` field)
✅ **Complete Audit Trail** (pipeline_events + audit_log)
✅ **Dry-Run Mode** for testing without changes
✅ **JSON Report Generation** for offline analysis
✅ **Statistics Tracking** (ready, not ready, failure breakdown)
✅ **Production-Grade Error Handling** with graceful degradation

---

**Date:** 2025-11-17
**Status:** ✅ Production Ready
**Tests:** 5/5 passing
**Total Code:** 650+ lines (main + tests)
**Maintainer:** Barton Outreach Core Team

