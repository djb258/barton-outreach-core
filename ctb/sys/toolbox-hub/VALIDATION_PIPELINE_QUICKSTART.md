# Validation Pipeline Quick Start Guide

**Purpose:** End-to-end guide for running Phase 1 + Phase 2 validation
**Status:** ✅ Production Ready
**Date:** 2025-11-17

---

## 📋 Pipeline Overview

```
                    VALIDATION PIPELINE
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Phase 1: Validation                                    │
│  ├─ Structure validation (5 rules)                      │
│  ├─ Slot presence (CEO, CFO, HR exist)                  │
│  └─ Output: validation_status = "valid"                 │
│                                                         │
│                      ↓                                  │
│                                                         │
│  Phase 2: Outreach Readiness                            │
│  ├─ Slot fills (15 checks total)                        │
│  ├─ Enrichment verification                             │
│  ├─ Email verification                                  │
│  ├─ Title matching                                      │
│  └─ Output: outreach_ready = true                       │
│                                                         │
│                      ↓                                  │
│                                                         │
│  Phase 3: Outreach Campaigns (Future)                   │
│  ├─ BIT signal generation                               │
│  ├─ Outbound campaigns                                  │
│  └─ Personalization engines                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Run Phase 1 Validation

**Purpose:** Validate company structure and ensure slots exist

```bash
# Validate all West Virginia companies
python backend/validator/retro_validate_neon.py --state WV

# Test first (dry-run mode)
python backend/validator/retro_validate_neon.py --state WV --dry-run

# Limit batch size for testing
python backend/validator/retro_validate_neon.py --state WV --limit 10
```

**Expected Output:**
```
✅ Loaded 150 companies from WV
✅ Valid: 145 companies
❌ Invalid: 5 companies (routed to Google Sheets)
```

**Database Changes:**
- `validation_status = 'valid'` for passing companies
- `validation_status = 'invalid'` for failing companies
- Logged to `pipeline_events` and `audit_log`

---

### Step 2: Run Phase 2 Outreach Readiness

**Purpose:** Check slot fills, enrichment, email verification, title matching

```bash
# Evaluate all validated WV companies
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated

# Test first (dry-run mode)
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated \
  --dry-run

# Limit batch size
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated \
  --limit 10
```

**Expected Output:**
```
✅ Loaded 145 validated companies
✅ Ready: 120 companies (15/15 checks passed)
❌ Not Ready: 25 companies (failures logged)

Failure Breakdown:
  Slot Not Filled: 10
  Enrichment Missing: 8
  Email Not Verified: 5
  Title Mismatch: 2
```

**Database Changes:**
- `outreach_ready = true` for passing companies
- `outreach_ready = false` for failing companies
- Logged to `pipeline_events` and `audit_log`

---

### Step 3: Query Ready Companies

**Purpose:** Get list of companies ready for outreach

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

**Use These Companies For:**
- BIT (Buyer Intent Tool) signal generation
- Outbound email campaigns
- Personalization engines
- Sales sequence automation

---

## 📊 Complete Workflow Example

### Scenario: Validate and Promote 50 WV Companies

```bash
# 1. Phase 1: Validate structure
echo "=== PHASE 1: VALIDATION ==="
python backend/validator/retro_validate_neon.py \
  --state WV \
  --limit 50

# Output: 47 valid, 3 invalid

# 2. Phase 2: Check outreach readiness
echo ""
echo "=== PHASE 2: OUTREACH READINESS ==="
python backend/enrichment/evaluate_outreach_readiness.py \
  --state WV \
  --only-validated \
  --limit 50

# Output: 42 ready, 5 not ready

# 3. Query results
echo ""
echo "=== RESULTS ==="
psql $NEON_CONNECTION_STRING -c "
SELECT
    COUNT(*) FILTER (WHERE validation_status = 'valid') as validated,
    COUNT(*) FILTER (WHERE outreach_ready = true) as ready_for_outreach
FROM marketing.company_master
WHERE state = 'WV';
"
```

**Expected Final State:**
```
         validated | ready_for_outreach
-------------------+--------------------
                47 |                 42
```

---

## 🎯 Phase Comparison

### Phase 1: Validation

| Check | Requirement | Failure Action |
|-------|------------|----------------|
| company_name | >= 3 characters | Route to Google Sheets |
| website | Starts with http/https | Route to Google Sheets |
| employee_count | > 50 | Route to Google Sheets |
| linkedin_url | Contains "linkedin.com/company/" | Route to Google Sheets |
| Slot presence | CEO, CFO, HR exist | Route to Google Sheets |

**Output:** `validation_status = 'valid'` or `'invalid'`

---

### Phase 2: Outreach Readiness

| Check (per slot) | Requirement | Failure Action |
|------------------|------------|----------------|
| Slot filled | is_filled = true, person_unique_id != NULL | Mark not ready |
| Person exists | Record in people_master | Mark not ready |
| Enrichment | enrichment_status = 'success' | Mark not ready |
| Email verified | email_status = 'valid' | Mark not ready |
| Title match | CEO/CFO/HR keywords in title | Mark not ready |

**Output:** `outreach_ready = true` or `false`
**Total Checks:** 5 checks × 3 slots = 15 checks per company

---

## 🗄️ Database State Tracking

### Check Validation Status

```sql
-- Summary by state
SELECT
    state,
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE validation_status = 'valid') as validated,
    COUNT(*) FILTER (WHERE outreach_ready = true) as ready
FROM marketing.company_master
GROUP BY state
ORDER BY ready DESC;
```

### Find Companies Needing Attention

```sql
-- Validated but not ready (need enrichment/verification)
SELECT
    company_unique_id,
    company_name,
    validation_status,
    outreach_ready
FROM marketing.company_master
WHERE validation_status = 'valid'
  AND (outreach_ready = false OR outreach_ready IS NULL)
  AND state = 'WV'
ORDER BY updated_at DESC
LIMIT 20;
```

### Track Pipeline Progress

```sql
-- Recent validation + readiness checks
SELECT
    event_type,
    payload->>'company_unique_id' as company_id,
    payload->>'reason' as result,
    created_at
FROM marketing.pipeline_events
WHERE event_type IN ('validation_check', 'outreach_readiness_check')
  AND created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 50;
```

---

## 🔍 Troubleshooting Common Issues

### Issue 1: "No companies to evaluate" in Phase 2

**Cause:** No companies have `validation_status = 'valid'`

**Solution:**
```bash
# Run Phase 1 first
python backend/validator/retro_validate_neon.py --state WV

# Then run Phase 2
python backend/enrichment/evaluate_outreach_readiness.py --state WV --only-validated
```

---

### Issue 2: All companies fail Phase 2 with "Slot Not Filled"

**Cause:** Slots exist but not filled with people

**Solution:**
```sql
-- Check slot fill status
SELECT
    cs.slot_type,
    cs.is_filled,
    cs.person_unique_id,
    COUNT(*) as count
FROM marketing.company_slot cs
JOIN marketing.company_master c ON cs.company_unique_id = c.company_unique_id
WHERE c.state = 'WV'
  AND c.validation_status = 'valid'
  AND cs.slot_type IN ('CEO', 'CFO', 'HR')
GROUP BY cs.slot_type, cs.is_filled, cs.person_unique_id;
```

**If slots unfilled:** Run enrichment process to fill slots

---

### Issue 3: "Enrichment Missing" errors

**Cause:** People exist but no enrichment records

**Solution:**
```sql
-- Find people without enrichment
SELECT
    p.unique_id,
    p.full_name,
    p.email,
    ce.enrichment_status
FROM marketing.people_master p
LEFT JOIN marketing.contact_enrichment ce ON p.unique_id = ce.person_unique_id
WHERE ce.enrichment_status IS NULL
  OR ce.enrichment_status != 'success'
ORDER BY p.created_at DESC
LIMIT 20;
```

**Action:** Trigger enrichment process for these people

---

### Issue 4: "Email Not Verified" errors

**Cause:** Email verification not run or failed

**Solution:**
```sql
-- Check email verification status
SELECT
    p.unique_id,
    p.email,
    ev.email_status,
    ev.verified_at
FROM marketing.people_master p
LEFT JOIN marketing.email_verification ev ON p.unique_id = ev.person_unique_id
WHERE ev.email_status IS NULL
  OR ev.email_status != 'valid'
ORDER BY p.created_at DESC
LIMIT 20;
```

**Action:** Trigger email verification process

---

## 📚 Documentation Reference

### Phase 1 Documentation
- **COMPLETE_VALIDATION_IMPLEMENTATION.md** - Complete implementation chronicle
- **PHASE1_VALIDATION_SUMMARY.md** - Phase 1 API reference
- **VALIDATE_COMPANY_FINAL.md** - Function specification
- **RETROACTIVE_VALIDATION_GUIDE.md** - User guide
- **RETRO_INTEGRATION_COMPLETE.md** - Integration details

### Phase 2 Documentation
- **PHASE2_OUTREACH_READINESS.md** - Complete Phase 2 guide
- **evaluate_outreach_readiness.py** - Source code
- **test_readiness.py** - Unit tests

---

## 🎯 Best Practices

### 1. Always Test with Dry-Run First
```bash
# Phase 1 dry-run
python backend/validator/retro_validate_neon.py --state WV --dry-run

# Phase 2 dry-run
python backend/enrichment/evaluate_outreach_readiness.py --state WV --only-validated --dry-run
```

### 2. Start with Small Batches
```bash
# Test with 10 companies
python backend/validator/retro_validate_neon.py --state WV --limit 10
python backend/enrichment/evaluate_outreach_readiness.py --state WV --only-validated --limit 10
```

### 3. Monitor Pipeline Events
```sql
-- Check recent pipeline activity
SELECT
    event_type,
    COUNT(*) as count,
    MAX(created_at) as last_run
FROM marketing.pipeline_events
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY event_type
ORDER BY last_run DESC;
```

### 4. Review Audit Logs
```sql
-- Check audit trail
SELECT
    component,
    event_type,
    event_data,
    created_at
FROM shq.audit_log
WHERE component IN ('retro_validator', 'outreach_readiness_evaluator')
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🚦 Production Deployment Checklist

**Before Running in Production:**

- [ ] Environment variables set (NEON_CONNECTION_STRING)
- [ ] Dry-run tests completed successfully
- [ ] Small batch tests (10-20 companies) verified
- [ ] Database backups created
- [ ] Pipeline events table has space
- [ ] Audit log table has space
- [ ] Google Sheets webhooks configured (Phase 1 only)
- [ ] Enrichment process configured (for Phase 2 failures)
- [ ] Email verification process configured (for Phase 2 failures)
- [ ] Monitoring queries ready
- [ ] Team notified of deployment

**After Running:**

- [ ] Check validation_status field updates
- [ ] Check outreach_ready field updates
- [ ] Review pipeline_events logs
- [ ] Review audit_log entries
- [ ] Check Google Sheets for invalid records (Phase 1)
- [ ] Review failure breakdown statistics
- [ ] Verify ready companies count matches expectations
- [ ] Save JSON reports for offline analysis

---

## ⏱️ Performance Estimates

**Phase 1 (Structure Validation):**
- ~50 companies: 5-10 seconds
- ~500 companies: 30-60 seconds
- ~1000 companies: 1-2 minutes

**Phase 2 (Outreach Readiness):**
- ~50 companies: 10-20 seconds (includes 5 database lookups per company)
- ~500 companies: 2-4 minutes
- ~1000 companies: 4-8 minutes

**Combined Pipeline:**
- ~50 companies: 15-30 seconds total
- ~500 companies: 2-5 minutes total
- ~1000 companies: 5-10 minutes total

---

**Last Updated:** 2025-11-17
**Status:** ✅ Production Ready
**Maintainer:** Barton Outreach Core Team

